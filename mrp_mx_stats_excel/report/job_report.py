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

class MrpProductionInherit(orm.Model):
    """ Model name: Mrp Production Reports
    """
    _inherit = 'mrp.production'

    def server_action_extract_excel_job_report(self, cr, uid, context=None):
        """ Jobs: Extract Job report
        """
        if context is None:
            context = {}

        # Pool used:
        job_pool = self.pool.get('mrp.production.workcenter.line')  # Job/SL
        excel_pool = self.pool.get('excel.writer')

        _logger.info('Job report')

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
            5, 15, 15,
            20, 18,
            30, 10,
        ]
        excel_pool.column_width(ws_name, width)

        header = [
            u'Job ID', u'MRP', u'Line',
            u'Job ref.', u'Date',
            u'Product', u'Q.',
        ]
        row = 0
        excel_pool.write_xls_line(ws_name, row, header, default_format=excel_format['header'])

        job_ids = job_pool.search(cr, uid, [
            ('state', '=', 'done'),
        ], context=context)
        color_format = excel_format['']
        for job in job_pool.browse(cr, uid, job_ids, context=context):
            product = job.product
            mrp = job.production_id
            line = job.workcenter_id
            # product_price_calc

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                job.id,
                mrp.name,
                line.name,

                job.name,
                job.real_date_planned,

                '%s (%s)' % (
                    product.name,
                    product.default_code,
                ),

                (job.product_qty, color_format['number']),
            ], default_format=color_format['text'])

        return excel_pool.return_attachment(
            cr, uid, 'Job completed', name_of_file=False, version='7.0', php=True, context=context)

