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
        ''' Write confirmed weight (load or unload documents)
        '''
        if context is None:
            context = {}

        # Pool used:
        bom_pool = self.pool.get('mrp.bom')
        mrp_pool = self.pool.get('mrp.production')
        material_pool = self.pool.get('mrp.production.material')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        load_pool = self.pool.get('mrp.production.workcenter.load')

        current = self.browse(cr, uid, ids, context=context)[0]
        from_product = current.from_id.id
        to_product = current.to_id.id
        qty = current.qty
        force_price = current.force_price
        # TODO Check if passed price and qty!!!
        
        now = datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        
        # ---------------------------------------------------------------------
        # A. Create DB if not present
        # ---------------------------------------------------------------------
        bom_ids = self.search(cr, uid, [
            ('product_id', '=', to_product.id),
            ], context=context)
        if bom_ids:
            bom_id = bom_ids[0]    
        else:
            # Create minimal BOM:
            bom_id = bom_pool.create(cr, uid, {
                'product_id': to_product.id,
                'type': 'normal',
                'name': _('WASTE %s') % to_product.name,
                'product_uom': to_product.uom_id.id,
                'product_qty': 1.0,
                }, context=context)    
            
            # Create line:
            bom_pool.create(cr, uid, {
                'bom_id': bom_id,
                'product_id': from_product.id,
                #'type': 'normal',
                'name': from_product.name,
                'product_uom': from_product.uom_id.id,
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
            }, context=context)

        # ---------------------------------------------------------------------
        # C. Create production material
        # ---------------------------------------------------------------------
        total = 0.0
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
                'pedimento_price': lot.product_id.standard_price,
                'quantity': qty,
                }, context=context)

        if not total:
            raise osv.except_osv(
                _('Error'), 
                _('The "from product" contains nothing to waste!'),
                )
        # ---------------------------------------------------------------------
        # D. Create job:
        # ---------------------------------------------------------------------
        mrp_pool.add_new_lavoration(cr, uid, [mrp_id], context=context)
        
        # Add cycle detail:
        lavoration_ids = lavoration_pool.search(cr, uid, [
            ('production_id': mrp_id),  # TODO check
            ], context=context)
        if not lavoration_ids:
            raise osv.except_osv(
                _('Error'), 
                _('Cannot create production job'),
                )
        
        # Update cycle information:        
        lavoration_pool.write(cr, uid, lavoration_ids, {
            'cycle': 1,
            'single_cycle_duration': 0,
            'single_cycle_qty': total,
            'qty': total,
            'product_qty': total,
            #'workcenter_id': 1 # TODO
            }, context=context)
            
        # Update component (unload materials)    
        lavoration_pool.load_material_from_production(
            cr, uid, lavoration_ids, context=context)    
            
        
        # ---------------------------------------------------------------------
        # Confirm unload
        # ---------------------------------------------------------------------
        # Create fake wizard element
        
        # Raise workflow:
        
        # ---------------------------------------------------------------------
        # Confirm load
        # ---------------------------------------------------------------------
        # Create fake wizard element
        
        # Raise Workflow action:
        
        # TODO mark production as waste generator!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        
        return True

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
            return {'value': {
                'remain_detail': detail,
                'remain_qty': qty,
                'remain_price': total / qty if qty else 0.0,
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
        'remain_qty': fields.float('Remain qty', readonly=True,
            digits=(16, 2), help='Remain q. present in stock'),
        'remain_price': fields.float('Remain price', readonly=True,
            digits=(16, 2), help='Medium price of lot present'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
