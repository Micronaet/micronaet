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
    def get_mm_compare_status(
            self, cr, uid, document, partner_code, year=False, context=None):
        """ Return data list generated from:
            Table: MM_TESTATE, MM_RIGHE
            document: filter for this reference, ex.: BC, FT
            partner_code: filter for this partner code, ex.: 201.00001
            year: query on database (multi year mode) selected
        """
        table_header = "mm_testate"
        table_line = "mm_righe"

        if self.pool.get('res.company').table_capital_name(
                cr, uid, context=context):
            table_header = table_header.upper()
            table_line = table_line.upper()

        pdb.set_trace()
        cursor = self.connect(cr, uid, year=year, context=context)

        # -------------------
        # Manage where clause
        # -------------------
        where = 'WHERE h.CSG_DOC IN %s' % (document, )
        if partner_code:
            where += ' AND r.CKY_CNT_CLFR = \'%s\';' % partner_code

        # Filter document type:
        # TODO change query linked to header if there's originator
        query = """
            SELECT
                r.CKY_CNT_CLFR as partner_code, 
                h.DTT_DOC as date,

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
            return cursor  # with the query set up
        except:
            _logger.error("Problem launch query: %s [%s]" % (
                query.replace('\n', ' '), sys.exc_info()))
            return False

    def get_report_data(
            self, cr, uid, partner_code=False, context=None):
        """ Loop for report
        """
        partner_pool = self.pool.get('res.partner')

        # ---------------------------------------------------------------------
        # Parameters:
        # ---------------------------------------------------------------------
        # Fixed:
        level = 1  # 3  # Max year with current
        document = ('BC', 'RC')

        # Calculated:
        current_year = datetime.now().year
        years = range(current_year + 1 - level, current_year + 1)

        # Data dict:
        mysql_data = {}
        partner_db = {}
        for year in years:
            # Load this year:
            mysql_cursor = self.get_mm_compare_status(
                cr, uid,
                document=document,
                partner_code=partner_code,
                year=year,
                context=context)

            # Explode record:
            for record in mysql_cursor.fetchall():
                default_code = record['product_code']
                partner_code = record['partner_code']
                date = record['data']
                if date:
                    date_month = '%s-%s' % date[:4], date[5:7]
                else:
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
                partner = partner_db.get[partner_code]

                key = (partner, date_month)  # product, category mode?
                if key not in mysql_data:
                    mysql_data[key] = [
                        0.0,  # quantity
                        0.0,  # total
                    ]
                # Update data:
                mysql_data[key][0] += record['quantity']
                mysql_data[key][1] += record['total']
        return True

class CrmTrip(osv.osv):
    """ Update partner for launch report
    """
    _inherit = 'crm.trip'

    def compare_invoiced_for_partner(self, cr, uid, ids, context=None):
        """ Return report for compare
        """
        account_pool = self.pool.get('micronaet.accounting')

        current = self.browse(cr, uid, ids, context=context)[0]
        partner_code = current.partner_ids[0].partner_id.sql_customer_code

        return account_pool.get_report_data(
            cr, uid, partner_code=partner_code, context=context)
