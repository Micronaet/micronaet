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
import pdb
import sys
import logging
import openerp
import re
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)

class MrpProductionInherit(orm.Model):
    """ Model name: Mrp Production Reports
    """
    _inherit = 'mrp.production'

    def server_action_extract_excel_job_report_saveas(self, cr, uid, context=None):
        """ Extract with force
        """
        if context is None:
            context = {}

        call_context = context.copy()
        call_context['force_filename'] = '/tmp/job_status.xlsx'

        self.server_action_extract_excel_job_report(cr, uid, context=call_context)
        return context['force_filename']

    def server_action_extract_excel_job_report(self, cr, uid, context=None):
        """ Jobs: Extract Job report
        """
        if context is None:
            context = {}

        force_filename = context.get('force_filename')

        # Pool used:
        job_pool = self.pool.get('mrp.production.workcenter.line')  # Job/SL
        excel_pool = self.pool.get('excel.writer')

        _logger.info('Job report')
        re_pattern = r"[-+]?\d*\.\d+|\d+"

        # ---------------------------------------------------------------------
        # Excel start:
        # ---------------------------------------------------------------------
        # Page Check:
        ws_name = 'Jobs completed'
        excel_pool.create_worksheet(name=ws_name)

        # Format:
        excel_format = self.get_excel_format(excel_pool)

        # Column:
        width = [
            5, 15, 25,
            20, 15,
            30,
            12, 12, 12, 12, 12,
        ]
        excel_pool.column_width(ws_name, width)

        header = [
            u'Job ID', u'MRP', u'Line',
            u'Job ref.', u'Date',
            u'Product',
            u'Q. planned', u'Raw mat.', u'Final prod.', u'Waste', u'Load price',
        ]
        row = 0
        excel_pool.write_xls_line(ws_name, row, header, default_format=excel_format['header'])
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)
        excel_pool.freeze_panes(ws_name, row + 1, 3)

        job_ids = job_pool.search(cr, uid, [
            ('state', '=', 'done'),
        ], context=context)
        color_format = excel_format['']
        jobs = job_pool.browse(cr, uid, job_ids, context=context)
        for job in sorted(jobs, key=lambda j: j.real_date_planned, reverse=True):
            product = job.product
            mrp = job.production_id
            line = job.workcenter_id
            # product_price_calc

            # 1. Raw Materials
            unload_qty = 0.0
            for item in job.bom_material_ids:
                unload_qty += item.quantity

            # 2. Final product
            load_qty = waste_qty = 0.0
            for item in job.load_ids:
                load_qty += item.product_qty
                waste_qty += item.waste_qty

            product_price_calc = job.product_price_calc or ''
            match = re.findall(re_pattern, product_price_calc)
            if match:
                try:
                    medium_price = float(match[-1])
                except:
                    medium_price = 'ERROR: {}'.format(match[-1])
            else:
                medium_price = ''

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                job.id,
                mrp.name,
                line.name,

                job.name,
                job.real_date_planned[:10],

                '%s (%s)' % (
                    product.name,
                    product.default_code,
                ),

                (job.product_qty, color_format['number']),

                (unload_qty, color_format['number']),
                (load_qty, color_format['number']),
                (waste_qty, color_format['number']),
                (medium_price, color_format['number']),

            ], default_format=color_format['text'])

        if force_filename:
            return excel_pool.save_file_as(force_filename)
        else:
            return excel_pool.return_attachment(
                cr, uid, 'Job completed', name_of_file=False, version='7.0', php=True, context=context)

