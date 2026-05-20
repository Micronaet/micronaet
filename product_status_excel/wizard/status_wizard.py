# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
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


class ProductProductInherit(osv.Model):
    """ Add extra function
    """
    _inherit = 'product.product'

    # ------------------------------------------------------------------------------------------------------------------
    # Utility for report:
    # ------------------------------------------------------------------------------------------------------------------
    def get_external_supplier_deadline_order(self, cr, uid, deadline, context=None):
        """ Collect OF buy from deadline to today
            Return product: quantity dict
        """
        accounting_pool = self.pool.get('micronaet.accounting')
        company_pool = self.pool.get('res.company')
        mode = 'mm' # 'OF'

        cursor_of = accounting_pool.get_of_line_quantity_deadline(cr, uid)

        table = "{}_righe".format(mode)
        if company_pool.table_capital_name(cr, uid, context=context):
            table = table.upper()

        # Loop on all year till deadline:
        current_year = datetime.now().year
        from_year = int(deadline[:4])
        supplier_product = {}
        log_f = open('/tmp/report_stock_level_{}.csv'.format(mode), 'w')
        _logger.info('Create log file {}'.format(log_f))
        try:
            for year in range(from_year, current_year + 1):
                cursor = accounting_pool.connect(cr, uid, year=year, context=context)
                # todo add deadline in query:
                # CSG_DOC, NGB_SR_DOC, NGL_DOC, NPR_RIGA, CKY_ART, DTT_SCAD, NGB_TIPO_QTA, NQT_RIGA_O_PLOR, NCF_CONV
                if mode == 'mm':  # BF
                    cursor.execute("""
                        SELECT CKY_ART, DTT_SCAD, NQT_RIGA_ART_PLOR as quantity, NCF_CONV,
                               CSG_DOC, NGB_SR_DOC, NGL_DOC, DTT_SCAD
                        FROM %s 
                        WHERE CSG_DOC = 'BF';
                        """ % table)
                else:  # OF mode
                    cursor.execute("""
                        SELECT CKY_ART, DTT_SCAD, NQT_RIGA_O_PLOR as quantity, NCF_CONV,
                               CSG_DOC, NGB_SR_DOC, NGL_DOC, DTT_SCAD
                        FROM %s;""" % table)

                if not cursor_of:
                    _logger.error('Error access OF {}'.format(year))
                else:
                    for supplier_order in cursor_of:  # all open OC
                        of_deadline = supplier_order['DTT_SCAD'].strftime('%Y-%m-%d')
                        if of_deadline < deadline:
                            continue  # Not used

                        ref = supplier_order['CKY_ART'].strip()
                        if ref not in supplier_product:
                            supplier_product[ref] = 0.0

                        conversion = supplier_order['NCF_CONV'] or 1.0
                        quantity = float(supplier_order['NQT_RIGA_O_PLOR'] or 0.0) * (1.0 / conversion)
                        supplier_product[ref] += quantity
                        log_f.write('{}|{}-{}-{}|{}|{}|{}\n'.format(
                            mode,
                            supplier_order['CSG_DOC'],
                            supplier_order['NGB_SR_DOC'],
                            supplier_order['NGL_DOC'],
                            supplier_order['DTT_SCAD'],
                            ref,
                            quantity,
                        ))
        except:
            _logger.error(sys.exc_info())
        return supplier_product


    def preload_data_load_unload_product(self, cr, uid, ids, days=180, context=None):
        """ Preload data from BF, OF, SL, CL
            products: preload objects
            context parameters:
            days = 180: Maximum period for document date
        """
        master_data = {}
        from_date_dt = datetime.now() - timedelta(days=days)
        deadline = from_date_dt.strftime('%Y-%m-%d')
        deadline_time = from_date_dt.strftime('%Y-%m-%d 00:00:00')

        # --------------------------------------------------------------------------------------------------------------
        # Prepare master data:
        # --------------------------------------------------------------------------------------------------------------
        log_f = open('/tmp/report_stock_level_ALL.csv', 'w')
        _logger.info('Create log file {}'.format(log_f))
        products = self.browse(cr, uid, ids, context=context)
        for product in products:
            default_code = product.default_code or ''
            if not default_code:
                continue

            if default_code not in master_data:
                master_data[default_code] = {
                    'BF': 0.0,
                    'BC': 0.0,
                    'SL': 0.0,
                    'CL': 0.0,
                }

        # --------------------------------------------------------------------------------------------------------------
        # BF (Load):
        # --------------------------------------------------------------------------------------------------------------
        # SQL Table for bf:
        supplier_orders = self.get_external_supplier_deadline_order(cr, uid, deadline=deadline, context=context)
        for default_code in supplier_orders:
            if not default_code or default_code not in master_data:
                _logger.warning('BF. Not used "{}"'.format(default_code))
                continue
            master_data[default_code]['BF'] += supplier_orders[default_code]

        # --------------------------------------------------------------------------------------------------------------
        # SL (Unload):
        # --------------------------------------------------------------------------------------------------------------
        sl_pool = self.pool.get('mrp.production.workcenter.line')
        # Filter: real_date_planned (datetime) state 'done'
        sl_ids = sl_pool.search(cr, uid, [
            ('real_date_planned', '>=', deadline_time),
            ('state', '=', 'done'),
        ], context=context)

        # Data: bom_material_ids: product_id, quantity
        for sl in sl_pool.browse(cr, uid, sl_ids, context=context):
            for line in sl.bom_material_ids:
                default_code = line.product_id.default_code or ''
                if not default_code or default_code not in master_data:
                    _logger.warning('SL. Not used "{}"'.format(default_code))
                    continue
                master_data[default_code]['SL'] += line.quantity
                log_f.write('SL|{}|{}|{}|{}\n'.format(
                    sl.name,
                    sl.real_date_planned,
                    default_code,
                    line.quantity,
                ))


        # --------------------------------------------------------------------------------------------------------------
        # CL (Load FP, Unload package, pallet):
        # --------------------------------------------------------------------------------------------------------------
        cl_pool = self.pool.get('mrp.production.workcenter.load')
        # Filter: date (datetime):
        cl_ids = cl_pool.search(cr, uid, [
            ('date', '>=', deadline_time),
        ], context=context)

        # Data:
        for cl in cl_pool.browse(cr, uid, cl_ids, context=context):
            # Loop on 3 cases:
            move_loop = (
                # Product
                (cl.recycle_product_id.default_code or cl.product_id.default_code or '', cl.product_qty or 0.0, 'CL'),
                # Package:
                (cl.package_id.linked_product_id.default_code or '', cl.ul_qty or 0.0, 'SL'),
                # Pallet:
                (cl.pallet_product_id.default_code or '', cl.pallet_qty or 0.0, 'SL'),
                )

            for default_code, quantity, mode in move_loop:
                if not default_code or default_code not in master_data:
                    _logger.warning('CL-{}. Not used "{}"'.format(mode, default_code))
                else:
                    master_data[default_code][mode] += quantity
                    log_f.write('CL-Op. {}|{}|{}|{}|{}\n'.format(
                        mode,
                        cl.accounting_cl_code,
                        cl.date,
                        default_code,
                        quantity,
                    ))

        # --------------------------------------------------------------------------------------------------------------
        # DDT (Unload):
        # --------------------------------------------------------------------------------------------------------------
        bc_pool = self.pool.get('stock.ddt')
        # Filter: date (date) state 'done'
        bc_ids = bc_pool.search(cr, uid, [
            ('date', '>=', deadline),
            ('state', '=', 'done'),
        ], context=context)
        # Data: line_ids: - product_id, product_uom_qty
        for bc in bc_pool.browse(cr, uid, bc_ids, context=context):
            for line in bc.line_ids:
                default_code = line.product_id.default_code or ''
                if not default_code or default_code not in master_data:
                    _logger.warning('BC. Not used "{}"'.format(default_code))
                    continue
                master_data[default_code]['BC'] += line.product_uom_qty
                log_f.write('BC|{}-{}|{}|{}|{}\n'.format(
                    bc.series_id.name,
                    bc.name,
                    bc.date,
                    default_code,
                    line.product_uom_qty,
                ))

        return master_data

