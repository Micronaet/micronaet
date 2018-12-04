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
import xlrd
import shutil
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

class MrpProductionWorkcenterLoad(orm.Model):
    """ Model name: MrpProductionWorkcenterLoad
        Add extra fields for waste management:
    """
    
    _inherit = 'mrp.production.workcenter.load'
    
    _columns = {
        'waste_id': fields.many2one('product.product', 'Waste product',
            help='When there\'s some waste production this product is loaded'),
        'waste_qty': fields.float('Waste Qty', digits=(16, 2)),
        }

class MrpProductionMaterial(orm.Model):
    """ Model name: Material pedimento
    """
    
    _inherit = 'mrp.production.material'
    
    _columns = {
        'pedimento_id': fields.many2one(
            'product.product.pedimento', 'Pedimento'),
        }

class product_product_extra(osv.osv):
    ''' Extra fields for product.product object
    '''
    _inherit = "product.product"

    def rpc_import_stock_status_mx(
            self, cr, uid, stock, context=None):
        ''' Launched externally (store procedure and passed database)
        '''
        _logger.info('Import stock status from external')

        if not stock: 
            _logger.error('Cannot import, no stock and pedimento stock passed')
            return False
            
        # ---------------------------------------------------------------------
        #                          PEDIMENTO STOCK:
        # ---------------------------------------------------------------------
        # Clean pedimento:
        pedimento_pool = self.pool.get('product.product.pedimento')
        _logger.info('Delete pedimentos')
        pedimento_ids = pedimento_pool.search(cr, uid, [], context=context)
        pedimento_pool.unlink(cr, uid, pedimento_ids, context=context)

        # Import pedimento and stock:
        total = {}
        for row in stock:
            # -----------------------------------------------------------------
            # Read parameters:
            # -----------------------------------------------------------------
            if len(row) == 3:
                default_code = row[0]
                name = row[1]
                product_qty = row[2]
                pedimento = False
                cost = 0.0 # TODO
            else:
                default_code = row[0]
                name = row[1]
                pedimento = row[2]
                cost = row[3]
                product_qty = row[4]
                # TODO log management
                     
            # -------------------------------------------------------------
            # Mandatory fields check:
            # -------------------------------------------------------------
            if not default_code:
                _logger.error('%s. Code empty (jump line)' % row)
                continue

            product_ids = self.search(cr, uid, [
                ('default_code', '=', default_code),
                ], context=context)
            if not product_ids:
                _logger.error(
                    '%s. Code not found in ODOO %s (jump line)' % (
                        row, default_code))
                continue
            product_id = product_ids[0]

            # -------------------------------------------------------------
            # Total update:
            # -------------------------------------------------------------
            if product_id not in total:
                total[product_id] = [0, cost]                        
            total[product_id][0] += product_qty

            # -------------------------------------------------------------
            # Pedimento:
            # -------------------------------------------------------------
            # Pedimento present with q positive
            if pedimento and product_qty > 0: 
                pedimento_pool.create(cr, uid, {
                    'name': pedimento,
                    'product_id': product_id,
                    'product_qty': product_qty,
                    'standard_price': cost,
                    }, context=context)

            # -------------------------------------------------------------
            # Log management
            # -------------------------------------------------------------
            # TODO 

        # -----------------------------------------------------------------
        # Reset accounting qty in ODOO:
        # -----------------------------------------------------------------
        _logger.info('Update product total:')
        product_ids = self.search(cr, uid, [
            ('accounting_qty', '!=', 0),
            ], context=context)
        self.write(cr, uid, product_ids, {
            'accounting_qty': 0.0,
            }, context=context)

        for product_id in total:
            product_qty, cost = total[product_id]
            # -------------------------------------------------------------
            # Update product data:
            # -------------------------------------------------------------
            self.write(cr, uid, product_id, {
                'accounting_qty': product_qty,
                'standard_price': cost,
                }, context=context)
        _logger.info('End import product account status')
        return True
    
    # -------------------------------------------------------------------------
    #                               Scheduled actions
    # -------------------------------------------------------------------------
    def schedule_etl_product_state_mx(
            self, cr, uid, path=False, start=1, context=None):
        ''' Import from Import Excel file from accounting
        '''
        _logger.info('Start import product account status on path %s' % path)

        if not path:
            _logger.error('No file path XLSX: %s' % path)
            return False       

        # Pool used:        
        pedimento_pool = self.pool.get('product.product.pedimento')

        # ---------------------------------------------------------------------
        # Read product status:
        # ---------------------------------------------------------------------
        path = os.path.expanduser(path)
        history = os.path.join(path, 'imported')

        for root, folders, files in os.walk(path):
            files = sorted(files, key=lambda x: (x[4:8], x[2:4], x[:2]))
            if not files:
                break
                
            # -----------------------------------------------------------------
            # Clean pedimento:
            # -----------------------------------------------------------------
            _logger.info('Delete pedimentos')
            pedimento_ids = pedimento_pool.search(cr, uid, [], context=context)
            pedimento_pool.unlink(cr, uid, pedimento_ids, context=context)

            # -----------------------------------------------------------------
            # Use last for import, most updated!            
            # -----------------------------------------------------------------
            filename = os.path.join(path, files[-1])
            history_name = os.path.join(history, files[-1])
            try:
                WB = xlrd.open_workbook(filename)
            except:
                _logger.error('Cannot read XLS file: %s' % filename)
            _logger.info('Read XLS file: %s' % filename)
            
            WS = WB.sheet_by_index(0)
            total = {}
            for row in range(start, WS.nrows):
                # -------------------------------------------------------------
                # Read fields:
                # -------------------------------------------------------------
                default_code = WS.cell(row, 0).value
                pedimento = WS.cell(row, 1).value
                cost = WS.cell(row, 2).value
                product_qty = WS.cell(row, 3).value
                # TODO log management
                
                # -------------------------------------------------------------
                # Mandatory fields check:
                # -------------------------------------------------------------
                if not default_code:
                    _logger.error('%s. Code empty (jump line)' % row)
                    continue

                product_ids = self.search(cr, uid, [
                    ('default_code', '=', default_code),
                    ], context=context)
                if not product_ids:
                    _logger.error(
                        '%s. Code not found in ODOO %s (jump line)' % (
                            row, default_code))
                    continue
                product_id = product_ids[0]

                # -------------------------------------------------------------
                # Total update:
                # -------------------------------------------------------------
                if product_id not in total:
                    total[product_id] = [0, cost]                        
                total[product_id][0] += product_qty

                # -------------------------------------------------------------
                # Pedimento:
                # -------------------------------------------------------------
                # Pedimento present with q positive
                if pedimento and product_qty > 0: 
                    pedimento_pool.create(cr, uid, {
                        'name': pedimento,
                        'product_id': product_id,
                        'product_qty': product_qty,
                        }, context=context)

                # -------------------------------------------------------------
                # Log management
                # -------------------------------------------------------------
                # TODO 

            # -----------------------------------------------------------------
            # Reset accounting qty in ODOO:
            # -----------------------------------------------------------------
            _logger.info('Update product total:')
            product_ids = self.search(cr, uid, [
                ('accounting_qty', '!=', 0),
                ], context=context)
            self.write(cr, uid, product_ids, {
                'accounting_qty': 0.0,
                }, context=context)

            for product_id in total:
                product_qty, cost = total[product_id]
                # -------------------------------------------------------------
                # Update product data:
                # -------------------------------------------------------------
                self.write(cr, uid, product_id, {
                    'accounting_qty': product_qty,
                    'standard_price': cost,
                    }, context=context)
            _logger.info('End import product account status')
            
            # -----------------------------------------------------------------
            # Move file on history
            # -----------------------------------------------------------------
            try:
                WB.release_resources()
                del WB
            except:
                _logger.info('Error close %s' % filename)
            try:
                shutil.move(filename, history_name)
                _logger.info('Move %s in %s' % (filename, history_name))
            except:
                _logger.info('Error moving file %s > %s' % (
                    filename, history_name))
                    
            # -----------------------------------------------------------------
            # Move old files
            # -----------------------------------------------------------------
            for f in files[:-1]:
                filename = os.path.join(path, f)
                history_name = os.path.join(history, f)
                shutil.move(filename, history_name)
                _logger.info('Not used too old: %s > %s' % (
                    filename, history_name))        

            break # no more walk folder        
        return True

    def get_waste_product(self, cr, uid, ids, context=None):
        ''' Update if present same product with R
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        default_code = current_proxy.default_code or ''
        waste_code = 'R' + default_code[1:] # Same as code but used R* format
        product_ids = self.search(cr, uid, [
            ('default_code', '=', waste_code),
            ], context=context)
        if product_ids:
            return self.write(cr, uid, ids, {
                'waste_ids': product_ids[0],
                }, context=context)
        else:
            raise osv.except_osv(
                _('Waste code'), 
                _('Product %s doesn\'t have waste code: %s' % (
                    default_code,
                    waste_code,
                    )),
                )            
        return True

    _columns = {
        'waste_id': fields.many2one('product.product', 'Waste product',
            help='When there\'s some waste production this product is loaded'),
        'forced_price': fields.float(
            'Forced price', digits=(16, 3), 
            help='Force price for raw material in product price'),
        }

class MrpProductionWorkcenterLineExtra(osv.osv):
    ''' Update some _defaults value
    '''
    _inherit = 'mrp.production.workcenter.line'

    # Override for manage pedimento
    # >>> ORM Function:
    def create(self, cr, uid, vals, context=None):
        """ Override create method only for generare BOM materials in subfield
            bom_materials_ids, initially is a copy of mrp.production ones
        """
        mrp_pool = self.pool.get('mrp.production')
        material_pool = self.pool.get('mrp.production.material')
        
        vals['real_date_planned_end'] = self.add_hour(
            vals.get('real_date_planned',False), 
            vals.get('hour',False))
        if vals.get('force_cycle_default', False):
            res = self.cycle_historyzation(cr, uid, vals, context=context)
            vals['force_cycle_default'] = False 
            # after historization force return False

        res_id = super(MrpProductionWorkcenterLineExtra, self).create(
            cr, uid, vals, context=context)
        if res_id: # Create bom for this lavoration: (only during creations)!! 
            # TODO test if is it is not created (or block qty if present)?
            mrp_proxy = mrp_pool.browse(
                cr, uid, [vals.get('production_id', 0)], context=context)[0]
            total = mrp_proxy.product_qty

            # Delete previous procedure records:            
            material_ids = material_pool.search(cr, uid, [
                ('workcenter_production_id','=', res_id),
                ], context=context)                
            material_pool.unlink(cr, uid, material_ids, context=context)
            
            for item in mrp_proxy.bom_material_ids:
                # proportionally created on total production order 
                # and total lavoration order
                item_id = material_pool.create(cr, uid, {
                    'product_id': item.product_id.id,
                    'quantity': item.quantity * vals.get(
                        'product_qty', 0.0) / total if total else 0.0,
                    # current yet created WC line:    
                    'workcenter_production_id': res_id, 
                    'pedimento_id': item.pedimento_id.id or False,
                    }, context=context)
        return res_id

    def _create_bom_lines(self, cr, uid, lavoration_id, from_production=False, 
            context=None):
        ''' Create a BOM list for the passed lavoration
            Actual items will be deleted and reloaded with quantity passed
        '''
        lavoration_browse = self.browse(
            cr, uid, lavoration_id, context=context)
        try:
            mrp = lavoration_browse.production_id
            bom = mrp.bom_id
            if not bom and not lavoration_browse.product_qty:
                return False # TODO raise error

            # Delete all elements:
            material_pool = self.pool.get('mrp.production.material')
            material_ids = material_pool.search(cr, uid, [
                ('workcenter_production_id','=', lavoration_id),
                ], context=context)
            material_pool.unlink(cr, uid, material_ids, context=context)

            # Create elements from bom:
            if from_production:
                for element in mrp.bom_material_ids:
                    material_pool.create(cr, uid, {
                        'product_id': element.product_id.id,
                        'quantity': element.quantity / mrp.product_qty * \
                            lavoration_browse.product_qty \
                            if mrp.product_qty else 0.0,
                        'pedimento_id': element.pedimento_id.id,    
                        'uom_id': element.product_id.uom_id.id,
                        'workcenter_production_id': lavoration_id,
                    }, context=context)
            else:                
                for element in bom.bom_lines:
                    material_pool.create(cr, uid, {
                        'product_id': element.product_id.id,
                        'quantity': element.product_qty * \
                            lavoration_browse.product_qty / bom.product_qty \
                            if bom.product_qty else 0.0,
                        'pedimento_id': False,
                        'uom_id': element.product_id.uom_id.id,
                        'workcenter_production_id': lavoration_id,
                    }, context=context)
            return True
        except:
            return False
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
