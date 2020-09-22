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


class ProductExtractProductXlsWizard(orm.TransientModel):
    """ Wizard for extract XLS report
    """
    _name = 'product.product.extract.xls.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_done(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        # Pool used:
        product_pool = self.pool.get('product.product')
        excel_pool = self.pool.get('excel.writer')

        wiz_browse = self.browse(cr, uid, ids, context=context)[0]

        # ---------------------------------------------------------------------
        # Create dynamic domain
        # ---------------------------------------------------------------------
        domain = []

        # Search block:
        filter_used = ''
        if not wiz_browse.with_empty_code:
            domain.append(('default_code', '!=', False))
            filter_used += 'Solo prodotti con codice '

        if wiz_browse.mode == 'negative':
            domain.append(('accounting_qty', '<=', 0.0))
            filter_used += 'Solo prodotti negativi (<0) '
        elif wiz_browse.mode == 'positive':
            domain.append(('accounting_qty', '>', 0.0))
            filter_used += 'Solo prodotti positivi (>0) '
        elif wiz_browse.mode == 'zero':
            domain.append(('accounting_qty', '=', 0.0))
            filter_used += 'Solo prodotti zero (=0) '
        else:
            filter_used += 'Tutti i prodotti '

        if wiz_browse.from_code:
            domain.append(('default_code', '>=', wiz_browse.from_code))
            filter_used += ', Codice >= %s ' % wiz_browse.from_code
        if wiz_browse.to_code:
            domain.append(('default_code', '<=', wiz_browse.to_code))
            filter_used += ', Codice <= %s ' % wiz_browse.to_code

        if wiz_browse.statistic_category:
            domain.append(
                ('statistic_category', '=', wiz_browse.statistic_category))
            filter_used += ', Cat. stat. = %s ' % wiz_browse.statistic_category

        if wiz_browse.categ_id:
            domain.append(('categ_id', '=', wiz_browse.categ_id.id))
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

        product_ids = product_pool.search(cr, uid, domain, context=context)

        # Excel generation
        ws_name = 'Prodotti'
        excel_pool.create_worksheet(ws_name)

        # Format used:
        # excel_pool.set_format()
        format_title = excel_pool.get_format('title')
        format_header = excel_pool.get_format('header')
        format_text = excel_pool.get_format('text')

        format_number_white = excel_pool.get_format('bg_white_number')
        format_number_red = excel_pool.get_format('bg_red_number')

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'Filtro: ',
            filter_used,
            ], format_title)

        excel_pool.column_width(ws_name, [10, 40, 20, 10, 12, 30, 10])
        header = [
            u'Codice',
            u'Nome',
            u'Categoria',
            u'Cat. stat.',
            u'Cod. doganale',
            u'Primo fornitore',
            u'Q.',
            ]

        row += 2
        excel_pool.write_xls_line(ws_name, row, header, format_header)
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)

        for product in sorted(product_pool.browse(
                cr, uid, product_ids, context=context),
                key=sort_key):
            row += 1
            if product.accounting_qty >= 0:
                format_number = format_number_white
            else:
                format_number = format_number_red

            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                product.name,
                product.categ_id.name,
                product.statistic_category,
                product.duty_id.name or '/',
                product.first_supplier_id.name or '/',
                (product.accounting_qty, format_number),
                ], format_text)

        return excel_pool.return_attachment(
            cr, uid, 'Prodotti',
            name_of_file=False, version='7.0', php=True,
            context=context)

    _columns = {
        'with_empty_code': fields.boolean('Rimuovi senza codice'),
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
        }

    _defaults = {
        'mode': lambda *x: 'all',
        'sort': lambda *x: 'default_code',
        }
