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


class MrpProduction(orm.Model):
    """ Model name: MrpProduction
    """

    _inherit = 'mrp.production'

    def extract_mrp_stats_excel_report(
            self, cr, uid, report_mode='all', context=None):
        """ Extract report statistic and save in Excel file:
        """
        # =====================================================================
        #                             UTILITY:
        # =====================================================================
        def _get_product_mode(product):
            """ Extract final product, raw material, italian product
            """
            product_type = product.product_type
            default_code = (product.default_code or '').upper()
            if not product_type or not default_code:
                return 'ERR'

            if product_type == 'PT':
                if default_code.endswith('X'):
                    return 'PF'
                else:
                    return 'IT'  # Comes from Italy
            else:
                return 'MP'

        def _get_load_date(load):
            """ Problem: much load was done in the same day in initial phase
            """
            date = load.date
            if date >= '2019-08-01':
                # Use correct load date:
                return date
            else:
                # Use production date:
                return load.line_id.production_id.date_planned

        def _get_period_date_dict(range_date):
            """ Generate period dict:
            """
            year_cols = {}  # Used for hide columns in report page
            res = {}
            ref_date = range_date[0]
            col = 0

            while ref_date <= range_date[1]:
                res[ref_date] = col

                # Update ref_date:
                year = ref_date[:4]

                # Total month per years (for hide after)
                if year not in year_cols:
                    year_cols[year] = 0
                year_cols[year] += 1

                if ref_date[5:7] == '12':
                    ref_date = '%s-01' % (int(ref_date[:4]) + 1)
                else:
                    ref_date = '%s-%02d' % (
                        year,
                        int(ref_date[5:7]) + 1,
                        )
                col += 1
            return res, year_cols

        # =====================================================================
        #                         INITIAL SETUP:
        # =====================================================================
        year_cols = {
            'unload': {},
            'load': {},
            }

        currency = 'MXP'
        if context is None:
            context = {}
        save_mode = context.get('save_mode')

        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')
        job_pool = self.pool.get('mrp.production.workcenter.line')

        # Collect data:
        now = ('%s' % datetime.now())[:7]
        total = {
            # Stock status:
            'product': {},  # Product stock status

            # MRP:
            'load': {},  # Product load
            'unload': {},  # Raw material unload

            'production': {},  # Total production for product

            'check': {},  # Check production totals (in and out)
            }

        # month_column = []
        _logger.info('%s. Start extract MRP statistic: %s' %
                    (now, save_mode))

        # =====================================================================
        #                     STOCK PRODUCT DATA:
        # =====================================================================

        # ---------------------------------------------------------------------
        # Lot status:
        # ---------------------------------------------------------------------
        ws_name = u'Inventario'  # Create before (Lotes didn't hide as first)
        excel_pool.create_worksheet(name=ws_name)

        ws_name = 'Lotes'
        excel_pool.create_worksheet(name=ws_name)
        # excel_pool.freeze_panes(ws_name, row, col)

        if report_mode == 'minimal':
            excel_pool.hide(ws_name)

        # Format:
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')

        f_text = excel_pool.get_format('text')
        f_text_red = excel_pool.get_format('bg_red')
        f_text_bg_blue = excel_pool.get_format('bg_blue')
        f_text_bg_yellow = excel_pool.get_format('bg_yellow')

        f_number = excel_pool.get_format('number')
        f_number_red = excel_pool.get_format('bg_red_number')
        f_number_bg_blue = excel_pool.get_format('bg_blue_number')
        f_number_bg_yellow = excel_pool.get_format('bg_yellow_number')
        f_number_bg_blue_bold = excel_pool.get_format('bg_blue_number_bold')
        f_number_bg_red_bold = excel_pool.get_format('bg_red_number_bold')
        f_number_bg_green_bold = excel_pool.get_format('bg_green_number_bold')

        # Column:
        width = [
            5, 12, 30, 20, 5,
            10, 10, 15, 5
            ]
        header = [
            u'Tipo', u'Codigo', u'Descripción', u'Lote', u'UM',
            u'C.', u'Precio', u'Subtotal', u'Moneda'
            ]

        row = 0
        excel_pool.column_width(ws_name, width)

        # Data:
        product_ids = product_pool.search(cr, uid, [], context=context)
        product_proxy = product_pool.browse(
            cr, uid, product_ids, context=context)

        page_total = {}
        temp_list = []
        for product in sorted(
                product_proxy, key=lambda x: (x.default_code, x.name)):
            for lot in product.pedimento_ids:
                qty = lot.product_qty
                if not qty:
                    continue

                uom = product.uom_id
                price = lot.current_price  # ex. lot.standard_price
                subtotal = qty * price

                # -------------------------------------------------------------
                # Total block:
                # -------------------------------------------------------------
                if uom not in page_total:
                    page_total[uom] = [0.0, 0.0]
                page_total[uom][0] += qty
                page_total[uom][1] += subtotal

                # -------------------------------------------------------------
                # COLLECT DATA:
                # -------------------------------------------------------------
                # PAGE: Prodotti
                if product not in total['product']:
                    # Quantity, Subtotal, Check OK
                    total['product'][product] = [0.0, 0.0, True]
                total['product'][product][0] += qty
                total['product'][product][1] += subtotal

                # Color setup:
                if subtotal:
                    f_text_current = f_text
                    f_number_current = f_number
                else:
                    f_text_current = f_text_red
                    f_number_current = f_number_red
                    total['product'][product][2] = False  # Not OK

                # Write data:
                temp_list.append(([
                    _get_product_mode(product),
                    product.default_code or '',
                    product.name,
                    lot.code or '',
                    uom.name,
                    (qty, f_number_current),
                    (price, f_number_current),
                    (subtotal, f_number_current),
                    currency,
                    ], f_text_current))

        # ---------------------------------------------------------------------
        # Write total:
        # ---------------------------------------------------------------------
        # Write subtotal:
        master_total = 0.0
        for uom in sorted(page_total, key=lambda x: x.name):
            qty, subtotal = page_total[uom]
            master_total += subtotal
            # Write data:
            excel_pool.write_xls_line(
                ws_name, row, [
                    '', '', '',
                    u'Parcial',
                    uom.name,
                    qty,
                    '',
                    subtotal,
                    currency
                    ], default_format=f_number_bg_blue_bold)
            row += 1

        # Write end total:
        excel_pool.write_xls_line(
            ws_name, row, [
                u'Total:',
                master_total,
                currency
                ], default_format=f_number_bg_green_bold, col=6)

        # ---------------------------------------------------------------------
        # Write all data:
        # ---------------------------------------------------------------------
        # Header:
        row += 2 # extra space
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # Auto-filter:
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)

        # Data:
        for record, f_text_current in temp_list:
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, record, default_format=f_text_current)

        # ---------------------------------------------------------------------
        # Product status:
        # ---------------------------------------------------------------------
        ws_name = u'Inventario'

        # Column:
        width = [
            5, 12, 30, 5,
            10, 15,
            5, 5,
            ]
        header = [
            u'Tipo', u'Codigo', u'Productos', u'UM',
            u'C.', u'Subtotal',
            u'Moneda', u'Error',
            ]

        row = 0
        excel_pool.column_width(ws_name, width)

        # Data:
        partial = 0.0  # Stock value

        temp_list = []
        for product in sorted(total['product'],
                key=lambda x: (x.default_code, x.name)):
            qty, subtotal, ok = total['product'][product]

            # Color setup:
            if ok:
                f_text_current = f_text
                f_number_current = f_number
            else:
                f_text_current = f_text_red
                f_number_current = f_number_red

            # Write data:
            temp_list.append(([
                _get_product_mode(product),
                product.default_code or '',
                product.name,
                product.uom_id.name,
                (qty, f_number_current),
                (subtotal, f_number_current),
                currency,
                '' if ok else 'X',
                ], f_text_current))

        # ---------------------------------------------------------------------
        # Write total:
        # ---------------------------------------------------------------------
        master_total = 0.0
        for uom in sorted(page_total, key=lambda x: x.name):
            qty, subtotal = page_total[uom]
            master_total += subtotal
            # Write data:
            excel_pool.write_xls_line(
                ws_name, row, [
                    '', '',
                    u'Parcial',
                    uom.name,
                    qty,
                    subtotal,
                    currency,
                    ], default_format=f_number_bg_blue_bold)
            row += 1

        # Write data:
        excel_pool.write_xls_line(
            ws_name, row, [
                u'Total:',
                master_total,
                currency,
                ], default_format=f_number_bg_green_bold, col=4)

        # ---------------------------------------------------------------------
        # Write data:
        # ---------------------------------------------------------------------
        # Header:
        row += 2
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # Autofilter:
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)

        for record, f_text_current in temp_list:
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, record, default_format=f_text_current)

        # =====================================================================
        #                   Collect data for Production:
        # =====================================================================
        # Data:
        job_ids = job_pool.search(cr, uid, [
            ('production_id.mode', '=', 'production'),
            ('state', '=', 'done'),
            ], context=context)

        page_total = {}
        for job in job_pool.browse(cr, uid, job_ids, context=context):
            # -----------------------------------------------------------------
            # Check data page:
            # -----------------------------------------------------------------
            mrp = job.production_id
            if mrp not in total['check']:
                total['check'][mrp] = [0.0, 0.0] # raw material, final product

            # -----------------------------------------------------------------
            # Load data:
            # -----------------------------------------------------------------
            for load in job.load_ids:
                # Check data page:
                total['check'][mrp][1] += load.product_qty  # Final product

                # (Mode, Product, Qty, Price, Recycle)
                production_price = (load.accounting_cost / load.product_qty) \
                    if load.product_qty else 0.0

                try:
                    package_price = \
                        load.package_pedimento_id.current_price or \
                        load.package_id.linked_product_id.standard_price
                except:
                    _logger.error('No package price, no product linked')
                    package_price = 0.0
                try:
                    pallet_price = \
                        load.pallet_pedimento_id.current_price or \
                        load.pallet_product_id.standard_price,
                except:
                    _logger.error('No pallet price, no product linked')
                    pallet_price = 0.0

                loop = [(
                    # Product:
                    'load',
                    job.product,
                    load.product_qty - load.waste_qty,
                    production_price,
                    False), (

                    # Package:
                    'unload',
                    load.package_id.linked_product_id,
                    load.ul_qty,
                    package_price,
                    False), (

                    # Pallet:
                    'unload',
                    load.pallet_product_id,
                    load.pallet_qty,
                    pallet_price,
                    False),
                    ]

                if load.waste_qty:  # load.recycle:
                    loop.append((
                        # Recycle:
                        'load',
                        load.waste_id,
                        load.waste_qty,
                        production_price,  # Same as real production
                        True,
                        ))

                for mode, product, qty, price, recycle in loop:
                    if not product:
                        continue

                    if product not in total[mode]:
                        total[mode][product] = []
                    total[mode][product].append((
                        _get_load_date(load)[:10],  # Date operation (sort key)
                        load.line_id,  # Workcenter line
                        qty,
                        price,
                        recycle,
                        ))

            # -----------------------------------------------------------------
            # Unload data:
            # -----------------------------------------------------------------
            for unload in job.bom_material_ids:
                product = unload.product_id
                date = job.production_id.date_planned[:10]  # Directly MRP Date

                if product not in total['unload']:
                    total['unload'][product] = []
                total['unload'][product].append((
                    date,
                    job,  # Workcenter line
                    unload.quantity,
                    unload.current_pedimento_price or unload.standard_price,
                    0.0,  # Never present
                    ))

                # Check data page:
                total['check'][mrp][0] += unload.quantity  # Raw material

        # =====================================================================
        #                        PRODUCTION DETAIL:
        # =====================================================================

        # ---------------------------------------------------------------------
        # Production loaded product:
        # ---------------------------------------------------------------------
        ws_name = u'Cargas de producción'
        excel_pool.create_worksheet(name=ws_name)
        if report_mode == 'minimal':
            excel_pool.hide(ws_name)

        # Column:
        width = [
            10, 15, 15, 30, 10,
            5, 10, 10,
            15, 15, 5,
            ]
        header = [
            u'Fecha', u'Referencia', u'Producto', u'Descripción', u'Linea',
            u'UM', u'C.', u'C. incorrecta',
            u'Precio carga', u'Subtotal', u'Moneda',
            ]

        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        range_date = [False, False]
        for product in sorted(
                total['load'],
                key=lambda x: (x.default_code, x.name)):

            # Readability:
            for date, job, qty, price, recycle in sorted(
                    total['load'][product], reverse=True):

                # Setup range data for load:
                period = date[:7]
                if not range_date[0] or period < range_date[0]:
                    range_date[0] = period
                if not range_date[1] or period > range_date[1]:
                    range_date[1] = period

                subtotal = price * qty

                if recycle:
                    recycle_qty = qty
                    qty = 0.0
                    f_text_color = f_text_bg_blue
                    f_number_color = f_number_bg_blue
                else:
                    recycle_qty = 0.0
                    f_text_color = f_text
                    f_number_color = f_number

                # Write data:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [
                        date,
                        job.name,
                        product.default_code or '',
                        product.name,
                        job.workcenter_id.name,

                        product.uom_id.name or '',
                        (qty, f_number_color),
                        (recycle_qty, f_number_color),

                        (price, f_number_color),
                        (subtotal, f_number_color),
                        currency,
                        ], default_format=f_text_color)
        load_col, year_cols['load'] = _get_period_date_dict(range_date)

        # ---------------------------------------------------------------------
        # Production unloaded product:
        # ---------------------------------------------------------------------
        ws_name = u'Descargas de producción'
        excel_pool.create_worksheet(name=ws_name)
        if report_mode == 'minimal':
            excel_pool.hide(ws_name)

        # Column:
        width = [
            10, 15, 15, 30, 10,
            5, 10,
            15, 15, 5,
            ]
        header = [
            u'Fecha', u'Referencia', u'Materia prima', u'Descripción',
            u'Líneas', u'UM', u'C.',
            u'Precio descarga', u'Subtotal', u'Moneda',
            ]

        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        range_date = [False, False]  # reset previous assigned
        # todo Sort not necessary here!?!
        for product in sorted(
                total['unload'],
                key=lambda x: (x.default_code, x.name),
                ):

            # Readability:
            for date, job, qty, price, recycle in sorted(
                    total['unload'][product], reverse=True):

                # Setup range data for load:
                period = date[:7]
                if not range_date[0] or period < range_date[0]:
                    range_date[0] = period
                if not range_date[1] or period > range_date[1]:
                    range_date[1] = period

                subtotal = price * qty

                # Write data:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [
                        date,
                        job.name,
                        product.default_code or '',
                        product.name,
                        job.workcenter_id.name,

                        product.uom_id.name or '',
                        (qty, f_number),

                        (price, f_number),
                        (subtotal, f_number),
                        currency,
                        ], default_format=f_text)

        unload_col, year_cols['unload'] = _get_period_date_dict(range_date)

        # =====================================================================
        #                           REPORT FOR CHECK
        # =====================================================================
        # ---------------------------------------------------------------------
        # Production in / out data:
        # ---------------------------------------------------------------------
        ws_name = u'Control de producción'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            22, 25,
            5, 12, 12,
            10, 10,
            ]
        header = [
            u'Producción', u'Productos',
            u'UM', u'Materies primas', u'P. terminado',
            u'Reducción', u'R. %',
            ]

        row = 0
        excel_pool.column_width(ws_name, width)

        page_total = [0.0, 0.0]
        temp_list = []
        for mrp in sorted(
                total['check'],
                key=lambda x: x.name,
                reverse=True,
                ):
            material, product = total['check'][mrp]
            mrp_product = mrp.product_id
            # Page total:
            page_total[0] += material
            page_total[1] += product

            lost = material - product
            if product:
                if material:
                    rate = lost / material * 100.0
                else:
                    rate = 0.0
            else:
                rate = 0.0

            # Setup color:
            if not rate:
                f_text_color = f_text_bg_blue
                f_number_color = f_number_bg_blue
            elif rate > 10.0:
                f_text_color = f_text_bg_yellow
                f_number_color = f_number_bg_yellow
            elif rate < 0.0:
                f_text_color = f_text_red
                f_number_color = f_number_red
            else:
                f_text_color = f_text
                f_number_color = f_number

            # Write fixed col data:
            sort_date = mrp.date_planned[:10]
            temp_list.append((
                sort_date,
                [
                    ('%s del %s' % (mrp.name, sort_date), f_text_color),
                    ('[%s] %s' % (
                        mrp_product.default_code or '-',
                        mrp_product.name or '',
                        ), f_text_color),
                    (mrp_product.uom_id.name, f_text_color),

                    '%10.2f' % round(material, 2),
                    '%10.2f' % round(product, 2),
                    '%10.2f' % round(lost, 2),
                    '%10.2f' % round(rate, 2),
                ],
                f_number_color))

        # ---------------------------------------------------------------------
        # Write total:
        # ---------------------------------------------------------------------
        total_material, total_product = page_total
        lost = total_material - total_product

        excel_pool.write_xls_line(
            ws_name, row, [
                (u'Totales', f_header),
                (u'KG', f_header),
                total_material,
                total_product,
                u'%10.2f' % round(lost, 2),
                u'%10.2f' % round(100.0 * lost / total_material, 2),
                ], default_format=f_number_bg_green_bold, col=1)

        # ---------------------------------------------------------------------
        # Write data:
        # ---------------------------------------------------------------------
        # Header:
        row += 1
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        for sort_date, record, f_number_color in sorted(
                temp_list, reverse=True):
            # , key=lambda r: r[0][0], reverse=True
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, record, default_format=f_number_color)

        # =====================================================================
        #                           REPORT x PERIOD
        # =====================================================================
        # Create all sheet in reverse order per years:
        # =====================================================================
        all_year = set(year_cols['load']) | set(year_cols['unload'])
        for year_block in sorted(all_year, reverse=True):
            if year_block in year_cols['load']:
                # Production in period:
                ws_name = u'Producción en el periodo %s' % year_block
                excel_pool.create_worksheet(name=ws_name)

            if year_block in year_cols['unload']:
                # Material in period:
                ws_name = u'Descargas en el periodo %s' % year_block
                excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [10, 30, 4, 10]
        header = [u'Productos', u'Descripción', u'UM', u'Total']

        fixed_col = len(header)
        col_total = []

        for col in sorted(load_col):
            width.append(8)
            header.append(col)
            col_total.append(0.0)  # always KG
        empty = col_total[:]

        temp_list = []
        for product in sorted(
                total['load'],
                key=lambda x: (x.default_code, x.name)):

            row_total = {}
            data = empty[:]
            for date, job, qty, price, recycle in total['load'][product]:
                period = date[:7]
                if period[:4] in row_total:
                    row_total[period[:4]] += qty
                else:
                    row_total[period[:4]] = qty

                col = load_col.get(period)

                # Totals:
                data[col] += qty
                col_total[col] += qty

            temp_list.append(([
                product.default_code or '',
                product.name,
                product.uom_id.name,
                row_total,
                ], data))

        # =====================================================================
        #                    PRODUCTION PER YEARS:
        # =====================================================================
        for year_block in sorted(
                year_cols['load'],
                reverse=True,
                ):
            # -----------------------------------------------------------------
            # Production in period:
            # -----------------------------------------------------------------
            ws_name = u'Producción en el periodo %s' % year_block
            # excel_pool.create_worksheet(name=ws_name)

            # -----------------------------------------------------------------
            # Write total (row 0):
            # -----------------------------------------------------------------
            row = 0

            excel_pool.column_width(ws_name, width)
            # Write fixed col data:
            excel_pool.write_xls_line(
                ws_name, row, [u'Totales KG', ], default_format=f_header,
                col=fixed_col - 1)

            # Write variable col data:
            excel_pool.write_xls_line(
                ws_name, row, col_total, default_format=f_number_bg_green_bold,
                col=fixed_col)
            row += 1

            # -----------------------------------------------------------------
            # Write data:
            # -----------------------------------------------------------------
            # Header:
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=f_header)

            for fixed, data in temp_list:
                row += 1
                new_fixed = fixed[:]
                new_fixed[-1] = (
                    new_fixed[-1].get(year_block),
                    f_number_bg_green_bold,
                    )

                # Write fixed col data:
                excel_pool.write_xls_line(
                    ws_name, row, new_fixed, default_format=f_text)

                # Write variable col data:
                excel_pool.write_xls_line(
                    ws_name, row, data, default_format=f_number, col=fixed_col)

                if not new_fixed[-1][0]:
                    # Hide row
                    excel_pool.row_hidden(ws_name, [row])

            # Hide unused colums:
            hide_this_cols = []
            left_start = fixed_col
            for year in sorted(year_cols['load']):
                total_month = year_cols['load'][year]
                for item in range(total_month):
                    if year != year_block:
                        hide_this_cols.append(left_start + item)
                left_start += year_cols['load'][year]
            excel_pool.column_hidden(ws_name, hide_this_cols)

        # =====================================================================
        #                       UNLOAD PER YEARS:
        # =====================================================================
        # Column:
        width = [10, 30, 4, 10]
        header = [u'Materia', u'Descripción', u'UM', u'Total']

        fixed_col = len(header)
        col_total = {}

        empty = []
        for col in sorted(load_col):
            width.append(8)
            header.append(col)
            empty.append(0.0)

        temp_list = []
        for product in sorted(
                total['unload'],
                key=lambda x: (x.default_code, x.name)):
            uom = product.uom_id
            if uom not in col_total:
                col_total[uom] = []
                for col in sorted(load_col):
                    col_total[uom].append(0.0)

            row_total = {}
            data = empty[:]
            for date, job, qty, price, recycle in total['unload'][product]:
                period = date[:7]
                if period[:4] in row_total:
                    row_total[period[:4]] += qty
                else:
                    row_total[period[:4]] = qty
                col = unload_col.get(period)

                # Totals:
                data[col] += qty
                col_total[uom][col] += qty

            temp_list.append(([
                product.default_code or '',
                product.name,
                product.uom_id.name,
                row_total,
                ], data))

        for year_block in sorted(
                year_cols['unload'],
                reverse=True,
                ):
            # -----------------------------------------------------------------
            # Material in period:
            # -----------------------------------------------------------------
            ws_name = u'Descargas en el periodo %s' % year_block
            # excel_pool.create_worksheet(name=ws_name)

            row = 0
            excel_pool.column_width(ws_name, width)

            # -----------------------------------------------------------------
            # Write total:
            # -----------------------------------------------------------------
            for uom in col_total:
                total = col_total[uom]

                # Write fixed col data:
                excel_pool.write_xls_line(
                    ws_name, row, [u'Totales %s' % uom.name],
                    default_format=f_header, col=fixed_col - 1)

                # Write variable col data:
                excel_pool.write_xls_line(
                    ws_name, row, total, default_format=f_number_bg_green_bold,
                    col=fixed_col)
                row += 1

            # -----------------------------------------------------------------
            # Write data:
            # -----------------------------------------------------------------
            # Header:
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=f_header)

            for fixed, data in temp_list:
                row += 1
                new_fixed = fixed[:]
                new_fixed[-1] = (
                    new_fixed[-1].get(year_block),
                    f_number_bg_green_bold,
                    )

                # Write fixed col data:
                excel_pool.write_xls_line(
                    ws_name, row, new_fixed, default_format=f_text)

                # Write variable col data:
                excel_pool.write_xls_line(
                    ws_name, row, data, default_format=f_number, col=fixed_col)

                if not new_fixed[-1][0]:
                    # Hide row
                    excel_pool.row_hidden(ws_name, [row])

            # Hide unused columns:
            hide_this_cols = []
            left_start = fixed_col
            for year in sorted(year_cols['unload']):
                total_month = year_cols['unload'][year]
                for item in range(total_month):
                    if year != year_block:
                        hide_this_cols.append(left_start + item)
                left_start += year_cols['unload'][year]
            excel_pool.column_hidden(ws_name, hide_this_cols)

        return excel_pool.save_file_as(save_mode)
