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
import sys
from openerp.osv import osv, fields
from datetime import datetime
from openerp.tools.translate import _
import time
import openerp.tools
import logging


_logger = logging.getLogger(__name__)

class chemical_element(osv.osv):
    ''' Chemical elements (periodic table element but also oxid etc.)
    '''
    _name = 'chemical.element'
    _description = 'Chemical element'

    def name_search(self, cr, uid, name, args = None, operator = 'ilike', context = None, limit = 80):
        """ Force name search also in symbol
        """
        if args is None:
            args = []
        if context is None:
            context={}
        ids = []
        ids = self.search(cr, uid, [('symbol', 'ilike', name)] + args, limit = limit, context = context)
        ids += self.search(cr, uid, [('name', operator, name)] + args, limit = limit, context = context)
        return self.name_get(cr, uid, ids, context)

    def name_get(self, cr, uid, ids, context = None):
        """ Force name of object with symbol
        """
        res = []
        for item in self.browse(cr, uid, ids, context = context):
            res.append((item.id, "%s [%s]" % (item.name, item.symbol)))
        return res

    _columns = {
        'name':fields.char('Element', size=64, required=True, readonly=False),
        'symbol':fields.char('Chemical symbol', size=15, required=False, readonly=False),
        'atomic': fields.integer('Atomic number', help="Atomic number if the element is a periodic table element, instead of not indicate")
    }

class chemical_product_category(osv.osv):
    ''' Category of product
    '''
    _name = 'chemical.product.category'
    _description = 'Category'

    _columns = {
        'name':fields.char('Type', size=64, required=True, readonly=False),
        'note': fields.text('Note'),
        'code':fields.char('Code', size=5, required=True, readonly=False, help="Usually 2 char of product code"),
    }

class chemical_product_analysis_model(osv.osv):
    ''' Element that could belong to a category
    '''
    _name = 'product.product.analysis.model'
    _description = 'Analysis mode'
    _order = 'family,name'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        """ Force name search also in family
        """
        if args is None:
            args = []

        ids = []
        ids = self.search(cr, uid, [('family', 'ilike', name)] + args, limit=limit, context=context)
        ids += self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def name_get(self, cr, uid, ids, context=None):
        """ Force name of object with group-family
        """
        res = []
        for item in self.browse(cr, uid, ids, context=context):
            res.append((item.id, "%s [%s]" % (item.name, item.family)))
        return res

    # --------
    # Utility:
    # --------
    def category_from_code(self, cr, uid, code, context=None):
        ''' Utility function for get category from code
        '''
        if not code:
            return False

        category_pool = self.pool.get('chemical.product.category')
        category_ids = category_pool.search(cr, uid, [('code', '=', code)], context=context)
        if category_ids:
            return category_ids[0]
        return False

    def model_from_product_code(self, cr, uid, default_code, context=None):
        ''' Utility function for get model id from code
        '''
        if not default_code or len(default_code)<6:
            return False

        model_ids = self.search(cr, uid, [('family', '=', default_code[:6])], context=context)
        if model_ids:
            return model_ids[0]
        return False

    def update_all_category_and_product(self, cr, uid, force=False, context=None):
        ''' Procedure Una tantum for updating all:
            1. In model set category depend on first 2 char
            2. In product set model analysis depend on family-group (first 6 char of the code)
            3. Update all old product standard value when empty

            force: force update instead don't touch record with model present
        '''
        # Update category from family-group:
        _logger.info("Update category in model depend on family-group code")
        model_ids = self.search(cr, uid, [], context=context)
        for model in self.browse(cr, uid, model_ids, context=context):
            self.write(cr, uid, model.id, {
                'chemical_category_id': self.category_from_code(cr, uid, model.family[:2], context=context)
            }, context=context)

        # Update product from family-group (onli from 01 - 10)
        _logger.info("Update produc model depend on default_code")
        product_pool = self.pool.get('product.product')
        domain = [('default_code', '>=', '01'), ('default_code', '<=', '10'), ]
        if not force:
            domain.append(('model_id', '=', False)) # only empty domain

        product_ids = product_pool.search(cr, uid, domain, context=context)
        for product in product_pool.browse(cr, uid, model_ids, context=context):
            product_pool.write(cr, uid, product.id, {
                'model_id': self.model_from_product_code(cr, uid, product.default_code, context=context)
            }, context=context)
        _logger.info("Updated %s product record (%s)!" % (len(product_ids), "force" if force else "not forced"))

        # Update standard value
        _logger.info("Update standard value where is empty")
        line_pool = self.pool.get('product.product.analysis.line')
        line_ids = line_pool.search(cr, uid, ['|', ('standard', '=', ''), ('standard', '=', False)], context=context)

        for line in line_pool.browse(cr, uid, line_ids, context=context):
            line_pool.write(cr, uid, line.id, {
                'standard': "> %s" % (line.min),
            }, context=context)

        _logger.info("Updated %s model line record!" % (len(line_ids)))
        return True

    # -----------------
    # On change events:
    # -----------------
    def on_change_family_code(self, cr, uid, ids, family, context=None):
        ''' Set chemical category depend on code
        '''
        res = {}
        res['value'] = {}
        if family:
            res['value']['chemical_category_id'] = self.category_from_code(cr, uid, family[:2], context=context)
        else:
            res['value']['chemical_category_id'] = False
        return res

    _columns = {
        'name':fields.char('Analysis model name', size=80, required=True, readonly=False),
        'chemical_category_id':fields.many2one('chemical.product.category', 'Chemical Category', required=False),
        'analysis_line_ids':fields.one2many('product.product.analysis.line', 'model_id', 'Lines per element', required=False),
        'note': fields.text("Note"),

        'family':fields.char('Group', size=15, required=False, readonly=False, help="Product code, first 6 chars, ex.: 010234"),
    }

