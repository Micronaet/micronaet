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
    """ Model name: SaleOrder
    """
    
    _inherit = 'mrp.production'
    
    def extract_mrp_stats_excel_report(self, cr, uid, context=None):
        ''' Extract report statistic and save in Excel file:
        '''
        if context is None:
            context = {}
        
        _logger.info('Start extract MRP statistic')
        
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

        # ---------------------------------------------------------------------
        # Stock status:
        # ---------------------------------------------------------------------               
        ws_name = 'Lotti'
        excel_pool.create_worksheet(name=ws_name)

        # Format:
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')

        f_text = excel_pool.get_format('text')
        f_text_red = excel_pool.get_format('text_red')
        f_text_bg_blue = excel_pool.get_format('bg_blue')
        
        f_number = excel_pool.get_format('number')
        f_number_red = excel_pool.get_format('number_red')
        f_number_bg_blue = excel_pool.get_format('bg_blue_number')
        f_number_bg_blue_bold = excel_pool.get_format('bg_blue_number_bold')
        f_number_bg_red_bold = excel_pool.get_format('bg_red_number_bold')
        f_number_bg_green_bold = excel_pool.get_format('bg_green_number_bold')
        
        # Column:
        width = [30, 15, 10, 10, 15]
        header = ['Prodotto', 'Codice', 'Q.', 'Prezzo', 'Subtotale']
        
        # Header:
        row = 0
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # Data:        
        product_ids = product_pool.search(cr, uid, [], context=context)
        product_proxy = sale_pool.browse(
            cr, uid, product_ids, context=context)
            
        partial = 0.0 # Stock value
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=f_header)

        for product in sorted(
                product_proxy, key=lambda x: x.default_code, x.name):
            for lot in product.pedimento_ids:
                row += 1
                qty = lot.qty
                price = lot.price
                subtotal = qty * price
                partial += subtotal
                
                # Color setup:
                if not subtotal:
                    f_text_current = f_text_red
                    f_number_current = f_number_red
                else:
                    f_text_current = f_text
                    f_number_current = f_number

                # Write data:                    
                excel_pool.write_xls_line(                    
                    ws_name, row, [
                        product.name,
                        product.default_code or '',
                        (qty, f_number_current),                    
                        (price, f_number_current),                    
                        (subtotal, f_number_current),                    
                        ], default_format=f_text_current)

                # -------------------------------------------------------------
                # COLLECT DATA:
                # -------------------------------------------------------------
                # PAGE: Prodotti
                if product not in total['product']:
                    total['product'] = [0.0, 0.0]
                total['product'][0] += qty
                total['product'][1] += price
                


        month_column = sorted(month_column)
        try:
            index_today = month_column.index(now)
        except:
            index_today = False
            
        # Total page order: 
        for currency in sorted(total, key=lambda x: x.symbol):
            excel_pool.write_xls_line(
                ws_name, row, [
                    'Totale',
                    currency.symbol, # Order
                    (total[currency][0], f_number_bg_blue_bold),    
                    currency.symbol, # Payment
                    (total[currency][1], f_number_bg_blue_bold),    
                    (total[currency][2], f_number_bg_red_bold),    
                    ], default_format=f_text_bg_blue, col=4)
            row += 1        
            
        # ---------------------------------------------------------------------
        # Docnaet Quotation (pending and lost):
        # ---------------------------------------------------------------------   
        # Setup:
        ws_setup = [
            ('Offerte', [
                ('sale_state', '=', 'pending'),
                ('sale_order_amount', '>', 0.0),
                ]),
            ('Perse', [
                ('sale_state', '=', 'lost'),
                ('sale_order_amount', '>', 0.0),
                ]),
            ]

        width = [
            38, 18, 10, 10, 50,
            3, 12,
            3, 12, 12, 12, 40
            ]
        header = [
            'Partner', 'Commerciale', 'Data', 'Scadenza', 'Oggetto', 
            'Val.', 'Totale', 
            'Val.', 'Pag. aperti', 'Di cui scaduti', 'FIDO', 'Note',
            ]
            
        for ws_name, document_filter in ws_setup:
            docnaet_ids = docnaet_document.search(
                cr, uid, document_filter, context=context)
            if not docnaet_ids:    
                continue # Not written

            excel_pool.create_worksheet(name=ws_name)
            row = 0
                    
            # Column:
            excel_pool.column_width(ws_name, width)
            
            # Header:
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=f_header)
            row += 1   

            document_proxy = docnaet_document.browse(
                cr, uid, docnaet_ids, context=context)

            total = {}
            for document in sorted(
                    document_proxy, 
                    key=lambda x: x.date,
                    reverse=True):
                partner = document.partner_id
                currency = document.sale_currency_id
                currency_payment = partner.duelist_currency_id or currency

                if partner not in partner_total:
                    partner_total[partner] = {}
                if currency not in partner_total[partner]:
                    partner_total[partner][currency] = [
                        0.0, # Order
                        0.0, # Quotation
                        0.0, # Lost
                        ]    
                if ws_name == 'Offerte':        
                    partner_total[partner][currency][1] += order.amount_untaxed
                else:    
                    partner_total[partner][currency][2] += order.amount_untaxed
                
                # -------------------------------------------------------------
                # Update total in currency mode:
                # -------------------------------------------------------------
                if currency not in total:
                    # order, exposition, deadlined
                    total[currency] = [0.0, 0.0, 0.0]

                if currency_payment not in total:
                    # order, exposition, deadlined
                    total[currency_payment] = [0.0, 0.0, 0.0]
                    
                total[currency][0] += document.sale_order_amount
                total[currency_payment][1] += partner.duelist_exposition_amount
                total[currency_payment][2] += partner.duelist_uncovered_amount

                # Setup color:
                if partner.duelist_uncovered or partner.duelist_over_fido:
                    f_text_current = f_text_red
                    f_number_current = f_number_red
                else:
                    f_text_current = f_text
                    f_number_current = f_number
                    
                excel_pool.write_xls_line(
                    ws_name, row, [
                        partner.name,
                        document.user_id.name,
                        document.date,
                        document.deadline,
                        '%s %s' % (
                            document.name or '',
                            document.description or '',
                            ),
                        currency.symbol,
                        (document.sale_order_amount, f_number_current),
                        
                        currency_payment.symbol,
                        (partner.duelist_exposition_amount or '', 
                            f_number_current),             
                        (partner.duelist_uncovered_amount or '', 
                            f_number_current),
                        (partner.duelist_fido or '', f_number_current),             
                        get_partner_note(partner),
                        ], default_format=f_text_current)
                row += 1

            # -----------------------------------------------------------------
            # Total page order:
            # -----------------------------------------------------------------
            for currency in sorted(total, key=lambda x: x.symbol):
                excel_pool.write_xls_line(
                    ws_name, row, [
                        'Totale',
                        currency.symbol,
                        (total[currency][0], f_number_bg_blue_bold),    
                        currency.symbol,
                        (total[currency][1], f_number_bg_blue_bold),    
                        (total[currency][2], f_number_bg_red_bold),
                        ], default_format=f_text_bg_blue, col=4)
                row += 1        

        # ---------------------------------------------------------------------
        # Docnaet Customer total:
        # ---------------------------------------------------------------------               
        ws_name = 'Clienti'
        excel_pool.create_worksheet(name=ws_name)
        width = [
            40, 
            3, 12, 12, 12, 
            3, 12, 12, 
            12, 40,
            ]
        header = [
            'Partner', 
            'Val.', 'Ordini', 'Offerte', 'Off. perse', 
            'Val.', 'Pag. aperti', 'Di cui scaduti', 
            'FIDO', 'Note',
            ]
        row = 0
                
        # Column:
        excel_pool.column_width(ws_name, width)
        
        # Header:
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        row += 1   
        
        total = {}
        for partner in sorted(partner_total, key=lambda x: x.name):
            currency_payment = partner.duelist_currency_id or currency

            first = True
            for currency in partner_total[partner]:
                order, quotation, lost = partner_total[partner][currency]
                # -------------------------------------------------------------
                # Update total in currency mode:
                # -------------------------------------------------------------                
                if currency not in total:
                    # order, exposition, deadlined
                    total[currency] = [
                        0.0, 0.0, 0.0, 
                        0.0, 0.0, 0.0,
                        ]

                if currency_payment not in total:
                    # order, exposition, deadlined
                    total[currency_payment] = [
                        0.0, 0.0, 0.0, 
                        0.0, 0.0, 0.0,
                        ]

                total[currency][0] += order
                total[currency][1] += quotation # TODO problem if different currency
                total[currency][2] += lost # TODO problem if different currency
                
                # Payment:
                total[currency_payment][3] += partner.duelist_exposition_amount
                total[currency_payment][4] += partner.duelist_uncovered_amount

                # -----------------------------------------------------------------
                # Setup color:
                # -----------------------------------------------------------------
                if partner.duelist_uncovered or partner.duelist_over_fido:
                    f_text_current = f_text_red
                    f_number_current = f_number_red
                else:
                    f_text_current = f_text
                    f_number_current = f_number
                if first:
                    first = False
                    excel_pool.write_xls_line(
                        ws_name, row, [
                            partner.name,
                            
                            currency.symbol,
                            (order or '', f_number),                    
                            (quotation or '', f_number),       
                            (lost or '', f_number_red),                    

                            currency_payment.symbol,
                            (partner.duelist_exposition_amount or '', 
                                f_number_current),             
                            (partner.duelist_uncovered_amount or '', 
                                f_number_current),
                            (partner.duelist_fido or '', f_number_current),             
                            get_partner_note(partner),
                            ], default_format=f_text_current)
                else:            
                    excel_pool.write_xls_line(
                        ws_name, row, [
                            #partner.name,
                            
                            currency.symbol,
                            (order or '', f_number),                    
                            (quotation or '', f_number),       
                            (lost or '', f_number_red),                    

                            #currency_payment.symbol,
                            #(partner.duelist_exposition_amount or '', 
                            #    f_number_current),             
                            #(partner.duelist_uncovered_amount or '', 
                            #    f_number_current),
                            #(partner.duelist_fido or '', f_number_current),             
                            #get_partner_note(partner),
                            ], default_format=f_text_current, col=1)
                row += 1

        # ---------------------------------------------------------------------
        # Total page order:
        # ---------------------------------------------------------------------
        for currency in sorted(total, key=lambda x: x.symbol):
            excel_pool.write_xls_line(
                ws_name, row, [
                    'Totale',
                    currency.symbol,
                    (total[currency][0], f_number_bg_blue_bold),    
                    (total[currency][1], f_number_bg_blue_bold),    
                    (total[currency][2], f_number_bg_red_bold),    
                    currency.symbol,
                    (total[currency][3], f_number_bg_blue_bold),    
                    (total[currency][4], f_number_bg_red_bold),
                    ], default_format=f_text_bg_blue)
            row += 1        

        # ---------------------------------------------------------------------
        # Docnaet Product total:
        # ---------------------------------------------------------------------               
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
            
        #excel_pool.row_height(ws_name, [row, ], height=50)
        #text_total_row = []
        #for record in total_row:
        #    res = ''
        #    for uom_code in record:
        #        res += '%s.00 %s\n' % (
        #        record[uom_code],
        #        uom_code,
        #        )
        #    text_total_row.append(res)
    
        #excel_pool.write_xls_line(
        #    ws_name, row, text_total_row, 
        #        default_format=f_number_bg_green_bold, 
        #        col=start)
            
        if save_mode: # Save as a file:
            _logger.info('Save mode: %s' % save_mode)
            return excel_pool.save_file_as(save_mode)            
        else: # Send mail:
            _logger.info('Send mail mode!')
            return excel_pool.send_mail_to_group(cr, uid, 
                'docnaet_sale_excel.group_sale_statistic_mail', 
                'Statistiche vendite', 
                'Statistiche giornaliere vendite', 
                'sale_statistic.xlsx',
                context=context)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
