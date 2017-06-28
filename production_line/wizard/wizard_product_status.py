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


_logger = logging.getLogger(__name__)


# WIZARD PRINT REPORT ########################################################
class product_status_wizard(osv.osv_memory):
    ''' Parameter for product status per day
    '''    
    _name = 'product.status.wizard'
    _description = 'Product status wizard'

    # Utility:
    def send_mail(
            self, send_from, send_to, subject, text, xls_filename, server, 
            port, username='', password='', isTls=False):
        ''' Send mail procedure:
        '''    
        import smtplib
        import ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.text import MIMEText
        from email.utils import formatdate
        from email import encoders

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

        #context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
        #SSL connection only working on Python 3+
        smtp = smtplib.SMTP(server, port)
        if isTls:
            smtp.starttls()
        smtp.login(username,password)
        smtp.sendmail(send_from, send_to, msg.as_string())        
        smtp.quit()
        return True
        
    
    # -------------------------------------------------------------------------
    # Events:
    # -------------------------------------------------------------------------
    def get_data_description(self, data=None):
        ''' Prepare description filter string from data dict
        '''
        if data is None:
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
        ''' Prepare data dict
        '''
        wiz_proxy = self.browse(cr, uid, ids)[0]
        datas = {}
        if wiz_proxy.days:
            datas['days'] = wiz_proxy.days

        datas['row_mode'] = wiz_proxy.row_mode
        #datas['active'] = wiz_proxy.row_mode
        #datas['negative'] = wiz_proxy.negative
        datas['with_medium'] = wiz_proxy.with_medium
        datas['month_window'] = wiz_proxy.month_window
        datas['with_order_detail'] = wiz_proxy.with_order_detail
        
        datas['fake_ids'] = wiz_proxy.fake_ids
        return datas

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    def export_excel(self, cr, uid, ids, context=None):
        ''' Export excel file
            Procedure used also for sent mail (used context parameter 
            sendmail for activate with datas passed)
        '''
        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def write_supplier_order_detail(record):
            '''
            '''
            if not record:
                return ''
            res = ''
            for d, q in record.iteritems():
                res += '%s-%s-%s Q.: %s' % (
                    d[8:10], d[5:7], d[:4],
                    int(q),
                    )
            return res        
                
        def write_xls_mrp_line(WS, row, line):
            ''' Write line in excel file
            '''
            col = 0
            for item, format_cell in line:
                WS.write(row, col, item, format_cell)
                col += 1
            return True
        
        def use_row(row, data=None):
            ''' Check if row must be used depend on row_mode
            '''
            if data is None:
                data = {}            
            row_mode = data.get('row_mode', 'active')
            
            # All record, All value
            if row_mode == 'all':
               return True # no filter is required
         
            # Record with data but no elements:   
            elif row_mode == 'active' and not any(row):
                return False
            
            # Only negative but no any negative:
            elif row_mode == 'negative':
                partial = 0
                for q in row:
                    partial += q
                    if partial < 0:
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
            'bg_color': '#ffff99', #'yellow',
            'border': 1,
            'num_format': num_format,
            })
        format_red = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ff9999', #'red',
            'border': 1,
            'num_format': num_format,
            })
        format_green = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#c1ef94', #'green',
            'border': 1,
            'num_format': num_format,
            })

        # ---------------------------------------------------------------------
        # Format columns:
        # ---------------------------------------------------------------------
        # Column dimension:
        WS.set_column ('A:A', 35) # Image colums
        WS.set_row(0, 30)
        WS_product.set_column ('A:A', 35) # Image colums
        WS_product.set_row(0, 30)
            
        # Generate report for export:
        context['lang'] = 'it_IT'
        mrp_pool._start_up(cr, uid, data, context=context)        
        start_product = False
        cols = mrp_pool._get_cols()
        
        if data.get('with_order_detail', False):
            supplier_orders = mrp_pool._get_supplier_orders()
        else:
            supplier_orders = {}        
        
        # Start loop for design table for product and material status:
        # Header: 
        header = [
            [_('Material'), format_title], # list for update after for product
            [_('Code'), format_title],
            [_('Min. stock'), format_title],
            [_('OF detail'), format_title],
            (_('m(x) last %s month') % data['month_window'], format_title),
            ]        
        for col in cols:
            header.append((col, format_title))
            
        # Material header:
        write_xls_mrp_line(WS, 0, header)
        # Product header
        header[0][0] = _('Product')
        write_xls_mrp_line(WS_product, 0, header)

        # Body:
        i = 1 # row position (before 0)
        rows = mrp_pool._get_rows()

        table = mrp_pool._get_table() # For check row state

        for row in rows:
            # Check mode: only active
            if not use_row(table[row[1]], data):
                 _logger.error('No: %s' % (table[row[1]], ))
                 continue
            else:     
                 _logger.info('Yes: %s' % (table[row[1]], ))

            if not start_product and row[0] == 'P':
                WS = WS_product # change ref. for use second sheet
                start_product = True
                i = 1 # jump one line
                                    
            status_line = 0.0
            default_code = row[2].default_code or '/'
            body = [
                (row[2].name, format_text),
                (default_code, format_text),
                (row[2].minimum_qty, format_white),
                (write_supplier_order_detail(
                    supplier_orders.get(default_code, '')), format_text),
                (row[3], format_white),
                ]
            j = 0
            for col in cols:
                (q, minimum) = mrp_pool._get_cel(j, row[1])
                j += 1
                status_line += q                    
                # Choose the color:
                if not status_line: # value = 0
                    body.append((status_line, format_white))
                elif status_line > minimum: # > minimum value (green)
                    body.append((status_line, format_green))
                    pass # Green
                elif status_line > 0.0: # under minimum (yellow)
                    body.append((status_line, format_yellow))
                elif status_line < 0.0: # under 0 (red)
                    body.append((status_line, format_red))
                else: # ("=", "<"): # not present!!!
                    body.append((status_line, format_white))
            write_xls_mrp_line(WS, i, body)
            i += 1                
        _logger.info('End export status on %s' % filename)        
        WB.close()

        xlsx_raw = open(filename, 'rb').read()
        b64 = xlsx_raw.encode('base64')
        if sendmail:        
            # ---------------------------------------------------------------------
            # Send via mail:
            # ---------------------------------------------------------------------
            _logger.info('Sending status via mail: %s' % filename)
            date = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # Send mail with attachment:
            group_pool = self.pool.get('res.groups')
            model_pool = self.pool.get('ir.model.data')
            thread_pool = self.pool.get('mail.thread')
            server_pool = self.pool.get('ir.mail_server')
            
            group_id = model_pool.get_object_reference(
                cr, uid, 'production_line', 'group_stock_negative_status')[1]    
            partner_email = []
            for user in group_pool.browse(
                    cr, uid, group_id, context=context).users:
                partner_email.append(user.partner_id.email) # .id
                
            #thread_pool = self.pool.get('mail.thread')
            #thread_pool.message_post(cr, uid, False, 
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
            for email in partner_email:
                _logger.warning('... sending mail: %s' % email)
                self.send_mail(
                    'openerp@micronaet.com', 
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
            # ---------------------------------------------------------------------
            # Open attachment form:
            # ---------------------------------------------------------------------
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
                'type': 'ir.actions.act_window',
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

    def schedule_send_negative_report(self, cr, uid, wizard=None, context=None):
        ''' Send mail to group user for negative elements
        '''                
        if context is None:
            context = {}
            
        context['datas'] = {
            'days': 30,
            'row_mode': 'negative',
            'with_medium': True,
            'month_window': 3,
            'with_order_detail': True,
            'fake_ids': [],
            }

        if wizard is not None:
            context['datas'].update(wizard)
            
        self.export_excel(cr, uid, False, context=context)    
        return True    
        
    def print_report(self, cr, uid, ids, context=None):
        ''' Redirect to bom report passing parameters
        ''' 
        datas = self.prepare_data(cr, uid, ids, context=context)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'webkitstatus',
            'datas': datas,
            }
        
    _columns = {
        'days':fields.integer('Days from today', required=True),
        # REMOVE:
        #'active':fields.boolean('Only record with data', required=False, 
        #    help="Show only product and material with movement"),
        #'negative': fields.boolean('Only negative', required=False, 
        #    help="Show only product and material with negative value in range"),
        # USE:
        'row_mode': fields.selection([
            ('all', 'All data'),
            ('active', 'With data'),
            ('negative', 'With negative'),
            ], 'Row mode', required=True),            
                
        'month_window':fields.integer('Statistic production window ', 
            required=True, help="Month back for medium production monthly index (Kg / month of prime material)"),
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
    ''' Parameter for product status per day
    '''    
    _inherit = 'product.status.wizard'
    
    _columns = {
        'fake_ids': fields.one2many(
            'product.status.production.fake.wizard', 'wizard_id', 
            'Production fake'),
        }
           
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