class chemical_product_category_line(osv.osv):
    ''' Analysis model line (range for single element)
    '''
    _name = 'product.product.analysis.line'
    _description = 'Analysis model line'

    # -----------------
    # On change events:
    # -----------------
    def onchange_standard_value(self, cr, uid, ids, standard, context=None):
        ''' Compute min and max value depend on standard value
        '''
        def get_float(value):
            ''' Parse text return float
            '''
            try:
                value = float(value.strip().replace(",","."))
                if value < 0.0 or value > 100.0:
                    return 0.0
                return value
            except:
                pass
            return 0.0

        res = {}
        if not standard:
            return res
        min_value = 0.0
        max_value = 100.0

        if standard[:1] == ">":
            if standard[1:2] == "=":
                min_value = get_float(standard[2:])
            else:
                min_value = get_float(standard[1:])
            error = not(min_value) # error if not present
        elif standard[:1] == "<":
            if standard[1:2] == "=":
                max_value = get_float(standard[2:])
            else:
                max_value = get_float(standard[1:])
            error = not(max_value) # error if not present
        else:
            error = True
        if error:
            res['warning'] = {}
            res['warning']['title'] = _('Check format:')
            res['warning']['message'] = _('The standard value is not in correct format\nExamples:\n> 10.5\n>= 11\n<=4.56\nNote: numbers are from 0 to 100.')
        else:
            res['value'] = {}
            res['value']['min'] = min_value
            res['value']['max'] = max_value

        return res

    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=True),
        'symbol': fields.related('name','symbol', type='char', string='Symbol'),
        'model_id':fields.many2one('product.product.analysis.model', 'Model', required=False, on_delete='cascade'),
        'min': fields.float('Min %', digits=(16, 4), help="Min value of element for this category"),
        'max': fields.float('Max %', digits=(16, 4), help="Max value of element for this category"),
        'valutation': fields.selection([
            ('=','In range'),
            ('<','> Min %'),
            ('>','< Max %'),
        ],'Valutation', readonly=False),
        'standard':fields.char('Standard', size=15, required=False, readonly=False, help="Use values like: '>14.45' or '<100'"),
    }

    _defaults = {
        'valutation': lambda *x: '=',
    }

class chemical_product_analysis_model(osv.osv):
    ''' Element that could belong to a category
    '''
    _name = 'product.product.analysis.model'
    _inherit = 'product.product.analysis.model'

    _columns = {
        'analysis_line_ids':fields.one2many('product.product.analysis.line', 'model_id', 'Lines per element', required=False),
    }

