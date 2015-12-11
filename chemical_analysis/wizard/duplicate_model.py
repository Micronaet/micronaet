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
from openerp.osv import osv, fields
from datetime import datetime
from openerp.tools.translate import _

class chemical_model_duplicate_model_wizard(osv.osv_memory):
    """ Search range of value for elements in analysis for lot
    """    
    _name = 'chemical.model.duplicate.model.wizard'
    _description = 'Duplicate model wizard'

    #def onchange_family(self, cr, uid, ids, family, context=None):
    #    ''' Test if family exist
    #    '''
        
    def duplicate_button(self, cr, uid, ids, context=None):
        ''' Run wizard
        '''        
        if context is None:
            context = {}
            
        old_model_id = context.get('active_id', False)
        if not old_model_id:
            # raise error no original model
            return False
            
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]        
        
        model_pool = self.pool.get("product.product.analysis.model")
        model_ids = model_pool.search(cr, uid, [
            ('family', '=', wiz_proxy.family)], context=context)
            
        new_model_id = False    
        if model_ids: # Esistent, open it            
            new_model_id = model_ids[0]
            
        if not model_ids or wiz_proxy.force:    
            # Create header:
            original_model_proxy = model_pool.browse(cr, uid, old_model_id, context=context)
            try:
                chemical_category_id = model_pool.on_change_family_code(cr, uid, old_model_id, wiz_proxy.family, context=context)['value']['chemical_category_id']
            except:
                chemical_category_id = False

            line_pool = self.pool.get("product.product.analysis.line")
            product_pool = self.pool.get("product.product")
            if new_model_id: # yet present but to force:
                line_delete_ids = line_pool.search(cr, uid, [('model_id','=',new_model_id)], context=context)
                line_pool.unlink(cr, uid, line_delete_ids, context=context)
            else:       
                product_ids = product_pool.search(cr, uid, [('default_code', '=', wiz_proxy.family)], context=context)
                if product_ids:
                    product_proxy = product_pool.browse(cr, uid, product_ids, context=context)[0]
                    analysis_name = product_proxy.name
                else:
                    analysis_name = original_model_proxy.name
                    
                new_model_id = model_pool.create(cr, uid, {
                    'name': analysis_name,
                    'family': wiz_proxy.family,
                    'note': original_model_proxy.note,
                    'chemical_category_id': chemical_category_id,            
                }, context=context)
                
            # Create detail line:
            for line in original_model_proxy.analysis_line_ids:                
                line_pool.create(cr, uid, {
                    'name': line.name.id,
                    'symbol': line.symbol,
                    'model_id': new_model_id,
                    'min': line.min,
                    'max': line.max,
                    'valutation': line.valutation,
                    'symbol': line.symbol,
                    'standard': line.standard,
                }, context=context)

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.product.analysis.model', 
            #'views': views,
            #'views': [(False,'tree'),(False,'form')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            #'target': 'new',
            'domain':[('id', '=', new_model_id)],
            'res_id': new_model_id, # ID selected
        }
        
    _columns = {
        'family': fields.char('New group', size=14, required=True, readonly=False),
        'force':fields.boolean('Force', required=False, help="If exit delete elements and replace with this model"),
    }
    _defaults = {
        'force': lambda *a: False,
    }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
