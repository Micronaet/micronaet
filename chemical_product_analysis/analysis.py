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
from datetime import datetime
from tools.translate import _
import time
import tools

class chemical_element(osv.osv):
    ''' Chemical elements (periodic table element but also oxid etc.)
    '''
    _name = 'chemical.element'
    _description = 'Chemical element'
    
    _columns = {
        'name':fields.char('Element', size=64, required=True, readonly=False),
        'symbol':fields.char('Chemical symbol', size=15, required=False, readonly=False),
        'atomic': fields.integer('Atomic number', help="Atomic number if the element is a periodic table element, instead of not indicate")        
    }
chemical_element()

class chemical_product_category_type(osv.osv):
    ''' Type of category product:
        every product belongs to a category every category has a type
    '''
    _name = 'chemical.product.category.type'
    _description = 'Type of category'
    
    _columns = {
        'name':fields.char('Type', size=64, required=True, readonly=False),
        'note': fields.text('Note'),
    }
chemical_product_category_type()

class chemical_product_category(osv.osv):
    ''' Category of product:
        every product belongs to a category (evey category has a list of element)
    '''
    _name = 'chemical.product.category'
    _description = 'Category'
    _columns = {
        'name':fields.char('Product category', size=64, required=True, readonly=False),
        'note': fields.text('Note'),
        'type_id':fields.many2one('chemical.product.category.type', 'Type', required=True),
    }
chemical_product_category()

class chemical_product_category_line(osv.osv):
    ''' Element that could belong to a category
    '''
    _name = 'chemical.product.category.line'
    _description = 'Element for category'
    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=False),
        'symbol': fields.related('name','symbol', type='char', string='Symbol'),
        'category_id':fields.many2one('chemical.product.category', 'Category', required=False),
        'min': fields.float('Min', digits=(16, 2), help="Min value of element for this category"),
        'max': fields.float('Max', digits=(16, 2), help="Max value of element for this category"),
    }
chemical_product_category_line()

class chemical_product_category(osv.osv):
    ''' Category for add o2m fields
    '''
    _name = 'chemical.product.category'
    _inherit = 'chemical.product.category'

    _columns = {
        'line_ids':fields.one2many('chemical.product.category.line', 'category_id', 'Default element', required=False),
    }
chemical_product_category()

class product_product_add_fields(osv.osv):
    ''' Add field to product for manage analysis
    '''
    
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'need_analysis': fields.boolean('Need analysis', help='Check this if the product require an analysis every purchase or sold', required=False), 
        'chemical_category_id':fields.many2one('chemical.product.category', 'Chemical Category', required=False),
        'category_type_id': fields.related('chemical_category_id','type_id', type='many2one', relation='chemical.product.category.type', string='Category type'),
    }
    
    _defaults = {
        'need_analysis': lambda *a: True,
    }
product_product_add_fields()

