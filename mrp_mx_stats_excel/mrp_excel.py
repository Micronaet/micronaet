#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class MrpProduction(orm.Model):
    """ Model name: MrpProduction
    """
    
    _inherit = 'mrp.production'
    
    def extract_mrp_stats_excel_report(self, cr, uid, context=None):
        ''' Extract report statistic and save in Excel file:
        '''
        if context is None:
            context = {}
        save_mode = context.get('save_mode')
        
        
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')
        
        # Collect data:
        now = ('%s' % datetime.now())[:7]
        total = {
            'product': {},
            'production': {},
            'material': {},     
            } 
        #month_column = []
        _logger.info('%s. Start extract MRP statistic: %s' % 
            (now, save_mode))

        # ---------------------------------------------------------------------
        # Lot status:
        # ---------------------------------------------------------------------               
        ws_name = 'Lotti'
        excel_pool.create_worksheet(name=ws_name)

        # Format:
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')

        f_text = excel_pool.get_format('text')
        f_text_red = excel_pool.get_format('bg_red')
        f_text_bg_blue = excel_pool.get_format('bg_blue')
        
        f_number = excel_pool.get_format('number')
        f_number_red = excel_pool.get_format('bg_red_number')
        f_number_bg_blue = excel_pool.get_format('bg_blue_number')
        f_number_bg_blue_bold = excel_pool.get_format('bg_blue_number_bold')
        f_number_bg_red_bold = excel_pool.get_format('bg_red_number_bold')
        f_number_bg_green_bold = excel_pool.get_format('bg_green_number_bold')
        
        # Column:
        width = [
            12, 30, 15, 
            10, 10, 15,
            ]
        header = [
            'Codice', 'Descrizione', 'Lotto', 
            'Q.', 'Prezzo', 'Subtotale',
            ]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # Data:        
        product_ids = product_pool.search(cr, uid, [], context=context)
        product_proxy = product_pool.browse(
            cr, uid, product_ids, context=context)
            
        partial = 0.0 # Stock value
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=f_header)

        for product in sorted(
                product_proxy, key=lambda x: (x.default_code, x.name)):
            for lot in product.pedimento_ids:
                qty = lot.product_qty
                if not qty:
                    continue

                price = lot.standard_price
                subtotal = qty * price
                partial += subtotal
                
                # -------------------------------------------------------------
                # COLLECT DATA:
                # -------------------------------------------------------------
                # PAGE: Prodotti
                if product not in total['product']:
                    total['product'][product] = [0.0, 0.0, True]
                total['product'][product][0] += qty
                total['product'][product][1] += price

                # Color setup:
                if subtotal:
                    f_text_current = f_text
                    f_number_current = f_number
                else:
                    f_text_current = f_text_red
                    f_number_current = f_number_red
                    total['product'][product][2] = False # Not OK

                # Write data:                    
                row += 1
                excel_pool.write_xls_line(                    
                    ws_name, row, [
                        product.default_code or '',
                        product.name,
                        lot.code or '',
                        (qty, f_number_current),                    
                        (price, f_number_current),                    
                        (subtotal, f_number_current),                    
                        ], default_format=f_text_current)

        # ---------------------------------------------------------------------
        # Product status:
        # ---------------------------------------------------------------------               
        ws_name = 'Prodotti'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            12, 30, 
            10, 10, 15, 
            5,
            ]
        header = [
            'Codice', 'Prodotto', 
            'Q.', 'Prezzo', 'Subtotale', 
            'Errore',
            ]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # Data:        
        partial = 0.0 # Stock value
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=f_header)

        for product in sorted(total['product'], 
                key=lambda x: (x.default_code, x.name)):
            qty, price, ok = total['product'][product]
                
            # Color setup:
            if ok:
                f_text_current = f_text
                f_number_current = f_number
            else:
                f_text_current = f_text_red
                f_number_current = f_number_red

            # Write data:      
            row += 1              
            excel_pool.write_xls_line(                    
                ws_name, row, [
                    product.default_code or '',
                    product.name,
                    (qty, f_number_current),                    
                    (price, f_number_current),                    
                    (subtotal, f_number_current),                    
                    '' if ok else 'X',
                    ], default_format=f_text_current)

                
        # ---------------------------------------------------------------------
        # MRP status:
        # ---------------------------------------------------------------------               
        #month_column = sorted(month_column)
        #try:
        #    index_today = month_column.index(now)
        #except:
        #    index_today = False
            

        # ---------------------------------------------------------------------
        # Docnaet Product total:
        # ---------------------------------------------------------------------               
        """
        ws_name = 'Prodotti'
        
        excel_pool.create_worksheet(name=ws_name)
        
        width = [12, 30, 2, 10]
        cols = len(month_column)
        width.extend([9 for item in range(0, cols)])
        empty = ['' for item in range(0, cols)]
        if index_today != False:
            empty[index_today] = ('', f_number_bg_blue)

        header = ['Codice', 'Prodotto', 'UM', 'Totale']
        start = len(header)
        header.extend(month_column)
                
        # Column:
        row = 0
        excel_pool.column_width(ws_name, width)
        
        # Header:
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)        
            
        uom_total = {}
        for product in sorted(product_total, key=lambda x: x.default_code):
            uom_code = product.uom_id.account_ref or product.uom_id.name
            
            row += 1
            data = [
                product.default_code, 
                product.name, 
                uom_code,
                '',
                ]
            data.extend(empty)
            excel_pool.write_xls_line(
                ws_name, row, data, 
                default_format=f_text)
            total = 0.0

            for deadline in product_total[product]:
                if deadline == now:
                    f_number_color = f_number_bg_blue
                else:
                    f_number_color = f_number
                        
                subtotal = int(product_total[product][deadline])
                total += subtotal

                # -------------------------------------------------------------
                # Total setup:
                # -------------------------------------------------------------
                # TODO remove:
                #index = month_column.index(deadline)
                #if uom_code in total_row[index]:
                #    total_row[index][uom_code] += subtotal
                #else:    
                #    total_row[index][uom_code] = subtotal
                if uom_code not in uom_total:
                    uom_total[uom_code] = [0.0 for item in range(0, cols)]
                index = month_column.index(deadline)
                uom_total[uom_code][index] += subtotal
                
                excel_pool.write_xls_line(
                    ws_name, row, [
                        subtotal, 
                        ],
                        default_format=f_number_color, 
                        col=start + index)

            excel_pool.write_xls_line(
                ws_name, row, [
                    total, 
                    ], 
                    default_format=f_number_bg_green_bold, 
                    col=start-1)

        # Total Row:
        row += 1
        
        for uom_code in uom_total:
            excel_pool.write_xls_line(
                ws_name, row, [uom_code, 'Totale:'], 
                    default_format=f_text, 
                    col=start - 2)
                                    
            excel_pool.write_xls_line(
                ws_name, row, uom_total[uom_code], 
                    default_format=f_number_bg_green_bold, 
                    col=start)
            row += 1
        """ 
        return excel_pool.save_file_as(save_mode)            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
