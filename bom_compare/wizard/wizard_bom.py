# -*- encoding: utf-8 -*-
###############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import osv, fields


class bom_compare_wizard(osv.osv_memory):
    """ Parameter for bom report
    """

    _name = 'etl.bom.line.wizard'
    _description = 'BOM report wizard'

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    def extract_excel_report(self, cr, uid, ids, context=None):
        """ Extract Excel report
        """
        if context is None:
            context = {}

        # Pool used:
        bom_pool = self.pool.get('mrp.bom')
        excel_pool = self.pool.get('excel.writer')

        wizard = self.browse(cr, uid, ids, context=context)[0]
        domain = [
            ('bom_id', '=', False),
        ]
        if not wizard.all:
            domain.append(
                ('product_id.default_code', '=ilike', '%s%%' % wizard.parent),
            )

        # ---------------------------------------------------------------------
        # Excel report setup:
        # ---------------------------------------------------------------------
        ws_name = 'Ricette'
        excel_pool.create_worksheet(ws_name)

        # Format:
        excel_pool.set_format(
            number_format='#,##0.####0',
        )
        excel_format = {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),
            'text': excel_pool.get_format('text'),
            'number': excel_pool.get_format('number'),
            'red': {
                'text': excel_pool.get_format('bg_red'),
                'number': excel_pool.get_format('bg_red_number'),
            },
            'white': {
                'text': excel_pool.get_format('text'),
                'number': excel_pool.get_format('number'),
            },
        }

        # Column setup:
        excel_pool.column_width(ws_name, [
            40,
            15, 35, 5, 10,
        ])

        # Write header:
        row = 0
        header_line = [
            'Prodotto Ricetta',
            'Codice Componente', 'Nome', 'UM', 'Q.',
        ]
        excel_pool.write_xls_line(
            ws_name, row, header_line, default_format=excel_format['header'])
        cols = len(header_line) - 1
        excel_pool.freeze_panes(ws_name, 1, 1)

        bom_ids = bom_pool.search(cr, uid, domain, context=context)
        boms = sorted(
            bom_pool.browse(cr, uid, bom_ids, context=context),
            key=lambda b: b.product_id.default_code or '',
            )
        for bom in boms:
            row += 1
            data = [
                u'%s [%s]' % (
                    bom.product_id.default_code,
                    bom.product_id.name,
                ),
                'Codice', 'Nome', 'UM', 'Q.',
                ]
            excel_pool.write_xls_line(
                ws_name, row, data, default_format=excel_format['header'])
            total = 0.0
            for line in bom.bom_lines:
                row += 1
                component = line.product_id
                uom = line.product_uom
                quantity = line.product_qty * 100.0
                total += quantity

                data = [
                    '',
                    component.default_code or '',
                    component.name or '',
                    uom.name or '',
                    (quantity, excel_format['number']),
                ]
                excel_pool.write_xls_line(
                    ws_name, row, data, default_format=excel_format['text'])

            # Total line:
            row += 1
            if abs(total - 100.0) < 0.000001:
                color_format = excel_format['white']
            else:
                color_format = excel_format['red']
            data = [
                '', '', '', '',
                (total, color_format['number']),
            ]
            excel_pool.merge_cell(
                ws_name,
                [row, 0, row, cols - 1])
            excel_pool.write_xls_line(
                ws_name, row, data, default_format=excel_format['text'])

            # Separator line:
            row += 1
            excel_pool.merge_cell(
                ws_name,
                [row, 0, row, cols])

        return excel_pool.return_attachment(
            cr, uid, 'Disinte base', version='7.0', php=True,
            context=context)

    def print_report(self, cr, uid, ids, context=None):
        """ Redirect to bom report passing parameters
        """
        wiz_proxy = self.browse(cr, uid, ids)[0]

        datas = {}
        if wiz_proxy.all:
            datas['primary'] = False
        else:
            datas['primary'] = wiz_proxy.parent

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'webkitbomline',
            'datas': datas,
        }

    _columns = {
        'all': fields.boolean('All', required=False),
        'parent': fields.char(
            'Parent code', size=40, required=False, readonly=False),
        }

    _defaults = {
        'all': lambda *a: True,
        }


bom_compare_wizard()
