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

class confirm_mrp_production_update_wizard(osv.osv_memory):
    """ Update that confirm production/lavoration
    """
    _inherit = 'mrp.production.confirm.wizard'

    def onchange_package_partial_id(self, cr, uid, ids, 
            package_id, product_id, real_product_qty, partial, 
            context=None):
        """ Override with extra parameters 
        """
        if context is None:
            context = {}

        res = self.onchange_package_id(
            cr, uid, ids, 
            package_id, product_id, real_product_qty, 
            context=context)
        
        if 'value' not in res:
            res['value'] = {}
        if partial:
            res['value']['yield_comment'] = False
            #res['value']['yield_comment_hide'] = False
        else:
            # Pool used:
            mrp_pool = self.pool.get('mrp.production')
            lavoration_pool = self.pool.get('mrp.production.workcenter.line')
            current_lavoration_id = context.get('active_id', 0)
            lavoration = lavoration_pool.browse(
                cr, uid, current_lavoration_id, context=context)
            mrp = lavoration.production_id    

            # -----------------------------------------------------------------
            # Update extra field for check data:
            # -----------------------------------------------------------------
            # A. load
            load_qty = real_product_qty # for current
            for load in mrp.load_ids:
                load_qty += load.product_qty
            
            # B. Unoad:
            unload_qty = 0.0
            for unload in mrp.workcenter_lines:
                for line in unload.bom_material_ids:                    
                    unload_qty += line.quantity
            
            # A / B Rate:
            if unload_qty:
                rate = 100.0 * load_qty / unload_qty    
            else:
                rate = 0.0

            mrp_medium_yield = mrp.product_id.mrp_medium_yield    
            if mrp.product_id.mrp_medium_yield > 100.0:
                mrp.product_id.mrp_medium_yield = 100.0

            # Color setup:
            if not mrp_medium_yield:
                color = '#fcdcdd'
                comment = 'Non trovato rendimento per prodotto!</b>'                
            elif rate < mrp_medium_yield:
                color = '#fcdcdd'
                comment = '< <b>%10.3f: Non congruo!</b>' % mrp_medium_yield
            else:    
                color = '#dcfce5'
                comment = '> <b>%10.3f: Congruo!</b>' % mrp_medium_yield

            yield_comment = '''
                <div style="background-color: %s">
                    <b>Dettaglio rendimento:</b><br/>
                    Totale materiale scaricato: <b>%s</b><br/>
                    Totale prodotto caricato: <b>%s</b><br/>
                    Rendimento produzione: <b>%10.3f</b><br/>
                    %s
                </div>
                ''' % (
                    color,
                    unload_qty,
                    load_qty,
                    rate,
                    comment,
                    )
            res['value']['yield_comment'] = yield_comment
            res['value']['yield_comment_hide'] = yield_comment
        return res

    _columns = {
        'yield_comment': fields.text('Rendimento'),
        # Not used for now:
        'yield_comment_hide': fields.text('Rendimento (nascosto)'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
