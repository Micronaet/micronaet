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


class MrpProductionDailyReport(orm.Model):
    """ Model name: Mrp Production for daily report
    """
    
    _inherit = 'mrp.production'
    
    # -------------------------------------------------------------------------
    # Scheduled action:
    # -------------------------------------------------------------------------
    def extract_daily_mrp_stats_excel_report(self, cr, uid, context=None):
        ''' Jobs: unload and load material last production day
        '''
        import pdb; pdb.set_trace()

        # Pool used:
        load_pool = self.pool.get('mrp.production.workcenter.line') # Job / SL
        unload_pool = self.pool.get('mrp.production.workcenter.load') # CL
        excel_pool = self.pool.get('excel.writer')
        
        today = datetime.now()
        last = False
        for day in range(1, 7):
            last = today - timedelta(days=day)
            if last.isoweekday() in range(1, 5): # Working day 1-5
                break
                
        if not last:
            _logger.error('Cannot find last day!')
            return False

        last_date = ('%s' % last)[:10]
        from_last = '%s 00:00:00' % last_date
        to_last = '%s 23:59:00' % last_date
        
        _logger.info('Reporting moved product in day: [%s - %s]' % (
            from_last, to_last))

        # ---------------------------------------------------------------------
        # Excel start:
        # ---------------------------------------------------------------------               
        ws_name = u'Lotes'
        excel_pool.create_worksheet(name=ws_name)

        # Format:
        excel_pool.set_format()
        excel_format = {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),
            'text': {
                '': excel_pool.get_format('text'),
                'red': excel_pool.get_format('bg_red'),
                'yellow': excel_pool.get_format('bg_yellow'),
                'blue': excel_pool.get_format('bg_blue'),
                },
            'number': {
                '': excel_pool.get_format('number'),
                'red': excel_pool.get_format('bg_red_number'),
                'yellow': excel_pool.get_format('bg_yellow_number'),
                'blue': excel_pool.get_format('bg_blue_number'),
                },
            }
        
        # Column:
        width = [15, 40, 10, 8]
        excel_pool.column_width(ws_name, width)

        # ---------------------------------------------------------------------         
        # Unload documents (over last date):
        # ---------------------------------------------------------------------         
        product_moved = {
            'Materie prime': {},
            'Prodotto finito': {},
            }
        header = [u'Codice', u'Descrizione', u'Linea', u'# SL']

        row = 0
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        unload_ids = unload_pool.search(cr, uid, [        
            ('real_date_planned', '<=', to_last),
            ('real_date_planned_end', '>=', from_last),
            ], context=context)

        unload_document = unload_pool.browse(
                cr, uid, unload_ids, context=context)
        for unload in unload_document:
            # Excel log:
            row += 1 
            excel_pool.write_xls_line(ws_name, row, [(
                unload.name,
                'Prodotto: %s' % unload.product.default_code,
                unload.workcenter_id.name,
                unload.accounting_sl_code,
                )], default_format=excel_format['text'])

            # Product collect:
            for material in unload.bom_material_ids:
                product = material.product_id
                if product not in product_moved['Materie prime']:
                    product_moved['Materie prime'].append(product)
        
        # ---------------------------------------------------------------------         
        # Load documents (in last date):
        # ---------------------------------------------------------------------         
        header = [u'Codice', u'Descrizione', u'# CL']

        row += 2
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        load_ids = load_pool.search(cr, uid, [        
            ('date', '>=', from_last),
            ('date', '<=', to_last),
            ], context=context)

        for load in load_pool.browse(cr, uid, load_ids, context=context):
            # Excel log:
            row += 1 
            excel_pool.write_xls_line(ws_name, row, [(
                load.name,
                'Prodotto: %s' % load.product.default_code,
                load.accounting_cl_code,
                )], default_format=excel_format['text'])

            # Product collect:
            product = load.product_id
            # product_qty
            if product not in product_moved['Prodotto finito']:
                product_moved['Prodotto finito'].append(product)

        # ---------------------------------------------------------------------         
        # Product / Material status:        
        # ---------------------------------------------------------------------         
        for mode in product_moved:
            row += 2
            header = [mode, u'Nome', u'Magaz.']
            excel_pool.write_xls_line(                    
                ws_name, row, header, default_format=excel_format['header'])
        
            for product in sorted(
                    product_moved[mode], key=lambda x: x.default_code):
                excel_pool.write_xls_line(ws_name, row, [
                    product.default_code,
                    product.name,
                    product.accounting_qty,
                    ], default_format=excel_format['text'])
                                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
