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
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse


_logger = logging.getLogger(__name__)

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects': self.get_objects,
            'get_header': self.get_header,
            'get_bom': self.get_bom,
        })

    def get_header(self, data=None):
        '''Return header for document
        '''        
        if data is None:
            data = {}

        pricelist_id = data.get('pricelist_id')
        description = data.get('description', '')
        pl_pool = self.pool.get('product.pricelist')
        pl_proxy = pl_pool.browse(self.cr, self.uid, pricelist_id)
        try:
            if description:
                return description
            else:     
                return "%s (%s)" % (_(pl_proxy.name), pl_proxy.currency_id.name)
        except:
            return _("Pricelist report")
        
    def get_bom(self, product_id):
        ''' Return BOM browse for product passed
        '''
        bom_pool = self.pool.get('mrp.bom')
        bom_ids = bom_pool.search(self.cr, self.uid, [
            ('product_id', '=', product_id)])
        if len(bom_ids) == 1:
            return bom_pool.browse(self.cr, self.uid, bom_ids)[0].bom_lines
        else:
            return []

    def get_objects(self, data=None): #pricelist_id):
        '''Procedure adapted for (normal use and) Wizard use
           Read all product on product.product and calculate price with date 
           today and one year price.
           After sorting return the list to print
        '''
        if data is None:
            data = {}

        res = [] # [product_id, product_name (Note: language), Pricelist, Pricelist -1,] # UOM, UOS]
        product_pool = self.pool.get('product.product')
        partner_pool = self.pool.get('res.partner')
        
        # Read parameters:
        description = data.get('description', '')
        pricelist_id = data.get('pricelist_id', False)
        report_type = data.get('type', 'product') # default report product
        partner_id = data.get('partner_id', False)
        decimal = data.get('decimal', 3)
        with_cost = data.get('with_cost', False)
        
        float_format = "%s2.%sf" % ("%", decimal) # Set mask for float format
        
        # TODO manage extra parameters:
        structured = data.get('structured', False)
        commented = data.get('commented', False)
        with_category = data.get('with_category', False)
        
        # Generate record depend on type:
        if report_type == 'product':
            product_ids = product_pool.search(self.cr, self.uid, [
                ('in_pricelist', '=', True)], )

        elif report_type == 'category':            
            product_ids = []
            for category in data.get('category_ids', False):
                domain = [('categ_id', '=', category[0])]
                
                if category[1]: # with _child # TODO find all child elements
                    pass #domain = [('categ_id','=',category[0])]                
                    
                if not category[2]: # all
                    domain.append(('in_pricelist', '=', True))
                     
                product_ids.extend(product_pool.search(
                    self.cr, self.uid, domain))
            
        elif report_type == 'partner':
            product_ids = []
            for item in partner_pool.browse(self.cr, self.uid, partner_id).pricelist_product_ids:
                if item.in_pricelist and item.product_id:                    
                    product_ids.append(item.product_id.id)
        
        if not product_ids:
            raise osv.except_osv(_('Error!'), _(
               'No records with parameter selected, try change something in form'))
            
        product_proxy = product_pool.browse(self.cr, self.uid, product_ids)
        for product in product_proxy:
            price = self.pool.get('product.pricelist').price_get(
                self.cr, self.uid, [pricelist_id], product.id, 1.0, False, 
                    {
                    'uom': False,    # uom
                    'date': False,   # date_order,
                    })[pricelist_id]
                    
            if with_cost: 
                if price:    
                    percent = product.standard_price / price * 100.0
                else:
                    percent = 0.0
                        
                cost = "%s (%s%s)" % (
                    float_format % product.standard_price,
                    float_format % percent,
                    "%",
                    )                    
            else:
                cost = ""

            if product.standard_price:
                price = float_format % price if price else "NO REGOLE!"
            else:
                price = "NO COSTO!"                    
                    
            res.append([
                product.code, 
                product.name, 
                price,
                cost, 
                product.categ_id.name if product.categ_id and with_category else "",
                product.id,
                ])                    
        return res