class ProductExtractProductXlsWizard(orm.TransientModel):
    """ Wizard for extract XLS report
    """
    _name = 'product.product.extract.xls.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_done_filename(self, cr, uid, filename, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['save_mode'] = filename
        return self.action_done(cr, uid, False, context=ctx)

    # todo xlrd library cannot installed on old Debian 7 Wheezy:
    '''
    def action_import(self, cr, uid, ids, context=None):
        """ Event for button import file
        """
        if context is None:
            context = {}
        product_pool = self.pool.get('product.product')

        # ---------------------------------------------------------------------
        # Save file passed:
        # ---------------------------------------------------------------------
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        if not current_proxy.file:
            raise osv.except_osv(
                _('No file:'),
                _('Please pass a XLSX file for import order'),
                )
        b64_file = base64.decodestring(current_proxy.file)
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        filename = '/tmp/tx_%s.xlsx' % now.replace(':', '_').replace('-', '_')
        f = open(filename, 'wb')
        f.write(b64_file)
        f.close()

        # ---------------------------------------------------------------------
        # Load force name (for web publish)
        # ---------------------------------------------------------------------
        try:
            WB = xlrd.open_workbook(filename)
        except:
            raise osv.except_osv(
                _('Error XLSX'),
                _('Cannot read XLS file: %s' % filename),
                )

        # ---------------------------------------------------------------------
        # Loop on all pages:
        # ---------------------------------------------------------------------
        for ws_name in WB.sheet_names():
            WS = WB.sheet_by_name(ws_name)
            _logger.warning('Read page: %s' % ws_name)

            start = False
            i = 0
            for row in range(WS.nrows):
                i += 1
                # -------------------------------------------------------------
                # Read product code:
                # -------------------------------------------------------------
                item_id = WS.cell(row, 0).value
                if item_id == 'ID':
                    start = True
                    _logger.info('%s. Find header line' % i)
                    continue
                if not start:
                    _logger.info('%s. Jump line not used' % i)
                    continue

                # Original value:
                excluded = WS.cell(row, 1).value.upper in ('SX')
                day_leadtime = WS.cell(row, 2).value
                day_min_level = WS.cell(row, 3).value

                # New value:
                new_excluded = WS.cell(row, 4).value.upper in ('SX')
                new_day_leadtime = WS.cell(row, 11).value
                new_day_min_level = WS.cell(row, 12).value

                if (excluded == new_excluded and
                        day_leadtime == new_day_leadtime and
                        day_min_level == new_day_min_level):
                    _logger.info('%s. No change' % i)
                    continue
                try:
                    product_pool.write(cr, uid, [item_id], {
                        'not_in_status': new_excluded,
                        'day_leadtime': new_day_leadtime,
                        'day_min_level': new_day_min_level,
                    }, context=context)
                    _logger.info('%s. Update record' % i)
                except:
                    _logger.error('%s. Error updating record' % i)
                    continue
        _logger.info('Importazione terminata')
    '''

    def action_done(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        if context is None:
            context = {}
        save_mode = context.get('save_mode', False)
        if save_mode:
            _logger.info('Start extract save mode: %s' % save_mode)

        # Pool used:
        product_pool = self.pool.get('product.product')
        excel_pool = self.pool.get('excel.writer')

        # Medium days:
        now = datetime.now()
        days = (now - datetime.strptime('%s-01-01' % now.year, '%Y-%m-%d')).days + 1
        windows_days = 180

        comment_parameters = {
            'width': 450,
            'font_name': 'Courier New',
        }

        # --------------------------------------------------------------------------------------------------------------
        # Create dynamic domain
        # --------------------------------------------------------------------------------------------------------------
        filter_used = ''
        wizard_domain = []
        if not save_mode:
            wiz_browse = self.browse(cr, uid, ids, context=context)[0]

            # Search block:
            if not wiz_browse.with_empty_code:
                wizard_domain.append(('default_code', '!=', False))
                filter_used += 'Solo prodotti con codice '

            if wiz_browse.mode == 'negative':
                wizard_domain.append(('accounting_qty', '<=', 0.0))
                filter_used += 'Solo prodotti negativi (<0) '
            elif wiz_browse.mode == 'positive':
                wizard_domain.append(('accounting_qty', '>', 0.0))
                filter_used += 'Solo prodotti positivi (>0) '
            elif wiz_browse.mode == 'zero':
                wizard_domain.append(('accounting_qty', '=', 0.0))
                filter_used += 'Solo prodotti zero (=0) '
            else:
                filter_used += 'Tutti i prodotti '

            if wiz_browse.from_code:
                wizard_domain.append(
                    ('default_code', '>=', wiz_browse.from_code))
                filter_used += ', Codice >= %s ' % wiz_browse.from_code
            if wiz_browse.to_code:
                wizard_domain.append(
                    ('default_code', '<=', wiz_browse.to_code))
                filter_used += ', Codice <= %s ' % wiz_browse.to_code

            if wiz_browse.statistic_category:
                wizard_domain.append(
                    ('statistic_category', '=', wiz_browse.statistic_category))
                filter_used += ', Cat. stat. = %s ' % wiz_browse.statistic_category

            if wiz_browse.categ_id:
                wizard_domain.append(('categ_id', '=', wiz_browse.categ_id.id))
                filter_used += ', Categoria = %s ' % wiz_browse.categ_id.name

            # Sort function:
            if wiz_browse.sort == 'default_code':
                sort_key = lambda x: x.default_code
            elif wiz_browse.sort == 'name':
                sort_key = lambda x: x.name
            elif wiz_browse.sort == 'categ_id':
                sort_key = lambda x: (x.categ_id.name, x.default_code)
            elif wiz_browse.sort == 'statistic_category':
                sort_key = lambda x: (x.statistic_category, x.default_code)
        else:
            # Default sort for mail report mode:
            sort_key = lambda x: x.default_code

        # --------------------------------------------------------------------------------------------------------------
        #                                     Master loop for page:
        # --------------------------------------------------------------------------------------------------------------
        removed_ids = []  # Compiled when removed in first n-1 loop
        cr.execute('''
            SELECT id 
            FROM product_product 
            WHERE substring(default_code, 1, 1) in ('C', 'V')
            ''')
        excluded_ids = [record[0] for record in cr.fetchall()]

        cr.execute('''
            SELECT id 
            FROM product_product 
            WHERE substring(default_code, 1, 1) not in 
                ('A', 'B', 'C', 'L', 'M', 'R', 'V', 'Z');
            ''')
        product_ids = [record[0] for record in cr.fetchall()]
        master_loop = [
            ('Materie A', [
                ('default_code', '=ilike', 'A%'),
            ]),
            ('Materie B', [
                ('default_code', '=ilike', 'B%'),
            ]),
            ('Prodotti', [
                ('id', 'in', product_ids),
            ]),
            ('Recuperi', [
                ('default_code', '=ilike', 'R%'),
            ]),
            ('Macchinari', [
                ('default_code', '=ilike', 'M%'),
            ]),
            ('Lavorazioni', [
                '|',
                ('default_code', '=ilike', 'L%'),
                ('default_code', '=ilike', 'Z%'),
            ]),
            ('Codici vecchi', [
                ('id', 'in', excluded_ids),
            ]),
            ('Esclusi', [
                ('id', 'in', removed_ids),
            ]),
        ]


        # --------------------------------------------------------------------------------------------------------------
        # Preload all products movements:
        # --------------------------------------------------------------------------------------------------------------
        all_product_ids = product_pool.search(cr, uid, [
            ('default_code', '!=', False)
            ], context=context)
        # SQL load / Unload data:
        preload_stock_stats = product_pool.preload_data_load_unload_product(
            cr, uid, all_product_ids, days=windows_days, context=context)

        # --------------------------------------------------------------------------------------------------------------
        # Write page per page:
        # --------------------------------------------------------------------------------------------------------------
        format_loaded = False
        for ws_name, page_domain in master_loop:
            if not save_mode:
                domain = wizard_domain + page_domain
            else:
                domain = page_domain
            product_ids = product_pool.search(cr, uid, domain, context=context)

            # Excel generation
            excel_pool.create_worksheet(ws_name)

            # ----------------------------------------------------------------------------------------------------------
            # Preload data: Load / Unload references
            # ----------------------------------------------------------------------------------------------------------
            products = product_pool.browse(cr, uid, product_ids, context=context)

            # ----------------------------------------------------------------------------------------------------------
            # Format used:
            # ----------------------------------------------------------------------------------------------------------
            # excel_pool.set_format()
            if not format_loaded:  # Load once
                format_title = excel_pool.get_format('title')
                format_header = excel_pool.get_format('header')

                format_number_white = excel_pool.get_format(
                    'bg_white_number')
                format_number_yellow = excel_pool.get_format(
                    'bg_yellow_number')
                format_number_red = excel_pool.get_format(
                    'bg_red_number')

                format_text_white = excel_pool.get_format(
                    'text')
                format_text_yellow = excel_pool.get_format(
                    'bg_yellow')
                format_text_red = excel_pool.get_format(
                    'bg_red')
                format_loaded = True

            # ----------------------------------------------------------------------------------------------------------
            # Header part:
            # ----------------------------------------------------------------------------------------------------------
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                '', '', '', '', 'Stato prodotti, Filtro: ', filter_used,
                ], format_title)

            excel_pool.column_width(ws_name, [
                1, 1, 1, 1,
                5,
                10, 40, 10, 10, 10, 10,
                20, 10, 12, 30,
                10, 10, 10, 15,
            ])
            header = [
                # Hidden
                'ID',
                'Escludi (orig.)',
                u'Leadtime',
                u'gg. approvv.',

                'ESCL.',

                u'Codice',
                u'Nome',
                u'Q.',
                u'Car. 180gg',
                u'Scar. 180gg',
                u'Vend. 180gg',

                u'Categoria',
                u'Cat. stat.',
                u'Cod. doganale',
                u'Primo fornitore',

                u'LEADTIME',
                u'GG. APPROV.',
                u'Liv. riord.',
                'Stato',

                'TCAR',
                'TSCAR',
                'days',
                ]

            row += 2
            excel_pool.write_xls_line(ws_name, row, header, format_header)
            excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)
            excel_pool.freeze_panes(ws_name, row + 1, 6)
            excel_pool.column_hidden(ws_name, [0, 1, 2, 3, 19, 20, 21])

            comment = 'Dato medio calcolato prendendo il totale %s da ' \
                      'inizio anno : giorni x 180 (simulazione ' \
                      'consumo ultimo semestre)'

            excel_pool.write_comment(ws_name, row, 8, comment % 'carico', parameters=comment_parameters)
            excel_pool.write_comment(ws_name, row, 9, comment % 'scarico', parameters=comment_parameters)

            # ----------------------------------------------------------------------------------------------------------
            # Data part:
            # ----------------------------------------------------------------------------------------------------------
            for product in sorted(products, key=sort_key):
                default_code = product.default_code or '/'
                # Only not obsolete or with stock will be written:
                if ws_name != 'Esclusi' and product.stock_obsolete and not product.accounting_qty:
                    removed_ids.append(product.id)  # For last loop 'Rimossi'
                    continue

                row += 1
                min_stock = product.min_stock_level
                if product.accounting_qty > min_stock:
                    format_number = format_number_white
                    format_text = format_text_white
                    state = 'Presente'
                elif product.accounting_qty > 0:  # Yellow (under min)
                    format_number = format_number_yellow
                    format_text = format_text_yellow
                    state = 'Sottoscorta'
                else:  # not present or negative
                    format_number = format_number_red
                    format_text = format_text_red
                    state = 'Non presente'

                # Medium last 180 gg.
                if default_code in preload_stock_stats:
                    preload_data = preload_stock_stats[default_code]
                    load_qty = preload_data['BF'] + preload_data['CL']
                    unload_qty = preload_data['SL']
                    sold_qty = preload_data['BC']
                else:
                    load_qty = unload_qty = sold_qty = 0

                # if days > 0:
                #    tscar = 180.0 * product.accounting_tscar_qty / days
                #    tcar = 180.0 * product.accounting_tcar_qty / days
                # else:
                #    tscar = tcar = 0.0

                excel_pool.write_xls_line(ws_name, row, [
                    # Hidden:
                    product.id,
                    'X' if product.stock_obsolete else '',  # used as excluded (for reimport the file)
                    (product.day_leadtime, format_number),
                    (product.day_min_level, format_number),

                    # Showed
                    'X' if product.stock_obsolete else '',
                    product.default_code,
                    product.name,
                    (product.accounting_qty, format_number),
                    (load_qty, format_number),
                    (unload_qty, format_number),
                    (sold_qty, format_number),
                    product.categ_id.name,
                    product.statistic_category,
                    product.duty_id.name or '/',
                    product.first_supplier_id.name or '/',
                    (product.day_leadtime, format_number),
                    (product.day_min_level, format_number),
                    (min_stock, format_number),
                    state,

                    # Hidden:
                    product.accounting_tcar_qty,
                    product.accounting_tscar_qty,
                    days,
                    ], format_text)

        # ---------------------------------------------------------------------
        # Save mode:
        # ---------------------------------------------------------------------
        if save_mode:  # Save as a file:
            _logger.warning('Save mode: %s' % save_mode)
            excel_pool.save_file_as(save_mode)
            return True

        return excel_pool.return_attachment(
            cr, uid, 'Prodotti',
            name_of_file=False, version='7.0', php=True,
            context=context)

    _columns = {
        'with_empty_code': fields.boolean('Includi i senza codice'),
        'from_code': fields.char('From code', size=20),
        'to_code': fields.char('To code', size=20),
        'statistic_category': fields.char('Statistic_category', size=20),
        'categ_id': fields.many2one(
            'product.category', 'Category'),
        'mode': fields.selection([
            ('all', 'All products'),
            ('positive', 'Positive (>0)'),
            ('negative', 'Negative (<0)'),
            ('zero', 'Zero (=0)'),
            ], 'Mode', required=True),
        'sort': fields.selection([
            ('default_code', 'Product code'),
            ('name', 'Product name'),
            ('categ_id', 'Categoria prodotto'),
            ('statistic_category', 'Statistic category'),
            ], 'Sort mode', required=True),

        # Import:
        'file': fields.binary('File XLSX', help='File da reimportare'),
        }

    _defaults = {
        'mode': lambda *x: 'all',
        'sort': lambda *x: 'default_code',
        }