class chemical_analysis(osv.osv):
    ''' Chemical Analysis:
        This is the analysis element linked to a stock move for every product that
        enter in company (or for the product that required it)        
    '''
    _name = 'chemical.analysis'
    _description = 'Analysis'
    
    _columns = {
        'name':fields.char('Description', size=64, required=True, readonly=False),
        'date': fields.date('Date'),
        'quantity': fields.float('Q. anal. (int.)', digits=(16, 2), help="Quantity used for intenral analysis"), # TODO update store movements removing this quantity?
        'quantity_laboratory': fields.float('Q. anal. (lab.)', digits=(16, 2), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?

        'prodlot_id':fields.many2one('stock.production.lot', 'Lot', required=True),
        'product_id': fields.related('prodlot_id','product_id', type='many2one', relation='product.product', string='Product'),
        #'stock_move_id': fields.related('prodlot_id','prodlot_id', type='many2one', relation='stock.production.lot', string='Lot'),
        'date_in': fields.related('prodlot_id','date', type='datetime', string='Date create'),
        'note': fields.text('Note'),

        'laboratory_id':fields.many2one('res.partner', 'Laboratory', required=False),
    }

    _defaults = {
        'quantity': lambda *a: 0.0,
        'quantity_laboratory': lambda *a: 0.0,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
chemical_analysis()

class stock_move_add_fields(osv.osv):
    ''' Add field to stock movement for manage analysis
    '''
    
    _name = 'stock.production.lot'
    _inherit = 'stock.production.lot'

    ''' TODO if create a button to open firs analysis
    def _get_first_analysis(self, cr, uid, ids, field_name, arg, context):
         res = {} 
         for item in self.browse(cr, uid, ids):
             res[item.id]=item.chemical_analysis_ids[0].id if item.chemical_analysis_ids else False
         return res'''
         
    _columns = {
        'granulometric': fields.text('Granulometric analysis'), # TODO complete if are not only this
        'visual': fields.text('Visual analysis'),
        'hygro': fields.float('% Hygro', digits=(5, 2)),        

        'chemical_analysis_ids': fields.one2many('chemical.analysis', 'prodlot_id', 'Analysis', required=False),
        #'chemical_analysis_id': fields.function(_get_first_analysis, method=True, type='int', string='First analysis ID', store=False),
    }
stock_move_add_fields()

class stock_picking_add_fields(osv.osv):
    """ Add extra field to stock.picking document
    """
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def create_all_analysis(self, cr, uid, ids, context=None):
        ''' Start from a pick in document and create all analysis for all
            stock.production.lot in stock.move (if not exist yet!)
            populate with default element for every chemical category linked to
            the product (better if there is a lot linked to line/product)
        '''
        res=[]
        try:
            picking_proxy=self.browse(cr, uid, ids[0]) # only one is present
            for item in picking_proxy.move_lines: # Create analysis for all movement in stock.picking
                if item.prodlot_id and item.product_id.chemical_category_id: # test if lot is created (or associated to stock.move) and product has category
                    search_id=self.pool.get('chemical.analysis').search(cr, uid, [('prodlot_id', '=', item.prodlot_id.id)])
                    if not search_id: # test if exist yet                        
                        #if item.product_id.need_analysis: # TODO filter for product that require?                 
                        analysis_data = {
                                        'name': "An.: %s [%s]"%(item.product_id.name, item.prodlot_id.name),
                                        'prodlot_id':item.prodlot_id.id,
                                        #'product_id': item.product_id.id,
                                        #'date_in': item.prdate,
                                        }
                        analysis_id=self.pool.get('chemical.analysis').create(cr, uid, analysis_data)
                        res.append(analysis_id)
                        
                        # Populare analysis element with default element of category
                        #import pdb; pdb.set_trace()
                        for element in item.product_id.chemical_category_id.line_ids:
                            analysis_line_data = {
                                        'name': element.name.id,
                                        'chemical_analysis_id': analysis_id,
                                        }
                            analysis_line_id=self.pool.get('chemical.analysis.line').create(cr, uid, analysis_line_data)
        except:
             raise osv.except_osv(_('Warning !'), _("Error creating analysis form for this picking element!"))                
        return True 
stock_picking_add_fields()

class res_partner_laboratory_extra_field(osv.osv):
    """ extra field for partner = laboratory
    """
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'is_laboratory':fields.boolean('Is laboratory', required=False),
    }
res_partner_laboratory_extra_field()

class chemical_analysis_line(osv.osv):
    ''' Chemical analysis line (list of element that is finded in product that
        require perc value
        Generated with auto mode from category of the product
    '''
    
    _name = 'chemical.analysis.line'
    _description = 'Line of analysis'

    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=True),
        'percentage': fields.float('% internal', digits=(16, 2), required=True),
        'percentage_supplier': fields.float('% supplier', digits=(16, 2), required=True),
        'percentage_laboratory': fields.float('% laboratory', digits=(16, 2), required=True),
        'note': fields.text('Note'),
        'symbol': fields.related('name', 'symbol', type='char', string='Symbol'),
        'chemical_analysis_id':fields.many2one('chemical.analysis', 'Analysis', required=False),
    }
    
    _defaults = {
        'percentage': lambda *a: 0.0,
        'percentage_supplier': lambda *a: 0.0,
        'percentage_laboratory': lambda *a: 0.0,
        'note': lambda *a: False,
    }
chemical_analysis_line()

class chemical_analysis(osv.osv):
    ''' Chemical Analysis inherit for o2m fields:
    '''
    _name = 'chemical.analysis'
    _inherit = 'chemical.analysis'
    
    _columns = {
       'line_ids': fields.one2many('chemical.analysis.line', 'chemical_analysis_id', 'Analysis', required=False),
    }
chemical_analysis()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
