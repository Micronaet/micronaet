# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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

from osv import osv, fields
import pdb
import decimal_precision as dp

class sale_order_bank(osv.osv):
    _name = 'sale.order.bank'
    _description = 'Sale oder bank'
    
    _columns = {
        'name':fields.char('Bank account', size=64, required=False, readonly=False),
        'information': fields.text('Information', translate=True, help="Descrizione del conto, IBAN ecc. che viene presentato sull'offerta"),        
    }
sale_order_bank()

class sale_product_return(osv.osv):
    ''' List of text sentences for the return of the product, this list are
        show in offer modules
    '''
    _name='sale.product.return'
    _description='Sale product return'
    _order='name'
    
    _columns={
             'name':fields.char('Description', size=64, required=False, readonly=False),
             'text': fields.text('Text', translate=True, required=True, readonly=False),
             }
sale_product_return()

class fiam_sale_order_fields(osv.osv):
    _name='sale.order'
    _inherit='sale.order'
    
    _columns={
             'bank_id':fields.many2one('sale.order.bank', 'Conto bancario', required=False),
             #'discount_rates_partner': fields.related('partner_id','discount_rates', type='char', relation='res.partner', string='Sconto riservato al partner'),        
             'print_address': fields.boolean('Stampa indirizzi aggiuntivi', required=False),             
             'print_only_prices': fields.boolean('Offerta con soli prezzi', required=False),              
             'has_master_header': fields.boolean('Intestazione tabella principale', 
                                                 required=False, 
                                                 help="Nei preventivi di sola comunicazione evita l'inserimento intestazione"),
             'return_id':fields.many2one('sale.product.return', 'Product return', required=False),
             }

    _defaults={
              'has_master_header': lambda *a: True,   
              }
fiam_sale_order_fields()

class fiam_sale_order_line_fields(osv.osv):
    _name='sale.order.line'
    _inherit ='sale.order.line'

    '''# Override del metodo presente nel modulo sale/sale.py TODO se cambia come ci comportiamo????
    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            if line.price_use_manual:
               price = line.price_unit_manual
            else:      
               price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.order_id.partner_invoice_id.id, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
        return res '''
        
    '''def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, 
            fiscal_position=False, flag=False,):
        import pdb; pdb.set_trace()    
        res = super(fiam_sale_order_line_fields, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag)
        if ids: 
            sol_proxy = self.browse(cr, uid, ids)[0]            
            res['value']['discount'] = self.on_change_multi_discount(cr, uid, ids, sol_proxy.multi_discount_rates)
        #else:
        #    sol_proxy = self.browse(cr, uid, ids)[0]                            
        return res'''
        
    def create(self, cr, uid, vals, context = None):
        """ Multi discount rate
        """
        if not vals.get('discount', 0.0) and vals.get('multi_discount_rates', False):
            res = self.on_change_multi_discount(cr, uid, 0, vals.get('multi_discount_rates'))['value']
            vals['discount'] = res.get('discount', '')
        return super(fiam_sale_order_line_fields, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context = None):
        """ Multi discount rate
        """
        if vals.get('multi_discount_rates', False):
            res = self.on_change_multi_discount(cr, uid, 0, vals.get('multi_discount_rates'))['value']
            vals['discount'] = res.get('discount', '')
        return super(fiam_sale_order_line_fields, self).write(cr, uid, ids, vals, context)        

    def on_change_multi_discount(self, cr, uid, ids, multi_discount_rates):
        ''' get multidiscount return compute of discount and better format of multi rates '''
        res={}        
        if multi_discount_rates:
           disc=multi_discount_rates.replace(' ','')  # remove spaces     
           disc=disc.replace(',','.')
           discount_list=disc.split('+')
           if discount_list: 
              base_discount=float(100)
              for aliquota in discount_list:
                  try: 
                     i=float(eval(aliquota))
                  except:
                     i=0.00
                  base_discount-=base_discount * i / 100.00 
              res['discount']=100 - base_discount                  # Return value
              res['multi_discount_rates']= '+ '.join(discount_list) # Better format of the string
           else:
              res['discount']=0.0
              res['multi_discount_rates']=''
        else:
           res['discount']= 0.00
           res['multi_discount_rates']=''
        return {'value':res}

    def _discount_rates_get(self, cr, uid, context=None):         
        if context is None:
            context = {}
        if context.get('partner_id'):
           cr.execute('select discount_rates, id from res_partner where id = %d' % (context['partner_id'],))
           res=cr.fetchall()
           if res[0][0]:
              return res[0][0]       
           else:
              return False
        else:
           return False

    def _discount_value_get(self, cr, uid, context=None):         
        if context is None:
            context = {}
        if context['partner_id']:
           cr.execute('select discount_value, id from res_partner where id = %d' % (context['partner_id'],))
           res=cr.fetchall()
           if res[0][0]:
              return res[0][0]       
           else:
              return False
        else:
           return False

    _columns = {
               'multi_discount_rates':fields.char('Discount scale', size=30, required=False, readonly=False), 
               # Part for manage net price with spot aprox:
               'price_use_manual': fields.boolean('Use manual net price', required=False, help="If specificed use manual net price instead of lordd price - discount"),             
               'price_unit_manual': fields.float('Manual net price', digits_compute= dp.get_precision('Sale Price')),
               # Part for manage image link on order (TODO aeroo link parametric actually not works
               'image_http': fields.boolean('Has image', required=False, help="Has link for image on the web"),             
               'image_replace_name':fields.char('Override name', 
                                                size=30, 
                                                required=False, 
                                                readonly=False, 
                                                help="Usually the name is art. code + '.PNG', es. 400.PNG, if you want to change write the name in this field!"), 
               }
    _defaults = {
                'multi_discount_rates': _discount_rates_get,       
                'discount': _discount_value_get,
                }
   
fiam_sale_order_line_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

