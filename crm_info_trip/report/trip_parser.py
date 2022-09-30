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
import openerp.netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

_logger = logging.getLogger(__name__)


class MicronaetAccounting(osv.osv):
    """ Object for keep function with the query
        Record are only table with last date of access
    """
    _inherit = "micronaet.accounting"

    # Override function:
    def get_mm_situation(
            self, cr, uid, document, partner_code, year=False,
            originator=False, context=None):
        """ Return quantity product usually bought with total and delivery
            where_document: list, tuple, string of document searched (ex. BS)
            where_partner: list, tuple, string for partner code searched
            Table: MM_RIGHE
            document: filter for this reference, ex.: BC, FT
            partner_code: filter for this partner code, ex.: 201.00001
            year: query on database (multi year mode) selected
            originator: query on origin document not current
                (so CSG_DOC_ORI instead of CSG_DOC)
        """
        query = "Not loaded"
        table_header = "mm_testate"
        table_line = "mm_righe"

        if self.pool.get('res.company').table_capital_name(
                cr, uid, context=context):
            table_header = table_header.upper()
            table_line = table_line.upper()

        cursor = self.connect(cr, uid, year=year, context=context)

        # -------------------
        # Manage where clause
        # -------------------
        # Filter document type:
        # TODO change query linked to header if there's originator
        if originator:
            query = """
                SELECT 
                    l.CKY_CNT_CLFR as CKY_CNT_CLFR, l.CKY_ART as CKY_ART,
                    l.CDS_VARIAB_ART as CDS_VARIAB_ART, 
                    SUM(l.NQT_RIGA_ART_PLOR * 
                        (IF(l.NCF_CONV=0, 1, 1/l.NCF_CONV))) as TOTALE, 
                    SUM(l.NPZ_UNIT * l.NQT_RIGA_ART_PLOR) as IMPONIBILE, 
                    count(*) as CONSEGNE 
                FROM %s h JOIN %s l 
                    ON (h.CSG_DOC = l.CSG_DOC AND h.NGB_SR_DOC = l.NGB_SR_DOC 
                    AND
                        h.NGL_DOC = l.NGL_DOC AND h.NPR_DOC = l.NPR_DOC) 
                GROUP BY
                    h.CSG_DOC_ORI, l.CKY_CNT_CLFR, l.CKY_ART, l.CDS_VARIAB_ART 
                HAVING 
                    h.CSG_DOC_ORI = '%s' AND l.CKY_CNT_CLFR = '%s';""" % (
                    table_header,
                    table_line,
                    document,
                    partner_code,
                    )
        else:
            query = """
                SELECT 
                    CKY_CNT_CLFR, CKY_ART, CDS_VARIAB_ART, 
                    SUM(NQT_RIGA_ART_PLOR * (IF(NCF_CONV=0, 1, 1/NCF_CONV))) 
                        as TOTALE, 
                    count(*) as CONSEGNE 
                FROM 
                    %s 
                GROUP BY
                    CSG_DOC, CKY_CNT_CLFR, CKY_ART, CDS_VARIAB_ART 
                HAVING 
                    CSG_DOC = '%s' AND CKY_CNT_CLFR = '%s';
                """ % (table_line, document, partner_code)

        try:
            cursor.execute(query)
            return cursor  # with the query setted up
        except:
            _logger.error("Problem launch query: %s [%s]" % (
                query, sys.exc_info()))
            return False


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_partner_offer': self.get_partner_offer,   # browse list
            'get_data': self.get_data,                     # return data dict
            'load_mysql_partner': self.load_mysql_partner,
            'format_date': self.format_date,

            # get/set method:
            'get_value': self.get_value,
            'set_value': self.set_value,

            'get_total_invoiced': self.get_total_invoiced,

            # Price variation:
            'load_price_variation': self.load_price_variation,
            'get_price_variation': self.get_price_variation,
        })

        cr = self.cr
        uid = self.uid
        context = {}

        # Parameters:
        self.values = {}         # dictionary for get/set manage
        self.products = {}       # for price variations
        self.products_last = {}  # last date of delivery
        self.products_uom = {}   # uom of product

        self.dictionary = {      # Query cursor dictionary
            'invoice': {'data': None},         # Browse object
            'invoice_header': {'data': None},
            'total': {'data': None}
            }

        self.causal = {}          # Causal movement list
        self.total_invoiced = {}  # Total invoiced per year

        today = datetime.now()

        # Load status parameters:
        self.status = {
            'green': today.strftime(
                DEFAULT_SERVER_DATE_FORMAT),  # 6 month
            'yellow': (today - timedelta(days=180)).strftime(
                DEFAULT_SERVER_DATE_FORMAT),  # 1 year
            'red': (today - timedelta(days=365)).strftime(
                DEFAULT_SERVER_DATE_FORMAT),  # 1 year + 6 month
            }

        # Load UOM parameters:
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [], context=context)
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            if not product.default_code:
                _logger.error('Product without code: %s' % product.name)
                continue
            if product.default_code == 'MQ340287':
                pdb.set_trace()
            self.products_uom[product.default_code] = (
                product.uom_id.account_ref or '',
                product.uom_id.moltiplicator or 1,
                )

    def get_total_invoiced(self, ):
        """ Return total_invoiced
        """
        return self.total_invoiced

    def format_date(self, value):
        """ Format date
        """
        if value:
            return "%02d/%02d/%s" % (value.day, value.month, value.year)

    # Method for get/set functions
    def get_value(self, name, default=''):
        """ Get name variable in self.values dictionary
        """
        if name not in self.values:
            self.values[name] = default
        return self.values.get(name, default)

    def set_value(self, name, value, return_value=False):
        """ Set value for variable name
        """
        self.values[name] = value
        if return_value:
            return value
        return

    def get_data(self, dict_type='invoice'):
        """ Return dict with all data collected during load_invoice_partner
            dict_type: key of dict with data ('total', 'invoice')
        """
        return self.dictionary.get(dict_type, {})

    def load_mysql_partner(
            self, partner_code, ref_year=False, dict_type='invoice'):
        """ Search total in MySQL database all BC for this partner
            partner_code: Account ref code (not odoo or ID)
            ref_year: Date from whom start SQL analysis (multi DB)
            dict_type: sql category (search perform, default invoice)
        """
        if not partner_code:
            return False

        query = self.pool.get('micronaet.accounting')
        current_year = datetime.now().year

        # Load movement description
        # for record in query.get_transportation(
        #    cr, uid, year=current_year, context=context):
        #    self.causal[record[CKY_]]

        years = []
        if ref_year:
            from_year = int(ref_year)
            if current_year > from_year:
                # Generate list of year (for DB search)
                years.extend(range(from_year, current_year))
        years.append(current_year)  # Last year (order crescent for year)
        # years.sort(reverse=True)
        # reverse year list # XXX reverse ok but purchase not!

        # Parametric code depend on dict_type:
        if dict_type == 'invoice':
            # -----------------------------------------------------------------
            #                   Accounting movement list
            # -----------------------------------------------------------------
            mysql_data = [] # dict of fetch all years
            for year in years:
                mysql_cursor = query.get_mm_header_line(  # get_mm_line(
                    self.cr, self.uid,
                    # TODO no FT only BC in this DB
                    where_document=('BC', 'BS'),
                    where_partner=partner_code,
                    originator=True,
                    year=year,
                    order_by="DTT_DOC desc",  # XXX desc
                    )
                mysql_data.append(mysql_cursor.fetchall())

        elif dict_type == 'invoice_header':
            # -----------------------------------------------------------------
            #                            Price change
            # -----------------------------------------------------------------
            mysql_data = []  # dict of fetch all years
            for year in years:
                mysql_cursor = query.get_mm_header_line(
                    self.cr, self.uid,
                    where_document=("BC", "BS"),
                    where_partner=partner_code,
                    originator=True,
                    year=year,
                    order_by="DTT_DOC_ORI desc",  # XX before DDT_DOC
                    )
                mysql_data.append(mysql_cursor.fetchall())

        elif dict_type == 'total':
            # -----------------------------------------------------------------
            #                    Totals (delivery and amount)
            # -----------------------------------------------------------------
            mysql_data = {}  # this is a dict not list

            for year in years:
                self.total_invoiced[year] = 0.0
                mysql_cursor = query.get_mm_situation(
                    self.cr, self.uid,
                    document='BC',
                    partner_code=partner_code,
                    originator=True,
                    year=year)

                # Generate dictionary for report directly:
                for record in mysql_cursor.fetchall():
                    default_code = record['CKY_ART']
                    if default_code not in mysql_data:
                        # Create default element:
                        mysql_data[default_code] = [
                            record['CDS_VARIAB_ART'],  # description
                            {},  # delivery per year
                            ]
                    # Add totals for this year
                    # TODO correct in query:
                    # get_mm_situation base_mssql_accounting
                    uom_name, moltiplicator = self.products_uom.get(
                        default_code, ('KG', 1000.0))
                    moltiplicator = 1.0  # Always for subtotal!

                    imponibile = record['IMPONIBILE'] / moltiplicator

                    # ---------------------------------------------------------
                    # XXX 21 gen 2018 Bugfix:
                    # ---------------------------------------------------------
                    if year not in mysql_data[default_code][1]:
                        mysql_data[default_code][1][year] = False
                    slot = mysql_data[default_code][1][year]
                    if slot:
                        slot[0] += record['CONSEGNE']
                        slot[1] += record['TOTALE']
                        slot[2] += imponibile
                    else:
                        mysql_data[default_code][1][year] = [
                            record['CONSEGNE'],
                            record['TOTALE'],
                            imponibile,
                            uom_name,
                            ]
                    # ---------------------------------------------------------

                    self.total_invoiced[year] += imponibile
                    # TODO also TOTALE?
        else:
            return False

        # Save list of cursor for report purpose:
        self.dictionary[dict_type]['data'] = mysql_data
        return True

    def load_price_variation(self, partner_code, ref_year):
        """ Create a product database with price variations
            partner_code: for filter
            ref_year: for evaluation period
        """
        last = {}                # CKY_ART: last price
        self.products = {}       # CKY_ART: [list of (date, price)]
        self.products_last = {}  # CKY_ART: date

        if self.load_mysql_partner(partner_code, ref_year, 'invoice_header'):
            for year in self.get_data('invoice_header')['data']:
                # sorted DTT_DOC_ORI (for change price):
                for invoice in sorted(year, key=lambda y: y['DTT_DOC_ORI']):
                    price = round(invoice['NPZ_UNIT'] / (
                        1.0 / invoice['NCF_CONV'] if
                        invoice['NCF_CONV'] else 1.0
                        ), 4)
                    date = self.format_date(invoice['DTT_DOC_ORI'])
                    # date_doc = self.format_date(invoice['DTT_DOC'])
                    # total = price * invoice['']

                    if invoice['CKY_ART'] not in self.products:
                        self.products[invoice['CKY_ART']] = []
                    self.products_last[invoice['CKY_ART']] = date
                    # last(XXX better)

                    if invoice['CKY_ART'] not in last or \
                            last[invoice['CKY_ART']] != price:
                        last[invoice['CKY_ART']] = price
                        self.products[invoice['CKY_ART']].append((
                            date, price,
                            # date_doc # real data document
                            ))
        return

    def get_price_variation(self, product_code, mode='price'):
        """ Return list of product variation (loaded before with
            load_price_variation)
            Used in list of changing price for product
            product_code: product code to evaluate
            mode:
             - price: return list of price variations
             - date: return last sold date
             - yellow: return last sold evaluation state (red, green, yellow)
        """
        if mode == 'price':
            return self.products.get(product_code, [])
        elif mode == 'date':
            return self.products_last.get(product_code, "#ERR Date?")
        elif mode == 'state':
            date = self.get_price_variation(product_code, mode='date')
            if not date:
                return False

            date = datetime.strptime(date, "%d/%m/%Y").strftime(
                DEFAULT_SERVER_DATE_FORMAT)

            if date < self.status['red']:
                return 'red'
            elif date < self.status['yellow']:
                return 'yellow'
            else:  # default
                return 'green'

    def get_partner_offer(self, partner_id, mode='order'):
        """ Return browse object of open offers
        """
        # Docnaet offer:
        if mode == 'docnaet':
            docnaet_pool = self.pool.get('docnaet.document')

            # Pending offer:
            docnaet_ids = docnaet_pool.search(self.cr, self.uid, [
                ('partner_id', '=', partner_id),
                ('sale_order_amount', '>', 0),
                ('sale_state', '=', 'pending'),
                ])
            return docnaet_pool.browse(self.cr, self.uid, docnaet_ids)

        # OpenERP Order:
        else:
            domain = [('partner_id', '=', partner_id)]
            offer_pool = self.pool.get('sale.order')

            # TODO da rivedere in base alla gestione che faremo delle offerte
            if mode == 'order':
                domain.append(('accounting_order', '=', True))  # else if offer
            elif mode == 'quotation':
                domain.append(('accounting_order', '=', False))  # else if off.

            offer_ids = offer_pool.search(self.cr, self.uid, domain)
            return offer_pool.browse(self.cr, self.uid, offer_ids)
