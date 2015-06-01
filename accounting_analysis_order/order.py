# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields

# Utility function: ############################################################
# Conversion function:
def prepare(valore):  
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:
       if valore: # TODO test correct date format
          return valore[:4] + "-" + valore[4:6] + "-" + valore[6:8]
    return False

def prepare_float(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

# ID function:
def get_partner_id(self, cr, uid, ref, context=None):
    ''' Get OpenERP ID for res.partner with passed accounting reference
    '''
    item_id = self.pool.get('res.partner').search(cr, uid, [('mexal_c', '=', ref)], context=context)
    if item_id:
       return item_id[0]
    return False

def browse_partner_id(self, cr, uid, item_id, context=None):
    ''' Return browse obj for partner id
    '''
    browse_ids = self.pool.get('res.partner').browse(cr, uid, [item_id], context=context)
    if browse_ids:
       return browse_ids[0]
    return False

def get_product_id(self, cr, uid, ref, context=None):
    ''' Get OpenERP ID for product.product with passed accounting reference
    '''
    item_id = self.pool.get('product.product').search(cr, uid, [('default_code', '=', ref)], context=context)
    if item_id:
       return item_id[0]
    return False

def browse_product_id(self, cr, uid, item_id, context=None):
    ''' Return browse obj for product id
    '''
    browse_ids = self.pool.get('product.product').browse(cr, uid, [item_id], context=context)
    if browse_ids:
       return browse_ids[0]
    return False

class sale_order_add_extra(osv.osv):
    ''' Create import scheduled action:
    '''
    _name = "sale.order"
    _inherit = "sale.order"

    # Utility function: ########################################################
    def get_uom(self, cr, uid, name, context=None):
        uom_id = self.pool.get('product.uom').search(cr, uid, [('name', '=', name),]) 
        if uom_id: 
            return uom_id[0] # take the first
        else:
            return False   
        
    # Scheduled action: ########################################################
    def schedule_etl_sale_order(self, cr, uid, path, file_name, context=None):
        ''' Import OC and create sale.order
        '''
        import logging, sys, os
        _logger = logging.getLogger('accounting_analysis_order')

        # Open CSV passed file (see arguments) mode: read / binary, delimiation char 
        # Carico gli elementi da file CSV:
        tot_col = 0
        old_order_ref = ''
        counter={'tot': 0, 'new':0, 'upd':0, 'order':0} # tot negative (jump N lines)

        uoms={}
        uoms['kg']=self.get_uom(cr, uid, 'kg', context=context)
        uoms['tn']=self.get_uom(cr, uid, 't', context=context)
        uoms['nr']=self.get_uom(cr, uid, 'Unit(s)', context=context)
        
        try: 
            file_input=os.path.join(os.path.expanduser(path),file_name)
            rows = open(file_input,'rb')   # prima era: rU
        except:
            _logger.error("Problem open file: [%s, %s]"%(path, file_name))
            return
        
        line_pool=self.pool.get('sale.order.line')
        try: # generic error:
            for row in rows:
                line=row.split(";")
                if tot_col==0: # memorizzo il numero colonne la prima volta
                   tot_col=len(line)
                   _logger.info("Start import [%s] Cols: %s"%(file_input, tot_col,))
                   
                if not (len(line) and (tot_col==len(line))): # salto le righe vuote e le righe con colonne diverse
                    _logger.error("Line: %s - Empty line or different cols [Org: %s - This %s]"%(counter['tot'],tot_col,len(line)))
                    continue 

                counter['tot']+=1 
                try: # line error (for not rollback all if there's only one record in error:
                    csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                    partner_ref = prepare(line[csv_id])
                    csv_id+=1      # Cliente descrizione
                    partner_name = prepare(line[csv_id]) 
                    csv_id+=1      # Order number
                    order_number = prepare(line[csv_id])
                    csv_id+=1      # Data OC formato: YYYYMMDD
                    order_date = prepare_date(line[csv_id]) or False
                    csv_id+=1      # Scadenza OC formato: YYYYMMDD
                    order_deadline = prepare_date(line[csv_id]) or False
                    csv_id+=1      # Articolo
                    product_ref = prepare(line[csv_id]) 
                    csv_id+=1      # Articolo descrizione   (oppure campo campo note nelle righe (D)escrittive )
                    product_description = prepare(line[csv_id]) 
                    csv_id+=1      # Quantity
                    quantity = prepare_float(line[csv_id]) or 0.0
                    csv_id+=1      # Tipo di riga (b si intende prodotto)
                    type_of_line = prepare(line[csv_id]) 
                    csv_id+=1      # Note
                    note = prepare(line[csv_id]) 
                    csv_id+=1      # Sequence (line of order)
                    sequence = int(prepare(line[csv_id]))
                    csv_id+=1      # Product price for this order
                    product_price_total = prepare_float(line[csv_id]) or 0.0
                    csv_id+=1      # Product price for this order
                    product_price = prepare_float(line[csv_id]) or 0.0
                    csv_id+=1      # Article for production
                    csv_id+=1      # UM
                    uom = prepare(line[csv_id]).lower()  # tn o KG

                    # Calculated field:
                    # Dati dimensionali letti dal prodotto:
                    partner_id = get_partner_id(self, cr, uid, partner_ref, context=context)
                    partner_browse = browse_partner_id(self, cr, uid, partner_id, context=context)
                    product_id = get_product_id(self, cr, uid, product_ref, context=context)  
                    if (not partner_id) or (not product_id):                    
                        _logger.error("Line: %s - Error no partner (%s [%s]) or product (%s [%s])!"%(counter['tot'], partner_name, partner_id, product_description, product_id))
                        continue

                    product_browse = browse_product_id(self, cr, uid, product_id, context=context)
                    if uom=="tn": # TODO remove
                        uom="kg"
                    uom_id = uoms.get(uom, product_browse.uom_id.id if product_browse else False) # take default unit
                    name = "%s/%s"%(order_number, order_date[:4],)# [%s]"%(order_number, order_date[:4], partner_name)

                    # Create sale.order (header) ###############################
                    if old_order_ref != order_number: # code breaking (create header)
                        old_order_ref = order_number 
                        counter['order']+=1
                        
                        header = {'name': name,                    # max 64
                                  'origin': False,                 # Source Document
                                  #order_line # <<< TODO after
                                  #payment_term account.payment.term
                                  'picking_policy': 'direct',      # [["direct","Deliver each product when available"],["one","Deliver all products at once"]]
                                  'order_policy': 'manual',        # [["manual","On Demand"],["picking","On Delivery Order"],["prepaid","Before Delivery"]]
                                  'date_order': order_date,
                                  'partner_id': partner_id,
                                  'user_id': uid,
                                  'note': note,                    # Terms and conditions
                                  'state': 'draft',                # [["draft","Draft Quotation"],["sent","Quotation Sent"],["cancel","Cancelled"],["waiting_date","Waiting Schedule"],["progress","Sales Order"],["manual","Sale to Invoice"],["shipping_except","Shipping Exception"],["invoice_except","Invoice Exception"],["done","Done"]]
                                  'invoice_quantity': 'order',     #  [["order","Ordered Quantities"],["procurement","Shipped Quantities"]]
                                  'date_deadline': order_deadline,
                                  'pricelist_id': partner_browse.property_product_pricelist.id if partner_browse else 1,  # product.pricelist   # TODO put default!!!
                                  'partner_invoice_id': partner_id,
                                  'partner_shipping_id': partner_id,                                  
                                  #'currency_id' # function
                                  #incoterm  # stock.incoterms # project_id # account.analytic.account
                                  #partner_shipping_id #shipped #date_confirm #section_id # crm.case.section
                                  #create_date: False, #invoice_ids #invoice_exists
                                  #shop_id #client_order_ref   Customer Reference
                                  #amount_tax #fiscal_position account.fiscal.position
                                  #company_id #picking_ids #invoiced #portal_payment_options
                                  #picked_rate #amount_untaxed #amount_total #invoiced_rate #message_unread
                                 }

                        # Manage order header: #################################
                        order_ids = self.search(cr, uid, [('name','=',name)], context=context)
                        if order_ids: # Update
                            create_header=False
                            try:
                                update = self.write(cr, uid, order_ids, header, context=context)
                                order_id=order_ids[0] # Used for lines                            
                            except:
                                _logger.error("Line: %s - Error update sale order header!"%(counter['tot'],))
                            _logger.info("Line: %s - Order header updated: %s"%(counter['tot'],name))
                            
                            # TODO evaluate if necessary comunicate variation of order!!!!
                            # Remove order line TODO: better solution!!
                            #remove_line_ids = line_pool.search(cr, uid, [('order_id','=',order_id)], context=context)
                            #remove = line_pool.unlink(cr, uid, remove_line_ids, context=context)
                        else:         # Create:
                            create_header=True
                            try:
                               order_id = self.create(cr, uid, header, context=context)
                            except:
                               _logger.error("Line: %s - Error create sale order header!"%(counter['tot'],))
                            _logger.info("Line: %s - Order header insert: %s"%(counter['tot'],name))

                    if create_header: # Create lines only if is yet created header
                        # Details line
                        data={'name': product_browse.name if product_browse else "Art. # %s"%(sequence),
                              'order_id': order_id,
                              'product_id': product_id,
                              'product_uom_qty': quantity, 
                              'product_uom': uom_id,
                              'price_unit': product_price,
                              'sequence': sequence,
                              'tax_id': [(6,0,[product_browse.taxes_id[0].id,] if product_browse and product_browse.taxes_id else [])],
                              }

                        #order_line_ids = line_pool.search(cr, uid, [('product_id','=',product_id),('sequence','=',sequence)], context=context)  
                        try: 
                             line_id=line_pool.create(cr, uid, data, context=context)  
                        except:
                            _logger.error("Line: %s - Error adding line #%s to order"%(counter['tot'],sequence,))
                       
                        _logger.info("Line: %s - Line #%s insert"%(counter['tot'],sequence,))
                except:
                    _logger.error("Line: %s - Generic line-record error!"%(counter['tot'],))                    
        except:
            _logger.error("Line: %s - Importation error"%(counter['tot'],))

        _logger.info("End importation OC [%s]"%(counter,))
        return
        
    _columns = {
        'date_deadline': fields.date('Deadline'),
    }

class sale_order_line_extra(osv.osv):
    ''' Create extra fields in sale.order.line obj
    '''
    _name="sale.order.line"
    _inherit="sale.order.line"
    
    import openerp.addons.decimal_precision as dp
    
    # Override 
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        ''' Override for field subtotal
        '''
        return super(sale_order_line_extra, self)._amount_line(cr, uid, ids, field_name, arg, context=context)
    
    _columns = {
        'date_order': fields.related('order_id','date_order', type='date', string='Date', store=True),
        'date_deadline': fields.related('order_id','date_deadline', type='date', string='Deadline', store=True),
        'partner_id': fields.related('order_id','partner_id', type='many2one', relation='res.partner', string='Partner', store=True),
        # override:
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute= dp.get_precision('Account'), store=True),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
