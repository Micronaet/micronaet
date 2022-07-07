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
import openerp.netsvc as netsvc
import logging
import xmlrpclib
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class res_company(osv.osv):
    """ Extra fields for res.company object
    """
    _name = "res.company"
    _inherit = "res.company"

    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def sql_mrp_get_cl(self, cr, uid, year, context=None):
        """ Load CL document
        """
        sql_pool = self.pool.get('micronaet.accounting')

        if self.table_capital_name(cr, uid, context=context):
            table = 'MM_TESTATE'
        else:
            table = 'mm_testate'

        cursor = sql_pool.connect(cr, uid, year=False, context=context)
        if not cursor:
            raise Exception('Impossibile leggere i dati contabili')

        res = {
            'CL': [],
            'SL': [],
            }
        try:
            cursor.execute("""
                SELECT
                    NGL_DOC, CSG_DOC  
                FROM %s
                WHERE 
                    CSG_DOC in ('SL', 'CL') AND 
                    CDS_NOTE = 'OPENERP';
                """ % table)
            for record in cursor.fetchall():
                number = str(record['NGL_DOC'])
                if record['CSG_DOC'] == 'SL':
                    res['SL'].append(number)
                else:
                    res['CL'].append(number)
            return res
        except:
            _logger.error('Error reading CL and SL')
            return res  # empty

    def sql_get_price(self, record):
        """ Generate price:
        """
        price = record['NPZ_UNIT']
        conversion = record['NCF_CONV']

        if conversion:
            price *= conversion
        return price

    def sql_mm_line_get_data(self, cr, uid, year, context=None):
        """ Load CL document
        """
        sql_pool = self.pool.get('micronaet.accounting')
        reference = 200.0  # +/- 200% of range

        if self.table_capital_name(cr, uid, context=context):
            table = 'MM_RIGHE'
        else:
            table = 'mm_righe'

        cursor = sql_pool.connect(cr, uid, year=False, context=context)
        if not cursor:
            raise Exception('Impossibile leggere i dati contabili')

        res = {}
        empty = []
        cursor.execute("""
            SELECT *  
            FROM %s
            WHERE 
                CSG_DOC in ('BF', 'SL', 'CL');
            """ % table)

        records = cursor.fetchall()
        _logger.warning('Record selected from %s: %s' % (
            table, len(records),
            ))
        for record in records:
            default_code = record['CKY_ART']
            if default_code[:1] in 'M':
                _logger.warning('Code not used: %s' % default_code)
                continue

            current_price = self.sql_get_price(record)
            if not current_price:
                if default_code.startswith('VV'):
                    _logger.warning('Water product jump: %s' % default_code)
                else:
                    _logger.warning('No price for code: %s' % default_code)
                    empty.append(record)
                continue

            if default_code not in res:
                res[default_code] = {
                    'price': current_price,
                    'problem': False,
                    'record': [],
                    'sum': 0.0,
                    'counter': 0,
                }
            # Medium part:
            res[default_code]['sum'] += current_price
            res[default_code]['counter'] += 1

            # Price check:
            reference_price = res[default_code]['price']
            res[default_code]['record'].append(record)
            if not reference_price:
                pdb.set_trace()
            gap = 100.0 * abs(current_price - reference_price) / \
                reference_price

            if not res[default_code]['problem'] and gap >= reference:
                res[default_code]['problem'] = True  # There's a problem
        return res, empty

    def check_price_out_of_scale(self, cr, uid, ids, context=None):
        """ Check out of scale price on MySQL
        """
        reference = 200.0  # +/- 200% of range

        excel_pool = self.pool.get('excel.writer')
        account_data, empty_data = self.sql_mm_line_get_data(
            cr, uid, False, context=context)

        ws_name = 'Movimenti magazzino'
        excel_pool.create_worksheet(ws_name)
        excel_pool.set_format()
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
            15, 12, 12, 12, 18, 15,
        ])
        header = [
            'Codice prodotto', 'Prezzo medio',
            'Prezzo', '% Varianza', 'Documento', 'Data'
        ]

        # Write title:
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'Movimenti di magazzino con confronto prezzi prodotto',
        ], default_format=excel_format['title'])

        # Write title:
        row += 1
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        _logger.warning('Product found: %s' % len(account_data))
        for default_code in account_data:
            data = account_data[default_code]

            problem = data['problem']
            medium = data['sum'] / data['counter']

            if not problem:
                continue

            first = True
            for record in data['record']:
                row += 1
                price = self.sql_get_price(record)

                variant = 100.0 * (price - medium) / medium

                if abs(variant) >= reference:
                    color = excel_format['red']
                else:
                    color = excel_format['white']
                line = [
                    default_code if first else '',
                    medium if first else '',
                    price,
                    variant,
                    '%s/%s %s' % (
                        record['CSG_DOC'],
                        record['NGB_SR_DOC'],
                        record['NGL_DOC'],
                        ),
                    record['DTT_SCAD'],
                ]
                excel_pool.write_xls_line(
                    ws_name, row, line,
                    default_format=color['text'])
                first = False

        # Empty data:
        ws_name = 'Prezzi a zero'
        excel_pool.create_worksheet(ws_name)

        # Column setup:
        excel_pool.column_width(ws_name, [
            15, 15, 20, 15,
        ])
        header = [
            'Codice prodotto', 'Prezzo', 'Documento', 'Data'
        ]

        # Write title:
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'Documenti con prezzi a zero',
        ], default_format=excel_format['title'])

        # Write title:
        row += 1
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        _logger.warning('Empty found: %s' % len(empty_data))
        for record in empty_data:
            default_code = record['CKY_ART']

            row += 1
            price = self.sql_get_price(record)
            line = [
                default_code,
                price,
                '%s/%s %s' % (
                    record['CSG_DOC'],
                    record['NGB_SR_DOC'],
                    record['NGL_DOC'],
                    ),
                record['DTT_SCAD']
            ]
            excel_pool.write_xls_line(
                ws_name, row, line,
                default_format=excel_format['text'])

        return excel_pool.return_attachment(
            cr, uid, 'Stato documenti di MRP', version='7.0', php=True,
            context=context)

    def check_account_document(self, cr, uid, ids, context=None):
        """ Check CL and CL
        """
        load_pool = self.pool.get('mrp.production.workcenter.load')
        unload_pool = self.pool.get('mrp.production.workcenter.line')
        excel_pool = self.pool.get('excel.writer')

        now = str(datetime.now())
        year = now[:4]
        account_data = self.sql_mrp_get_cl(cr, uid, year, context=context)

        # ---------------------------------------------------------------------
        # Collect data:
        # ---------------------------------------------------------------------
        # Load:
        load_ids = load_pool.search(cr, uid, [
            ('date', '>=', '%s-01-01' % year),  # This year
            ('accounting_cl_code', '!=', False),
            ], context=context)

        _logger.warning('Load document found #%s' % len(load_ids))
        loads = load_pool.browse(cr, uid, load_ids, context=context)

        # Unload:
        unload_ids = unload_pool.search(cr, uid, [
            ('date_start', '>=', '%s-01-01' % year),  # This year
            ('accounting_sl_code', '!=', False),
            ], context=context)

        _logger.warning('Unload document found #%s' % len(unload_ids))
        unloads = unload_pool.browse(cr, uid, unload_ids, context=context)

        loop = [
            ('Carichi di produzione', 'CL', loads),
            ('Scarichi di produzione', 'SL', unloads),
        ]

        excel_format = False
        for ws_name, document, records in loop:
            excel_pool.create_worksheet(ws_name)

            # Format:
            if not excel_format:
                excel_pool.set_format()
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
                15, 15, 20,
            ])

            # Write header:
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                'Documenti %s da OpenERP e Gestionale' % document,
                ], default_format=excel_format['title'])

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                'Numero OpenERP',
                'Numero Gestionale',
                'Stato'
            ], default_format=excel_format['header'])

            _logger.warning('Load document found #%s' % len(records))
            for record in records:
                if document == 'CL':
                    name = record.accounting_cl_code
                else:
                    name = record.accounting_sl_code

                fullname = '%s-%s' % (document, name)
                if name in account_data[document]:
                    state = ''
                    account_name = fullname
                    # Clean record:
                    account_data[document].remove(name)
                else:
                    state = 'Non trovato'
                    account_name = ''

                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    fullname,
                    account_name,
                    state,
                ], default_format=excel_format['text'])

        # Remain only in Account:
        for document in account_data:
            records = account_data[document]
            ws_name = '%s solo a gestionale' % document

            excel_pool.create_worksheet(ws_name)
            # Write header:
            excel_pool.column_width(ws_name, [
                15, 15, 20,
            ])

            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                'Documenti %s solo a gestionale' % document,
                ], default_format=excel_format['title'])
            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                'Documento',
            ], default_format=excel_format['header'])

            for record in records:
                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    record,
                ], default_format=excel_format['text'])

        return excel_pool.return_attachment(
            cr, uid, 'Stato documenti di MRP', version='7.0', php=True,
            context=context)

    def get_production_parameter(self, cr, uid, context=None):
        """ Return browse object for default company for get all parameter
            created
        """
        company_id = self.search(cr, uid, [], context=context)
        if company_id:
            return self.browse(cr, uid, company_id, context=context)[0]
        else:
            return False

    def xmlrpc_get_server(self, cr, uid, context=None):
        """ Configure and retur XML-RPC server for accounting
        """
        parameters = self.get_production_parameter(cr, uid, context=context)
        try:
            mx_parameter_server = parameters.production_host
            mx_parameter_port = parameters.production_port

            xmlrpc_server = "http://%s:%s" % (
                mx_parameter_server,
                mx_parameter_port,
            )
        except:
            raise osv.except_osv(
                _('Import CL error!'),
                _('XMLRPC for calling importation is not response'), )

        return xmlrpclib.ServerProxy(xmlrpc_server)

    _columns = {
        'production_export': fields.boolean(
            'Production export',
            help="Enable export of CL and SL document via XML-RPC with exchange file"),
        'production_mx': fields.boolean(
            'Installazione MX',
            help="Installazione succursale Messico"),
        'production_demo': fields.boolean(
            'Production demo', help="Jump XMLRPC for demo test"),
        'production_mount_mandatory': fields.boolean(
            'Mount mandatory',
            help="Test if folder for interchange files must be mounted"),
        'production_host': fields.char(
            'Production XMLRPC host', size=64,
            help="Host name, IP address: 10.0.0.2 or hostname: server.example.com"),
        'production_port': fields.integer(
            'MS SQL server port', help="XMLRPC port, example: 8000"),
        'production_cl': fields.char(
            'Production interchange file CL', size=64,
            help="File name for CL exhange file"),
        'production_cl_upd': fields.char(
            'Production interchange file SL', size=64,
            help="File name for SL exhange file"),
        'production_sl': fields.char(
            'Production interchange file SL', size=64,
            help="File name for SL exhange file"),

        # Mount point:
        'production_path': fields.text(
            'Production interchange path',
            help="Path of folder used for interchange, passed as a list: ('~','home','exchange')"),
        # 'production_mount_unc':fields.char('Windows UNC name', size=64,
        # help="Example: //server_ip/share_name"),
        # 'production_mount_user':fields.char('Windows user for mount
        # resource', size=64, readonly=False),
        # 'production_mount_password':fields.char('Windows user for mount
        # resource', size=64, password=True),
        # 'production_mount_sudo_password':fields.char('Linux sudo password',
        # size=64, password=True),
        # 'production_mount_uid':fields.char('Linux user group for mount
        # resource', size=64, readonly=False),
        # 'production_mount_gid':fields.char('Linux user group for mount
        # resource', size=64, readonly=False),
    }
    _defaults = {
        'production_demo': lambda *x: False,
        'production_mount_mandatory': lambda *x: True,
        'production_port': lambda *a: 8000,
        'production_cl': lambda *a: "cl.txt",
        'production_sl': lambda *a: "sl.txt",
        'production_cl_upd': lambda *a: "cl_upd.txt",
        'production_export': lambda *a: False,

        # 'production_mount_user': lambda *a: "administrator",
        # 'production_mount_uid': lambda *a: "openerp",
        # 'production_mount_gid': lambda *a: "openerp",
    }