class product_product_extra_fields(osv.osv):
    ''' Extra field to catalog product for chemical category and composition range
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    _description = 'Category'

    def onchange_default_code(self, cr, uid, ids, default_code, model_id, context=None):
        ''' Search default model if not present
        '''
        res = {}
        if model_id or not default_code or len(default_code)<6: # no code or model yet present
            return res

        chemical_pool = self.pool.get('product.product.analysis.model')
        chemical_ids = chemical_pool.search(cr, uid, [('family', '=', default_code[:6])], context=context)
        if chemical_ids:
            res['value'] = {}
            res['value']['model_id']=chemical_ids[0]
        return res


    _columns = {
        'model_id':fields.many2one('product.product.analysis.model', 'Model', required=False, on_delete='cascade'),
        'need_analysis': fields.boolean('Need analysis', help='Check this if the product require an analysis every purchase or sold', required=False),
        'chemical_category_id': fields.related('model_id', 'chemical_category_id', type='many2one', relation="chemical.product.category", string='Category', readonly=True, store=True),
    }

    _defaults = {
        'need_analysis': lambda *a: True,
    }

class chemical_analysis(osv.osv):
    ''' Chemical Analysis:
        This is the analysis element linked to a stock move for every product that
        enter in company (or for the product that required it)
    '''
    _name = 'chemical.analysis'
    _description = 'Analysis'
    _order = 'code desc,date desc'

    # ---------
    # Override:
    # ---------
    '''def create(self, cr, uid, vals, context = None):
        """ Add code from sequence
        """
        import pdb; pdb.set_trace()
        if 'code' not in vals:
            vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'chemical.analysis')
            res_id = super(chemical_analysis, self).create(cr, uid, vals, context = context)
        else:
            res_id = False    
        return res_id'''

    # -------
    # button:
    # -------

    def load_from_model(self, cr, uid, ids, context = None):
        ''' Button for load elements from model:
        '''
        analysis_proxy = self.browse(cr, uid, ids, context = context)[0]
        actual = [line.name.id for line in analysis_proxy.line_ids]
        if not(analysis_proxy.prodlot_id and analysis_proxy.prodlot_id.product_id and analysis_proxy.prodlot_id.product_id.model_id):
            raise osv.except_osv(_('Error!'), _('No model found in product linked to lot!'))

        try:
            chemical_line_pool = self.pool.get('chemical.analysis.line')
            model_pool = self.pool.get('product.product.analysis.model')
            model_ids = model_pool.search(cr, uid, [('id', '=', analysis_proxy.prodlot_id.product_id.model_id.id)], context = context)
            for line in model_pool.browse(cr, uid, model_ids, context = context)[0].analysis_line_ids:
                if line.name.id in actual: # update min / max value
                    chemical_line_pool.write(cr, uid, line.id, {
                        'model_line_id': line.id,
                        'valutation': line.valutation,
                        'min': line.min,
                        'max': line.max,
                        'standard': line.standard
                    }, context = context)
                    actual.remove(line.name.id)
                else:
                    chemical_line_pool.create(cr, uid, {
                        'name': line.name.id,
                        'chemical_analysis_id': analysis_proxy.id,
                        'model_line_id': line.id,
                        'valutation': line.valutation,
                        'min': line.min,
                        'max': line.max,
                        'standard': line.standard
                    }, context = context)
            #model_pool.unlink(cr, uid, actual, context = context)
        except:
            raise osv.except_osv(_('Error!'), _('Caricamento non riuscito [%s]!' % (sys.exc_info()[0], )))

        return True
    """
    #============================#
    # Workflow Activity Function #
    #============================#
    def form_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)
 
    def form_complete(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'complete'}, context=context)

    def form_cancel(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'cancel'}, context=context)"""

    _columns = {
        'code': fields.char('Code', size = 8, required = False, readonly = False),
        'name': fields.char('Description', size=100, required=True, readonly=False),
        'date': fields.date('Date'),
        'quantity': fields.float('Q. anal. (int.)', digits=(16, 4), help="Quantity used for intenral analysis"), # TODO update store movements removing this quantity?
        'quantity_lab1': fields.float('Q. anal. (lab.1)', digits=(16, 4), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'quantity_lab2': fields.float('Q. anal. (lab.2)', digits=(16, 4), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'quantity_lab3': fields.float('Q. anal. (lab.3)', digits=(16, 4), help="Quantity used for laboratory analysis"), # TODO update store movements removing this quantity?
        'code_lab1':fields.char('Code pattern 1', size=8, required=False, readonly=False),
        'code_lab2':fields.char('Code pattern 2', size=8, required=False, readonly=False),
        'code_lab3':fields.char('Code pattern 3', size=8, required=False, readonly=False),

        'prodlot_id':fields.many2one('stock.production.lot', 'Lot', required=True, on_delete='cascade'),
        'product_id': fields.related('prodlot_id','product_id', type='many2one', relation='product.product', string='Product', store = True),
        'model_id': fields.related('product_id','model_id', type='many2one', relation='product.product.analysis.model', string='Analysis model'),
        'chemical_category_id': fields.related('product_id','chemical_category_id', type='many2one', relation="chemical.product.category", string='Chem Category', readonly=True,),
        'date_in': fields.related('prodlot_id','date', type='datetime', string='Date create'),
        'note': fields.text('Note'),

        'laboratory1_id':fields.many2one('res.partner', 'Laboratory 1', required=False),
        'laboratory2_id':fields.many2one('res.partner', 'Laboratory 2', required=False),
        'laboratory3_id':fields.many2one('res.partner', 'Laboratory 3', required=False),

        #'state': fields.selection([
        #     ('draft', 'Draft'),
        #     ('complete', 'Complete'),
        #     ('cancel', 'Cancel'),], 'State', select=True),
    }

    _defaults = {
        'quantity': lambda *a: 0.0,
        'quantity_lab1': lambda *a: 0.0,
        'quantity_lab2': lambda *a: 0.0,
        'quantity_lab3': lambda *a: 0.0,
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'code': lambda s, cr, uid, ctx: s.pool.get('ir.sequence').get(cr, uid, 'chemical.analysis')
        #'state': lambda *a: 'draft',
    }

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

class res_partner_laboratory_extra_field(osv.osv):
    """ extra field for partner = laboratory
    """
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'is_laboratory':fields.boolean('Is laboratory', required=False),
    }

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
        res = {}

        for line in self.browse(cr, uid, ids):
            if line.model_line_id:  # only if there's the generator line
               test_value=[
                   item for item in (
                       line.percentage,
                       line.percentage_supplier,
                       line.percentage_lab1,
                       line.percentage_lab2,
                       line.percentage_lab3,
                   ) if item > 0.0]
               res[line.id] = {}
               # default values:
               res[line.id]['out_of_range'] = False
               res[line.id]['min_all'] = 0.0
               res[line.id]['max_all'] = 0.0

               if test_value:  # jump all empty
                  res[line.id]['min_all'] = min(test_value)
                  res[line.id]['max_all'] = max(test_value)
                  if res[line.id]['min_all'] < line.model_line_id.min or res[line.id]['max_all'] > line.model_line_id.max: # over value?
                     res[line.id]['out_of_range']=True
        return res

    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=True),
        'chemical_analysis_id': fields.many2one(
            'chemical.analysis', 'Analysis', required=False,
            on_delete='cascade'),

        'percentage': fields.float('% internal', digits=(16, 4), required=True, help="Supplier value"),
        'percentage_supplier': fields.float('% supplier', digits=(16, 4), required=True, help="Internal value"),
        'percentage_lab1': fields.float('% laboratory 1', digits=(16, 4), required=True, help="Laboratory 1 value"),
        'percentage_lab2': fields.float('% laboratory 2', digits=(16, 4), required=True, help="Laboratory 2 value"),
        'percentage_lab3': fields.float('% laboratory 3', digits=(16, 4), required=True, help="Laboratory 3 value"),

        'note': fields.text('Note'),
        'symbol': fields.related('name', 'symbol', type='char', string='Symbol'),

        'model_line_id': fields.many2one('product.product.analysis.line', 'Model line', required=False, on_delete='cascade', help="reference for range for this element"),

        'min': fields.related('model_line_id', 'min', type='float', digits=(16, 4), string='Min'),
        'max': fields.related('model_line_id', 'max', type='float', digits=(16, 4), string='Max'),

        'out_of_range': fields.function(_function_is_in_range, method=True, type='boolean', string='Out of range', store=True, multi=True), #fnct_search=_function_search_in_range,
        'min_all': fields.function(_function_is_in_range, method=True, type='float', digits=(16, 4), string='Min % of all', store=True, multi=True),
        'max_all': fields.function(_function_is_in_range, method=True, type='float', digits=(16, 4), string='Min % of all', store=True, multi=True),
        'valutation': fields.selection([
            ('=','In range'),
            ('<','> Min %'),
            ('>','< Max %'),
        ],'Valutation', readonly=False),

        'standard': fields.related('model_line_id', 'standard', type='char', size=10, string='Standard'),
    }

    _defaults = {
        'percentage': lambda *x: 0.0,
        'percentage_supplier': lambda *x: 0.0,
        'percentage_lab1': lambda *x: 0.0,
        'percentage_lab2': lambda *x: 0.0,
        'percentage_lab3': lambda *x: 0.0,
        'note': lambda *x: False,
    }

class chemical_analysis(osv.osv):
    ''' Chemical Analysis inherit for o2m fields:
    '''
    _name = 'chemical.analysis'
    _inherit = 'chemical.analysis'

    _columns = {
       'line_ids': fields.one2many('chemical.analysis.line', 'chemical_analysis_id', 'Analysis', required=False),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
