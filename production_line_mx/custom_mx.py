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
import xlrd
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

class product_product_extra(osv.osv):
    ''' Extra fields for product.product object
    '''
    _inherit = "product.product"
    # -------------------------------------------------------------------------
    #                               Scheduled actions
    # -------------------------------------------------------------------------
    def schedule_etl_product_state_mx(
            self, cr, uid, filename=False, start=1, context=None):
        ''' Import from Import Excel file from accounting
        '''
        _logger.info('Start import product account status')
        if not filename:
            _logger.error('No file XLSX passed: %s' % filename)
            return False            
        filename = os.path.expanduser(filename)

        # Pool used:        
        pedimento_pool = self.pool.get('product.pedimento')
        
        # ---------------------------------------------------------------------
        # Clean pedimento:
        # ---------------------------------------------------------------------
        _logger.info('Delete pedimentos')
        pedimento_ids = pedimento_pool.search(cr, uid, [], context=context)
        pedimento_pool.unlink(cr, uid, pedimento_ids, context=context)
             
        # ---------------------------------------------------------------------
        # Read product status:
        # ---------------------------------------------------------------------
        try:
            WB = xlrd.open_workbook(filename)
        except:
            _logger.error('Cannot read XLS file: %s' % filename)
        _logger.info('Read XLS file: %s' % filename)

        WS = WB.sheet_by_index(0)
        total = {}
        for row in range(start, WS.nrows):
            # -----------------------------------------------------------------
            # Read fields:
            # -----------------------------------------------------------------
            default_code = WS.cell(row, 0).value
            pedimento = WS.cell(row, 1).value
            cost = WS.cell(row, 2).value
            qty = WS.cell(row, 3).value
            # TODO log management
            
            # -----------------------------------------------------------------
            # Mandatory fields check:
            # -----------------------------------------------------------------
            if not default_code:
                _logger.error('%s. Code empty (jump line)' % row)
                continue

            product_ids = self.search(cr, uid, [
                ('default_code', '=', default_code)], context=context)
            if not product_ids:
                _logger.error('%s. Code not found in ODOO %s (jump line)' % (
                    row, default_code))
                continue

            product_id = product_ids[0]

            # -----------------------------------------------------------------
            # Total update:
            # -----------------------------------------------------------------
            if product_id not in total:
                total[product_id] = 0
                
            total[product_id] += qty

            # -----------------------------------------------------------------
            # Pedimento:
            # -----------------------------------------------------------------
            if pedimento and qty > 0: # Pedimento present with q positive
                pedimento_pool.create(cr, uid, {
                    'name': pedimento,
                    'product_id': product_id,
                    }, context=context)

            # -----------------------------------------------------------------
            # Log management
            # -----------------------------------------------------------------            
            # TODO 
        
        # ---------------------------------------------------------------------
        # Reset accounting qty in ODOO:
        # ---------------------------------------------------------------------        
        _logger.info('Update product total:')
        product_ids = self.search(cr, uid, [
            ('accounting_qty', '!=', 0),
            ], context=context)
        self.write(cr, uid, product_ids, {
            'accounting_qty': 0.0,
            }, context=context)    
        for product_id in total:
            # -----------------------------------------------------------------
            # Update product data:
            # -----------------------------------------------------------------
            self.write(cr, uid, product_id, {
                'accounting_qty': total[product_id],
                }, context=context)
        _logger.info('End import product account status')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
