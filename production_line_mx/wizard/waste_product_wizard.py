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
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare,
    )


_logger = logging.getLogger(__name__)


class MrpProductionWasteWizard(osv.osv_memory):
    ''' Wizard for create waste product
    '''
    _name = 'mrp.production.waste.wizard'

    # -------------------------------------------------------------------------
    #                        Wizard button events:
    # -------------------------------------------------------------------------
    def action_confirm_move(self, cr, uid, ids, context=None):
        ''' Create unload from product and load to product
            1. Create BOM empty lines
            2. Create production
            3. Create material list from from_product
            4. Create empty mrp job
            5. Extract unload and load in Excel for Account program
        '''
        if context is None:
            context = {}

        # Pool used:
        company_pool = self.pool.get('rec.company')
        bom_pool = self.pool.get('mrp.bom')
        mrp_pool = self.pool.get('mrp.production')
        material_pool = self.pool.get('mrp.production.material')
        excel_pool = self.pool.get('excel.writer')

        # ---------------------------------------------------------------------
        # Get wizard parameters:
        # ---------------------------------------------------------------------
        current = self.browse(cr, uid, ids, context=context)[0]
        from_product = current.from_id
        to_product = current.to_id
        qty = current.remain_qty
        price = current.force_price or current.remain_price
        calc = current.remain_detail # TODO
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
        # ---------------------------------------------------------------------
        # A. Create DB if not present
        # ---------------------------------------------------------------------
        bom_ids = bom_pool.search(cr, uid, [
            ('bom_id', '=', False), # Master bom
            ('product_id', '=', to_product.id),
            ], context=context)
        import pdb; pdb.set_trace()
        if bom_ids:
            bom_id = bom_ids[0]    
        else:
            # Create minimal BOM (empty):
            bom_id = bom_pool.create(cr, uid, {
                'product_id': to_product.id,
                'type': 'normal',
                'name': _('WASTE %s') % to_product.name,
                'product_uom': to_product.uom_id.id,
                'product_qty': 1.0,
                }, context=context)    
            
        # ---------------------------------------------------------------------
        # B. Create production
        # ---------------------------------------------------------------------
        mrp_id = mrp_pool.create(cr, uid, {
            'product_id': to_product.id,
            'bom_id': bom_id,
            'product_qty': qty,
            'date_planned': now,
            'user_id': uid,
            'mode': 'waste',
            'state': 'close', # yet close
            }, context=context)
        mrp_pool.add_new_lavoration(cr, uid, [mrp_id], context=context)
        mrp = mrp_pool.browse(cr, uid, mrp_id, context=context)
        lavoration_id = mrp.workcenter_lines[0].id
        # ---------------------------------------------------------------------
        #                           Excel transit files:
        # ---------------------------------------------------------------------
        folder = company_pool.get_contipaq_folder_parameters(
            cr, uid, context=context)

        # ---------------------------------------------------------------------
        # Check mount test file:
        # ---------------------------------------------------------------------
        if not os.path.isfile(folder['whoami']):
            raise osv.except_osv(
                _('Mount error'),
                _('Windows server not mounted (%s)!' % folder['whoami']),
                )

        # ---------------------------------------------------------------------
        # LOAD file:
        # ---------------------------------------------------------------------
        ws_name = 'load'
        excel_pool.create_worksheet(ws_name)

        row = 0
        excel_pool.write_xls_line(ws_name, row, [
                _('product_code'),
                _('quantity'),
                _('uom'),
                _('cost'),
                _('lot'), # Pedimento
                ])

        row += 1
        excel_pool.write_xls_line(ws_name, row, [
            to_product.default_code,
            qty,
            to_product.uom_id.contipaq_ref,
            price,
            mrp.name, # Use production name
            ])
        excel_pool.save_file_as(folder['load']['data'] % \
            lavoration_id)

        # ---------------------------------------------------------------------
        # UNLOAD file:
        # ---------------------------------------------------------------------
        excel_pool = self.pool.get('excel.writer')
        del(excel_pool)
        excel_pool = self.pool.get('excel.writer')

        ws_name = 'unload'
        excel_pool.create_worksheet(ws_name)
        
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
                _('material_code'),
                _('quantity'),
                _('uom'),
                _('cost'),
                _('pedimento'),
                _('lot'),
                _('stock'),
                ])

        # ---------------------------------------------------------------------
        # C. Create production material
        # ---------------------------------------------------------------------
        total = 0.0
        stock_number = '2' if from_product.product_type == 'MP' else '1'
        for lot in from_product.pedimento_ids:                
            qty = lot.product_qty
            if not qty:
                # Jump not present
                continue

            total += qty
            material_pool.create(cr, uid, {
                'production_id': mrp_id, # TODO Check!
                'product_id': lot.product_id.id,
                'standard_price': lot.product_id.standard_price,
                'pedimento_id': lot.id,
                'pedimento_price': lot.standard_price,
                'quantity': qty,
                }, context=context)

            # -----------------------------------------------------------------
            # Excel unload:
            # -----------------------------------------------------------------
            # Pedimento / Lot column: 
            if from_product.product_mode == 'lot':
                pedimento_name = ''
                lot_name = \
                    lot.pedimento_id.name if unload.pedimento_id else ''
            else: # pedimento   
                pedimento_name = \
                    lot.pedimento_id.name if unload.pedimento_id else ''
                lot_name = ''
            standard_price = \
                lot.standard_price or lot.product_id.standard_price 

            row += 1
            excel_pool.write_xls_line(ws_name, row, [
                to_product.default_code,
                qty,
                to_product.uom_id.contipaq_ref,
                standard_price,
                pedimento_name,
                lot_name,
                stock_number,
                ])

        if not total:
            raise osv.except_osv(
                _('Error'), 
                _('The "from product" contains nothing to waste!'),
                )

        excel_pool.save_file_as(folder['unload']['data'] % lavoration_id)

        # Update with calc:
        return lavoration_pool.write(cr, uid, [lavoration_id], {
            'state': 'done',
            'product_price_calc': calc,
            }, context=context)

    def onchange_product_id(self, cr, uid, ids, from_id, context=None):
        ''' Onchange product id update product stock status
        '''
        product_pool = self.pool.get('product.product')

        detail = ''
        qty = total = 0.0
        if from_id:                
            product = product_pool.browse(cr, uid, from_id, context=context)
            for lot in product.pedimento_ids:                
                subtotal = lot.standard_price * lot.product_qty
                qty += lot.product_qty
                total += subtotal
                detail += \
                    _('<font%s>Code: %s Q. %s [Price %s]</font><br/>') % (
                        '' if subtotal else ' color="red"',
                        lot.code,
                        lot.product_qty,
                        lot.standard_price,
                        )

            medium_price = total / qty if qty else 0.0
            detail += _('<b>Remain q. %s (medium price %s)</b>') % (
                qty, medium_price)
            return {'value': {
                'remain_detail': detail,
                'remain_qty': qty,
                'remain_price': medium_price,
                }}
        else:        
            return {'value': {
                'remain_detail': '',
                'remain_qty': 0.0,
                'remain_price': 0.0,
                }}
        
    _columns = {
        'from_id': fields.many2one('product.product', 'Waste product',
            help='Current product to be moved in waste',
            required=True),
        'to_id': fields.many2one('product.product', 'Waste product',
            help='Product considered waste', required=True),
        'force_price': fields.float('Force price', digits=(16, 2)),

        # Stock detail:
        'remain_detail': fields.text('Remain detail', readonly=True, 
            help='Detail of all lot / pedimentos present'), 
        'remain_qty': fields.float('Remain qty',
            digits=(16, 2), help='Remain q. present in stock'),
        'remain_price': fields.float('Remain price',
            digits=(16, 2), help='Medium price of lot present'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
