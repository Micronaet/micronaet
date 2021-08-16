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
# import base64
# import xlrd

_logger = logging.getLogger(__name__)


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
        pdb.set_trace()
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

        filter_used = ''
        wizard_domain = []
        if not save_mode:
            wiz_browse = self.browse(cr, uid, ids, context=context)[0]

            # -----------------------------------------------------------------
            # Create dynamic domain
            # -----------------------------------------------------------------
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
                filter_used += ', Cat. stat. = %s ' % \
                               wiz_browse.statistic_category

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

        # ---------------------------------------------------------------------
        # Master loop for page:
        # ---------------------------------------------------------------------
        removed_ids = []  # Compiled when removed in first n-1 loop
        cr.execute('''
            SELECT id from product_product 
            WHERE substring(default_code, 1, 1) in ('C', 'V')
            ''')
        excluded_ids = [record[0] for record in cr.fetchall()]

        cr.execute('''
            SELECT id from product_product 
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
            ('Esclusi', [
                ('id', 'in', excluded_ids),
            ]),
            ('Rimossi', [
                ('id', 'in', removed_ids),
            ]),
        ]
        format_loaded = False
        for ws_name, page_domain in master_loop:
            if not save_mode:
                domain = wizard_domain + page_domain
            else:
                domain = page_domain
            product_ids = product_pool.search(cr, uid, domain, context=context)

            # Excel generation
            excel_pool.create_worksheet(ws_name)

            # Format used:
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

            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                '', '', '', '', '', 'Stato prodotti, Filtro: ', filter_used,
                ], format_title)

            excel_pool.column_width(ws_name, [
                1, 1, 1, 1,
                5,
                10, 40, 20, 10, 12, 30,
                10, 10, 10, 10, 15])
            header = [
                'ID',
                'Escludi (orig.)',
                u'Leadtime',
                u'gg. approvv.',

                'ESCL.',

                u'Codice',
                u'Nome',
                u'Categoria',
                u'Cat. stat.',
                u'Cod. doganale',
                u'Primo fornitore',

                u'LEADTIME',
                u'GG. APPROV.',
                u'Liv. riord.',
                u'Q.',
                'Stato',
                ]

            row += 2
            excel_pool.write_xls_line(ws_name, row, header, format_header)
            excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)
            excel_pool.freeze_panes(ws_name, row + 1, 8)
            excel_pool.column_hidden(ws_name, [0, 1, 2, 3])

            for product in sorted(product_pool.browse(
                    cr, uid, product_ids, context=context),
                    key=sort_key):

                # Only not obsolete or with stock will be written:
                if ws_name != 'Rimossi' and product.stock_obsolete and \
                        not product.accounting_qty:
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

                excel_pool.write_xls_line(ws_name, row, [
                    # Hidden:
                    product.id,
                    'X' if product.stock_obsolete else '',  # used as excl.!
                    (product.day_leadtime, format_number),
                    (product.day_min_level, format_number),

                    # Showed
                    'X' if product.stock_obsolete else '',
                    product.default_code,
                    product.name,
                    product.categ_id.name,
                    product.statistic_category,
                    product.duty_id.name or '/',
                    product.first_supplier_id.name or '/',
                    (product.day_leadtime, format_number),
                    (product.day_min_level, format_number),
                    (min_stock, format_number),
                    (product.accounting_qty, format_number),
                    state,
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
