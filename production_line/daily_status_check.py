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

excluded = (
    'SCONTO', 'VV',
    )    

class MrpProductionDailyReport(orm.Model):
    """ Model name: Mrp Production for daily report
    """
    
    _inherit = 'mrp.production'

        
    # -------------------------------------------------------------------------    
    # Utility:
    # -------------------------------------------------------------------------    
    def get_excel_format(self, excel_pool):
        """ Return dict for all excel format used
        """
        excel_pool.set_format()
        return {
            'title': excel_pool.get_format('title'),
            'header': excel_pool.get_format('header'),
            '': {
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
            'yellow': {
                'text': excel_pool.get_format('bg_yellow'),
                'number': excel_pool.get_format('bg_yellow_number'),
                },
            }

    def get_oc_detail_x_product(self, cr, uid, context=None):
        """ Check yesterday movement for correct negative stock
        """
        sql_pool = self.pool.get('micronaet.accounting')
        
        table_header = 'OC_TESTATE'
        table_line = 'OC_RIGHE'
        table_partner = 'PA_RUBR_PDC_CLFR'
        if not self.pool.get('res.company').table_capital_name(
                cr, uid, context=context):
            table_header = table_header.lower()
            table_line = table_line.lower()
            table_partner = table_partner.lower()
            
        # Query:    
        cursor = sql_pool.connect(cr, uid, year=False, context=context)
        query = """
            SELECT 
                l.CKY_ART as Article,
                CONCAT (
                    h.CSG_DOC, "/", 
                    h.NGB_SR_DOC, "/", 
                    h.NGL_DOC, ": ", r.CDS_CNT) as Ref, 
                l.DTT_SCAD as Deadline, 
                l.NQT_RIGA_O_PLOR as Qty,
                l.NCF_CONV as Conv
            FROM 
                %s h JOIN %s l 
                ON (
                    h.CSG_DOC = l.CSG_DOC AND 
                    h.NGB_SR_DOC = l.NGB_SR_DOC AND
                    h.NGL_DOC = l.NGL_DOC)
                JOIN %s r
                ON (h.CKY_CNT_CLFR = r.CKY_CNT);
            """ % (
               table_header, 
               table_line,
               table_partner,
               # TODO excluded
               )
        cursor.execute(query)

        res = {}
        res_comment = {}
        res_total = {}
        for line in cursor.fetchall():
            # Field used:
            default_code = line['Article']
            if default_code in excluded:
                _logger.warning('Excluded code: %s' % default_code)
                continue
                
            ref = line['Ref']
            qty = line['Qty']
            deadline = line['Deadline']
            conversion = line['Conv']
            if conversion:
                qty /= conversion
            if default_code not in res:
                res[default_code] = ''
                res_comment[default_code] = []
                res_total[default_code] = 0.0
            
            res[default_code] += ('[Q. %s > Rif. %s Scad. %s]' % (
                qty, ref, deadline)).replace(' 00:00:00', '')
            res_comment[default_code].append(('[%s] %10.0f: %s\n' % (
                deadline, # TODO
                qty,
                ref,
                )).replace(' 00:00:00', ''))
            res_total[default_code] += qty

        return res, res_comment, res_total
    
    def get_oc_status_yesterday(self, cr, uid, context=None):
        """ SQL get previous day order
        """
        sql_pool = self.pool.get('micronaet.accounting')
        company_pool = self.pool.get('res.company')
        
        # Find last worked date:
        days = 0
        while True:
            days -= 1
            check_date_dt = datetime.now() + relativedelta(days=days)
            if check_date_dt.weekday() in (5, 6):
                continue # No week end date
                
            check_date = check_date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
            break
                
        # ---------------------------------------------------------------------        
        # Stock negative:
        # ---------------------------------------------------------------------        
        cursor = sql_pool.connect(cr, uid, year=False, context=context)

        if company_pool.table_capital_name(cr, uid, 
                context=context):
            table = "AQ_QUANTITA" 
        else:
            table = "aq_quantita"
        
        store = 1
        year_ref = 9        
        query = """
            SELECT CKY_ART, NQT_INV + NQT_CAR - NQT_SCAR as qty
            FROM %s
            WHERE 
                NKY_DEP=%s and 
                NDT_ANNO=%s and 
                (NQT_INV + NQT_CAR - NQT_SCAR) < 0;
            """ % (table, store, year_ref)
        cursor.execute(query)

        stock_negative = {}
        for line in cursor.fetchall():
            # Field used:
            default_code = line['CKY_ART']
            qty = line['qty']
            stock_negative[default_code] = qty

        # ---------------------------------------------------------------------        
        # ACCOUNT MOVEMENT:        
        # ---------------------------------------------------------------------        
        _logger.info('Check account movement, data: %s [Excluded: %s]' % (
            check_date, excluded))
        
        if company_pool.table_capital_name(
                cr, uid, context=context):
            table_header = 'MM_TESTATE'
            table_line = 'MM_RIGHE'
        else:
            table_header = 'mm_testate'
            table_line = 'mm_righe'

        query = """
            SELECT 
                h.CSG_DOC, h.NGB_SR_DOC, h.NGL_DOC, h.DTT_DOC, h.CKY_CNT_CLFR, 
                l.CKY_ART, l.NPZ_UNIT, l.NQT_RIGA_ART_PLOR, l.NCF_CONV, 
                h.CDS_NOTE
            FROM %s h JOIN %s l ON (
                h.CSG_DOC = l.CSG_DOC AND 
                h.NGB_SR_DOC = l.NGB_SR_DOC AND
                h.NGL_DOC = l.NGL_DOC AND
                h.NPR_DOC = l.NPR_DOC
                )
            WHERE
                h.DTT_DOC >= '%s 00:00:00' AND 
                h.CSG_DOC in ('BC', 'SL', 'CL', 'BF', 'BD', 'RC', 'BS');
            """ % (
               table_header, 
               table_line,
               check_date,
               )  #  AND h.CDS_NOTE != 'OPENERP'
        cursor.execute(query)

        stock_movement = []
        for line in cursor.fetchall():
            # Field used:
            default_code = line['CKY_ART']
            if default_code in excluded:
                _logger.warning('Excluded code: %s' % default_code)
                continue
            document = line['CSG_DOC']
            try:
                date_document = line['DTT_DOC'].strftime(
                    DEFAULT_SERVER_DATE_FORMAT)
            except:
                date_document = ''    
            number = '%s: %s/%s' % (
                document, line['NGB_SR_DOC'], line['NGL_DOC'])
            qty = line['NQT_RIGA_ART_PLOR']
            conversion = line['NCF_CONV']
            if default_code[:1] in 'AB':
                product_type = 'Materie prime'
            elif default_code[:1] in 'M':
                product_type = 'Macchinari'
            else:   
                product_type = 'Prodotti finiti'

            if document in ('BC', 'SL', 'BD', 'RC', 'BS'):
                sign = -1
            else:  # CL
                sign = +1    
            
            if conversion:
                qty *= sign * 1.0 / conversion
            stock_movement.append((                
                document, 
                number,
                product_type,
                default_code,
                '%s: %s' % (product_type, default_code),
                qty,
                line['CDS_NOTE'], # Comment
                date_document
                ))
        return stock_movement, stock_negative
        

    def get_used_line(
            self, cr, uid, product_id, production_history, context=None):
        """ Load statistic on production and use for get line
        """ 
        if not production_history:
            wc_pool = self.pool.get('mrp.workcenter')
            wc_db = {}
            wc_ids = wc_pool.search(cr, uid, [], context=context)
            for wc in wc_pool.browse(cr, uid, wc_ids, context=context):
                wc_db[wc.id] = wc

            query = '''
                SELECT 
                    p.product_id, l.workcenter_id, sum(l.qty) 
                FROM 
                    mrp_production_workcenter_line l join 
                    mrp_production p 
                    ON (l.production_id = p.id) 
                WHERE 
                    l.state = 'done' 
                GROUP BY 
                    p.product_id, 
                    l.workcenter_id 
                ORDER BY 
                    p.product_id, sum(l.qty) DESC;
                '''
            cr.execute(query)
            _logger.warning('Uploading statistic for choose line')
            for record in cr.fetchall():
                product_id = record[0]
                wc_id = record[1]
                total = record[2]
                
                wc_line = wc_db.get(wc_id)
                if product_id not in production_history:
                    # Save reference line and comment for production stats
                    production_history[product_id] = [wc_line, '']
                
                # Update comment:    
                production_history[product_id][1] += '%s: q. %s\n' % (
                    wc_line.name,
                    total,
                    )
        return production_history.get(product_id, (False, False))
                
                    
        if product_id in production_history:
            return production_history[product_id]
        
        wc_pool = self.pool.get('mrp.production.workcenter.line')    
        wc_ids = wc_pool.search(cr, uid, [
            ('product', '=', product_id),
            ], context=context)
        return wc.id, wd.name   
    # -------------------------------------------------------------------------
    # Scheduled action:
    # -------------------------------------------------------------------------
    
    def extract_oc_status_x_line_excel_report(self, cr, uid, context=None):
        """ Get detail for ordered product in line
        """
        if context is None:
            context = {}
        save_mode = context.get('save_mode', False)

        order_pool = self.pool.get('sale.order')
        excel_pool = self.pool.get('excel.writer')
        workcenter_pool = self.pool.get('mrp.workcenter')
        
        exclude_product = ('VV', 'SCONTO', 'VV1', )
        exclude_start = 'ABCM'

        # ---------------------------------------------------------------------
        # Excel start:
        # ---------------------------------------------------------------------
        # Page Check:
        ws_name = 'Carico delle linee'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [
            10, 9, 12, 30, 15, 
            9, 7, 24, 
            17, 10, 10]
        
        # Format:
        excel_format = self.get_excel_format(excel_pool)
        
        # ---------------------------------------------------------------------         
        # Sale order data:
        # ---------------------------------------------------------------------
        header = [
            'Rif.', 'Data', 'Incoterms', 'Cliente', 'Nazione', 
            ]
        gap = len(header)  # Detail gap for write data
        header.extend([     
            'Scadenza', 'Prodotto', 'Descrizione', 
            'Linea', 'Q. ord.', 'Q. pronta',
            #'Linea Carico', 'Linea pronti',
            ])
        line_gap = len(header)  # Line gap for variable columns
        # TODO Line headers    

        # Extend with Line columns data:
        wc_db = {}  # Column start for write
        workcenter_ids = workcenter_pool.search(cr, uid, [], context=None)
        wc_lines = sorted(
            workcenter_pool.browse(cr, uid, workcenter_ids, context=context), 
            key=lambda x: x.name,
            )
            
        i = 0
        line_cols = 2
        total_line = []
        
        # Header for total block
        row = 0
        excel_pool.write_xls_line(                    
            ws_name, row, ['Totali', ''], 
            default_format=excel_format['header'],
            col=line_gap + i - 2)
        # TODO Unificare
        excel_pool.merge_cell(
            ws_name, 
            [row, line_gap + i - 2, row, line_gap + i - 1])
        
        # Write extra line data:
        product_data = []
        col = 0
        for workcenter in wc_lines:        
            line_name = workcenter.name
            wc_db[workcenter.id] = col # line_gap + i
            col += 1
            
            # Title:
            excel_pool.write_xls_line(                    
                ws_name, row, [line_name, ''], 
                default_format=excel_format['header'],
                col=line_gap + i)
            # TODO Unificare
            excel_pool.merge_cell(
                ws_name, 
                [row, line_gap + i, row, line_gap + i + 1])
            
            i += line_cols

            # Total:
            total_line.extend([0.0, 0.0])
            product_data.extend([0.0, 0.0])
            
            # Header:
            header.extend(['Da fare', 'Fatti'])
            width.extend([8, 8])
            
        row = 2
        excel_pool.column_width(ws_name, width)
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        excel_pool.freeze_panes(ws_name, 3, 7)
        
        order_ids = order_pool.search(cr, uid, [
            ('state', 'in', ('draft', 'sent',)),
            ], context=context)
        
        excluded_product = []    
        production_history = {}  # Rememer for speed
        comment_parameters = {
            'width': 400, 
            'font_name': 'Courier New',
            }
        
        for order in order_pool.browse(cr, uid, order_ids, context=context):
            partner = order.partner_id
            order_header = [
                order.name,
                order.date_order,
                '', # Incoterms
                partner.name,
                partner.country_id.name,                
                ]
                
            for line in order.order_line:
                product = line.product_id
                default_code = product.default_code
                if default_code in exclude_product or \
                        default_code[:1] in exclude_start:
                    _logger.warning('Code not used %s' % default_code)
                    if product not in excluded_product:
                        excluded_product.append(product)
                    continue

                wc_line, wc_comment = self.get_used_line(
                    cr, uid, product.id, production_history, context=context)

                # Header:
                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, order_header, 
                    default_format=excel_format['']['text'])

                # Detail:
                done_qty = 0.0 # TODO 
                line_detail = [
                    line.date_deadline,
                    product.default_code,
                    product.name,
                    wc_line.name if wc_line else 'Non trovata',
                    (line.product_uom_qty, excel_format['']['number']),
                    (done_qty, excel_format['']['number']),
                    ]
                    
                # Add wc comment:
                excel_pool.write_comment(
                    ws_name, row, gap + 3, 
                    wc_comment, parameters=comment_parameters)                    

                excel_pool.write_xls_line(
                    ws_name, row, line_detail, 
                    default_format=excel_format['']['text'], col=gap)
                
                current_data = product_data[:]
                if not wc_line or wc_line.id not in wc_db:
                    #TODO manage 
                    continue
                    
                col = line_cols * wc_db[product.id] # TODO set default position
                current_data[col] = qty
                # TODO produced qty!

                excel_pool.write_xls_line(
                    ws_name, row, current_data, 
                    default_format=excel_format['']['number'], col=line_gap)

        # Write total
        row = 1
        excel_pool.write_xls_line(                    
            ws_name, row, total_line, 
            default_format=excel_format['']['number'],
            col=line_gap,
            )
            
        if save_mode:
            return excel_pool.save_file_as(save_mode)         
        else:
            return excel_pool.return_attachment(
                cr, uid, 'Carico linee su ordinato', 
                name_of_file=False, version='7.0', php=True,
                context=context)


    def extract_daily_mrp_stats_excel_report(self, cr, uid, context=None):
        ''' Jobs: unload and load material last production day
        '''
        if context is None:
            context = {}
        save_mode = context.get('save_mode', False)

        # Pool used:
        unload_pool = self.pool.get('mrp.production.workcenter.line') # Job/SL
        load_pool = self.pool.get('mrp.production.workcenter.load') # CL
        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')
        
        today = datetime.now()
        last = False
        for day in range(1, 7):
            last = today - timedelta(days=day)
            if last.isoweekday() in range(1, 5): # Working day 1-5
                break
                
        if not last:
            _logger.error('Cannot find last day!')
            return False

        last_date = ('%s' % last)[:10]
        from_last = '%s 00:00:00' % last_date
        to_last = '%s 23:59:00' % last_date
        
        _logger.info('Reporting moved product in day: [%s - %s]' % (
            from_last, to_last))

        # ---------------------------------------------------------------------
        # Excel start:
        # ---------------------------------------------------------------------
        # Page Check:
        ws_name = 'Controlli da fare'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [13, 35, 18, 18, 80]
        excel_pool.column_width(ws_name, width)
        
        # Page Detail:
        ws_name = u'Dettaglio movimentazioni'
        excel_pool.create_worksheet(name=ws_name)

        # Format:
        excel_format = self.get_excel_format(excel_pool)
        
        # Column:
        width = [13, 45, 18, 38, 15]
        excel_pool.column_width(ws_name, width)

        product_moved = {
            'Materie prime': [],
            'Prodotti finiti': [],
            'Macchinari': [],
            }

        # ---------------------------------------------------------------------         
        # Account movement (over last date):
        # ---------------------------------------------------------------------
        header = [u'Doc. contabile', u'Descrizione', u'Q.', u'Commento', 
            u'Date']
        row = 0
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        document_move = {}
        stock_movement, stock_negative = self.get_oc_status_yesterday(
            cr, uid, context=context)
        
        for record in stock_movement:
            (document, number, product_type, default_code, description, 
                qty, comment, date_document) = record
                
            #if qty >= 0:
            color_format = excel_format['']
            #else:    
            #    color_format = excel_format['red']
            
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code),
                ], context=context)
            if product_ids:
                product = product_pool.browse(
                    cr, uid, product_ids, context=context)[0]
                product_name = product.name
            else:
                product_name = '/'    
                
            # Excel log:
            row += 1             
            excel_pool.write_xls_line(ws_name, row, [
                number,
                '%s (%s)' % (
                    description, 
                    product_name,
                    ),
                (qty, color_format['number']),
                comment,
                date_document,
                ], default_format=color_format['text'])
                             
            product_pool = self.pool.get('product.product')
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code),
                ], context=context)
            if not product_ids:
                print 'Code not found, create minimal: %s' % default_code
                product_id = product_pool.create(cr, uid, {
                    'default_code': default_code,
                    'name': default_code,
                    }, context=context)
                product_ids = [product_id]    
            
            product = product_pool.browse(
                cr, uid, product_ids, context=context)[0]
            
            if product not in product_moved[product_type]:
                product_moved[product_type].append(product)
                document_move[product] = ''
            document_move[product] += '%s q. %s [%s]\n' % (
                number,
                qty,
                date_document,
                )

        # ---------------------------------------------------------------------         
        # Unload documents (over last date):
        # ---------------------------------------------------------------------         
        header = [u'# SL', u'Descrizione', u'Linea', u'Lavorazione']

        row += 2
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        unload_ids = unload_pool.search(cr, uid, [      
            ('state', 'not in', ('cancel', )),  
            ('real_date_planned', '<=', to_last),
            ('real_date_planned_end', '>=', from_last),
            ], context=context)

        unload_document = unload_pool.browse(
                cr, uid, unload_ids, context=context)
        for unload in unload_document:
            if unload.accounting_sl_code:
                color_format = excel_format['']
            else:    
                color_format = excel_format['red']
                
            # Excel log:
            row += 1             
            excel_pool.write_xls_line(ws_name, row, [
                unload.accounting_sl_code,
                'Prodotto: %s' % unload.product.default_code,
                unload.workcenter_id.name,
                unload.name,
                ], default_format=color_format['text'])

            # Product collect: # 17 apr 2020 remove from material list
            #for material in unload.bom_material_ids:
            #    product = material.product_id
            #    if product not in product_moved['Materie prime']:
            #        product_moved['Materie prime'].append(product)
        
        # ---------------------------------------------------------------------         
        # Load documents (in last date):
        # ---------------------------------------------------------------------         
        header = [u'# CL', u'Descrizione', 'Q.', 'Stato']

        row += 2
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        load_ids = load_pool.search(cr, uid, [        
            ('date', '>=', from_last),
            ('date', '<=', to_last),
            ], context=context)

        for load in load_pool.browse(cr, uid, load_ids, context=context):
            if load.accounting_cl_code:
                color_format = excel_format['']
            else:    
                color_format = excel_format['red']

            # Excel log:
            row += 1 
            product = load.product_id
                        
            excel_pool.write_xls_line(ws_name, row, [
                load.accounting_cl_code or '',
                u'Prodotto: %s %s' % (
                    product.default_code or '',
                    '[REC.]' if load.recycle else '',
                    ),
                (load.product_qty, color_format['number']),
                'Imballo: %s x %s,  Pallet: %s x %s' % (
                    '0' if not load.ul_qty else load.ul_qty,
                    '/' if not load.package_id else load.package_id.code,
                    '0' if not load.pallet_qty else load.pallet_qty,
                    '/' if not load.pallet_product_id else \
                        load.pallet_product_id.code,            
                    )
                ], default_format=color_format['text'])

            # Product collect: # 17 apr 2020 remove from product list
            # product_qty
            #if product not in product_moved['Prodotti finiti']:
            #    product_moved['Prodotti finiti'].append(product)

        # ---------------------------------------------------------------------         
        # Product / Material status:        
        # ---------------------------------------------------------------------         
        # Collect comment
        comment_line, comment_detail, comment_total = \
            self.get_oc_detail_x_product(cr, uid, context=context)
        comment_parameters = {
            'width': 500, 
            'font_name': 'Courier New',
            }
    
        # XXX Return to check page:
        ws_name = 'Controlli da fare'
        row = -2
        for mode in product_moved:
            row += 2
            header = [mode, u'Nome', 'Tot. OC', u'Magaz.', 'Commento']
            excel_pool.write_xls_line(                    
                ws_name, row, header, default_format=excel_format['header'])
        
            for product in sorted(
                    product_moved[mode], key=lambda x: x.default_code):
                default_code = product.default_code or ''
                if default_code.startswith('VV'): 
                    continue # Not use water!
                if product.accounting_qty < 0.0:
                    color_format = excel_format['red']
                else:    
                    color_format = excel_format['']

                row += 1           
                comment = comment_line.get(default_code) or ''
                oc_total = comment_total.get(default_code) or ''
                excel_pool.write_xls_line(ws_name, row, [
                    default_code,
                    product.name,
                    (oc_total, color_format['number']),
                    (product.accounting_qty, color_format['number']),
                    comment,
                    ], default_format=color_format['text'])
                
                movements = document_move.get(product, '')
                excel_pool.write_comment(
                    ws_name, row, 0, 
                    movements, 
                    comment_parameters)
                
                if comment:
                    tooltip = ''.join(
                        sorted(
                            comment_detail.get(default_code, [])
                            ))
                    excel_pool.write_comment(
                        ws_name, row, 3, 
                        tooltip, 
                        comment_parameters)

        # ---------------------------------------------------------------------         
        # Negative product 
        # ---------------------------------------------------------------------
        ws_name = 'Negativi'
        excel_pool.create_worksheet(name=ws_name)

        # Column:
        width = [20, 35, 15]
        excel_pool.column_width(ws_name, width)
        
        header = [u'Codice', u'Nome', u'Quantità']
        row = 0
        excel_pool.write_xls_line(                    
            ws_name, row, [
                'Solo materie prime e prodotti negativi (tolti '\
                'codici che iniziano per Z, M, L e C'
                ], default_format=excel_format['title'])
        row += 2
        excel_pool.write_xls_line(                    
            ws_name, row, header, default_format=excel_format['header'])

        for default_code in sorted(stock_negative):
            if default_code in excluded:
                continue
            if default_code[:1] in 'ZzMmLlCc':
                continue
            row += 1 

            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code),
                ], context=context)
            if product_ids:
                product = product_pool.browse(
                    cr, uid, product_ids, context=context)[0]
                product_name = product.name
            else:
                product_name = '/'    

            excel_pool.write_xls_line(ws_name, row, [
                default_code,
                product_name,
                (stock_negative[default_code], excel_format['']['number']),
                ], default_format=color_format['text'])

        if save_mode:
            return excel_pool.save_file_as(save_mode)         
        else:
            return excel_pool.return_attachment(cr, uid, 'Movimenti di ieri', 
                name_of_file=False, version='7.0', php=True,
                context=context)
                                   
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
