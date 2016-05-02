# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
from openerp.osv import fields, osv
import logging

_logger = logging.getLogger(__name__)

class sale_order_line(osv.osv):
    ''' Extra field in order line
    '''
    _inherit = "sale.order.line"
    
    _columns = {
        'partner_id': fields.related('order_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True),
        'price_comment': fields.text("Price comment", help = "Extra comment about price used in this quotation")
    }

class res_partner_pricelist_product(osv.osv):
    ''' Pricelist product usually order for partner
    '''
    _inherit = 'res.partner.pricelist.product'

    # ----------------
    # Pricelist values
    # ----------------
    def _get_price_from_pricelist(self, cr, uid, ids, field_name, arg, context = None):
        ''' Calculate all pricelist version set up in partner
        '''
        if context is None:
            context = {}
            
        res = {}
        partner_id = context.get('default_partner_id', False)
        pricelist = {
            'pricelist1': False,
            'pricelist2': False,
            'pricelist3': False,
        }
        
        if partner_id:
            partner_pool = self.pool.get('res.partner')
            partner_proxy = partner_pool.browse(cr, uid, partner_id, context = context)
            pricelist['pricelist1'] = partner_proxy.property_product_pricelist.id if partner_proxy.property_product_pricelist else False
            pricelist['pricelist2'] = partner_proxy.pricelist_model_id.id if partner_proxy.pricelist_model_id else False
            pricelist['pricelist3'] = partner_proxy.pricelist_model_history_id.id if partner_proxy.pricelist_model_history_id else False

        pricelist_pool = self.pool.get('product.pricelist')
        for item in self.browse(cr, uid, ids, context = context):
            res[item.id] = {}
            for field in pricelist:
                if pricelist[field]:
                    res[item.id][field] = pricelist_pool.price_get(
                        cr, uid, [pricelist[field]], item.product_id.id, 1.0, False, {
                            'uom': False,    # uom
                            'date': False,   # date_order,
                        })[pricelist[field]]
                else:
                    res[item.id][field] = 0.0
        return res
           

    _columns = {
        'in_pricelist': fields.boolean('In pricelist'),
        'pricelist1': fields.function(
            _get_price_from_pricelist, method = True, type = 'float', string = 'Default pricelist', store = False, multi = "Pricelist"),
        'pricelist2': fields.function(
            _get_price_from_pricelist, method = True, type = 'float', string = 'Model pricelist', store = False, multi = "Pricelist"),
        'pricelist3': fields.function(
            _get_price_from_pricelist, method = True, type = 'float', string = 'History pricelist', store = False, multi = "Pricelist"),
        }

    _defaults = {
        'in_pricelist': lambda *x: True,
        }

class res_partner(osv.osv):
    """ Extra fields for manage product pricelist
    """
    _inherit = 'res.partner'

    #----------------------
    # Scheduled operations:
    #----------------------
    def schedules_pricelist_partner(self, cr, uid, file_name, context = None):
        ''' Create a customer pricelist depend on partner particularity
        '''
        _logger.info("Start import pricelist:")

        status = "Start pool creation"
        pricelist_pool = self.pool.get('product.pricelist')               
        version_pool = self.pool.get('product.pricelist.version')               
        item_pool = self.pool.get('product.pricelist.item')               
        
        status = "Startup operations"
        pricelist = {}  # name from accounting_id
        products = {}   # converter from product id accounting_id
        bug_start_value = 0.0 # for problems in pricelist starting with cost price = 0 
        tot = 0
        for full_line in open(os.path.expanduser(file_name), 'r'):
            status = "Start read line"
            line = full_line.split(";")
            try:
                if tot < 0:  # jump n lines of header 
                   tot += 1
                else: 
                    if len(line): # jump empty lines
                       tot += 1 
                       product_id = line[0].strip()
                       accounting_id = line[1].strip()
                       price = eval(line[2].replace(",",".").strip())
                       
                       # -------------------
                       # Search partner info
                       # -------------------
                       status = "Start search partner"
                       if accounting_id not in pricelist:
                           partner_ids = self.search(cr, uid, [
                               ('mexal_c', '=', accounting_id)], context=context)
                           if partner_ids:
                               partner_proxy = self.browse(
                                   cr, uid, partner_ids, context = context)[0]
                               pricelist[accounting_id] = [
                                   partner_ids[0],             # 0. partner id
                                   "%s [%s] (Customer)" % (    # 1. pl name
                                       partner_proxy.name, accounting_id), 
                                   False,                      # 2. pl
                                   False,                      # 3. plv
                                   partner_proxy.pricelist_model_history_id.id if partner_proxy.pricelist_model_history_id else False,            # 4. history (for reference for extra product)
                               ]
                           else:
                               _logger.error("[Row %s] Partner not found: %s" % (tot, accounting_id))    
                               continue
                               
                       name = pricelist[accounting_id][1]
                       
                       # -------------------------
                       # Search customer pricelist
                       # -------------------------
                       status = "Start search pricelist"
                       if not pricelist[accounting_id][2]:
                           pricelist_ids = pricelist_pool.search(cr, uid, [ 
                               ('tipology', '=', 'customer'), 
                               ('accounting_id', '=', accounting_id)
                               ], context = context)                               
                           if pricelist_ids:
                               pricelist_id = pricelist_ids[0]
                           else:
                               pricelist_id = pricelist_pool.create(cr, uid, {
                                   'name': name,
                                   #'currency_id': currency_id, # default?
                                   'type': 'sale',  # Sale already exist, created from first base importation of PL
                                   'accounting_id': accounting_id, # << extra fields
                                   'tipology': 'customer',
                               })  
                               # Save current pricelist in partner:
                               self.write(cr, uid, pricelist[accounting_id][0], 
                                   {'property_product_pricelist': pricelist_id}, context = context)
                           pricelist[accounting_id][2] = pricelist_id

                       # ------------------------
                       # Search pricelist version
                       # ------------------------
                       status = "Start search pricelist version"
                       if not pricelist[accounting_id][3]: # test pricelist version presence
                           version_ids = version_pool.search(cr, uid, [ 
                               ('accounting_id', '=', accounting_id)], context = context)                               
                           if version_ids:
                               version_id = version_ids[0]
                           else:
                               version_id = version_pool.create(cr, uid, {
                                   'name': "%s version" % (name),
                                   'pricelist_id': pricelist_id, 
                                   'accounting_id': accounting_id,
                                                                                                          
                               })  
                           pricelist[accounting_id][3] = version_id 
                       
                       # -----------------
                       # search product_id
                       # -----------------
                       status = "Start search product"
                       if product_id not in products:
                           product_pool = self.pool.get('product.product')
                           product_ids = product_pool.search(cr, uid, [('mexal_id', '=', product_id)], context = context)                           
                           if product_ids:
                               products[product_id] = product_ids[0]
                           else:    
                               _logger.error("No product found: %s" % (product_id, ) )
                               continue
                               
                       product_openerp_id = products[product_id]                       
                       
                       # ----------------------
                       # Create history product
                       # ----------------------
                       status = "Create history partner-product"
                       history_pool = self.pool.get('res.partner.pricelist.product')
                       history_ids = history_pool.search(cr, uid, [
                           ('product_id','=',product_openerp_id), 
                           ('partner_id', '=', pricelist[accounting_id][0]),
                           ], context = context)
                       if not history_ids:
                           history_pool.create(cr, uid, {
                               'product_id': product_openerp_id,
                               'partner_id': pricelist[accounting_id][0],
                               'in_pricelist': True,
                           }, context = context)                       
                       
                       status = "Start creating rule item"
                       if price: # if exist price prepare PL item  
                           item_data = {
                               'price_round': 0.01, 
                               'price_version_id': version_id,
                               'sequence': 100,
                               'name': 'Accounting prod: %s' % (product_id),
                               'base': 1, # base price (product.price.type) TODO
                               'min_quantity': 1,
                               'price_surcharge': price - bug_start_value, # Recharge on used base price 
                               'product_id': product_openerp_id,
                               }

                           item_ids = item_pool.search(cr, uid, [
                               ('price_version_id', '=', version_id), ('product_id', '=', product_openerp_id)], context = context)
                           if item_ids: # update
                               item_pool.write(cr, uid, item_ids, item_data, context = context)
                           else:    
                               item_pool.create(cr, uid, item_data, context = context)
                       _logger.info("[Row %s] PL item import %s:" % (tot, line))
            except:
                _logger.error("[Row %s] Generic error %s (status: %s)" % (tot, sys.exc_info(), status))
                continue
        _logger.info("Start importing last rule (history)")      
        for key in pricelist:
            pl = pricelist[key]
            try:
                # Create last rule for partner version (history ones)
                if pl[4] and pl[3]: # history pl 
                    item_based_data = {
                        'price_round': 0.01,        #'price_discount': 0.0, 
                        'is_extra_reference': True,
                        'base_pricelist_id': pl[4],
                        'sequence': 99999, 
                        'base': -1,                 # Price list
                        'price_version_id': pl[3], 
                        'min_quantity': 1, 
                        'name': "Extra product reference (history for partner)",
                        }

                    item_based_id = item_pool.search(cr, uid, [
                        ('price_version_id', '=', pl[3]), ('is_extra_reference', '=', True)]) 
                    if item_based_id: # update
                        item_pool.write(cr, uid, item_based_id[0], item_based_data, context = context)
                    else:
                        item_pool.create(cr, uid, item_based_data, context = context)
            except:
                _logger.error("[Row %s] Generic error %s" % (tot, sys.exc_info()))
                continue
        _logger.info("End import pricelist particular for customer") 
        return True   
        
    def scheduled_product_creations(self, cr, uid, context = None):
        ''' Check in order, invoice and also importation (if present) what are
            the product that usually bought the customer
            This list are for product a pricelist depend on his default
        '''
        order_pool = self.pool.get('sale.order')
        pricelist_pool = self.pool.get('res.partner.pricelist.product')
        
        order_ids = order_pool.search(cr, uid, [], context = context)
        for order in order_pool.browse(cr, uid, order_ids, context = context):
            partner_filter = ('partner_id', '=', order.partner_id.id)
            for line in order.order_line:
                pricelist_ids = pricelist_pool.search(cr, uid, [partner_filter, 
                    ('product_id', '=', line.product_id.id),
                    ], context = context)
                if not pricelist_ids: 
                    pricelist_pool.create(cr, uid, {
                        'partner_id': order.partner_id.id,
                        'product_id': line.product_id.id,
                        'in_pricelist': True,
                    }, context = context)
        
        return True
    
    _columns = {
        'auto_updatable': fields.boolean('Auto updatable'),

        # Togliere solo per demo:
        'sale_order_line_ids': fields.one2many('sale.order.line', 'partner_id', 
            'Orders', required=False, readonly=False)
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
