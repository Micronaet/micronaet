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
        # ---------------------------------------------------------------------
        # Utility:
        # ---------------------------------------------------------------------
        def _get_load_date(load):
            ''' Problem: much load was done in the same day in initial phase
            '''
            date = load.date
            if date >= '2019-08-01':
                # Use correct load date:
                return date
            else:
                # Use production date:
                return load.line_id.production_id.date_planned
                
        def _get_period_date_dict(range_date):
            ''' Generate period dict:
            '''
            res = {}
            ref_date = range_date[0]
            col = 0

            while ref_date <= range_date[1]:
                res[ref_date] = col

                # Update ref_date:
                if ref_date[5:7] == '12':
                    ref_date = '%s-01' % (int(ref_date[:4]) + 1)
                else:    
                    ref_date = '%s-%02d' % (
                        ref_date[:4],
                        int(ref_date[5:7]) + 1,
                        )
                col += 1
            return res
        
        if context is None:
            context = {}
        save_mode = context.get('save_mode')
        
        
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')
        job_pool = self.pool.get('mrp.production.workcenter.line')
        
        # Collect data:
        now = ('%s' % datetime.now())[:7]
        total = {
            # Stock status:
            'product': {}, # Product stock status
            
            # MRP:
            'load': {}, # Product load
            'unload': {}, # Raw material unload

            'production': {}, # Total production for product
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
            12, 30, 20, 5,
            10, 10, 15,
            ]
        header = [
            'Codice', 'Descrizione', 'Lotto', 'UM',
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
            
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=f_header)

        page_total = {}
        for product in sorted(
                product_proxy, key=lambda x: (x.default_code, x.name)):
            for lot in product.pedimento_ids:
                qty = lot.product_qty
                if not qty:
                    continue

                uom = product.uom_id
                price = lot.standard_price
                subtotal = qty * price

                # -------------------------------------------------------------
                # Total block:
                # -------------------------------------------------------------
                if uom not in page_total:
                    page_total[uom] = [0.0, 0.0]
                page_total[uom][0] += qty
                page_total[uom][1] += subtotal
                
                # -------------------------------------------------------------
                # COLLECT DATA:
                # -------------------------------------------------------------
                # PAGE: Prodotti
                if product not in total['product']:
                    # Quantity, Subtotal, Check OK
                    total['product'][product] = [0.0, 0.0, True]
                total['product'][product][0] += qty
                total['product'][product][1] += subtotal

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
                        uom.name,
                        (qty, f_number_current),                    
                        (price, f_number_current),                    
                        (subtotal, f_number_current),                    
                        ], default_format=f_text_current)

        # ---------------------------------------------------------------------
        # Write total:
        # ---------------------------------------------------------------------
        master_total = 0.0
        for uom in sorted(page_total, key=lambda x: x.name):
            qty, subtotal = page_total[uom]
            master_total += subtotal
            # Write data:                    
            row += 1
            excel_pool.write_xls_line(                    
                ws_name, row, [
                    'Parziali',
                    uom.name,
                    qty,
                    '',
                    subtotal,
                    ], default_format=f_number_bg_blue_bold, col=2)
            
        # Write data:                    
        row += 1
        excel_pool.write_xls_line(                    
            ws_name, row, [
                'Totale:',
                master_total,
                ], default_format=f_number_bg_green_bold, col=5)

        # ---------------------------------------------------------------------
        # Product status:
        # ---------------------------------------------------------------------               
        ws_name = 'Prodotti'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            12, 30, 5,
            10, 15, 
            5,
            ]
        header = [
            'Codice', 'Prodotto', 'UM',
            'Q.', 'Subtotale', 
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
            qty, subtotal, ok = total['product'][product]
                
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
                    product.uom_id.name,
                    (qty, f_number_current),                    
                    (subtotal, f_number_current),                    
                    '' if ok else 'X',
                    ], default_format=f_text_current)

        # ---------------------------------------------------------------------
        # Write total:
        # ---------------------------------------------------------------------
        master_total = 0.0
        for uom in sorted(page_total, key=lambda x: x.name):
            qty, subtotal = page_total[uom]
            master_total += subtotal
            # Write data:                    
            row += 1
            excel_pool.write_xls_line(                    
                ws_name, row, [
                    'Parziali',
                    uom.name,
                    qty,
                    subtotal,
                    ], default_format=f_number_bg_blue_bold, col=1)
            
        # Write data:                    
        row += 1
        excel_pool.write_xls_line(                    
            ws_name, row, [
                'Totale:',
                master_total,
                ], default_format=f_number_bg_green_bold, col=3)

        # ---------------------------------------------------------------------
        #                   Collect data for Production:
        # ---------------------------------------------------------------------               
        # Data:        
        job_ids = job_pool.search(cr, uid, [
            ('production_id.mode', '=', 'production'),
            ('state', '=', 'done'),
            ], context=context)

        page_total = {}
        for job in job_pool.browse(cr, uid, job_ids, context=context):
            # -----------------------------------------------------------------
            # Load data:        
            # -----------------------------------------------------------------
            for load in job.load_ids:
                # (Mode, Product, Qty, Price, Recycle)
                production_price = (load.accounting_cost / load.product_qty)\
                    if load.product_qty else 0.0
                loop = [(
                    # Product:
                    'load',
                    job.product, 
                    load.product_qty - load.waste_qty, 
                    production_price, 
                    False), (

                    # Package:    
                    'unload',
                    load.package_id.linked_product_id, 
                    load.ul_qty, 
                    load.package_pedimento_id.standard_price or \
                        load.package_id.linked_product_id.standard_price, 
                    False), (

                    # Pallet:        
                    'unload',
                    load.pallet_product_id, 
                    load.pallet_qty, 
                    load.pallet_pedimento_id.standard_price or \
                        load.pallet_product_id.standard_price, 
                    False),
                    ]
                if load.waste_qty: #load.recycle:
                    loop.append((
                        # Recycle:    
                        'load',
                        load.waste_id, 
                        load.waste_qty, 
                        production_price, # Same as real production
                        True,
                        ))

                for mode, product, qty, price, recycle in loop:
                    if not product:
                        continue
                    if product not in total[mode]:
                        total[mode][product] = []     
                    total[mode][product].append((
                        _get_load_date(load)[:10], # Date operation (sort key!)
                        load.line_id, # Workcenter line
                        qty, 
                        price, 
                        recycle,
                        ))
                
            # -----------------------------------------------------------------
            # Unload data:        
            # -----------------------------------------------------------------
            for unload in job.bom_material_ids:
                product = unload.product_id
                date = job.production_id.date_planned # Directly MRP Date!
                
                if product not in total['unload']:
                    total['unload'][product] = []
                total['unload'][product].append((
                    date,
                    job, # Workcenter line
                    unload.quantity, 
                    unload.pedimento_price or unload.standard_price,
                    0.0, # Never present
                    ))

        # ---------------------------------------------------------------------
        # Production loaded product:
        # ---------------------------------------------------------------------               
        ws_name = 'Carichi produzione'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            10, 15, 15, 30, 10,
            10, 10, 
            15, 15,
            ]
        header = [
            'Data', 'Riferimento', 'Prodotto', 'Descrizione', 'Linea',
            'Q.', 'Q. errata', 
            'Prezzo carico', 'Subtotale',
            ]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        
        range_date = [False, False]
        for product in sorted(total['load'], 
                key=lambda x: (x.default_code, x.name)):

            # Readability:    
            for date, job, qty, price, recycle in sorted(
                    total['load'][product]):

                # Setup range data for load:
                period = date[:7]
                if not range_date[0] or period < range_date[0]:
                    range_date[0] = period
                if not range_date[1] or period > range_date[1]:
                    range_date[1] = period
                    
                subtotal = price * qty

                if recycle:
                    recycle_qty = qty
                    qty = 0.0
                    f_text_color = f_text_bg_blue
                    f_number_color = f_number_bg_blue
                else:    
                    recycle_qty = 0.0
                    f_text_color = f_text
                    f_number_color = f_number

                # Write data:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [
                        date,
                        job.name,
                        product.default_code or '',
                        product.name,
                        job.workcenter_id.name,
                        
                        (qty, f_number_color),
                        (recycle_qty, f_number_color),
                        
                        (price, f_number_color),
                        (subtotal, f_number_color),                    
                        ], default_format=f_text_color)

        load_col = _get_period_date_dict(range_date)

        # ---------------------------------------------------------------------
        # Production unloaded product:
        # ---------------------------------------------------------------------               
        ws_name = 'Scarichi produzione'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            10, 15, 15, 30, 10,
            10,
            15, 15,
            ]
        header = [
            'Data', 'Riferimento', 'Materia prima', 'Descrizione', 'Linea',
            'Q.',
            'Prezzo scarico', 'Subtotale',
            ]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        
        range_date = [False, False] # reset previous assigned
        for product in sorted(total['unload'], 
                key=lambda x: (x.default_code, x.name)):

            # Readability:    
            for date, job, qty, price, recycle in sorted(
                    total['unload'][product]):

                # Setup range data for load:
                period = date[:7]
                if not range_date[0] or period < range_date[0]:
                    range_date[0] = period
                if not range_date[1] or period > range_date[1]:
                    range_date[1] = period
                    
                subtotal = price * qty

                # Write data:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [
                        date,
                        job.name,
                        product.default_code or '',
                        product.name,
                        job.workcenter_id.name,
                        
                        (qty, f_number),
                        
                        (price, f_number),
                        (subtotal, f_number),
                        ], default_format=f_text)

        unload_col = _get_period_date_dict(range_date)

        # ---------------------------------------------------------------------               
        # Production in period:
        # ---------------------------------------------------------------------               
        ws_name = 'Produzioni periodo'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [10, 30, 4, 10]
        header = ['Prodotto', 'Descrizione', 'UM', 'Totale']

        fixed_col = len(header)
        col_total = []

        for col in sorted(load_col):
            width.append(8)
            header.append(col)
            col_total.append(0.0) # always KG
        empty = col_total[:]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        
        for product in sorted(total['load'], 
                key=lambda x: (x.default_code, x.name)):
            row_total = 0.0            
            data = empty[:]
            for date, job, qty, price, recycle in total['load'][product]:
                period = date[:7]
                col = load_col.get(period)

                # Totals:
                data[col] += qty
                row_total += qty
                col_total[col] += qty

            row += 1
            # Write fixed col data:
            excel_pool.write_xls_line(
                ws_name, row, [
                    product.default_code or '',
                    product.name,
                    product.uom_id.name,
                    (row_total, f_number_bg_green_bold),
                    ], default_format=f_text)

            # Write variable col data:
            excel_pool.write_xls_line(
                ws_name, row, data, default_format=f_number, col=fixed_col)

        # Write total:
        row += 1
        # Write fixed col data:
        excel_pool.write_xls_line(
            ws_name, row, ['Totale', ], default_format=f_header,
            col= fixed_col - 1)
        # Write variable col data:
        excel_pool.write_xls_line(
            ws_name, row, col_total, default_format=f_number_bg_green_bold, 
            col=fixed_col)
    

        # ---------------------------------------------------------------------
        # Production unloaded materials:
        # ---------------------------------------------------------------------               
        ws_name = 'Scarichi periodo'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            10, 15, 15, 30, 10,
            10, 10, 
            15, 15,
            ]
        header = [
            'Data', 'Riferimento', 'Prodotto', 'Descrizione', 'Linea',
            'Q.', 'Q. errata', 
            'Prezzo carico', 'Subtotale',
            ]
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

                
        return excel_pool.save_file_as(save_mode)            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
