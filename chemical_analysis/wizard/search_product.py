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
import time


# Generic function
def return_view(self, cr, uid, domain):
    """Function that return dict action for next step of the wizard
    """
    # res_id, view_name):
    # view_element=view_name.split(".")
    # views=[]
    # if len(view_element)==2:
    #   model_id=self.pool.get('ir.model.data').search(cr, uid, [
    #   ('model','=','ir.ui.view'),
    #   ('module','=',view_element[0]),
    #   ('name', '=', view_element[1])])
    #   if model_id:
    #      view_id=self.pool.get('ir.model.data').read(cr, uid, model_id)[
    #      0]['res_id']
    #      views=[(view_id,'tree')]

    return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.production.lot', # object linked to the view
            # 'views': views,
            # 'views': [(False,'tree'),(False,'form')],
            'view_id': False,
            'type': 'ir.actions.act_window',
            # 'target': 'new',
            'domain':[('id', 'in', domain)],
            # 'res_id': res_id,  # ID selected
           }

class search_element_wizard(osv.osv_memory):
    """ Search range of value for elements in analysis for lot
    """
    _name = 'search.element.wizard'

    def search_button(self, cr, uid, ids, context=None):
        """ Search button:
            search the element selected in analysis line and test the range of
            element after redirect to lot view showing only lot that have
            element in analyisis with correct values
        """
        if context is None:
           context = {}

        # read wizard to get value:
        wizard_proxy=self.read(cr, uid, ids, context=context)[0]

        analysis_line_proxy=self.pool.get('chemical.analysis.line')

        # search elements line to get lot (after)
        # TODO create a filter more restricted (only one value can works instead of the range all include)
        find_line_ids=analysis_line_proxy.search(cr, uid, [('name','=',wizard_proxy['name']),
                                                           ('min_all','>=',wizard_proxy['min']),
                                                           ('min_all','<=',wizard_proxy['max']),
                                                           ('max_all','>=',wizard_proxy['min']),
                                                           ('max_all','<=',wizard_proxy['max']),
                                                           ])

        # get lot list from analysis lines:
        domain_list_ids=[item.chemical_analysis_id.prodlot_id.id for item in analysis_line_proxy.browse(cr, uid, find_line_ids) if item.chemical_analysis_id.prodlot_id]
        return return_view(self, cr, uid, domain_list_ids)

    _columns = {
        'name': fields.many2one('chemical.element', 'Element', required=True),
        'min': fields.float('Min %', digits=(16, 2), help="Min value of element in %", required=True),
        'max': fields.float('Max %', digits=(16, 2), help="Max value of element in %", required=True),
        'note': fields.text('Note'),
    }

    _defaults = {
        'min': lambda *a: 0.0,
        'max': lambda *a: 100.0,
        'note': lambda *a: """Search lot that have analysis for this element that stay in setted range,\nnote that every element can have 5 measure,\nsupplier, customer, labs, so every line have a min value and a max value,\nthe range setted here must comprend all 2 values!""",
    }
search_element_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
