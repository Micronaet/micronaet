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
import logging
import shutil
from openerp.osv import fields, osv, expression, orm
from openerp.tools.translate import _
import pdb

_logger = logging.getLogger(__name__)


class ResCompanyButton(orm.Model):
    """ Model name: Company
    """
    _inherit = 'res.company'

    def button_bom_last_cost_evaluate(self, cr, uid, ids, context=None):
        """ Report for check status for pallet and for account
        """
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        bom_pool = self.pool.get('mrp.bom')

        # --------------------------------------------------------------------------------------------------------------
        # Collect data:
        # --------------------------------------------------------------------------------------------------------------
        bom_ids = bom_pool.search(cr, uid, [
            ('bom_id', '=', False),
        ], context=context)
        boms = bom_pool.browse(cr, uid, bom_ids, context=context)

        report_data = {}
        for bom in boms:
            product = bom.product_id
            default_code = (product.default_code or '').upper()
            if default_code in report_data:
                report_data[default_code]['error'] = True
                report_data[default_code]['error_comment'].add('Doppione presente')
                _logger.error('BOM yet present!')
                continue
            else:
                report_data[default_code] = {
                    'bom': bom,
                    'product': product,
                    'detail': '',  # BOM detail
                    'total': 0.0,
                    'error': False,
                    'error_comment': set(),
                }

            weight = 0.0
            for line in bom.bom_lines:
                material = line.product_id
                material_code = (material.default_code or '').upper()
                product_uom = material.uom_id
                qty = line.product_qty
                price = material.standard_price
                partial = qty * price
                # product.force_manual
                # product.manual_price
                weight += qty

                report_data[default_code]['detail'] += u'%s: %s%s x %s = %s [%s] (F. %s)\n' % (
                    material_code,
                    # material.name,
                    qty,
                    product_uom.name,
                    price,
                    partial,
                    material.name or '',
                    material.first_supplier_id.name or u'Non presente',
                    )
                report_data[default_code]['total'] += partial
                if not partial and material_code[:2] != 'VV':
                    report_data[default_code]['error'] = True
                    report_data[default_code]['error_comment'].add('Prezzi a zero nella ricetta')
            if abs(weight - 1.0) > 0.00000001:
                report_data[default_code]['error'] = True
                report_data[default_code]['error_comment'].add('Ricetta non a peso 100%')

        # --------------------------------------------------------------------------------------------------------------
        # Generate Excel File:
        # --------------------------------------------------------------------------------------------------------------
        row = 0
        ws_name = 'Ricette'
        excel_pool.create_worksheet(ws_name)

        # Format:
        excel_pool.set_format(number_format='0.#0')
        excel_pool.get_format()
        excel_format = {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),
            'white': {
                'text': excel_pool.get_format('text'),
                'number': excel_pool.get_format('number')
            },
            'green': {
                'text': excel_pool.get_format('bg_green'),
                'number': excel_pool.get_format('bg_green_number')
            },
            'red': {
                'text': excel_pool.get_format('bg_red'),
                'number': excel_pool.get_format('bg_red_number')
            },
            'blue': {
                'text': excel_pool.get_format('bg_blue'),
                'number': excel_pool.get_format('bg_blue_number')
            },
        }

        # Column setup width:
        col_width = [
            11, 30, 5, 10,
            10, 45,
            5, 45,
        ]
        excel_pool.column_width(ws_name, col_width)

        # Header:
        header = [
            'Codice', 'Nome', 'Obsol.', 'Prezzo',
            'Ultima prod.', 'Dettaglio',
            'Errore', 'Commento errore'
        ]
        excel_pool.write_xls_line(ws_name, row, header, excel_format['header'])
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)
        excel_pool.freeze_panes(ws_name, row + 1, 2)

        for default_code in sorted(report_data):
            row += 1
            record = report_data[default_code]
            bom = record['bom']
            product = record['product']
            # is_primary = bom.is_primary

            # Setup color:
            if record['error']:
                color_format = excel_format['red']
            else:
                color_format = excel_format['white']

            data = [
                default_code,
                product.name,
                'X' if bom.obsolete else ' ',
                (record['total'], color_format['number']),
                bom.last_mrp_use or '',
                record['detail'],
                'X' if record['error'] else ' ',
                '\n'.join(tuple(record['error_comment']))
                ]
            excel_pool.write_xls_line(
                ws_name, row, data, color_format['text'])

        return excel_pool.return_attachment(
            cr, uid, name='Costo prodotti', name_of_file='bom_price.xlsx',
            version='7.0', php=True, context=context)

