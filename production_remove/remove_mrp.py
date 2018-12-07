#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class MrpProduction(orm.Model):
    """ Model name: MrpProduction
    """
    
    _inherit = 'mrp.production'

    # Button event:
    def remove_production(self, cr, uid, ids, context=None): 
        ''' Remove MRP document and all linked documents
        '''
        production_id = ids[0]
        mask = 'DELETE FROM %s WHERE %s = %s;'        

        # Delete workcenter line:        
        delete_line = [
            ('mrp_production_material', 'workcenter_production_id'),
            ('mrp_production_workcenter_load', 'line_id'),        
            ]
        for mrp in self.browse(cr, uid, ids, context=context):
            for line in mrp.workcenter_lines:
                line_id = line.id
                for record in delete_line:
                    table, field = record
                    query = mask % (table, field, line_id)
                    print query
                    cr.execute(query)
                    
                
        # Delete linked document query:
        delete_record = [
            # Cascade:
            #('mrp_production_assign_wizard', 'production_id'),
            ('mrp_production_material', 'mrp_production_id'),  
            ('mrp_production_material', 'mrp_waste_id'),
            ('mrp_production_move_ids', 'production_id'),
            ('mrp_production_package', 'production_id'),
            ('mrp_production_workcenter_line', 'production_id'),

            # Set Null
            ('mrp_operations_operation', 'production_id'),
            ('mrp_production_product_line', 'production_id'),
            ('mrp_production_product_packaging', 'production_id'),
            ('mrp_production_workcenter_load', 'production_id'),
            ('procurement_order', 'production_id'),
            ('sale_order_line', 'mrp_production_id'),
            ('stock_move', 'production_id'),
            
            # This:
            ('mrp_production', 'id'),
            ]
        for record in delete_record:
            table, field = record
            query = mask % (table, field, production_id)
            print query
            cr.execute(query)
        return True        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
