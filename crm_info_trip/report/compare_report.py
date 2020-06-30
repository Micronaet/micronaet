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
import pdb
import os
import sys
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class MicronaetAccounting(osv.osv):
    """ Object for keep function with the query
        Record are only table with last date of access
    """
    _inherit = "micronaet.accounting"

    # Override function:
    def get_mm_compare_status(
            self, cr, uid, document, account_code, year=False, context=None):
        """ Return data list generated from:
            Table: MM_TESTATE, MM_RIGHE
            document: filter for this reference, ex.: BC, FT
            account_code: filter for this partner code, ex.: 201.00001
            year: query on database (multi year mode) selected
        """
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
        where = 'WHERE h.CSG_DOC IN %s' % (document, )
        if account_code:
            where += ' AND r.CKY_CNT_CLFR = \'%s\';' % account_code

        # Filter document type:
        # TODO change query linked to header if there's originator
        query = """
            SELECT
                r.CKY_CNT_CLFR as partner_code, 
                h.DTT_DOC as date,
                r.CSG_DOC as sigla,

                r.CKY_ART as product_code,
                r.CDS_VARIAB_ART as description, 

                (r.NQT_RIGA_ART_PLOR * 
                    (IF(r.NCF_CONV=0, 1, 1 / r.NCF_CONV))) as quantity, 
                (r.NPZ_UNIT * r.NQT_RIGA_ART_PLOR) as total 

            FROM %s h JOIN %s r 
                ON (
                    h.CSG_DOC = r.CSG_DOC AND 
                    h.NGB_SR_DOC = r.NGB_SR_DOC AND
                    h.NGL_DOC = r.NGL_DOC AND 
                    h.NPR_DOC = r.NPR_DOC) 
            %s
            """ % (table_header, table_line, where)

        try:
            cursor.execute(query)
            _logger.warning(query.replace('\n', ' '))
            return cursor  # with the query set up
        except:
            _logger.error("Problem launch query: %s [%s]" % (
                query.replace('\n', ' '), sys.exc_info()))
            return False

    def get_report_with_compare_data(
            self, cr, uid, account_code=False, context=None):
        """ Loop for report
        """
        partner_pool = self.pool.get('res.partner')
        excel_pool = self.pool.get('excel.writer')

        # ---------------------------------------------------------------------
        # Parameters:
        # ---------------------------------------------------------------------
        # Fixed:
        level = 3  # Max year with current
        document = ('BC', 'RC')
        detail_page = False

        # Calculated:
        this_year = datetime.now().year
        this_month = '%s-%02d' % (
            this_year, datetime.now().month,
        )
        years = range(this_year + 1 - level, this_year + 1)

        # ---------------------------------------------------------------------
        # Collect data:
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # Log for check:
        if detail_page:
            ws_name = 'Dettaglio'
            excel_pool.create_worksheet(name=ws_name)
            row = 0

        # Data dict:
        mysql_data = {}
        partner_db = {}
        for year in years:
            # Load this year:
            mysql_cursor = self.get_mm_compare_status(
                cr, uid,
                document=document,
                account_code=account_code,
                year=year,
                context=context)

            # Explode record:
            records = mysql_cursor.fetchall()
            _logger.warning('Read year %s [# %s]' % (year, len(records)))
            for record in records:
                # default_code = record['product_code']  # TODO not used now
                partner_code = record['partner_code']
                date = '%s' % record['date']
                if record['sigla'] in ('RC', ):
                    sign = -1
                else:
                    sign = +1
                if date:
                    date_month = '%s-%s' % (date[:4], date[5:7])
                else:
                    _logger.error('Date not found: %s' % (record, ))
                    date_month = '0000-00'  # Not found
                if partner_code not in partner_db:
                    partner_ids = partner_pool.search(cr, uid, [
                        ('sql_customer_code', '=', partner_code),
                    ], context=context)
                    if partner_ids:
                        partner_db[partner_code] = partner_pool.browse(
                            cr, uid, partner_ids, context=context)[0]
                    else:
                        _logger.error('Partner not found: %s' % partner_code)
                partner = partner_db[partner_code]

                key = (partner, date_month)  # product, category mode?
                if key not in mysql_data:
                    mysql_data[key] = [
                        0.0,  # quantity
                        0.0,  # total
                    ]
                # Update data:
                mysql_data[key][0] += record['quantity'] * sign
                mysql_data[key][1] += record['total'] * sign
                if detail_page:
                    excel_pool.write_xls_line(
                        ws_name, row, [
                            partner.name,
                            partner_code,
                            date,
                            date_month,
                            mysql_data[key][0],
                            mysql_data[key][1],
                        ])
                    row += 1

        # ---------------------------------------------------------------------
        # Excel generation:
        # ---------------------------------------------------------------------
        parameters = {}
        ws_name = 'Confronto annuale'
        excel_pool.create_worksheet(name=ws_name)
        header = [
            'Cliente', 'Codice', 'Anno',
            'Gen.', 'Feb.', 'Mar.', 'Apr.', 'Mag.', 'Giu.',
            'Lug.', 'Ago.', 'Set.', 'Ott', 'Nov.', 'Dic.',
            ]
        width = [
            45, 15, 10,
            9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
            ]
        excel_pool.column_width(ws_name, width)

        # Format list:
        excel_pool.set_format()
        format_list = {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),

            'white': {
                'text': excel_pool.get_format('text'),
                'number': excel_pool.get_format('number'),
                },
            'red': {
                'text': excel_pool.get_format('bg_red'),
                'number': excel_pool.get_format('bg_red_number'),
                },
            'blue': {
                'text': excel_pool.get_format('bg_blue'),
                'number': excel_pool.get_format('bg_blue_number'),
                },
            'green': {
                'text': excel_pool.get_format('bg_green'),
                'number': excel_pool.get_format('bg_green_number'),
                },
            }

        row = 0
        excel_pool.write_xls_line(
            ws_name, row, ['Differenze di fatturato rispetto anno precedente'],
            default_format=format_list['title'])
        row += 2

        excel_pool.write_xls_line(
            ws_name, row, header,
            default_format=format_list['header'])
        excel_pool.autofilter(ws_name, row, 0, row, 2)
        excel_pool.freeze_panes(ws_name, 3, 3)
        row += 1

        report_year = years[1:]
        report_year.reverse()
        for partner in sorted(partner_db.values(), key=lambda p: p.name):
            for year in report_year:  # Not used first year
                record = [partner.name, partner.sql_customer_code, year]
                excel_pool.write_xls_line(
                    ws_name, row, record,
                    default_format=format_list['white']['text'])

                # month mode:
                month_record = ['' for item in range(0, 12)]
                has_negative = False
                for month in range(1, 13):
                    # ---------------------------------------------------------
                    # Current:
                    current_month = '%s-%02d' % (year, month)
                    key = (partner, current_month)
                    current_data = mysql_data.get(key)
                    if current_data:
                        current_quantity, current_total = current_data
                    else:
                        current_quantity = current_total = 0.0

                    # Previous
                    previous_month = '%s-%02d' % (year - 1, month)
                    key = (partner, previous_month)
                    previous_data = mysql_data.get(key)
                    if previous_data:  # check difference:
                        previous_quantity, previous_total = previous_data
                    else:
                        previous_quantity = previous_total = 0.0
                    # ---------------------------------------------------------

                    # ---------------------------------------------------------
                    # A. Total invoiced calc:
                    delta_total = (current_total - previous_total)
                    if previous_total:
                        delta_rate_total = (
                            100.0 * delta_total / previous_total)
                    else:
                        delta_rate_total = 100.0

                    # B. Total quantity calc:
                    # TODO not for now
                    # ---------------------------------------------------------

                    # Format color
                    if delta_total < 0.0:
                        has_negative = True
                        color = format_list['red']
                    if delta_total > 0.0:
                        color = format_list['green']
                    # elif this_month < current_month:
                    #    color = format_list['blue']
                    else:
                        color = format_list['white']

                    month_record[month - 1] = (
                        '%9.2f %%' % delta_rate_total, color['text'])
                    if any((current_total, previous_total)):
                        comment = '%s-%s = %s' % (
                            round(current_total, 0),
                            round(previous_total, 0),
                            round(delta_total, 0),
                        )
                        comment_col = len(record) + month - 1
                        excel_pool.write_comment(
                            ws_name, row, comment_col, comment,
                            parameters=parameters)

                # B. Data part:
                excel_pool.write_xls_line(
                    ws_name, row, month_record,
                    default_format=format_list['white']['text'],
                    col=len(record))
                row += 1

        return excel_pool.return_attachment(
            cr, uid, 'Compare invoiced', name_of_file='compare_invoiced.xlsx',
            version='7.0', php=True, context=context)


class CrmTrip(osv.osv):
    """ Update partner for launch report
    """
    _inherit = 'crm.trip'

    def compare_invoiced_for_partner(self, cr, uid, ids, context=None):
        """ Return report for compare
        """
        account_pool = self.pool.get('micronaet.accounting')

        current = self.browse(cr, uid, ids, context=context)[0]
        account_code = False  # TODO All
        # current.partner_ids[0].partner_id.sql_customer_code

        return account_pool.get_report_with_compare_data(
            cr, uid,
            # account_code=account_code,
            context=context)
