# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import openerp.netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class micronaet_invoice_line(osv.osv):
    _name = 'micronaet.invoice.line'
    _description = 'Invoice line'
    _order = 'date'

    _columns = {
        'name': fields.char('Invoice number', size=10, required=True),
        'partner': fields.char('Invoice number', size=9, required=False),
        'price': fields.char('Invoice number', size=15, required=False),
        'quantity': fields.char('Invoice number', size=10, required=False),
        'product': fields.char('Invoice number', size=10, required=False),
        'date': fields.char('Invoice number', size=10, required=False),
    }

# Product pricelist from model to generated:
class product_pricelist_generator(osv.osv_memory):
    """ Product pricelist generator 
        Copy an inactive pricelist creating a new pricelist with all product and
        calculate the price with actual pricelist rules
    """
    _name = "product.pricelist.generator"
    _description = "Product pricelist generator"

    _columns = {
        'pricelist_org_id': fields.many2one('product.pricelist', 'Original pricelist', required=True, help="Choose original pricelist used to calculate new complete pricelist/version"),
        'new': fields.boolean('New', required=False, help="Generate a new pricelist with this name"),
        'new_name': fields.char('New version name', size=64),
        'pricelist_des_id': fields.many2one('product.pricelist', 'Destination pricelist', required=False, help="If no new pricelist, use this pricelist to upgrade fields"),
    }

    _defaults = {
        'new': lambda *x: True,
    }

    def do_create_update(self, cr, uid, ids, context=None):
        """
        Create or update pricelist
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of ids
        
        @return: Action dictionary
        """
        
        if context is None:
           context = {}
           
        pricelist_pool = self.pool.get('product.pricelist')
        product_pool = self.pool.get('product.product')
        wiz_browse = self.browse(cr, uid, ids[0], context = context)
        pricelist_ref_id = wiz_browse.pricelist_org_id.id

        if wiz_browse.new: # per ora facciamo questo
            if not wiz_browse.new_name: # TODO and duplicated!
                # TODO comunicate error!
                return {'type': 'ir.actions.act_window_close'}
              
            # Create new pricelist and pricelist version
            pricelist_id = pricelist_pool.create(cr, uid, {
                'name': wiz_browse.new_name, 
                'type': 'sale',
                'tipology': 'historical',
                'currency_id': wiz_browse.pricelist_org_id.currency_id and wiz_browse.pricelist_org_id.currency_id.id,
            })
            
            if pricelist_id:
                version_id = self.pool.get('product.pricelist.version').create(cr, uid, {
                    'name': "Versione: %s definitiva" % (wiz_browse.new_name, ),
                    'pricelist_id': pricelist_id,
                    #'date_end': False, 'date_start': False, 'company_id': False, 'active': True, 
                })
            else:
                pass # TODO comunicate error                                                                                 
        else: # Update pricelist
            # Get pricelist and pricelist version            
            pricelist_id = 0
            version_id = 0
        if pricelist_id and version_id and wiz_browse.pricelist_org_id: # devono essere creati o trovati i listino/versione e deve esistere l'origine
            product_ids = product_pool.search(cr, uid, [('in_pricelist', '=', True)], context = context)
            for product in product_pool.browse(cr, uid, product_ids, context = context):
                price_calc = pricelist_pool.price_get(cr, uid, [pricelist_ref_id], product.id, 1.0, False, {'uom': False, 'date': False, })[pricelist_ref_id]
                            
                self.pool.get('product.pricelist.item').create(cr, uid, {
                    'price_round': 0.00001, 
                    'price_discount': 0.0, # 0.052600000000000001,
                    'sequence': 200, 
                    'price_max_margin': 0.0, 
                    'product_id': product.id, 
                    'base': 1, 
                    'price_version_id': version_id,  # [3, 'Rif. anno 2011'], 
                    'min_quantity': 1, 
                    'price_surcharge': price_calc,   # TODO Calcolare in funzione del listino
                    'name': "[%s] %s" % (product.code, product.name),
                    #'company_id': False, 'product_tmpl_id': False, 'base_pricelist_id': False, 'price_min_margin': 0.0, 'categ_id': False,
                })
        else:
            pass # TODO comunicate error!
        return {'type': 'ir.actions.act_window_close'}

