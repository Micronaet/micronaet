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

        current = self.browse(cr, uid, ids, context=context)[0]
        
        # Create DB if not present
        
        # Create production
        
        # Create job
        
        # Confirm unload
        
        # Confirm load
        
        return True

    def onchange_product_id(self, cr, uid, ids, from_id, context=None):
        ''' Onchange product id update product stock status
        '''
        product_pool = self.pool.get('product.product')

        detail = ''
        qty = total = 0.0
        if from_id:                
            product = product_pool.browse(cr, uid, from_id, context=context)
            for lot in product.pedimento_ids:                
                subtotal = lot.standard_price * lot.product_qty
                qty += lot.product_qty
                total += subtotal
                detail += _('<font %s>Code: %s Q. %s [Price %s]<br/>') % (
                    '' if subtotale else 'color="red"'  ,
                    lot.code,
                    lot.product_qty,
                    lot.standard_price,
                    )
            return {'value': {
                'remain_detail': detail,
                'remain_qty': qty,
                'remain_price': total / qty if qty else 0.0,
                }}
        else:        
            return {'value': {
                'remain_detail': '',
                'remain_qty': 0.0,
                'remain_price': 0.0,
                }}
        
    _columns = {
        'from_id': fields.many2one('product.product', 'Waste product',
            help='Current product to be moved in waste',
            required=True),
        'to_id': fields.many2one('product.product', 'Waste product',
            help='Product considered waste', required=True),
        'force_price': fields.float('Force price', digits=(16, 2)),

        # Stock detail:
        'remain_detail': fields.text('Remain detail', readonly=True, 
            help='Detail of all lot / pedimentos present'), 
        'remain_qty': fields.float('Remain qty', readonly=True,
            digits=(16, 2), help='Remain q. present in stock'),
        'remain_price': fields.float('Remain price', readonly=True,
            digits=(16, 2), help='Medium price of lot present'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
