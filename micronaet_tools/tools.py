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
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class micronaet_tools(orm.Model):
    ''' Empty class for export method as tools for utlity purposes
    '''
    _name = 'micronaet.tools'
    _description = 'Micronaet Tools'

    # -------------------------------------------------------------------------
    #                             Utility tools:
    # -------------------------------------------------------------------------
    
    # ---------------
    # Wizard utility:
    # ---------------
    def get_view_dict(self, cr, uid, args):
        ''' Return a dict for call view (as a return of a button)
            Parameter passed are (* are mandatory):
            
            param model*: object for the view
            param module*: module name for the view
            param record: record id to open
            param name: name of the view (caption)

            param tree: tree view name (or false)
            param form: form view name (or false)
            param calendar: calendar view name (or false)
            param gantt: gantt view name (or false)
            param graph: graph view name (or false)

            param default: default view (ex.: 'form', 'tree' etc)
            param type: type of view ('form' or 'tree)
            param domain: domain passed to new view
            param context: context passed to new view            

            @return: dict with view to return 
            
        '''
        model = args.get('model', False)
        module = args.get('module', False)
        if not (module and model):
            return {}

        # Read all parameters for view:
        default = args.get('default', False)
        view_id = False
        views = []
        
        data_pool = self.pool.get('ir.model.data')
        for view in ['form', 'tree', 'calendar', 'gantt', 'graph']:
            try: # compose views parameter:
                if view in args: 
                    name, item_id = data_pool.get_object_reference(
                        cr, uid, module, args.get(view))
                    views.append((item_id, view)) #[(form_id, 'form')],
                    if default == view: # Use as first view
                        view_id = item_id
            except:
                pass # no view if 

        return {
            'name': args.get('name', False),
            'view_type': args.get('type', 'form'),
            'view_mode': args.get('mode', 'form,tree'),
            'res_model': model,
            'res_id': args.get('record', False),
            'view_id': view_id,
            'views': views, 
            'domain': args.get('domain', False),
            'context': args.get('context', False),
            'type': 'ir.actions.act_window',
            }
    
    _columns = {}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
