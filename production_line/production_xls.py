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
import sys
import openerp.netsvc as netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp import tools
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from utility import *

_logger = logging.getLogger(__name__)

supplier_orders = {}
    
class mrp_production_extra(osv.osv):
    ''' Create extra fields in mrp.production obj
    '''
    _name = 'mrp.production'
    _inherit = ['mrp.production', 'mail.thread']

    # -------------------------------------------------------------------------
    # Utility for procedure:
    # -------------------------------------------------------------------------
    def add_element_material_composition(
            self, product, quantity, table, rows, with_medium, material_mx,
            month_window, start_date, range_date, real_date_planned, 
            col_ids, supplier_orders,
            ):
        ''' Block used for unload materials and for simulation
        '''            
        default_code = product.default_code
        
        if product.not_in_status: # Jump 'not in status' material
            return

        if with_medium and product:
            # Kg.
            try:
                media = material_mx.get(product.id, 0.0) / month_window
            except:
                media = 0.0    
        else:
            media = 0.0

        element = (
            'M',
            product.id,
            product, # XXX for minimum
            media,
            )
        if element not in rows:
            rows.append(element)
            # prepare data structure:
            table[element[1]] = [0.0 for item in range(0,range_date)] 
            # prepare data structure:
            table[element[1]][0] = product.accounting_qty or 0.0 

        if real_date_planned in col_ids:
            table[element[1]][col_ids[real_date_planned]] -= \
                quantity or 0.0 
        else:    # < today
            table[element[1]][1] -= quantity or 0.0 

        # -------------------------------------------------------------
        # OF order:
        # -------------------------------------------------------------
        if default_code in supplier_orders: # all OF orders
            for of_deadline in supplier_orders[default_code].keys():
                # deadline is present in the window of cols
                if of_deadline in col_ids:                            
                    table[element[1]][col_ids[of_deadline]] += \
                        supplier_orders[default_code][of_deadline] or\
                            0.0
                    # delete OF value (no other additions):        
                    del(supplier_orders[default_code][of_deadline]) 
                    
                elif of_deadline < start_date.strftime('%Y-%m-%d'):
                    # deadline < today:   
                    table[element[1]][1] += supplier_orders[
                        default_code][of_deadline] or 0.0
                    # delete OF value (no other additions):
                    del(supplier_orders[default_code][of_deadline]) 
        return

    # -------------------------------------------------------------------------
    # Utility for report:
    # -------------------------------------------------------------------------
    def _start_up(self, cr, uid, data=None, context=None):
        ''' Master function for prepare report
        '''        
        if data is None:
            data = {}

        # Pool used:
        accounting_pool = self.pool.get('micronaet.accounting')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')
        order_line_pool = self.pool.get('sale.order.line')
        
        # Global parameters:    
        global rows, cols, table, supplier_orders, minimum, error_in_print
        
        # initialize globals:
        rows = []
        cols = []
        #supplier_orders = {}
        minimum = {}
        table = {}
        error_in_print = '' # TODO manage for set in printer
        
        # TODO optimize:
        product_ids = product_pool.search(cr, uid, [], context=context)
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            minimum[product.id] = product.minimum_qty or 0.0

        # Init parameters:      
        col_ids = {}  
        range_date = data.get('days', 7) + 1
        start_date = datetime.now()
        end_date = datetime.now() + timedelta(days = range_date - 1)
        # with_order_detail = data.get('with_order_detail', False) # no used

        # 0 (<today), 1..n [today, today + total days], delta)
        for i in range(0, range_date): 
            if i == 0: # today
                d = start_date
                cols.append(d.strftime('%d/%m'))
                col_ids[d.strftime('%Y-%m-%d')] = 0
            elif i == 1: # before today
                d = start_date
                cols.append(d.strftime('< %d/%m')) 
                col_ids['before'] = 1 # not used!                    
            else: # other days
                d = start_date + timedelta(days = i - 1)
                cols.append(d.strftime('%d/%m'))
                col_ids[d.strftime('%Y-%m-%d')] = i

        # ---------------------------------------------------------------------
        #                     SYNCRONIZATION PRE REPORT
        # ---------------------------------------------------------------------
        # --------------------------------------
        # 1. Import status material and product:
        # --------------------------------------
                
        # ------------------------------
        # 2. Get OF lines with deadline:
        # ------------------------------
        # TODO Filter period?? (optimizing the query!)
        cursor_of = accounting_pool.get_of_line_quantity_deadline(cr, uid)
        if not cursor_of: 
            _logger.error(
                'Error access OF line table in accounting! (status webkit)')
        else:
            for supplier_order in cursor_of: # all open OC
                ref = supplier_order['CKY_ART'].strip()
                if ref not in supplier_orders:
                    supplier_orders[ref] = {}
                # TODO verify if not present
                of_deadline = supplier_order['DTT_SCAD'].strftime('%Y-%m-%d') 

                q = float(supplier_order['NQT_RIGA_O_PLOR'] or 0.0) * (
                    1.0 / supplier_order['NCF_CONV']\
                        if supplier_order['NCF_CONV'] else 1.0)
                if of_deadline not in supplier_orders[ref]: # TODO test UM
                    supplier_orders[ref][of_deadline] = q 
                else:
                    supplier_orders[ref][of_deadline] += q

        # -------------------
        # 3. Get OC elements:
        # -------------------

        # ---------------------------
        # 4. Get m(x) for production:
        # ---------------------------
        material_mx = {}
        with_medium = data.get('with_medium', False)
        month_window = data.get('month_window', 2)
        if with_medium:            
            from_date = (
                datetime.now() - timedelta(days=30 * month_window)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
            lavoration_material_ids = lavoration_pool.search(cr, uid, [
                ('real_date_planned', '>=', from_date),
                ('state', 'in', ('done', 'startworking')),
                ], context=context)
            for lavoration in lavoration_pool.browse(
                    cr, uid, lavoration_material_ids, context=context):
                for material in lavoration.bom_material_ids:
                    product = material.product_id # Readability:
                    if product.id in material_mx:
                        material_mx[product.id] += material.quantity or 0.0
                    else:
                        material_mx[product.id] = material.quantity or 0.0

        # ---------------------------------------------------------------------
        #                       GENERATE HEADER VALUES
        # ---------------------------------------------------------------------
        # -------------------------------
        # Get product list from OC lines:
        # -------------------------------
        # > populate cols 
        
        line_ids = order_line_pool.search(cr, uid, [
            ('date_deadline', '<=', end_date.strftime('%Y-%m-%d')),
            ], context=context) # only active from accounting
        for line in order_line_pool.browse(cr, uid, line_ids, context=context):
            if line.product_id.not_in_status: # jump line if product checked!
                _logger.warning(
                    'Not in status product: %s' % line.product_id.name)
                continue
            element = (
                'P', 
                line.product_id.id,
                line.product_id, # XXX used for minimum qty
                0.0,
                )
            # initialize row (today, < today, +1, +2, ... +n)                
            if element not in rows: 
                rows.append(element)
                
                # prepare data structure
                table[element[1]] = [0.0 for item in range(0, range_date)]
                 
                # start q.
                table[element[1]][0] = line.product_id.accounting_qty or 0.0 
                        
            if line.order_id.date_deadline in col_ids: # all date
                table[element[1]][col_ids[line.order_id.date_deadline]] -= \
                    line.product_uom_qty or 0.0  # OC deadlined this date    
            if not line.order_id.date_deadline or \
                    line.order_id.date_deadline < start_date.strftime(
                        '%Y-%m-%d'): # only < today
                # OC deadlined before today:        
                table[element[1]][1] -= line.product_uom_qty or 0.0

        # ---------------------------------------------------------------------
        #                   Get material list from Lavoration order
        # ---------------------------------------------------------------------
        # Populate cols:
        lavoration_ids = lavoration_pool.search(cr, uid, [
            # only < max date range
            ('real_date_planned', '<=', end_date.strftime(
                '%Y-%m-%d 23:59:59')),     
            ('state', 'not in', ('cancel','done')),
            ], context=context) # only open not canceled

        for lavoration in lavoration_pool.browse(
                cr, uid, lavoration_ids, context=context): # filtered BL orders
                
            real_date_planned = lavoration.real_date_planned[:10] # readability
            
            # -----------------------------------------------------------------
            # Product in lavoration order:
            # -----------------------------------------------------------------
            element = (
                'P', 
                lavoration.product.id, 
                lavoration.product,
                0.0,
                )

            if element not in rows:
                # prepare data structure:
                rows.append(element)            
                table[element[1]] = [0.0 for item in range(0, range_date)]       
                table[element[1]][0] = lavoration.product.accounting_qty or 0.0

            # Product production:
            if real_date_planned in col_ids: 
                table[element[1]][col_ids[real_date_planned]] += \
                    lavoration.product_qty or 0.0
            else: # < today  (element 1 - the second)
                table[element[1]][1] += lavoration.product_qty or 0.0

            # -----------------------------------------------------------------
            # Material in BOM:
            # -----------------------------------------------------------------
            for material in lavoration.bom_material_ids:     
                self.add_element_material_composition(
                    material.product_id, 
                    material.quantity,                    
                    table, 
                    rows,
                    # Medium block:
                    with_medium, material_mx, month_window,
                    # Period:
                    start_date, range_date, real_date_planned,
                    # OF data:                    
                    col_ids, supplier_orders,
                    )                

        # ---------------------------------------------------------------------
        #                 Production simulation:
        # ---------------------------------------------------------------------
        for fake in data['fake_ids']:
            qty = fake.qty     
            # Read BOM materials:
            for material in fake.bom_id.bom_lines:
                self.add_element_material_composition(
                    material.product_id, 
                    qty * material.product_qty,
                    table, 
                    rows,
                    # Medium block:
                    with_medium, material_mx, month_window,
                    # Period:
                    start_date, range_date, 
                    fake.production_date,
                    # OF data:                    
                    col_ids, supplier_orders,
                    )            
        rows.sort()

        # -----------------------
        # Generation table data: 
        # -----------------------
        # > Setup initial value:
        # > Import -q for material in lavoration:
        # > Import -q for sumulation of production:
        # > Import +q for product in lavoration:
        # > Import OC product in line with deadline:
        # > Import OF material with deadline:
        return True

    def _get_table(self, ):
        ''' Return reference for table
        '''
        global table            
        return table

    def _get_rows(self, context=None):
        ''' Rows list (generated by _start_up function)
        '''
        # Global parameters:    
        global rows
        return rows

    def _get_cols(self, context=None):
        ''' Cols list (generated by _start_up function)
        '''
        # Global parameters:    
        global cols
        return cols

    def _get_supplier_orders(self, context=None):
        ''' Cols list (generated by _start_up function)
        '''
        # Global parameters:    
        global supplier_orders
        return supplier_orders

    def _get_cel(self, col, row, context=None):
        ''' Cel value from col - row
            row=product_id
            col=n position
            return: (quantity, minimum value)
        '''
        # Global parameters:    
        global table
        global minimum
        
        # TODO get from table
        if row in table:
            return (table[row][col], minimum.get(row, 0.0))
        return (0.0, 0.0)
 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
