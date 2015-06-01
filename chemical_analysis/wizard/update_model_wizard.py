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


class chemical_model_update_wizard(osv.osv_memory):
    """ Search range of value for elements in analysis for lot
    """    
    _name = 'chemical.model.update.wizard'
    _description = 'Update model and category'
    
    def execute_button(self, cr, uid, ids, context=None):
        ''' Run wizard
        '''        
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        return self.pool.get('product.product.analysis.model').update_all_category_and_product(cr, uid, force=wiz_proxy.force, context=context)
        
    _columns = {
        'name': fields.char('Update mode wizard', size=64, required=False, readonly=False),
        'note': fields.text('Wizard specific'),
        'force': fields.boolean('Force', required=False),
    }
    
    _defaults = {
        'name': "Update wizard",
        'note': """
1. Update in all model the category according with 2 char 
  of start family-group.
2. Update in all product the model searchinh the 6-char 
  family-group in default code""",
        'force': False,               
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
