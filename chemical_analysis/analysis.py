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

class chemical_product_category(osv.osv):
    ''' Category of product
    '''
    _name = 'chemical.product.category'
    _description = 'Category'
    
    _columns = {
        'name':fields.char('Type', size=64, required=True, readonly=False),
        'note': fields.text('Note'),
    }
chemical_product_category()

class chemical_product_analysis_model(osv.osv):
    ''' Element that could belong to a category
    '''
    _name = 'product.product.analysis.model'
    _description = 'Analysis mode'
    _columns = {
        'name':fields.char('Analysis model name', size=80, required=True, readonly=False),
        'chemical_category_id':fields.many2one('chemical.product.category', 'Chemical Category', required=False),
        'analysis_line_ids':fields.one2many('product.product.analysis.line', 'model_id', 'Lines per element', required=False),
        'note': fields.text("Note"),

        'family':fields.char('Family', size=80, required=False, readonly=False, help="Product code, first 6 chars, ex.: 010234"),
    }
chemical_product_analysis_model()

class chemical_product_category_line(osv.osv):
    ''' Analysis model line (range for single element)
    '''
    _name = 'product.product.analysis.line'
    _description = 'Analysis model line'
    
    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=False),
        'symbol': fields.related('name','symbol', type='char', string='Symbol'),
        'model_id':fields.many2one('product.product.analysis.model', 'Model', required=False, on_delete='cascade'),
        'min': fields.float('Min %', digits=(16, 2), help="Min value of element for this category"),
        'max': fields.float('Max %', digits=(16, 2), help="Max value of element for this category"),
    }
chemical_product_category_line()

class chemical_product_analysis_model(osv.osv):
    ''' Element that could belong to a category
    '''
    _name = 'product.product.analysis.model'
    _inherit = 'product.product.analysis.model'
    
    _columns = {
        'analysis_line_ids':fields.one2many('product.product.analysis.line', 'model_id', 'Lines per element', required=False),
    }
chemical_product_analysis_model()

