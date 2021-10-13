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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class MrpProductionExtractStatWizard(orm.TransientModel):
    """ Wizard for extract data from sale, invoice
    """
    _name = 'mrp.production.extract.stat.wizard'
    _description = 'Extract Excel export'

    # -------------------------------------------------------------------------
    # Wizard button event:
    # -------------------------------------------------------------------------
    def action_report(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        def clean_tags(value):
            """ Clean tags element:
            """
            if not value:
                return ''

            res = value.replace('<b>', '').replace('</b>', '').replace(
                '<br />', '\n').replace('<br/>', '\n').replace(
                    '<br>', '\n') or ''
            return res.replace('\n\n', '\n')

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        work_pool = self.pool.get('mrp.production.material')
        excel_pool = self.pool.get('excel.writer')

        # ---------------------------------------------------------------------
        # Parameters:
        # ---------------------------------------------------------------------
        from_date = wiz_proxy.from_date
        to_date = wiz_proxy.to_date
        filter_product = wiz_proxy.product_id
        filter_material = wiz_proxy.material_id
        # report_mode = wiz_proxy.report_mode

        # ---------------------------------------------------------------------
        # Setup domain filter:
        # ---------------------------------------------------------------------
        domain = [
            ('workcenter_production_id', '!=', False),
            ('workcenter_production_id.state', 'not in', ('cancel', 'draft')),
            ]
        # filter_text = _('Report mode: %s') % report_mode
        filter_text = _('Filtro applicato: ')

        # Period:
        if from_date:
            domain.append(
                ('workcenter_production_id.real_date_planned', '>=', from_date)
                )
            filter_text += _(u'[Dalla data %s] ') % from_date
        if to_date:
            domain.append(
                ('workcenter_production_id.real_date_planned', '<=', to_date))
            filter_text += _(u'[Alla data %s] ') % to_date

        # Many2one:
        # Raw material:
        if filter_material:
            domain.append(
                ('product_id', '=', filter_material.id))
            filter_text += _(u'[Materia prima %s] '
                ) % filter_material.default_code

        # ---------------------------------------------------------------------
        #                              EXCEL:
        # ---------------------------------------------------------------------
        # Search and open line:
        work_ids = work_pool.search(cr, uid, domain, context=context)
        work_proxy = work_pool.browse(cr, uid, work_ids, context=context)

        # ---------------------------------------------------------------------
        # A. Detail Page:
        # ---------------------------------------------------------------------
        ws_name = _('Dettaglio')
        excel_pool.create_worksheet(ws_name)

        # Format list:
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')

        f_text = excel_pool.get_format('text')
        f_text_yellow = excel_pool.get_format('bg_yellow')
        f_text_red = excel_pool.get_format('bg_red')

        f_number = excel_pool.get_format('number')
        f_number_yellow = excel_pool.get_format('bg_yellow_number')
        f_number_red = excel_pool.get_format('bg_red_number')

        excel_pool.column_width(ws_name, [
            15, 20, 20,
            20, 30, 10, 15,
            ])

        # Title:
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            filter_text,
            ], default_format=f_title)

        # Header:
        row += 1
        excel_pool.write_xls_line(ws_name, row, [
            _('Data'), _('Produzione'), _('Lavorazione'),
            _('Codice'), _('Nome'), _('UM'), _('Q.')
            ], default_format=f_header)

        # Material line:
        wc_db = []
        product_report = {}
        material_report = {}
        job_report = {}

        for line in sorted(
                work_proxy,
                key=lambda x: x.workcenter_production_id.real_date_planned):
            row += 1

            # Get data:
            wc = line.workcenter_production_id
            mrp = wc.production_id
            product = mrp.product_id
            material = line.product_id
            qty = line.quantity

            # -----------------------------------------------------------------
            # Final product data:
            # -----------------------------------------------------------------
            # `Check if there's some filtered product:
            if not filter_product or product.id == filter_product.id:
                if wc not in wc_db:
                    wc_db.append(wc)
                    for load in wc.load_ids: # Normally one!
                        key = product # (product, load.recycle)
                        net_qty = load.product_qty - load.waste_qty
                        hour = wc.hour

                        # Product page:
                        if key in product_report:
                            product_report[key][0] += net_qty
                            product_report[key][1] += load.waste_qty
                            product_report[key][2] += hour
                        else:
                            product_report[key] = [
                                net_qty,
                                load.waste_qty,
                                hour
                                ]

                        # Job page:
                        if product not in job_report:
                            job_report[product] = []
                        job_report[product].append(load)

                        # package_id, ul_qty
                        # package_pedimento_id
                        # palled_product_id, pallet_qty
                        # accounting_cost
                        # recycle_product

            # -----------------------------------------------------------------
            # Raw material data:
            # -----------------------------------------------------------------
            key = material
            if key in material_report:
                material_report[key] += qty
            else:
                material_report[key] = qty

            # standard_price
            # pedimento_price
            # pedimento_id
            # lot_id
            # mrp_waste_id

            # subtotal = line.price_subtotal
            # net = (subtotal / qty) if qty else 0.0
            qty = material_report[material]
            excel_pool.write_xls_line(ws_name, row, [
                wc.real_date_planned,
                mrp.name,
                wc.name,

                material.default_code or '',
                material.name or '',
                material.uom_id.name,
                (qty, f_number),
                ], default_format=f_text)

        # ---------------------------------------------------------------------
        # B. Material total:
        # ---------------------------------------------------------------------
        ws_name = _('Materie prime')
        excel_pool.create_worksheet(ws_name)

        excel_pool.column_width(ws_name, [20, 30, 10, 15, 15])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Codice'), _('Nome'), _('UM'), _('Q.'), _('Magazzino'),
            ], default_format=f_header)

        for material in sorted(material_report, key=lambda x: x.default_code):
            row += 1
            qty = material_report[material]
            accounting_qty = material.accounting_qty

            # -----------------------------------------------------------------
            # Color setup:
            # -----------------------------------------------------------------
            if accounting_qty <= 0:
                f_text_color = f_text_red
                f_number_color = f_number_red
            elif accounting_qty <= 100:
                f_text_color = f_text_yellow
                f_number_color = f_number_yellow
            else:
                f_text_color = f_text
                f_number_color = f_number

            excel_pool.write_xls_line(ws_name, row, [
                material.default_code or '',
                material.name or '',
                material.uom_id.name,
                (qty, f_number_color),
                (accounting_qty, f_number_color),
                ], default_format=f_text_color)

        # ---------------------------------------------------------------------
        # C1. Material total:
        # ---------------------------------------------------------------------
        ws_name = _('Cicli lavorazioni')
        excel_pool.create_worksheet(ws_name)

        excel_pool.column_width(ws_name, [
            10, 10, 16, 13,
            8, 10, 10,
            10, 15, 15, 15, 15, 20])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Produzione'), _('Lavorazione'), _('Data'), _('Prodotto'),
            _('Cicli'), _('Q. ciclo'), _('H. ciclo'),
            _('H. totale'), _('Q. totale'), _('Q. produzione'),
            _('Q. carico'), _('Q. rec.'), _('Prod. rec.'),
            ], default_format=f_header)

        for product in sorted(job_report, key=lambda x: x.default_code):
            for load in sorted(job_report[product],
                    key=lambda x: x.line_id.real_date_planned):
                row += 1

                # TODO Check:
                wc = load.line_id
                production = wc.production_id

                # -----------------------------------------------------------------
                # Color setup:
                # -----------------------------------------------------------------
                excel_pool.write_xls_line(ws_name, row, [
                    # TODO remove:
                    # production.id,
                    # wc.id,
                    # load.id,

                    production.name,
                    wc.name,
                    wc.real_date_planned,
                    product.default_code,

                    (wc.cycle, f_number),
                    (wc.single_cycle_qty, f_number),
                    (wc.single_cycle_duration, f_number),

                    (wc.hour, f_number),
                    (wc.qty, f_number),
                    (production.product_qty, f_number),

                    (load.product_qty, f_number),
                    (load.waste_qty, f_number),
                    load.waste_id.default_code or ''
                    ], default_format=f_text_color)

        # ---------------------------------------------------------------------
        # C2. Final product:
        # ---------------------------------------------------------------------
        ws_name = _('Prodotto finito')
        excel_pool.create_worksheet(ws_name)

        excel_pool.column_width(ws_name, [20, 30, 10, 5, 15, 15, 15])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Codice'), _('Nome'), _('UM'), _('H'), _('Q.'), _('Riciclo'),
            _('Magazzino'),
            ], default_format=f_header)

        for product in sorted(
                product_report, key=lambda x: x.default_code):
            row += 1
            qty, waste_qty, hour = product_report[product]
            accounting_qty = product.accounting_qty

            # -----------------------------------------------------------------
            # Color setup:
            # -----------------------------------------------------------------
            if accounting_qty <= 0:
                f_text_color = f_text_red
                f_number_color = f_number_red
            elif accounting_qty <= 100:
                f_text_color = f_text_yellow
                f_number_color = f_number_yellow
            else:
                f_text_color = f_text
                f_number_color = f_number

            excel_pool.write_xls_line(ws_name, row, [
                product.default_code or '',
                product.name or '',
                product.uom_id.name,
                (hour, f_number_color),
                (qty, f_number_color),
                (waste_qty, f_number_color),
                (accounting_qty, f_number_color),
                # 'X' if recycle else '',
                ], default_format=f_text_color)

        # ---------------------------------------------------------------------
        # D. Final product:
        # ---------------------------------------------------------------------
        ws_name = _('Dettaglio lavorazioni')
        excel_pool.create_worksheet(ws_name)
        excel_pool.column_width(ws_name, [
            12, 30, 
            20, 30, 10, 15, 
            10, 10,
            80])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Codice'), _('Nome'), 
            _('Data'), _('Produzione'), _('Lavorazione'), _('State'),
            _('Q.'), _('Prezzo'),             
            _('Dettaglio'),
            ], default_format=f_header)

        for wc in sorted(wc_db, key=lambda x: x.real_date_planned):
            row += 1
            excel_pool.row_height(ws_name, row, height=140)
            production = wc.production_id
            product = production.product_id
            
            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                product.name,
                wc.real_date_planned,
                production.name,
                wc.name,
                wc.state,
                production.product_qty,  # Q.
                '/', # todo Prezzo,
                clean_tags(wc.product_price_calc),
                ], default_format=f_text)

        return excel_pool.return_attachment(cr, uid, _('Production statistic'),
            version='7.0',
            php=True,
            )

    _columns = {
        # Period:
        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <='),

        # Foreign keys:
        'product_id': fields.many2one('product.product', 'Product'),
        'material_id': fields.many2one('product.product', 'Material'),

        'report_mode': fields.selection([
            ('material', 'Material'),
            #('production', 'Production'),
            #('detail', 'Detail'),
            ], 'Report mode', required=True),
        }

    _defaults = {
        'report_mode': lambda *x: 'material',
        }