# Product pricelist for customer:
class product_pricelist_customer(osv.osv_memory):
    """ Product pricelist generator for customers
    """
    _name = "product.pricelist.customer"
    _description = "Product pricelist customer"

    # Button events:
    # --------------
    def update_stock_info(self, cr, uid, ids, context=None):
        ''' Button for refresh stock fields for analysis
        '''
        if context is None:
            context = {}
            
        # ---------------------------------------------------------------------
        #                        Load Stock information
        # ---------------------------------------------------------------------
        stock_pool = self.pool.get('product.pricelist.customer.stock')
        product_pool = self.pool.get('product.product')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        order_line_pool = self.pool.get("sale.order.line")

        product_id = context.get('product_id', False)    

        # ------------
        # Delete list:
        # ------------
        try:
            stock_ids = stock_pool.search(cr, uid, [
                ('wizard_id', '=', ids[0])], context=context)
            stock_pool.unlink(cr, uid, stock_ids, context=context)
        except:
            pass    

        # ----------------
        # Create new list:
        # ----------------
        if product_id:
            product_proxy = product_pool.browse(cr, uid, product_id, context=context)
            availability = product_proxy.accounting_qty or 0.0

            # Startup value from accounting (today):
            stock_pool.create(cr, uid, {
                'name': _("Accounting today"),
                'wizard_id': ids[0],
                'today': True,
                'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
                'quantity': availability,     # same first time
                'availability': availability,
                }, context=context)                
        else:
            availability = 0.0
             
        # --------------------
        # Lavoration elements:
        # --------------------
        lavoration_ids = lavoration_pool.search(cr, uid, [
            ('state', 'not in', ['cancel', 'done']),
            ('product', '=', product_id),
            ], order='real_date_planned', context=context)
        for lavoration in lavoration_pool.browse(cr, uid, lavoration_ids, context=context):
            stock_pool.create(cr, uid, {
                'name': lavoration.name,
                'wizard_id': ids[0],
                'date': lavoration.real_date_planned[:10],
                'quantity': lavoration.product_qty,     # same first time
                'increment': True,
                }, context=context)                
        
        # ---------------
        # Order delivery:
        # ---------------
        line_ids = order_line_pool.search(cr, uid, [
            ('product_id', '=', product_id),
            ], context=context)
        for line in order_line_pool.browse(cr, uid, line_ids, context=context):
        
            stock_pool.create(cr, uid, {
                'name': _("OC/%s [%s]") % (line.order_id.name, line.order_id.date_order),
                'wizard_id': ids[0],
                'date': line.date_deadline,
                'quantity': line.product_uom_qty or 0.0 , # TODO UM???
                'increment': False,
                }, context=context)                
        
        
        # -----------------------------
        # Recalculate for availability:
        # -----------------------------
        item_ids = stock_pool.search(cr, uid, [
            ('wizard_id', '=', ids[0]),
            ('today', '=', False),
            ], order='date', context=context)

        for item in stock_pool.browse(cr, uid, item_ids, context=context):
            if item.increment:
                availability += item.quantity
            else:    
                availability -= item.quantity
                
            stock_pool.write(cr, uid, item.id, {
                'availability': availability,
                }, context=context)
        
        return {
            'view_type': 'form',
            'view_mode': 'form', # ,tree',
            'res_model': 'product.pricelist.customer',
            #'views': [(False, 'tree'),(False, 'form')], # Put ID on False
            #'view_id': view_id,
            'type': 'ir.actions.act_window',
            #'name': "Import wizard",
            'res_id': ids[0], # Record
            'target': 'new',
            'nodestroy': True, # Preserve window (return same record)
            'context': {
                'default_product_id': context.get('product_id', False),
                'default_partner_id': context.get('partner_id', False),
                }, 
        }

    # ---------------
    # Field function:
    # ---------------
    def _get_product_productions(self, cr, uid, ids, field_names, arg=None, context=None):
        ''' Simulation of production one2many searching open production
            
        '''
        if context is None:
            context = {}
            
        res = {}
        product_id = context.get('product_id', False)
        lavoration_pool = self.pool.get('mrp.production')
        lavoration_ids = lavoration_pool.search(cr, uid, [
            ('accounting_state','not in',['cancel', 'close']),
            ('product_id', '=', product_id),
            ], context=context)
        lavoration_proxy = lavoration_pool.browse(cr, uid, lavoration_ids, context=context)
                
        res[ids[0]] = [item.id for item in lavoration_proxy] # all record in one ids
        return res
    
    #def _get_product_lavorations(self, cr, uid, ids, field_names, arg=None, context=None):
    #    '''
    #    '''
    #    res = {}
    #    if len(ids) > 1: print "Funzione:", ids# TODO eliminare
    #    lavoration_pool = self.pool.get('mrp.production.workcenter.line')
    #    lavoration_ids = lavoration_pool.search(cr, uid, [
    #        ('state','not in',['cancel', 'close']),
    #        ], context=context)
    #    lavoration_proxy = lavoration_pool.browse(cr, uid, lavoration_ids, context=context)
    #            
    #    res[ids[0]] = [item.id for item in lavoration_proxy] # all record in one ids
    #    return res
    
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=False,
            help="Choose partner to create custom pricelist or add quotations"),
        'comment': fields.char('Comment', size=64, 
            help="Need to be created or updated"),        
        'product_id': fields.many2one('product.product', 'Product'),
        'pricelist_id': fields.many2one('product.pricelist', 'Current pricelist', 
            help="Choose original pricelist used to calculate new complete pricelist/version"),
        'pricelist_model_history_id': fields.many2one('product.pricelist', 
            'Reference pricelist', 
            help="Listino di riferimento applicato nel caso mancassero degli "
                " articoli nel listino di base (usato per avere un raffronto "
                "nel caso esistessero particolarita'"),
        'pricelist_model_id': fields.many2one('product.pricelist', 
            'Compare pricelist', 
            help="Listino di paragone per avere un raffronto con il prezzo attuale del prodotto"),
        'price': fields.float('Customer pricelist', digits=(16, 5)),
        'price_model_history': fields.float('Reference pricelist', 
            digits=(16, 5)),
        'price_model': fields.float('Compare price', digits=(16, 5)),
        'price_history': fields.text('Historycal price'),
        'price_invoice_history': fields.text('Historical invoiced'),
        
        # Production info:
        'production_ids': fields.function(_get_product_productions,
            method=True, type='one2many', relation='mrp.production', 
            string='Production'),
        #'lavoration_ids': fields.function(_get_product_lavorations, 
        #    method=True, type='one2many', 
        #    relation='mrp.production.workcenter.line', 
        #    string='Lavoration'),
    }

    # -------------------
    # On change function:
    # -------------------
    def onchange_pricelist(self, cr, uid, ids, pricelist_id, product_id, context = None):
        ''' Read price from pricelist for product
        '''
        if context is None:
            context = {}
        
        res={'value': {}}
        if pricelist_id and product_id: # cerco il listino
            res['value']['price'] = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], product_id , 1.0, False, {'uom': False, 'date': False,})[pricelist_id]
            return res # fino a qui per ora
        #Azzero il prezzo
        return {'value': {'price': False,}}

    def onchange_partner_pricelist(self, cr, uid, ids, partner_id, pricelist_id, product_id, context = None):
        '''Create a new pricelist if not custom
           add custom price
           add old version as reference
        '''
        if context is None:
            context = {}
        
        res = {'value': {}}
        if partner_id: # cerco il listino
            partner=self.pool.get("res.partner").browse(cr, uid, partner_id)
            partner_pricelist_id = partner.property_product_pricelist.id or False

            if not pricelist_id: # pricelist_id only if not passed (to keep the change)
                pricelist_id = partner_pricelist_id 
           
            res['value']['pricelist_id'] = pricelist_id
            res['value']['pricelist_model_history_id'] = partner.pricelist_model_history_id.id or False
            res['value']['pricelist_model_id'] = partner.pricelist_model_id.id or False
            return res # fino a qui per ora

        return {'value': {}}
              
    def onchange_partner_pricelist_product(self, cr, uid, ids, partner_id, pricelist_id, product_id, pricelist_model_history_id, pricelist_model_id, context = None):
        '''Create a new pricelist if not custom
           add custom price
           add old version as reference
        '''
        if context is None:
           context = {}
        
        res = {'value': {}}

        if product_id and pricelist_id: # cerco il listino
            res['value']['price'] = self.pool.get('product.pricelist').price_get(
                cr, uid, [pricelist_id], product_id , 1.0, False, 
                {'uom': False, 'date': False,})[pricelist_id] if pricelist_id else ""
                
            res['value']['price_model_history'] = self.pool.get('product.pricelist').price_get(
                cr, uid, [pricelist_model_history_id], product_id , 1.0, False, 
                {'uom': False, 'date': False,})[pricelist_model_history_id] if pricelist_model_history_id else ""
                
            res['value']['price_model'] = self.pool.get('product.pricelist').price_get(
                cr, uid, [pricelist_model_id], product_id , 1.0, False, 
                {'uom': False, 'date': False,})[pricelist_model_id] if pricelist_model_id else ""

            # --------------
            # Order history:
            # --------------
            order_line_ids = self.pool.get('sale.order.line').search(
                cr, uid, [('product_id', '=', product_id), ('order_partner_id', '=', partner_id)]) 
            if order_line_ids:
                list_quotation = "%20s%20s%20s%40s\n" % (
                    "Data", "Ordine", "Prezzo", "Commento")            
 
                for line in self.pool.get('sale.order.line').browse(cr, uid, order_line_ids):
                    list_quotation += "%20s%20s%20s%40s\n" % (
                        datetime.strptime(line.order_id.date_order, '%Y-%m-%d').strftime('%d/%m/%Y'), 
                        line.order_id.name, 
                        line.price_unit, 
                        line.price_comment or "")
                res['value']['price_history'] = list_quotation
            else:
                res['value']['price_history'] = ""
 
            # ----------------
            # Invoice history:
            # ----------------
            product_proxy = self.pool.get('product.product').browse(cr, uid, product_id)
            product_code = product_proxy.code      # "C3114409"
            partner_proxy = self.pool.get('res.partner').browse(cr, uid, partner_id)
            partner_code = partner_proxy.mexal_c   # "230.00179" # TODO parametrizzare
            invoice_line_ids = self.pool.get('micronaet.invoice.line').search(
                cr, uid, [('product','=',product_code),('partner','=',partner_code)]) 
            if invoice_line_ids:
                list_quotation="%20s%20s%20s%20s\n"%("Data", "Fattura", "Prezzo", "Q.")            

                for line in self.pool.get('micronaet.invoice.line').browse(cr, uid, invoice_line_ids):
                    list_quotation += "%20s%20s%20s%20s\n" % (
                        datetime.strptime(line.date, '%Y%m%d').strftime('%d/%m/%Y'), 
                        line.name, 
                        line.price, 
                        line.quantity)
                res['value']['price_invoice_history'] = list_quotation
            else:
                res['value']['price_invoice_history'] = ""
            return res
           
        return { # All reset
            'value': {
                'price': False,
                'price_model_history': False,
                'price_model': False,
                'price_history': False,                          
                'price_invoice_history': False,                          
                }
            }

    # ---------------
    # event function:
    # ---------------
    def do_insert_quotation(self, cr, uid, ids, context=None):
       """
       Create or update pricelist if non custom and add personalization
       @param cr: the current row, from the database cursor,
       @param uid: the current user’s ID for security checks,
       @param ids: List of ids
       @return: Dictionary {}
       """
       
       if context is None:
          context={}

       wiz_browse = self.browse(cr, uid, ids[0], context=context)        
       customer_proxy=self.pool.get('res.partner').browse(cr, uid, wiz_browse.partner_id.id) 
       pricelist_org_id = wiz_browse.pricelist_id.id # old pricelist set up
       pricelist_proxy=self.pool.get('product.pricelist').browse(cr, uid, pricelist_org_id)
        
       if not pricelist_proxy.customized: # Create customized and first rule
          update=False
          pricelist_ref_id=self.pool.get('product.pricelist').create(cr, uid, {
              'name': "Personal: " + customer_proxy.name, 
              'type': 'sale',
              'customized': True,
              # TODO currency 
          })
          if pricelist_ref_id:
              version_ref_id=self.pool.get('product.pricelist.version').create(cr, uid, {
                  'name': "From " + customer_proxy.property_product_pricelist.name,
                  #'date_end': False, 
                  #'date_start': False, 
                  #'company_id': False, 
                  #'active': True, 
                  'pricelist_id': pricelist_ref_id, #appena creato
              })
          else:
              pass # TODO comunicate error                                                                                 
                                                                           
       else: # yet custom pricelist
          update=True
          pricelist_ref_id = customer_proxy.property_product_pricelist.id           
          version_ref_id = customer_proxy.property_product_pricelist.version_id[0].id # TODO take the first for now!
           
       if not (pricelist_ref_id and version_ref_id):
           # TODO comunicate error!
           return {'type': 'ir.actions.act_window_close'}
           
       pricelist_item_pool = self.pool.get('product.pricelist.item')
       # Creo l'ultima regola per prendere come riferimento il listino precedente
       if not update: # Create ref. pricelist only for first new!
           rule_id = pricelist_item_pool.create(cr, uid, {
               'price_round': 0.00001, 
               'price_discount': 0.0, #0.052600000000000001, 
               'sequence': 500,  # ultima
               'price_max_margin': 0.0, 
               'base': 2,  # pricelist version
               'price_version_id': version_ref_id, #owner version
               'min_quantity': 1, 
               'price_surcharge': 0.0, 
               'base_pricelist_id': pricelist_ref_id,
               'name': "Listino rif: " + customer_proxy.property_product_pricelist.name,
           })
       # Creo la regola in base a prezzo e prodotto attuale
       # TODO cercare se esiste già!!!!!
       rule_id = pricelist_item_pool.create(cr, uid, {
           'price_round': 0.00001, 
           'price_discount': 0.0,    # 0.052600000000000001, 
           'sequence': 10,           # tra le prime
           'price_max_margin': 0.0, 
           'product_id': wiz_browse.product_id.id, 
           'base': 1,
           'price_version_id': version_ref_id,
           'min_quantity': 1, 
           'price_surcharge': wiz_browse.price,
           'name': "[%s] %s" % (wiz_browse.product_id.code, wiz_browse.product_id.name),
       })
       # Set up partner with new pricelist                                     
       self.pool.get('res.partner').write(
           cr, uid, [wiz_browse.partner_id.id], {'property_product_pricelist': pricelist_ref_id,})
       #price_calc=self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_ref_id], product['id'], 1.0, False, {'uom': False, 'date': False,})[pricelist_ref_id]
       return {'type': 'ir.actions.act_window_close'}

class product_pricelist_customer_stock(osv.osv_memory):
    """ Product pricelist generator for customers
    """
    _name = "product.pricelist.customer.stock"
    _description = "Product status"
    _order = 'seq,date'
    
    _columns = {
        'name': fields.char('Description', size=64),
        'wizard_id': fields.many2one('product.pricelist.customer', 'Wizard', required=False),
        'seq': fields.integer('Seq.'),
        'today': fields.boolean('Today'),
        'increment': fields.boolean('Increment', 
            help="Quantity value increment stock else decrement"),
        'date': fields.date('Date'),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'availability': fields.float('Availability', digits=(16, 2), 
            help="Availability depend on order and productions"),
    }
    
    _defaults = {
        'date': lambda *a: datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
        'today': lambda *x: False,
    }

class product_pricelist_customer(osv.osv_memory):
    """ Product pricelist generator for customers
    """
    _name = "product.pricelist.customer"
    _inherit = "product.pricelist.customer"

    _columns = {
        'stock_status_ids': fields.one2many('product.pricelist.customer.stock',
            'wizard_id', 'Stock status', required=False),        
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
