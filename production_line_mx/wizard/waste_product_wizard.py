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
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare,
    )


_logger = logging.getLogger(__name__)


class MrpProductionWasteWizard(osv.osv_memory):
    ''' Wizard for create waste product
    '''
    _name = 'mrp.production.waste.wizard'

    # -------------------------------------------------------------------------
    #                        Wizard button events:
    # -------------------------------------------------------------------------
    def action_confirm_move(self, cr, uid, ids, context=None):
        ''' Write confirmed weight (load or unload documents)
        '''
        if context is None:
            context = {}

        # Pool used:
        company_pool = self.pool.get('res.company')
        mrp_pool = self.pool.get('mrp.production')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')
        load_pool = self.pool.get('mrp.production.workcenter.load')

        # Create DB if not present
        
        # Create production
        
        # Create job
        
        # Confirm unload
        
        # Confirm load
        
        return True

    def _get_remain_information(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''    
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = {
                'remain_detail': '',
                'remain_qty': 0.0,                
                'remain_price': 0.0,                
                }
            from_id = item.product_id
            if not from_id:
                continue
 
            qty = total = 0.0
            for lot in from_id.pedimento_ids:                
                subtotal = lot.standard_price * lot.product_qty
                qty += lot.product_qty
                total += subtotal
                res[item.id][
                    'remain_detail'] += _('Code: %s Q. %s [Price %s]%s\n')  % (
                        lot.code,
                        lot.product_qty,
                        lot.standard_price,
                        '' if subtotal else _(' * ERROR!'),
                        )
            res[item.id]['remain_qty'] = qty
            res[item.id]['remain_price'] = total / qty if qty else 0.0
        return res
            
    _columns = {
        'from_id': fields.many2one('product.product', 'Waste product',
            help='Current product to be moved in waste'
            required=True),
        'to_id': fields.many2one('product.product', 'Waste product',
            help='Product considered waste'),
        'remain_detail': fields.function(
            _get_remain_information, method=True, 
            type='text', string='Remain detail', 
            help='Detail of all lot / pedimentos present'), 
        'remain_qty': fields.function(
            _get_remain_information, method=True, 
            type='float', string='Remain qty', 
            help='Remain q. present in stock'),
        'remain_price': fields.function(
            _get_remain_information, method=True, 
            type='float', string='Remain price', 
            help='Medium price of lot present'),
        'force_price': fields.float('Force price', digits=(16, 2)),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
