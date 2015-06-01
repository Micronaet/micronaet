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

class product_pricelist_report_wizard(osv.osv_memory):
    """ Print pricelist wizard
    """
    _name = "product.pricelist.report.wizard"
    _description = "Print pricelist wizard"

    _columns = {
        'description': fields.char('Description', size=100),    
        'pricelist_id': fields.many2one('product.pricelist', 'Print pricelist', 
           required=True, help="Choose pricelist to print"),
        'partner_id': fields.many2one('res.partner', 'Customer', 
           required=False, help="For type partner need to select"),
        'type': fields.selection([
            ('product', 'Product selected'),
            ('category', 'Category list'),
            ('partner', 'Partner product'),            
            ], 'Type', select=True),
        'structured': fields.boolean('Structured', 
            help="List splitted into categories"),
        'commented': fields.boolean('Commented', 
            help="With comment in report for write filter used"),
        'with_category': fields.boolean('With category', 
            help="Write category extra info in product"),
        'with_cost': fields.boolean('With cost indication', 
            help="Print cost of product and % of on total"),
        'with_bom': fields.boolean('With BOM indication', 
            help="Print BOM for cost computation"),
        'decimal': fields.integer('Decimal', required=True),
        }

    _defaults = {
        'type': lambda *x: 'product',
        'structured': lambda *x: False,
        'commented': lambda *x: False,
        'with_category': lambda *x: False,
        'with_bom': lambda *x: False,
        'decimal': lambda *x: 3,
        }

    def print_report(self, cr, uid, ids, context = None):
        """
        Print with selected parameters
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param ids: List of ids
        
        @return: Action dictionary
        """
        if context is None:
           context = {}

        datas = {}
        wiz_browse = self.browse(cr, uid, ids[0], context=context)

        datas['description'] = wiz_browse.description
        datas['pricelist_id'] = wiz_browse.pricelist_id.id
        datas['type'] = wiz_browse.type
        datas['partner_id'] = wiz_browse.partner_id.id if wiz_browse.partner_id else False
        datas['structured'] = wiz_browse.structured
        datas['commented'] = wiz_browse.commented
        datas['with_category'] = wiz_browse.with_category
        datas['category_ids'] = []
        datas['decimal'] = wiz_browse.decimal
        datas['with_cost'] = wiz_browse.with_cost
        datas['with_bom'] = wiz_browse.with_bom
        
        for category in wiz_browse.category_ids:
            datas['category_ids'].append(
                (category.category_id.id, category.with_child, category.all))
            
        return { # action report
            'type': 'ir.actions.report.xml',
            'report_name': "aeroo_pricelist_model_report",
            'datas': datas,
            }            

class product_pricelist_report_category(osv.osv_memory):
    """ List of category to print
    """
    _name = "product.pricelist.report.category"
    _description = "Category list for print"
    _rec_name = 'wizard_id'

    _columns = {
        'wizard_id': fields.many2one('product.pricelist.report.wizard', 
            'Wizard'),
        'category_id': fields.many2one('product.category', 'Category', 
            required=True, help="Category for print in pricelist"),
        'with_child': fields.boolean('With child'),
        'all': fields.boolean('All product'),
        }
    _defaults = {
        'with_child': lambda *a: True,
        'all': lambda *a: False,
        }

class product_pricelist_report_wizard(osv.osv_memory):
    """ Print pricelist wizard
    """
    _inherit = "product.pricelist.report.wizard"
    
    _columns = {
        'category_ids': fields.one2many('product.pricelist.report.category', 
            'wizard_id', 'Category'),
        }    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
