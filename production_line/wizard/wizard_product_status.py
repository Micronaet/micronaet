# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
##############################################################################
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
##############################################################################
import os
import pdb
import sys
import logging
import openerp
import xlsxwriter
from openerp.osv import fields, osv, expression
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

# Mail lib:
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders

_logger = logging.getLogger(__name__)


class MrpProductionExtraFunctions(osv.osv):
    """ Create extra fields in mrp.production obj
    """
    _inherit = 'mrp.production'

    def _start_up_weekly(self, cr, uid, data=None, context=None):
        """ Master function for prepare report weekly used
        """
        # ---------------------------------------------------------------------
        # Utility for procedure:
        # ---------------------------------------------------------------------
        def add_element_material_composition(
                product, quantity, master_data, extra_comment,
                real_date_planned
                ):
            """ Block used for unload materials and for simulation
            """
            if product.not_in_status:  # Jump 'not in status' material
                return

            element = (
                'M',
                product.id,
                product,  # XXX for minimum
            )
            if element not in master_data['rows']:
                master_data['rows'].append(element)

                # prepare data structure:
                master_data['table'][element[1]] = \
                    [0.0 for item in range(0, range_date)]
                master_data['table_comment'][element[1]] = \
                    ['' for item in range(0, range_date)]

                # Sapnaet integrazione:
                accounting_qty = product.accounting_qty
                try:
                    accounting_qty += product.locked_qty
                except:
                    pass  # No sapnaet mode

                master_data['table'][element[1]][0] = accounting_qty
                master_data['table_comment'][element[1]][0] += \
                    'Gest.: Q. %s\n' % accounting_qty

            isocalendar = datetime.strptime(
                real_date_planned[:10], DEFAULT_SERVER_DATE_FORMAT).\
                isocalendar()
            week_ref = '%s/%s' % (isocalendar[0], isocalendar[1])

            if week_ref in col_ids:
                position = col_ids[week_ref]
            else:  # XXX TODO manage over date!?! < today
                position = 1

            # Write data:
            master_data['table'][element[1]][position] -= quantity
            master_data['table_comment'][element[1]][position] += \
                'SL: Q. %s [%s] %s\n' % (
                    quantity,
                    real_date_planned,
                    extra_comment,
                    )
            return

        # ---------------------------------------------------------------------
        #                            Start procedure:
        # ---------------------------------------------------------------------
        if data is None:
            data = {}

        # Pool used:
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')

        # Global parameters:
        master_data = {
            'rows': [], 'cols': [],
            'minimum': {},  # Stock level
            'table': {},
            'table_comment': {},
            'error_in_print': '',
            }

        # todo optimize:
        product_ids = product_pool.search(cr, uid, [], context=context)
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            master_data['minimum'][product.id] = product.min_stock_level

        # Init parameters:
        col_ids = {}
        range_date = data.get('days', 7) + 1
        week_range = 1 + range_date // 7  # Total week
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days=range_date - 1)
        # with_order_detail = data.get('with_order_detail', False) # no used

        isocalendar = start_date.isocalendar()
        start_week = '%s/%s' % (isocalendar[0], isocalendar[1])

        # 0 (<today), 1..n [today, today + total days], delta)
        # todo change in Week
        for i in range(0, week_range):
            if i == 0:  # today
                master_data['cols'].append(start_week)
                col_ids[start_week] = 0
            elif i == 1:  # before today
                this_date = start_date
                master_data['cols'].append('< %s' % start_week)
                col_ids['before'] = 1  # not used!
            else:  # other days
                this_date = start_date + timedelta(days=7 * (i - 1))
                isocalendar = this_date.isocalendar()
                week_ref = '%s/%s' % (isocalendar[0], isocalendar[1])
                master_data['cols'].append(week_ref)
                col_ids[week_ref] = i - 1

        # ---------------------------------------------------------------------
        #                       GENERATE HEADER VALUES
        # ---------------------------------------------------------------------
        # Get material list from Job order
        # ---------------------------------------------------------------------
        lavoration_ids = lavoration_pool.search(cr, uid, [
            # only < max date range
            ('real_date_planned', '<=', end_date.strftime(
                '%Y-%m-%d 23:59:59')),
            ('state', 'not in', ('cancel', 'done')),
        ], context=context)  # only open not canceled

        for lavoration in lavoration_pool.browse(
                cr, uid, lavoration_ids, context=context):  # filtered BL ord.

            real_date_planned = lavoration.real_date_planned[:10]  # readab.
            # -----------------------------------------------------------------
            # Material in BOM:
            # -----------------------------------------------------------------
            extra_comment = '%s (Lav. %s)' % (
                lavoration.product.default_code, lavoration.name)
            for material in lavoration.bom_material_ids:
                add_element_material_composition(
                    material.product_id,
                    material.quantity,
                    master_data,
                    extra_comment,
                    real_date_planned,
                )
        master_data['rows'].sort()
        return master_data


