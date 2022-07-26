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
import pdb
import sys
import copy
import openerp.netsvc as netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp import tools
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from utility import *

_logger = logging.getLogger(__name__)


class mrp_production_extra(osv.osv):
    """ Create extra fields in mrp.production obj
    """
    _name = 'mrp.production'
    _inherit = ['mrp.production', 'mail.thread']

    # -------------------------------------------------------------------------
    # Utility for procedure:
    # -------------------------------------------------------------------------
    def add_element_material_composition(
            self, product, quantity, table, table_comment, extra_comment, rows,
            with_medium, material_mx, month_window, start_date, range_date,
            real_date_planned, col_ids, supplier_orders,
            ):
        """ Block used for unload materials and for simulation
        """
        default_code = product.default_code

        if product.not_in_status: # Jump 'not in status' material
            return

        if with_medium and product:
            # Kg.
            try:
                media = material_mx.get(product.id, 0.0) / month_window
            except:
                media = 0.0
        else:
            media = 0.0

        element = (
            'M',
            product.id,
            product, # XXX for minimum
            media,
            )
        if element not in rows:
            rows.append(element)
            # prepare data structure:
            table[element[1]] = [0.0 for item in range(0,range_date)]
            table_comment[element[1]] = ['' for item in range(0,range_date)]

            # prepare data structure:
            # Sapnaet integrazione:
            accounting_qty = product.accounting_qty
            try:
                accounting_qty += product.locked_qty
            except:
                pass  # No sapnaet mode

            table[element[1]][0] = accounting_qty
            table_comment[element[1]][0] += \
                'Gest.: Q. %s\n' % accounting_qty

        if real_date_planned in col_ids:
            position = col_ids[real_date_planned]
        else:  # XXX TODO manage over date!?! < today
            position = 1

        # Write data:
        table[element[1]][position] -= quantity
        table_comment[element[1]][position] += '%s: Q. %s [%s] %s\n' % (
            'CL prod.' if quantity > 0 else 'SL prod.',
            quantity,
            real_date_planned,
            extra_comment,
            )

        # -------------------------------------------------------------
        # OF order:
        # -------------------------------------------------------------
        if default_code in supplier_orders: # all OF orders
            for of_deadline in supplier_orders[default_code].keys():
                # deadline is present in the window of cols

                if of_deadline in col_ids:
                    position = col_ids[of_deadline]
                elif of_deadline < start_date.strftime('%Y-%m-%d'):
                    # deadline < today:
                    position = 1
                else:
                    continue

                of_qty = supplier_orders[default_code][of_deadline]
                table[element[1]][position] += of_qty
                # delete OF value (no other additions):
                del(supplier_orders[default_code][of_deadline])
                table_comment[element[1]][position] += 'OF: Q. %s [%s]\n' % (
                    of_qty,
                    real_date_planned,
                    )
        return

    # -------------------------------------------------------------------------
    # Utility for report:
    # -------------------------------------------------------------------------
    def get_external_supplier_order(self, cr, uid, context=None):
        """ Load OF order
        """
        accounting_pool = self.pool.get('micronaet.accounting')

        # todo Filter period?? (optimizing the query!)
        cursor_of = accounting_pool.get_of_line_quantity_deadline(cr, uid)
        supplier_orders = {}
        if not cursor_of:
            _logger.error(
                'Error access OF line table in accounting! (status webkit)')
        else:
            for supplier_order in cursor_of:  # all open OC
                ref = supplier_order['CKY_ART'].strip()
                if ref not in supplier_orders:
                    supplier_orders[ref] = {}
                # todo verify if not present
                of_deadline = supplier_order['DTT_SCAD'].strftime('%Y-%m-%d')

                q = float(supplier_order['NQT_RIGA_O_PLOR'] or 0.0) * (
                    1.0 / supplier_order['NCF_CONV']
                    if supplier_order['NCF_CONV'] else 1.0)
                if of_deadline not in supplier_orders[ref]:  # todo test UM
                    supplier_orders[ref][of_deadline] = q
                else:
                    supplier_orders[ref][of_deadline] += q
        return supplier_orders

    def _start_up(self, cr, uid, data=None, context=None):
        """ Master function for prepare report
        """
        if data is None:
            data = {}

        # Pool used:
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')
        order_line_pool = self.pool.get('sale.order.line')

        # Global parameters:
        global rows, cols, table, table_comment, history_supplier_orders, \
            minimum, error_in_print

        # initialize globals:
        rows = []
        cols = []
        minimum = {}
        table = {}
        table_comment = {}

        error_in_print = ''  # todo manage for set in printer

        # todo optimize:
        product_ids = product_pool.search(cr, uid, [], context=context)
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            minimum[product.id] = product.min_stock_level

        # Init parameters:
        col_ids = {}
        range_date = data.get('days', 7) + 1
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=range_date - 1)
        # with_order_detail = data.get('with_order_detail', False) # no used

        # 0 (<today), 1..n [today, today + total days], delta)
        for i in range(0, range_date):
            if i == 0:  # today
                d = start_date
                cols.append(d.strftime('%d/%m'))
                col_ids[d.strftime('%Y-%m-%d')] = 0
            elif i == 1:  # before today
                d = start_date
                cols.append(d.strftime('< %d/%m'))
                col_ids['before'] = 1  # not used!
            else:  # other days
                d = start_date + timedelta(days=i - 1)
                cols.append(d.strftime('%d/%m'))
                col_ids[d.strftime('%Y-%m-%d')] = i

        # ---------------------------------------------------------------------
        #                     SYNCRO PRE REPORT
        # ---------------------------------------------------------------------
        # --------------------------------------
        # 1. Import status material and product:
        # --------------------------------------

        # ------------------------------
        # 2. Get OF lines with deadline:
        # ------------------------------
        supplier_orders = self.get_external_supplier_order(
            cr, uid, context=context)

        # Used for print order detail in result:
        history_supplier_orders = copy.deepcopy(supplier_orders)

        # -------------------
        # 3. Get OC elements:
        # -------------------

        # ---------------------------
        # 4. Get m(x) for production:
        # ---------------------------
        material_mx = {}
        with_medium = data.get('with_medium', False)
        month_window = data.get('month_window', 2)
        if with_medium:
            from_date = (
                datetime.now() - timedelta(days=30 * month_window)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
            lavoration_material_ids = lavoration_pool.search(cr, uid, [
                ('real_date_planned', '>=', from_date),
                ('state', 'in', ('done', 'startworking')),
                ], context=context)
            for lavoration in lavoration_pool.browse(
                    cr, uid, lavoration_material_ids, context=context):
                for material in lavoration.bom_material_ids:
                    product = material.product_id # Readability:
                    if product.id in material_mx:
                        material_mx[product.id] += material.quantity or 0.0
                    else:
                        material_mx[product.id] = material.quantity or 0.0

        # ---------------------------------------------------------------------
        #                       GENERATE HEADER VALUES
        # ---------------------------------------------------------------------
        # -------------------------------
        # Get product list from OC lines:
        # -------------------------------
        # > populate cols

        line_ids = order_line_pool.search(cr, uid, [
            ('date_deadline', '<=', end_date.strftime('%Y-%m-%d')),
            ], context=context) # only active from accounting
        for line in order_line_pool.browse(cr, uid, line_ids, context=context):
            if line.product_id.not_in_status: # jump line if product checked!
                _logger.warning(
                    'Not in status product: %s' % line.product_id.name)
                continue
            element = (
                'P',
                line.product_id.id,
                line.product_id,  # XXX used for min qty
                0.0,
                )
            # initialize row (today, < today, +1, +2, ... +n)
            if element not in rows:
                rows.append(element)

                # prepare data structure
                table[element[1]] = [0.0 for item in range(0, range_date)]

                # start q.
                # Sapnaet integrazione (if stock linked to order)
                account_qty = line.product_id.accounting_qty
                try:
                    account_qty += line.product_id.locked_qty  # need dep.
                except:
                    pass  # No sapnaet mode
                table[element[1]][0] = account_qty

            if line.order_id.date_deadline in col_ids: # all date
                table[element[1]][col_ids[line.order_id.date_deadline]] -= \
                    line.product_uom_qty or 0.0  # OC deadlined this date
            if not line.order_id.date_deadline or \
                    line.order_id.date_deadline < start_date.strftime(
                        '%Y-%m-%d'):  # only < today
                # OC deadlined before today:
                table[element[1]][1] -= line.product_uom_qty or 0.0

        # ---------------------------------------------------------------------
        #                   Get material list from Lavoration order
        # ---------------------------------------------------------------------
        # Populate cols:
        lavoration_ids = lavoration_pool.search(cr, uid, [
            # only < max date range
            ('real_date_planned', '<=', end_date.strftime(
                '%Y-%m-%d 23:59:59')),
            ('state', 'not in', ('cancel','done')),
            ], context=context) # only open not canceled

        for lavoration in lavoration_pool.browse(
                cr, uid, lavoration_ids, context=context): # filtered BL orders

            real_date_planned = lavoration.real_date_planned[:10] # readability

            # -----------------------------------------------------------------
            # Product in lavoration order:
            # -----------------------------------------------------------------
            element = (
                'P',
                lavoration.product.id,
                lavoration.product,
                0.0,
                )

            if element not in rows:
                # prepare data structure:
                rows.append(element)
                table[element[1]] = [0.0 for item in range(0, range_date)]

                account_qty = lavoration.product.accounting_qty
                # Sapnaet integrazione (if stock linked to order)
                try:
                    account_qty += lavoration.product.locked_qty  # need dep.
                except:
                    pass  # No sapnaet mode
                table[element[1]][0] = account_qty

            # Product production:
            if real_date_planned in col_ids:
                table[element[1]][col_ids[real_date_planned]] += \
                    lavoration.product_qty
            else: # < today  (element 1 - the second)
                table[element[1]][1] += lavoration.product_qty

            # -----------------------------------------------------------------
            # Material in BOM:
            # -----------------------------------------------------------------
            extra_comment = '%s (Lav. %s)' % (
                lavoration.product.default_code, lavoration.name)
            for material in lavoration.bom_material_ids:

                self.add_element_material_composition(
                    material.product_id,
                    material.quantity,
                    table,
                    table_comment,
                    extra_comment,
                    rows,
                    # Medium block:
                    with_medium, material_mx, month_window,
                    # Period:
                    start_date, range_date,
                    real_date_planned,
                    # OF data:
                    col_ids, supplier_orders,
                    )

        # ---------------------------------------------------------------------
        #                 Production simulation:
        # ---------------------------------------------------------------------
        for fake in data['fake_ids']:
            qty = fake.qty
            # Read BOM materials:
            extra_comment = 'Simulaz. produz.'
            for material in fake.bom_id.bom_lines:
                self.add_element_material_composition(
                    material.product_id,
                    qty * material.product_qty,
                    table,
                    table_comment,
                    extra_comment,
                    rows,
                    # Medium block:
                    with_medium, material_mx, month_window,
                    # Period:
                    start_date, range_date,
                    fake.production_date,
                    # OF data:
                    col_ids, supplier_orders,
                    )
        rows.sort()

        # -----------------------
        # Generation table data:
        # -----------------------
        # > Setup initial value:
        # > Import -q for material in lavoration:
        # > Import -q for sumulation of production:
        # > Import +q for product in lavoration:
        # > Import OC product in line with deadline:
        # > Import OF material with deadline:
        # global rows, cols, table, history_supplier_orders, minimum, \
        #    error_in_print
        return True

    def _get_table(self, ):
        """ Return reference for table
        """
        global table, table_comment
        return table, table_comment

    def _get_rows(self, context=None):
        """ Rows list (generated by _start_up function)
        """
        # Global parameters:
        global rows
        return rows

    def _get_cols(self, context=None):
        """ Cols list (generated by _start_up function)
        """
        # Global parameters:
        global cols
        return cols

    def _get_history_supplier_orders(self, context=None):
        """ Cols list (generated by _start_up function)
        """
        # Global parameters:
        global history_supplier_orders
        return history_supplier_orders

    def _get_cel(self, col, row, context=None):
        """ Cel value from col - row
            row=product_id
            col=n position
            return: (quantity, minimum value)
        """
        # Global parameters:
        global table
        global minimum

        # TODO get from table
        if row in table:
            return (table[row][col], minimum.get(row, 0.0))
        return (0.0, 0.0)

