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
            
            'load': {},
            'unload': {},     
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
            for load in jo.load_ids:
                # (Product, Qty, Price, Recycle)
                loop = [
                    # Product:
                    (job.product, 
                        load.product_qty - load.waste_qty, 
                        load.accounting_cost, False),
                    # Package:    
                    (load.package_id, 
                        load.ul_quantity, 
                        load.package_pedimento_id.standard_price or \
                            load.package_id.standard_price, False),
                    # Pallet:        
                    (load.pallet_product_id, 
                        load.pallet_qty, 
                        load.pallet_pedimento_id.standard_price or \
                            load.pallet_product_id.standard_price, False),
                        ]

                if load.recycle:
                    loop.append((
                        # Recycle:    
                        load.recycle_product_id, 
                        load.waste_qty, 
                        load.accounting_cost, # Same as good product
                        True,
                        ) 

                for product, qty, price, recycle in loop:
                    if not product:
                        continue
                    if product not in total['load']:
                        total['load'][product] = []     
                    total['load'][product].append([load, qty, price, recycle])
                
            # -----------------------------------------------------------------
            # Unload data:        
            # -----------------------------------------------------------------
            for load in job.bom_material_ids:
                pass
                



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
        
        for product in sorted(total['load'], 
                key=lambda x: (x.default_code, x.name)):
                
            # Readability:    
            load, qty, price, recycle = total['load'][product]
            date = load.date # TODO job.real_date_planned (for bad load)
            job = load.line_id
            recycle_qty = 0.0
            subtotal = price * qty

            if recycle:
                recycle_qty = qty
                qty = 0.0

            # Write data:
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, [
                    date,
                    job.name,
                    product.default_code or '',
                    product.name,
                    job.workcenter_id.name,
                    
                    qty,
                    recycle_qty,
                    
                    price,
                    subtotal,                    
                    ], default_format=f_text)


        # ---------------------------------------------------------------------
        # Production unloaded materials:
        # ---------------------------------------------------------------------               
        ws_name = 'Scarichi produzione'
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
