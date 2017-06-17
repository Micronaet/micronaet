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

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
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
        return datas

    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    def export_excel(self, cr, uid, ids, context=None):
        ''' Export excel file
        '''
        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
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
            elif row_mode == 'negative' and not any(
                    [True for item in row if item < 0.0]):
                return False
            else:
                return True
            
        # Pool used:
        mrp_pool = self.pool.get('mrp.production')    
        data = self.prepare_data(cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # XLS file:
        # ---------------------------------------------------------------------
        filename = '~/etl/production_status.xlsx'
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
            'num_format': '0.00',
            })
        format_yellow = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ffff99', #'yellow',
            'border': 1,
            'num_format': '0.00',
            })
        format_red = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#ff9999', #'red',
            'border': 1,
            'num_format': '0.00',
            })
        format_green = WB.add_format({
            'font_name': 'Arial',
            'font_size': 9,
            'align': 'right',
            'bg_color': '#c1ef94', #'green',
            'border': 1,
            'num_format': '0.00',
            })

        # ---------------------------------------------------------------------
        # Format columns:
        # ---------------------------------------------------------------------
        # Column dimension:
        WS.set_column ('A:A', 40) # Image colums
        WS.set_row(0, 30)
        WS_product.set_column ('A:A', 40) # Image colums
        WS_product.set_row(0, 30)
            
        # Generate report for export:
        context['lang'] = 'it_IT'
        mrp_pool._start_up(cr, uid, data, context=context)
        start_product = False
        
        # Start loop for design table for product and material status:
        # Header: 
        header = [
            [_('Material'), format_title], # list for update after for product
            (_('m(x) last %s month') % data['month_window'], format_title),
            ]        
        for col in mrp_pool._get_cols():
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
                 _logger.error('No: %s' % (row, ))
                 continue
            else:     
                 _logger.info('Yes: %s' % (row, ))

            if not start_product and row[0][0] == 'P':
                WS = WS_product # change ref. for use second sheet
                start_product = True
                i = 1 # jump one line
                                    
            status_line = 0.0
            title = row[0].split(': ')[1]
            title_list = title.split('<b>')
            body = [
                (title_list[0] if len(title_list) == 2 else title, 
                    format_text),
                (title_list[1].replace('</b>', '') \
                    if len(title_list) == 2 else '', format_text),
                ]
            j = 0
            for col in mrp_pool._get_cols():
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
        }
        
    _defaults = {
        'days': lambda *a: 7,
        'month_window': lambda *x: 2,
        'with_medium': lambda *x: True,
        'row_mode': lambda *x: 'active',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
