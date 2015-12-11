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

from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'obj_product': self.obj_product,
        })

    def obj_product(self, pricelist_id):
        '''Read all product on product.product and calculate price with date today and 
           one year price.
           After sorting return the list to print
        '''
        product_ids=self.pool.get('product.product').search(self.cr, self.uid, []) # TODO all sellable product?
        product_proxy=self.pool.get('product.product').read(self.cr, self.uid, product_ids, ['id', 'name', 'code',])
        #product_proxy=self.pool.get('product.product').browse(self.cr, self.uid, product_ids)
        res_list=[] # [product_id, product_name (Note: language), Pricelist, Pricelist -1,] # UOM, UOS]
        for product in product_proxy:
            res_list.append([product['code'], 
                             product['name'], 
                             self.pool.get('product.pricelist').price_get(self.cr, self.uid, [pricelist_id],
                                  product['id'], 1.0, False, {
                                                           'uom': False, #uom
                                                           'date': False, #date_order,
                                                          })[pricelist_id]

                            ])
        return res_list
