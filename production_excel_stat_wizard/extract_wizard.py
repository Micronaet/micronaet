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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class MrpProductionExtractStatWizard(orm.TransientModel):
    ''' Wizard for extract data from sale, invoice
    '''
    _name = 'mrp.production.extract.stat.wizard'
    _description = 'Extract Excel export'

    # -------------------------------------------------------------------------
    # Report call:
    # -------------------------------------------------------------------------
    def get_report_material(self, cr, uid, wiz_proxy, context=None):
        ''' A. Report material 
        '''
        work_pool = self.pool.get('mrp.production.material')
        excel_pool = self.pool.get('excel.writer')
        
        # ---------------------------------------------------------------------
        # Parameters:
        # ---------------------------------------------------------------------
        from_date = wiz_proxy.from_date
        to_date = wiz_proxy.to_date
        product = wiz_proxy.product_id
        material = wiz_proxy.material_id
        report_mode = wiz_proxy.report_mode

        # ---------------------------------------------------------------------
        # Setup domain filter:
        # ---------------------------------------------------------------------
        domain = [
            ('workcenter_production_id', '!=', False),
            ]
        filter_text = _('Report mode: %s') % report_mode

        #Period:
        if from_date:
            domain.append(
                ('workcenter_production_id.real_date_planned', '>=', from_date)
                )
            filter_text += _(u'[Dalla data %s] ') % from_date    
        if to_date:
            domain.append(
                ('workcenter_production_id.real_date_planned', '<=', to_date))
            filter_text += _(u'[Alla data %s] ') % to_date    
            
        # Many2one:
        # Final Product
        #if product:
        #    domain.append(
        #        ('workcenter_production_id.product_id', '=', product.id))
        #    filter_text += u'[Prodotto finito %s] ' % product.default_code

        # Raw material:
        if material:
            domain.append(
                ('product_id', '=', material.id))
            filter_text += _(u'[Materia prima %s] ') % material.default_code

        # ---------------------------------------------------------------------        
        #                              EXCEL:
        # ---------------------------------------------------------------------        
        # Search and open line:
        work_ids = work_pool.search(cr, uid, domain, context=context)
        work_proxy = work_pool.browse(cr, uid, work_ids, context=context)

        # ---------------------------------------------------------------------        
        # A. Detail Page:
        # ---------------------------------------------------------------------        
        ws_name = _('Dettaglio')
        excel_pool.create_worksheet(ws_name)

        # Format list:
        excel_pool.set_format()
        f_title = excel_pool.get_format('title')
        f_header = excel_pool.get_format('header')
        f_text = excel_pool.get_format('text')
        f_number = excel_pool.get_format('number')
            
        excel_pool.column_width(ws_name, [
            15, 20, 20,
            20, 30, 10, 15,
            ])

        # Title:
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            filter_text,
            ], default_format=f_title)
            
        # Header:    
        row += 1        
        excel_pool.write_xls_line(ws_name, row, [
            _('Data'), _('Produzione'), _('Lavorazione'), 
            _('Codice'), _('Nome'), _('UM'), _('Q.')
            ], default_format=f_header)
            
        # Material line:
        wc_db = []
        product_report = {}
        material_report = {}

        for line in sorted(
                work_proxy, 
                key=lambda x: x.workcenter_production_id.real_date_planned):
            row += 1

            # Get data:
            wc = line.workcenter_production_id
            mrp = wc.production_id            
            product = mrp.product_id
            material = line.product_id
            qty = line.quantity

            # -----------------------------------------------------------------            
            # Final product data:
            # -----------------------------------------------------------------            
            if wc not in wc_db:
                wc_db.append(wc)
                for load in wc.load_ids:
                    key = (product, load.recycle)
                    if key in product_report:
                        product_report[key] += load.product_qty
                    else:    
                        product_report[key] = load.product_qty
                    # package_id, ul_qty
                    # package_pedimento_id
                    # palled_product_id, pallet_qty
                    # accounting_cost
                    # recycle_product
            
            # -----------------------------------------------------------------            
            # Raw material data:
            # -----------------------------------------------------------------            
            key = material
            if key in material_report:
                material_report[key] += qty
            else:    
                material_report[key] = qty

            # standard_price
            # pedimento_price
            # pedimento_id
            # lot_id
            # mrp_waste_id
            
            #subtotal = line.price_subtotal
            #net = (subtotal / qty) if qty else 0.0
            qty = material_report[material]
            excel_pool.write_xls_line(ws_name, row, [
                wc.real_date_planned,                
                mrp.name,
                wc.name,
                
                material.default_code or '', 
                material.name or '',
                material.uom_id.name,
                (qty, f_number),
                ], default_format=f_text)

        # ---------------------------------------------------------------------
        # B. Material total:
        # ---------------------------------------------------------------------
        ws_name = _('Materie prime')
        excel_pool.create_worksheet(ws_name)

        excel_pool.column_width(ws_name, [20, 30, 10, 15])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Codice'), _('Nome'), _('UM'), _('Q.')
            ], default_format=f_header)

        for material in material_report:
            row += 1
            qty = material_report[material]
            excel_pool.write_xls_line(ws_name, row, [
                material.default_code or '', 
                material.name or '',
                material.uom_id.name,
                (qty, f_number),
                ], default_format=f_text)

        # ---------------------------------------------------------------------
        # B. Material total:
        # ---------------------------------------------------------------------
        ws_name = _('Prodotto finito')
        excel_pool.create_worksheet(ws_name)

        excel_pool.column_width(ws_name, [20, 30, 10, 15, 1])

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
            _('Codice'), _('Nome'), _('UM'), _('Q.'), _('Recycle')
            ], default_format=f_header)

        for key in product_report:
            row += 1
            product, recycle = key
            qty = product_report[key]
            excel_pool.write_xls_line(ws_name, row, [
                product.default_code or '', 
                product.name or '',
                product.uom_id.name,
                (qty, f_number),
                'X' if recycle else '',
                ], default_format=f_text)

        return excel_pool.return_attachment(cr, uid, _('Production statistic'), 
            version='7.0', 
            #php=True,
            )

    # -------------------------------------------------------------------------
    # Wizard button event:
    # -------------------------------------------------------------------------
    def action_report(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        if wiz_proxy.report_mode == 'material':
            return self.get_report_material(
                cr, uid, wiz_proxy, context=context)
        #elif report_name == 'detail':
        #    key = lambda x: x.real_date_planned

    _columns = {
        # Period:
        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <='),
        
        # Foreign keys:
        'product_id': fields.many2one('product.product', 'Product'),
        'material_id': fields.many2one('product.product', 'Material'),

        'report_mode': fields.selection([
            ('material', 'Material'),
            #('production', 'Production'),
            #('detail', 'Detail'),
            ], 'Report mode', required=True),
        }
        
    _defaults = {
        'report_mode': lambda *x: 'material',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