# WIZARD PRINT REPORT ########################################################
class product_status_wizard(osv.osv_memory):
    """ Parameter for product status per day
    """
    _name = 'product.status.wizard'
    _description = 'Product status wizard'

    # Utility:
    def send_mail(
            self, send_from, send_to, subject, text, xls_filename, server,
            port, username='', password='', isTls=False):
        """ Send mail procedure:
        """
        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = send_to
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        msg.attach(MIMEText(text))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(xls_filename, 'rb').read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            'attachment; filename=stato_magazzino.xlsx',
            )
        msg.attach(part)

        # context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
        # SSL connection only working on Python 3+
        smtp = smtplib.SMTP(server, port)
        if isTls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.quit()
        return True

    # -------------------------------------------------------------------------
    # Events:
    # -------------------------------------------------------------------------
    def get_data_description(self, datas=None):
        """ Prepare description filter string from data dict
        """
        if datas is None:
            return _('No filter')

        res = ''
        res += 'Period in days: %s -' % datas.get('days', '')
        res += 'Row mode: %s -' % datas.get('row_mode', '')
        res += 'With medium: %s [month period %s]-' % (
            'yes' if datas.get('with_medium', False) else 'no',
            datas.get('month_window', '/'),
            )
        res += 'With OF detail' if datas.get(
            'with_order_detail', False) else 'No OF detail',
        res += 'With fake order: %s -' % (
            'yes' if datas.get('fake_ids', False) else 'no',
            )
        return res

    def prepare_data(self, cr, uid, ids, context=None):
        """ Prepare data dict
        """
        wiz_proxy = self.browse(cr, uid, ids)[0]
        datas = {}
        if wiz_proxy.days:
            datas['days'] = wiz_proxy.days

        datas['row_mode'] = wiz_proxy.row_mode
        # datas['active'] = wiz_proxy.row_mode
        # datas['negative'] = wiz_proxy.negative
        datas['with_medium'] = wiz_proxy.with_medium
        datas['month_window'] = wiz_proxy.month_window
        datas['with_order_detail'] = wiz_proxy.with_order_detail

        datas['fake_ids'] = wiz_proxy.fake_ids
        return datas

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    def export_material_used(self, cr, uid, ids, context=None):
        """ Export excel file
            Check material in job scheduled in period
        """
        if context is None:
            context = {}

        # Pool used:
        job_pool = self.pool.get('mrp.production.workcenter.line')
        excel_pool = self.pool.get('excel.writer')

        comment_parameters = {
            'width': 450,
            'font_name': 'Courier New',
        }

        wizard = self.browse(cr, uid, ids, context=context)[0]
        days = wizard.days or 7

        now_dt = datetime.now()
        end_dt = now_dt + timedelta(days=days)
        now_text = str(now_dt)[:10]
        end_text = str(end_dt)[:10]

        job_ids = job_pool.search(cr, uid, [
            ('real_date_planned', '>=', '%s 00:00:00' % now_text),
            ('real_date_planned', '<=', '%s 23:59:59' % end_text),
        ], context=context)
        material_db = {}
        for job in job_pool.browse(cr, uid, job_ids, context=context):
            for material in job.bom_material_ids:
                product = material.product_id
                quantity = material.quantity
                if product not in material_db:
                    material_db[product] = {
                        'quantity': 0.0,
                        'job': [],
                    }

                if job not in material_db[product]['job']:
                    material_db[product]['job'].append(
                        (quantity, job))  # for comment purposes
                material_db[product]['quantity'] += quantity

        ws_name = 'Modificati'
        excel_pool.create_worksheet(ws_name)

        # Format:
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
            20, 45, 15, 15,
        ])

        # Write header:
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            'Stato uscita materie prime lavorazioni schedulate dalla '
            'data {} alla data {}'.format(
                now_text,
                end_text
            )
        ], default_format=excel_format['title'])

        row += 1
        excel_pool.write_xls_line(ws_name, row, [
            'Codice',
            'Nome',
            'Q. Magazz.',
            'Q. uscita',
        ], default_format=excel_format['header'])

        for product in sorted(material_db, key=lambda p: p.default_code):
            record = material_db[product]
            jobs = material_db[product]['job']

            comment = ''
            for material_qty, job in jobs:
                comment += '%s x [%s: Produz. %s Job: %s]\n' % (
                    int(material_qty),
                    job.real_date_planned[:10],
                    job.product.default_code or '',
                    job.name,
                )

            row += 1
            account_qty = int(product.accounting_qty)
            used_qty = int(record['quantity'])
            if account_qty < used_qty:
                color = excel_format['red']
            else:
                color = excel_format['white']

            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                product.name,
                (account_qty, color['number']),
                (used_qty, color['number']),
            ], default_format=color['text'])
            excel_pool.write_comment(
                ws_name, row, 3, comment,
                parameters=comment_parameters)

        return excel_pool.return_attachment(
            cr, uid, 'Stato settimanale', version='7.0', php=True,
            context=context)

    def export_excel(self, cr, uid, ids, context=None):
        """ Export excel file
            Procedure used also for sent mail (used context parameter
            sendmail for activate with datas passed)
        """
        if context is None:
            context = {}

        save_mode = context.get('save_mode')
        _logger.info('Start extract save mode: %s' % save_mode)

        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def load_montly_peak_stats(self, cr, uid, ids, context=None):
            """ Load SL for row materials (monthly peak)
            """
            log_mode = True

            res = {}
            material_pool = self.pool.get('mrp.production.material')

            if log_mode:
                log_file = open('/tmp/peak_material.log', 'w')

            now = datetime.now()
            from_date = '%04d-%02d-01' % (
                now.year - 1,
                now.month,
            )
            material_ids = material_pool.search(cr, uid, [
                ('workcenter_production_id.state', '=', 'done'),
                ('workcenter_production_id.date_start', '>=', from_date),
            ], context=context)
            for material in material_pool.browse(
                    cr, uid, material_ids, context=context):
                wc = material.workcenter_production_id
                name = wc.name
                period = wc.date_start[:7]
                quantity = material.quantity
                product = material.product_id
                default_code = product.default_code or ''
                start = default_code[:1]

                if start and start not in 'AB':
                    continue  # Raw material only:

                if default_code not in res:
                    res[default_code] = {}
                if period not in res[default_code]:
                    res[default_code][period] = 0.0

                res[default_code][period] += quantity
                if log_mode:
                    log_file.write('%s|%s|%s|%s\n' % (
                        name,
                        default_code,
                        period,
                        quantity,
                    ))

            if log_mode:
                log_file.close()
            return res

        def write_supplier_order_detail(record):
            """
            """
            if not record:
                return ''

            res = ''
            for d, q in record.iteritems():
                try:
                    res += '[%s-%s-%s Q.: %s] ' % (
                        d[8:10], d[5:7], d[:4],
                        int(q),
                        )
                except:
                    return _('ERROR!')
            return res

        def write_xls_mrp_line(WS, row, line):
            """ Write line in excel file
            """
            col = 0
            for item, format_cell in line:
                WS.write(row, col, item, format_cell)
                col += 1
            return True

        def write_xls_mrp_line_comment(WS, row, line, gap_column=0):
            """ Write comment cell in excel file
            """
            parameters = {
                'width': 300,
                'font_name': 'Courier 10 Pitch',
                }
            col = gap_column
            for comment in line:
                if comment:
                    WS.write_comment(row, col, comment, parameters)
                col += 1
            return True

        def use_row(row, data=None, product=False):
            """ Check if row must be used depend on row_mode
            """
            if data is None:
                data = {}
            row_mode = data.get('row_mode', 'active')

            # -----------------------------------------------------------------
            # All record, All value
            # -----------------------------------------------------------------
            if row_mode == 'all':
               return True  # no filter is required

            # -----------------------------------------------------------------
            # Record with data but no elements:
            # -----------------------------------------------------------------
            elif row_mode == 'active' and not any(row):
                return False

            # -----------------------------------------------------------------
            # Negative or under level:
            # -----------------------------------------------------------------
            elif row_mode in ('negative', 'level'):
                if row_mode == 'negative' or not product:
                    level = 0.0
                else:
                    level = product.min_stock_level

                partial = 0
                for q in row:
                    partial += q
                    if partial < level:
                        return True
                return False
            else:
                return True

        if context is None:
            context = {}

        if context.get('datas', False):
            sendmail = True
            data = context.get('datas', {})
        else:
            sendmail = False
            data = self.prepare_data(cr, uid, ids, context=context)

        # Pool used:
        mrp_pool = self.pool.get('mrp.production')
        attachment_pool = self.pool.get('ir.attachment')

        # ---------------------------------------------------------------------
        # Preload
        # ---------------------------------------------------------------------
        # Monthly peak
        monthly_peak_data = load_montly_peak_stats(
            self, cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # XLS file:
        # ---------------------------------------------------------------------
        filename = '/tmp/production_status.xlsx'
        filename = os.path.expanduser(filename)
        _logger.info('Start export status on %s' % filename)

        # Open file and write header
        WB = xlsxwriter.Workbook(filename)
        # 2 Sheets
        WS = WB.add_worksheet('Material')
        WS_product = WB.add_worksheet('Product')

        # ---------------------------------------------------------------------
        # Format elements:
        # ---------------------------------------------------------------------
        num_format = '#,##0'
        format_title = WB.add_format({
            'bold': True,
            'font_color': 'black',
            'font_name': 'Arial',
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'gray',
            'border': 1,
            'text_wrap': True,
            })

        format_text = WB.add_format({
            'font_name': 'Arial',
            'align': 'left',
            'font_size': 9,
            'border': 1,
            })

        format_white = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': 'white',
            'border': 1,
            'num_format': num_format,
            })
        format_yellow = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ffff99',  # 'yellow',
            'border': 1,
            'num_format': num_format,
            })
        format_red = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ff9999',  # 'red',
            'border': 1,
            'num_format': num_format,
            })
        format_green = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#c1ef94',  # 'green',
            'border': 1,
            'num_format': num_format,
            })

        # ---------------------------------------------------------------------
        # Format columns:
        # ---------------------------------------------------------------------
        # Column dimension:
        WS.set_column('A:A', 35)
        WS.set_column('E:F', 20)
        WS.set_row(0, 30)
        WS_product.set_column('A:A', 35)
        WS_product.set_column('E:F', 20)
        WS_product.set_row(0, 30)

        # Generate report for export:
        context['lang'] = 'it_IT'
        mrp_pool._start_up(cr, uid, data, context=context)
        start_product = False
        cols = mrp_pool._get_cols()

        if data.get('with_order_detail', False):
            history_supplier_orders = mrp_pool._get_history_supplier_orders()
        else:
            history_supplier_orders = {}

        # Start loop for design table for product and material status:
        # Header:
        header = [
            # list for update after for product:
            [_('Material'), format_title],

            (_('Code'), format_title),
            (_('Mx. stock'), format_title),
            (_('Min. stock'), format_title),
            (_('OF detail'), format_title),

            (_('Picco mensile MP'), format_title),

            (_('m(x) last %s month') % data['month_window'], format_title),
            ]
        fixed_col = len(header)
        for col in cols:
            header.append((col, format_title))
        try:  # Override description for first column variable:
            header[fixed_col] = (_('Giacenza KG'), format_title)
        except:
            pass

        # Material header:
        write_xls_mrp_line(WS, 0, header)
        # Product header
        header[0][0] = _('Product')
        write_xls_mrp_line(WS_product, 0, header)

        # Body:
        i = 1  # row position (before 0)
        rows = mrp_pool._get_rows()

        table, table_comment = mrp_pool._get_table()  # For check row state

        for row in rows:
            # Check mode: only active
            if not use_row(table[row[1]], data, product=row[2]):
                # _logger.error('No: %s' % (table[row[1]], ))
                continue
            else:
                pass
                # _logger.info('Yes: %s' % (table[row[1]], ))

            if not start_product and row[0] == 'P':
                WS = WS_product  # change ref. for use second sheet
                start_product = True
                i = 1  # jump one line

            status_line = 0.0
            default_code = (row[2].default_code or '/').strip()

            # -----------------------------------------------------------------
            # Peak data:
            # -----------------------------------------------------------------
            monthly_peak = monthly_peak_data.get(default_code, {})
            peak_comment = []
            peak_data = ''
            if monthly_peak:
                peak_max = 0.0
                for period in monthly_peak:
                    peak_q = monthly_peak[period]
                    if peak_q > peak_max:
                        peak_max = peak_q
                        peak_data = '%s: Kg.%.0f' % (period, peak_q)

                    peak_comment.append('%s: Kg.%10.0f' % (period, peak_q))

            body = [
                (row[2].name, format_text),
                (default_code, format_text),
                (row[2].minimum_qty, format_white),  # min level account
                (row[2].min_stock_level, format_white),  # min level calc
                (write_supplier_order_detail(
                 history_supplier_orders.get(default_code, '')),
                 format_text,
                 ),  # OF detail
                (peak_data, format_white),  # Peak
                (row[3], format_white),  # m(x)
                ]
            gap_columns = len(body)
            peak_columns = gap_columns - 2

            j = 0
            for col in cols:
                (q, minimum) = mrp_pool._get_cel(j, row[1])
                j += 1
                status_line += q
                # Choose the color:
                if not status_line:  # value = 0
                    body.append((status_line, format_white))
                elif status_line > minimum:  # > minimum value (green)
                    body.append((status_line, format_green))
                    pass  # Green
                elif status_line > 0.0:  # under minimum (yellow)
                    body.append((status_line, format_yellow))
                elif status_line < 0.0:  # under 0 (red)
                    body.append((status_line, format_red))
                else:  # ("=", "<"): # not present!!!
                    body.append((status_line, format_white))
            write_xls_mrp_line(WS, i, body)

            # -----------------------------------------------------------------
            # Comment:
            # -----------------------------------------------------------------
            if peak_comment:
                peak_comment_text = '\n'.join(sorted(peak_comment))
                write_xls_mrp_line_comment(
                    WS, row=i, line=[peak_comment_text],
                    gap_column=peak_columns)
            comment_line = table_comment.get(row[1])
            if comment_line:
                write_xls_mrp_line_comment(
                    WS, row=i, line=comment_line, gap_column=gap_columns)

            i += 1
        _logger.info('End export status on %s' % filename)
        WB.close()

        xlsx_raw = open(filename, 'rb').read()
        b64 = xlsx_raw.encode('base64')
        if sendmail:
            # -----------------------------------------------------------------
            # Send via mail:
            # -----------------------------------------------------------------
            _logger.info('Sending status via mail: %s' % filename)
            date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # Send mail with attachment:
            group_pool = self.pool.get('res.groups')
            model_pool = self.pool.get('ir.model.data')
            # thread_pool = self.pool.get('mail.thread')
            server_pool = self.pool.get('ir.mail_server')

            group_id = model_pool.get_object_reference(
                cr, uid, 'production_line', 'group_stock_negative_status')[1]
            partner_email = []
            for user in group_pool.browse(
                    cr, uid, group_id, context=context).users:
                partner_email.append(user.partner_id.email) # .id

            # thread_pool = self.pool.get('mail.thread')
            # thread_pool.message_post(cr, uid, False,
            #    type='email',
            #    body=_('Negative stock status report'),
            #    subject='Stock status: %s' % date,
            #    partner_ids=[(6, 0, partner_ids)],
            #    attachments=[
            #        ('stock_status.xlsx', xlsx_raw)],
            #    context=context,
            #    )
            server_ids = server_pool.search(cr, uid, [
                ('active', '=', True),
                ], order='sequence', context=context)
            if not server_ids:
                _logger.error('No server for send mail!')
                return False
            server_proxy = server_pool.browse(
                cr, uid, server_ids, context=context)[0]
            _logger.info('SMTP server: %s:%s user: %s' % (
                server_proxy.smtp_host,
                server_proxy.smtp_port,
                server_proxy.smtp_user,
                ))

            # -----------------------------------------------------------------
            # Save mode:
            # -----------------------------------------------------------------
            if save_mode: # Save as a file:
                _logger.warning('Save mode: %s' % save_mode)
                return filename

            # -----------------------------------------------------------------
            # Mail mode:
            # -----------------------------------------------------------------
            for email in partner_email:
                _logger.warning('... sending mail: %s' % email)
                self.send_mail(
                    server_proxy.smtp_user,
                    email,
                    _('Negative stock status report'),
                    _('Stock status for negative product with production'),
                    filename,
                    server_proxy.smtp_host,
                    server_proxy.smtp_port,
                    username=server_proxy.smtp_user,
                    password=server_proxy.smtp_pass,
                    isTls=False,
                    )
        else:
            # -----------------------------------------------------------------
            # Open attachment form:
            # -----------------------------------------------------------------
            attachment_id = attachment_pool.create(cr, uid, {
                'name': 'Status MRP Report',
                'datas_fname': 'status_report.xlsx',
                'type': 'binary',
                'datas': b64,
                'partner_id': 1,
                'res_model': 'res.partner',
                'res_id': 1,
                }, context=context)

            return {
                'name': _('XLS file status'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': attachment_id,
                'res_model': 'ir.attachment',
                'views': [(False, 'form')],
                'context': context,
                'target': 'current',
                'nodestroy': False,
                }

    def export_excel_used_weekly(self, cr, uid, ids, context=None):
        """ Export excel file
            Procedure used also for sent mail (used context parameter
            sendmail for activate with datas passed)
        """
        def write_xls_mrp_line(WS, row, line):
            """ Write line in excel file
            """
            col = 0
            for item, format_cell in line:
                WS.write(row, col, item, format_cell)
                col += 1
            return True

        def write_xls_mrp_line_comment(WS, row, line, gap_column=0):
            """ Write comment cell in excel file
            """
            parameters = {
                'width': 300,
                'font_name': 'Courier 10 Pitch',
                }
            col = gap_column
            for comment in line:
                if comment:
                    WS.write_comment(row, col, comment, parameters)
                col += 1
            return True

        # ---------------------------------------------------------------------
        # Start procedure
        # ---------------------------------------------------------------------
        if context is None:
            context = {}

        if context.get('datas', False):
            sendmail = True
            data = context.get('datas', {})
        else:
            sendmail = False
            data = self.prepare_data(cr, uid, ids, context=context)

        # Pool used:
        mrp_pool = self.pool.get('mrp.production')
        attachment_pool = self.pool.get('ir.attachment')

        # ---------------------------------------------------------------------
        # XLS file:
        # ---------------------------------------------------------------------
        filename = '/tmp/production_weekly_used.xlsx'
        filename = os.path.expanduser(filename)
        _logger.info('Start export weekly used on %s' % filename)

        # Open file and write header
        WB = xlsxwriter.Workbook(filename)
        WS = WB.add_worksheet('Material')

        # ---------------------------------------------------------------------
        # Format elements:
        # ---------------------------------------------------------------------
        num_format = '#,##0'
        format_title = WB.add_format({
            'bold': True,
            'font_color': 'black',
            'font_name': 'Arial',
            'font_size': 10,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'gray',
            'border': 1,
            'text_wrap': True,
            })

        format_text = WB.add_format({
            'font_name': 'Arial',
            'align': 'left',
            'font_size': 9,
            'border': 1,
            })

        format_white = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': 'white',
            'border': 1,
            'num_format': num_format,
            })
        format_yellow = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ffff99',  # 'yellow',
            'border': 1,
            'num_format': num_format,
            })
        format_red = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ff9999',  # 'red',
            'border': 1,
            'num_format': num_format,
            })
        format_green = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#c1ef94',  # 'green',
            'border': 1,
            'num_format': num_format,
            })

        # ---------------------------------------------------------------------
        # Format columns:
        # ---------------------------------------------------------------------
        # Column dimension:
        WS.set_column('A:A', 30)
        # WS.set_column('E:F', 20)
        WS.set_row(0, 30)

        # Generate report for export:
        context['lang'] = 'it_IT'
        master_data = mrp_pool._start_up_weekly(cr, uid, data, context=context)
        cols = master_data['cols']

        # Start loop for design table for product and material status:
        # Header:
        header = [
            # list for update after for product:
            (_('Materiale'), format_title),
            (_('Codice'), format_title),
            ]
        fixed_col = len(header)
        for col in cols:
            header.append((col, format_title))

        # Material header:
        write_xls_mrp_line(WS, 0, header)

        # Body:
        i = 1  # row position (before 0)
        rows = master_data['rows']
        table = master_data['table']
        table_comment = master_data['table_comment']

        for row in rows:
            status_line = 0.0
            default_code = (row[2].default_code or '/').strip()

            body = [
                (row[2].name, format_text),
                (default_code, format_text),
                ]
            gap_columns = len(body)
            j = 0
            for col in cols:
                # (q, minimum) = mrp_pool._get_cel(j, row[1])
                product_id = row[1]
                data_position = master_data['cols'].index(col)
                if product_id in table:
                    q, minimum = (
                        table[product_id][data_position],
                        master_data['minimum'].get(product_id, 0.0))
                else:
                    q = minimum = 0.0

                j += 1
                status_line += q
                # Choose the color:
                if not status_line:  # value = 0
                    body.append((status_line, format_white))
                elif status_line > minimum:  # > minimum value (green)
                    body.append((status_line, format_green))
                    pass  # Green
                elif status_line > 0.0:  # under minimum (yellow)
                    body.append((status_line, format_yellow))
                elif status_line < 0.0:  # under 0 (red)
                    body.append((status_line, format_red))
                else:  # ("=", "<"): # not present!!!
                    body.append((status_line, format_white))
            write_xls_mrp_line(WS, i, body)

            # -----------------------------------------------------------------
            # Comment:
            # -----------------------------------------------------------------
            comment_line = table_comment.get(row[1])
            if comment_line:
                write_xls_mrp_line_comment(
                    WS, row=i, line=comment_line, gap_column=gap_columns)

            i += 1
        _logger.info('End export status on %s' % filename)
        WB.close()

        xlsx_raw = open(filename, 'rb').read()
        b64 = xlsx_raw.encode('base64')

        # -----------------------------------------------------------------
        # Open attachment form:
        # -----------------------------------------------------------------
        attachment_id = attachment_pool.create(cr, uid, {
            'name': 'Status MRP Weekly Used Report',
            'datas_fname': 'status_weekly_used_report.xlsx',
            'type': 'binary',
            'datas': b64,
            'partner_id': 1,
            'res_model': 'res.partner',
            'res_id': 1,
            }, context=context)

        return {
            'name': _('XLSX Weekly used status'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': attachment_id,
            'res_model': 'ir.attachment',
            'views': [(False, 'form')],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }

    def schedule_send_negative_report(
            self, cr, uid, wizard=None, context=None):
        """ Send mail to group user for negative elements
        """
        # XXX Was overridden!!!
        if context is None:
            context = {}

        # Default if not parameter
        context['datas'] = {
            'days': 30,
            'row_mode': 'negative',
            'with_medium': True,
            'month_window': 3,
            'with_order_detail': True,
            'fake_ids': [],  # todo << nothing?
            }

        if wizard is not None:
            context['datas'].update(wizard)

        # todo update previsional order?
        self.export_excel(cr, uid, False, context=context)
        return True

    def print_report(self, cr, uid, ids, context=None):
        """ Redirect to bom report passing parameters
        """
        datas = self.prepare_data(cr, uid, ids, context=context)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'webkitstatus',
            'datas': datas,
            }

    _columns = {
        'days': fields.integer('Days from today', required=True),
        # REMOVE:
        # 'active':fields.boolean('Only record with data', required=False,
        # help="Show only product and material with movement"),
        # 'negative': fields.boolean('Only negative', required=False,
        # help="Show only product and material with negative value in range"),
        # USE:
        'row_mode': fields.selection([
            ('all', 'All data'),
            ('active', 'With data'),
            ('negative', 'With negative'),
            ('level', 'Under minimum level'),
            ], 'Row mode', required=True),

        'month_window': fields.integer(
            'Statistic production window ',
            required=True,
            help="Month back for medium production monthly index (Kg / month of prime material)"),
        'with_medium': fields.boolean('With m(x)', required=False,
            help="if check in report there's production m(x), if not check report is more fast"),
        'with_order_detail': fields.boolean('With OF detail'),
        }

    _defaults = {
        'days': lambda *a: 7,
        'month_window': lambda *x: 2,
        'with_medium': lambda *x: True,
        'row_mode': lambda *x: 'active',
        }


class ProductStatusProductionFakeWizard(osv.osv_memory):
    """ Model name: MrpProductionFake
    """
    _name = 'product.status.production.fake.wizard'
    _rec_name = 'product_id'
    _order = 'product_id'

    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product', required=True),
        'qty': fields.float('Q.ty (Kg.)', digits=(16, 3), required=True),
        'production_date': fields.date('Date production', required=True),
        'bom_id': fields.many2one('mrp.bom', 'BOM', required=True),
        'wizard_id': fields.many2one(
            'product.status.wizard', 'Wizard ID'),
        }


class product_status_wizard(osv.osv_memory):
    """ Parameter for product status per day
    """
    _inherit = 'product.status.wizard'

    _columns = {
        'fake_ids': fields.one2many(
            'product.status.production.fake.wizard', 'wizard_id',
            'Production fake'),
        }