class product_product_extra_fields(osv.osv):
    ''' Extra field to catalog product for chemical category and composition range
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    
    _description = 'Category'
    _columns = {
        'model_id':fields.many2one('product.product.analysis.model', 'Model', required=False, on_delete='cascade'),
        'need_analysis': fields.boolean('Need analysis', help='Check this if the product require an analysis every purchase or sold', required=False), 
        
        'chemical_category_id': fields.related('model_id','chemical_category_id', type='many2one', relation="chemical.product.category", string='Category', readonly=True, store=True),
    }

    _defaults = {
        'need_analysis': lambda *a: True,
    }
product_product_extra_fields()

class chemical_analysis(osv.osv):
    ''' Chemical Analysis:
        This is the analysis element linked to a stock move for every product that
        enter in company (or for the product that required it)        
    '''    
    _name = 'chemical.analysis'
    _description = 'Analysis'
    
    _columns = {
        'name':fields.char('Description', size=100, required=True, readonly=False),
        'date': fields.date('Date'),
        'quantity': fields.float('Q. anal. (int.)', digits=(16, 2), help="Quantity used for intenral analysis"), # TODO update store movements removing this quantity?
        'quantity_lab1': fields.float('Q. anal. (lab.1)', digits=(16, 2), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'quantity_lab2': fields.float('Q. anal. (lab.2)', digits=(16, 2), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'quantity_lab3': fields.float('Q. anal. (lab.3)', digits=(16, 2), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'code_lab1':fields.char('Code pattern 1', size=8, required=False, readonly=False),
        'code_lab2':fields.char('Code pattern 2', size=8, required=False, readonly=False),
        'code_lab3':fields.char('Code pattern 3', size=8, required=False, readonly=False),

        'prodlot_id':fields.many2one('stock.production.lot', 'Lot', required=True, on_delete='cascade'),
        'product_id': fields.related('prodlot_id','product_id', type='many2one', relation='product.product', string='Product'),
        #'stock_move_id': fields.related('prodlot_id','prodlot_id', type='many2one', relation='stock.production.lot', string='Lot'),
        'model_id': fields.related('product_id','model_id', type='many2one', relation='product.product.analysis.model', string='Analysis model'),
        'chemical_category_id': fields.related('product_id','chemical_category_id', type='many2one', relation="chemical.product.category", string='Chem Category', readonly=True,),
        'date_in': fields.related('prodlot_id','date', type='datetime', string='Date create'),
        'note': fields.text('Note'),

        'laboratory1_id':fields.many2one('res.partner', 'Laboratory 1', required=False),
        'laboratory2_id':fields.many2one('res.partner', 'Laboratory 2', required=False),
        'laboratory3_id':fields.many2one('res.partner', 'Laboratory 3', required=False),
    }

    _defaults = {
        'quantity': lambda *a: 0.0,
        'quantity_lab1': lambda *a: 0.0,
        'quantity_lab2': lambda *a: 0.0,
        'quantity_lab3': lambda *a: 0.0,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }
chemical_analysis()

class stock_move_add_fields(osv.osv):
    ''' Add field to stock movement for manage analysis
    '''
    
    _name = 'stock.production.lot'
    _inherit = 'stock.production.lot'

    _columns = {
        'granulometric': fields.text('Granulometric analysis'), # TODO complete if are not only this
        'visual': fields.text('Visual analysis'),
        'hygro': fields.float('% Hygro', digits=(5, 2)),        

        'chemical_analysis_ids': fields.one2many('chemical.analysis', 'prodlot_id', 'Analysis', required=False),
    }
stock_move_add_fields()

class stock_picking_add_fields(osv.osv):
    """ Add extra field to stock.picking document
    """
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    def create_all_analysis(self, cr, uid, ids, context=None):
        ''' Start from one or mode pick-in document and create all analysis for all
            stock.production.lot in stock.move (if not exist yet!)
            populate with default element for every chemical model linked to
            the product (better if there is a lot linked to line/product)
        '''
        try:
            for picking_document in self.browse(cr, uid, ids):          # more than one pickin document
                for item in picking_document.move_lines:                # Create analysis for all movement in stock.picking
                    if item.prodlot_id and item.product_id.model_id and item.product_id.need_analysis: # test if lot is created (or associated to stock.move) and product has model
                        search_id=self.pool.get('chemical.analysis').search(cr, uid, [('prodlot_id', '=', item.prodlot_id.id)])
                        if not search_id: # test if exist yet
                            analysis_data = {
                                            'name': "An.: %s [%s]"%(item.product_id.name, item.prodlot_id.name),
                                            'prodlot_id':item.prodlot_id.id,
                                            #'product_id': item.product_id.id,
                                            #'date_in': item.prdate,
                                            }
                            analysis_id=self.pool.get('chemical.analysis').create(cr, uid, analysis_data)
                            
                            # Populare analysis element with default element of category
                            for element in item.product_id.model_id.analysis_line_ids:
                                analysis_line_data = {
                                            'name': element.name.id,
                                            'chemical_analysis_id': analysis_id,
                                            'model_line_id': element.id, # generator
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

    def _function_is_in_range(self, cr, uid, ids, field_name, arg, context=None):
        """ Test if all present value is in range
            return True if correct         
        """
        res={}
        
        for line in self.browse(cr, uid, ids):
            if line.model_line_id: # only if there's the generator line
               test_value=[item for item in (line.percentage,line.percentage_supplier, line.percentage_lab1, line.percentage_lab2, line.percentage_lab3,) if item>0.0]
               res[line.id]={}
               # default values:
               res[line.id]['out_of_range']=False; res[line.id]['min_all']=0.0; res[line.id]['max_all']=0.0
               
               if test_value: # jump all empty
                  res[line.id]['min_all']=min(test_value)
                  res[line.id]['max_all']=max(test_value)
                  if res[line.id]['min_all'] < line.model_line_id.min or res[line.id]['max_all'] > line.model_line_id.max: # over value?
                     res[line.id]['out_of_range']=True                        
        return res         
    
    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=True),
        'chemical_analysis_id':fields.many2one('chemical.analysis', 'Analysis', required=False, on_delete='cascade'),

        'percentage': fields.float('% internal', digits=(16, 2), required=True, help="Supplier value"),
        'percentage_supplier': fields.float('% supplier', digits=(16, 2), required=True, help="Internal value"),
        'percentage_lab1': fields.float('% laboratory 1', digits=(16, 2), required=True, help="Laboratory 1 value"),
        'percentage_lab2': fields.float('% laboratory 2', digits=(16, 2), required=True, help="Laboratory 2 value"),
        'percentage_lab3': fields.float('% laboratory 3', digits=(16, 2), required=True, help="Laboratory 3 value"),

        'note': fields.text('Note'),
        'symbol': fields.related('name', 'symbol', type='char', string='Symbol'),

        'model_line_id': fields.many2one('product.product.analysis.line', 'Model line', required=False, on_delete='cascade', help="reference for range for this element"),
        
        'min': fields.related('model_line_id', 'min', type='float', digits=(16, 2), string='Min'),
        'max': fields.related('model_line_id', 'max', type='float', digits=(16, 2), string='Max'),

        'out_of_range': fields.function(_function_is_in_range, method=True, type='boolean', string='Out of range', store=True, multi=True), #fnct_search=_function_search_in_range,
        'min_all': fields.function(_function_is_in_range, method=True, type='float', digits=(16, 2), string='Min % of all', store=True, multi=True),
        'max_all': fields.function(_function_is_in_range, method=True, type='float', digits=(16, 2), string='Min % of all', store=True, multi=True),
    }
    
    _defaults = {
        'percentage': lambda *a: 0.0,
        'percentage_supplier': lambda *a: 0.0,
        'percentage_lab1': lambda *a: 0.0,
        'percentage_lab2': lambda *a: 0.0,
        'percentage_lab3': lambda *a: 0.0,
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
