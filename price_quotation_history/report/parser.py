##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse
from datetime import datetime

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'product_pricelist': self.product_pricelist,
            'product_pricelist_old': self.product_pricelist_old,
        })

    def product_pricelist_old(self, order_id, product_id, partner_id ):
        ''' Order history and invoice history from accounting program
        '''
        # Order elements:
        res="Order:\n"
        order_line_ids=self.pool.get('sale.order.line').search(self.cr, self.uid, [('order_id','!=', order_id),('product_id','=',product_id),('order_partner_id','=',partner_id)]) # TODO inser filter on order_id.data_order
        if order_line_ids:
           for line in self.pool.get('sale.order.line').browse(self.cr, self.uid, order_line_ids):
               res+="%s)\t%s\n"%(datetime.strptime(line.order_id.date_order, '%Y-%m-%d').strftime('%d/%m/%Y'), line.price_unit)

        # Invoice elements:
        res+="\nInvoice:\n"
        product_proxy=self.pool.get('product.product').browse(self.cr, self.uid, product_id)
        product_code=product_proxy.code 
        partner_proxy=self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
        partner_code=partner_proxy.mexal_c 
        invoice_line_ids=self.pool.get('micronaet.invoice.line').search(self.cr, self.uid, [('product','=',product_code),('partner','=',partner_code)]) 
        if invoice_line_ids:
           for line in self.pool.get('micronaet.invoice.line').browse(self.cr, self.uid, invoice_line_ids):
               res+="%s) %sx%s [FT%s]\n"%(datetime.strptime(line.date, '%Y%m%d').strftime('%d/%m/%Y'), line.price, line.quantity, line.name)
        return res   
 
    def product_pricelist(self, product_id, pricelist_id):
        '''get price of product_id for pricelist_id selected
        '''
        #TODO return value according to number of product (now only for 1.0 item)
        price = self.pool.get('product.pricelist').price_get(self.cr, 
                                                            self.uid, 
                                                            [pricelist_id],
                                                            product_id, 
                                                            1.0, 
                                                            False, 
                                                            {
                                                              'uom': False, #uom
                                                              'date': False, #date_order,
                                                            }
                                                            )
        return price[pricelist_id]
