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

class ProductUom(osv.Model):
    ''' Product uom
    '''
    _inherit = 'product.uom'
    
    _columns = {
        'contipaq_ref': fields.char('ContipaQ ref.', size=15),
        }

class MrpProductionWorkcenterLoad(orm.Model):
    """ Model name: Load
    """
    
    _inherit = 'mrp.production.workcenter.load'
    
    _columns = {
        'package_pedimento_id': fields.many2one(
            'product.product.pedimento', 'Pedimento')
        }

class ResCompany(orm.Model):
    """ Model name: ResCompany
    """
    
    _inherit = 'res.company'

    def get_contipaq_folder_parameters(self, cr, uid, context=None):
        ''' Return dict with parameter structure:
        ''' 
        contipaq_samba_folder = self.browse(
            cr, uid, 1, context=context).contipaq_samba_folder

        if not contipaq_samba_folder:
            raise osv.except_osv(
                _('Setup parameter'), 
                _('No root folder setted up in company management'),
                )
        contipaq_samba_folder = os.path.expanduser(contipaq_samba_folder)
        return {
            'root': contipaq_samba_folder,
            'whoami': os.path.join(contipaq_samba_folder, 'whoami.winsrv'),
            'load': {
                'data': os.path.join(
                    contipaq_samba_folder, 'load', 'load_%s.xlsx'),
                'history': os.path.join(
                    contipaq_samba_folder, 'load', 'history'),
                'log': os.path.join(
                    contipaq_samba_folder, 'log', 'load.log'),
                },
            'unload': {
                'data': os.path.join(
                    contipaq_samba_folder, 'unload', 'unload_%s.xlsx'),
                'history': os.path.join(
                    contipaq_samba_folder, 'unload', 'history'),
                'log': os.path.join(
                    contipaq_samba_folder, 'log', 'unload.log'),
                },           
            }

    _columns = {
        'contipaq_samba_folder': fields.char(
            'ContipaQ Samba folder', size=180),
        }

class MrpProduction(osv.Model):
    ''' MRP production
    '''
    _inherit = 'mrp.production'

    _columns = {    
        # No more necessary:
        'accounting_sl_code': fields.char('Accounting SL code', size=16, 
            help='SL Code assigned during importation in accounting program'),
        'accounting_cl_code': fields.char('Accounting CL code', size=16, 
            help='CL Code assigned during importation in accounting program'),
        # ---------------------------------------------------------------------
    
        'force_production_rate': fields.float('Force rate', digits=(16, 4), 
            help='Force line rate only for this production.'),    
        }
    # -------------------------------------------------------------------------
    # Utility for SL and CL movement:
    # -------------------------------------------------------------------------
    def write_excel_CL(self, cr, uid, lavoration, folder, context=None):
        ''' Write CL document in Excel file
            excel_pool: Excel file manager
            lavoration: Laboration browse obj
            folder: Folder parameter
            
            Prepare Excel file in correct parameter folder with material and 
            Package used during lavoration process
        '''
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        load_pool = self.pool.get('mrp.production.workcenter.load')

        # ---------------------------------------------------------------------
        # Excel startup:
        # ---------------------------------------------------------------------
        ws_name = 'load'
        excel_pool.create_worksheet(ws_name)

        # ---------------------------------------------------------------------
        #                          Cost calculation:
        # ---------------------------------------------------------------------
        # Readability:
        mrp = lavoration.production_id # for force rate
        wc = lavoration.workcenter_id

        # Lavoration K cost (for line):
        try:
            # Check if forced during production
            line_rate_cost = mrp.force_production_rate or \
                wc.cost_product_id.standard_price or 0.0
        except:
            line_rate_cost = 0.0
        if not line_rate_cost:    
            raise osv.except_osv(
                _('Calculate lavoration cost!'),
                _('Error calculating lavoration cost, verify if '
                    'the workcenter has product linked'))

        # ---------------------------------------------------------------------
        # 1. Unloaded material this lavoration and package and pallet:
        # ---------------------------------------------------------------------
        unload_cost = unload_qty = 0.0 

        # ---------------------------------------------------------------------
        # A. Lavoration materials:
        # ---------------------------------------------------------------------
        for unload in lavoration.bom_material_ids:
            product = unload.product_id
            unload_qty += unload.quantity # Q

            # Cost for material:
            try:
                unload_cost += \
                    product.standard_price * unload.quantity
            except:
                raise osv.except_osv(
                    _('Lavoration cost error!'),
                    _('Material without cost: %s' % product.default_code))
        
        # ---------------------------------------------------------------------
        # 2. Unload from loading operation:
        # ---------------------------------------------------------------------
        # XXX Note: only one load
        load_qty = 0.0
        for load in lavoration.load_ids:
            load_qty = load.product_qty
            
            # -----------------------------------------------------------------
            # B. Package:
            # -----------------------------------------------------------------
            package = load.package_id
            link_product = package.linked_product_id
            
            if not package:
                raise osv.except_osv(
                    _('Lavoration cost error!'),
                    _('No package in load'))
                    
            if not link_product:
                raise osv.except_osv(
                    _('Lavoration cost errort!'),
                    _('No package product in load'))    
            
            # Package cost:
            unload_cost += \
                link_product.standard_price * load.ul_qty

            # -------------------------------------------------------------
            # C. Pallet:
            # -------------------------------------------------------------
            pallet = load.pallet_product_id
            
            # Pallet cost:
            if pallet: # There's pallet
                if not load.pallet_qty:
                    raise osv.except_osv(
                        _('Lavoration cost error!'),
                        _('Pallet product without cost!'))    
                unload_cost += \
                    pallet.standard_price * load.pallet_qty

        # ---------------------------------------------------------------------
        # D. Total cost of lavoration:
        # ---------------------------------------------------------------------
        raise osv.except_osv(
            _('Lavoration cost error!'),
            _('Load qty must be present!'))    
        
        # Add also Lavoration cost:
        unload_cost += (line_rate_cost * unload_qty) # K of Line (medium cost)
        
        # Calculate unit cost for production:
        unit_cost = unload_cost / load_qty #unload_qty #XXX before was material

        # ---------------------------------------------------------------------
        # Update all loads with total (master):
        # ---------------------------------------------------------------------
        # XXX Note: Only one
        load_ids = [load.id for load in lavoration.load_ids]
        load_pool.write(cr, uid, load.ids, {
            'accounting_cost': unit_cost * load.product_qty,
            }, context=context)
        
        # ---------------------------------------------------------------------
        #                             Excel file:
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
                _('Code'),
                _('Quantity'),
                _('UOM'),
                _('Cost'),
                _('Lot'), # Pedimento
                ])

        # ---------------------------------------------------------------------
        # Explode materials:
        # ---------------------------------------------------------------------
        for load in lavoration.load_ids:
            row += 1
            if load.recycle: 
                product = load.waste_id # Product was waste
                qty = load.waste_qty                            
                # Generate waste load:
                excel_pool.write_xls_line(ws_name, row, [
                    product.default_code,
                    qty,
                    product.uom_id.contipaq_ref,
                    unit_cost,
                    False, # No lot
                    ])
                qty = load.product_qty - waste_qty # remove waste
            else:        
                qty = load.waste_qty # all is good product
                
            product = load.product_id # Real product:
            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                qty,
                product.uom_id.contipaq_ref,
                unit_cost,
                load.product_code, # Lot code
                ])
        excel_pool.save_file_as(folder['load']['data'] % lavoration.id)
        
        # After creating CL write SL document
        del(excel_pool) 
        self.write_excel_SL(lavoration, folder)
        
        # ---------------------------------------------------------------------
        # wrkflow: lavoration is done:
        # ---------------------------------------------------------------------
        return lavoration_pool.write(cr, uid, [lavoration.id], {
            'state': 'done',
            }, context=context)
        
    def write_excel_SL(self, lavoration, folder):
        ''' Write SL document in Excel file
            self, cr, uid
            excel_pool: Excel file manager
            lavoration: Laboration browse obj
            folder: Folder parameter
            
            Prepare Excel file in correct parameter folder with material and 
            Package used during lavoration process
        '''
        excel_pool = self.pool.get('excel.writer')
        
        ws_name = 'unload'
        excel_pool.create_worksheet(ws_name)

        # ---------------------------------------------------------------------
        #                          Excel file:
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(ws_name, row, [
                _('Code'),
                _('Quantity'),
                _('UOM'),
                _('Cost'),
                _('Pedimento'),
                _('Lot'),
                ])

        # ---------------------------------------------------------------------
        # 1. Unload data from loading operation:
        # ---------------------------------------------------------------------
        for load in lavoration.load_ids:
            # -----------------------------------------------------------------
            # A. Unload package:
            # -----------------------------------------------------------------
            product = load.package_id.linked_product_id
            row +=1 
            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                load.ul_qty,
                product.uom_id.contipaq_ref,
                product.standard_price,
                load.package_pedimento_id.name or '', # pedimento
                '', # lot
                ])

            # -----------------------------------------------------------------
            # A. Unload Pallet:
            # -----------------------------------------------------------------
            if load.pallet_product_id:
                product = load.pallet_product_id
                row +=1 
                excel_pool.write_xls_line(ws_name, row, [
                    product.default_code,
                    load.pallet_qty,
                    product.uom_id.contipaq_ref,
                    product.standard_price,
                    '', # No pedimento
                    '', # No lot
                    ])

        # ---------------------------------------------------------------------
        # 2. Explode materials:
        # ---------------------------------------------------------------------
        for unload in lavoration.bom_material_ids:
            row += 1
            
            # -----------------------------------------------------------------
            # Check:                
            # -----------------------------------------------------------------
            default_code = unload.product_id.default_code
            if not default_code:
                raise osv.except_osv(
                    _('Unload material error:'),
                    _('No default code found for product'))

            standard_price = unload.product_id.standard_price
            if not standard_price:
                raise osv.except_osv(
                    _('Unload material error:'),
                    _('No standard price %s') % default_code)

            excel_pool.write_xls_line(ws_name, row, [
                default_code,
                unload.quantity,
                unload.product_id.uom_id.contipaq_ref,
                standard_price,
                unload.pedimento_id.name if \
                    unload.pedimento_id else '',
                '', # lot
                ])
        excel_pool.save_file_as(folder['unload']['data'] % lavoration.id)        
        return True
    
    # -------------------------------------------------------------------------    
    # TODO Procedure to update accounting_sl_code
    # -------------------------------------------------------------------------    
    
class ConfirmMrpProductionWizard(osv.osv_memory):
    ''' Wizard that confirm production/lavoration
    '''
    _inherit = 'mrp.production.confirm.wizard'

    # -------------------------------------------------------------------------
    #                                Onchange:
    # -------------------------------------------------------------------------
    def onchange_waste_qty(self, cr, uid, ids, product_qty, waste_qty, 
            context=None):
        ''' Check qty for waste
        ''' 
        if product_qty < waste_qty:
            return {'warning': {
                'title': _('Error'), 
                'message': _('Waste cannot exceed the production qty!'),
                }}
        return {}
        
    def onchange_waste(self, cr, uid, ids, product_id, recycle, context=None):         
        ''' Change filter for 
        '''
        res = {}
        if not recycle or not product_id:
            return res
        
        product_pool = self.pool.get('product.product')
        product_proxy = product_pool.browse(
            cr, uid, product_id, context=context) 

        waste_id = product_proxy.waste_id.id or False
        res['value'] = {'waste_id': waste_id, }        
        return res

    # -------------------------------------------------------------------------
    #                        Wizard button events:
    # -------------------------------------------------------------------------
    def action_confirm_mrp_production_order(self, cr, uid, ids, context=None):
        ''' Write confirmed weight (load or unload documents)
        '''
        if context is None:
            context = {}

        # Pool used:
        company_pool = self.pool.get('res.company')
        mrp_pool = self.pool.get('mrp.production')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')
        load_pool = self.pool.get('mrp.production.workcenter.load')

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        current_lavoration_id = context.get('active_id', 0)

        # ---------------------------------------------------------------------
        #                          Initial setup:
        # ---------------------------------------------------------------------
        # Wf management:
        wf_service = netsvc.LocalService('workflow')

        # Get parameters:
        folder = company_pool.get_contipaq_folder_parameters(
            cr, uid, context=context)

        # ---------------------------------------------------------------------
        # Check mount test file:
        # ---------------------------------------------------------------------
        if not os.path.isfile(folder['whoami']):
            raise osv.except_osv(
                _('Mount error'),
                _('Windows server not mounted!'),
                )
        
        lavoration_proxy = lavoration_pool.browse(
            cr, uid, current_lavoration_id, context=context)
            
        # Readability:
        mrp = lavoration_proxy.production_id # Production reference
        pallet = wiz_proxy.pallet_product_id
        wc = lavoration_proxy.workcenter_id
        partial = False # XXX Always last load! wiz_proxy.partial

        if wiz_proxy.state == 'material': # >> unload all material and package:
            # -----------------------------------------------------------------
            #                              SL Unload material
            # -----------------------------------------------------------------
            # Now go ahead only:
            accounting_sl_code = 'SL???' # TODO change when confirmed
            unload_confirmed = True
            lavoration_pool.write(
                cr, uid, [lavoration_proxy.id], {
                    'accounting_sl_code': accounting_sl_code,
                    'unload_confirmed': unload_confirmed,
                    },
                context=context)
            if unload_confirmed:
                wf_service.trg_validate(
                    uid, 'mrp.production.workcenter.line',
                    lavoration_proxy.id, 'button_done', cr)                        

        else: # wiz_proxy.state == 'product':
            # -----------------------------------------------------------------
            #                      CL  (lavoration load)
            # -----------------------------------------------------------------
            # XXX One load for one lavoration:
            if len(lavoration_proxy.load_ids) > 0:
                    raise osv.except_osv(
                        _('Load present:'),
                        _('Load is yet present, no other is possibile!'),
                        )

            # -----------------------------------------------------------------
            # Check operations before CL:
            # -----------------------------------------------------------------
            # MRP in cancel:                            
            if mrp.accounting_state in ('cancel'):
                raise osv.except_osv(
                    _('Production error:'),
                    _('Could not add other extra load (production cancelled)!')
                    )

            # Q. present if package:            
            if wiz_proxy.package_id and not wiz_proxy.ul_qty:
                raise osv.except_osv(
                    _('Package error:'),
                    _('If package is present quantity is mandatory [%s]!') % (
                        wiz_proxy.package_id.name,
                        ))
            # Q. present if pallet:
            if pallet and not wiz_proxy.pallet_qty:
                raise osv.except_osv(
                    _('Pallet error:'),
                    _('If pallet is present quantity is mandatory! [%s]' % (
                        pallet.name,
                        )))

            # -----------------------------------------------------------------
            #                    Create movement in list:
            # -----------------------------------------------------------------
            accounting_cl_code = 'CL???'
            product_qty = wiz_proxy.real_product_qty
            #wrong = wiz_proxy.wrong
            
            # -----------------------------------------------------------------
            # Manage recycle load
            # -----------------------------------------------------------------
            recycle = wiz_proxy.recycle
            if recycle:
                waste_id = wiz_proxy.waste_id.id or False
                waste_qty = wiz_proxy.waste_qty
                if waste_qty > product_qty:
                    raise osv.except_osv(
                        _('Waste error:'),
                        _('Waste %s must be <= of total lavoration: %s' % (
                            waste_qty, product_qty)))
            else:    
                waste_id = False
                waste_qty = 0.0

            # -----------------------------------------------------------------
            # Write record:
            # -----------------------------------------------------------------
            package_id = \
                wiz_proxy.package_id.id if wiz_proxy.package_id else False
            price = 0.0   
            load_id = load_pool.create(cr, uid, {
                'accounting_cl_code': accounting_cl_code,
                'product_qty': product_qty, # only the wrote total
                'line_id': lavoration_proxy.id,
                #XXX not manage, alwasy last! 'partial': wiz_proxy.partial,
                
                # Package:
                'package_id': package_id,
                'package_pedimento_id': wiz_proxy.package_pedimento_id.id,
                'ul_qty': wiz_proxy.ul_qty,
                
                # Pallet:
                'pallet_product_id': pallet.id if pallet else False,
                'pallet_qty': wiz_proxy.pallet_qty or 0.0,
                
                # Recycle:
                'recycle': recycle, # XXX not necessary!
                'waste_id': waste_id,
                'waste_qty': waste_qty,
                'wrong_comment': wiz_proxy.wrong_comment,                
                })
                
            # Reload record for get sequence value:
            sequence = load_pool.browse(
                cr, uid, load_id, context=context).sequence 

            # -----------------------------------------------------------------
            # Lot coding:
            # -----------------------------------------------------------------
            # Lot syntax:
            #     [(1)Famiglia - (6)Prodotto - (1).Pezzatura - (1)Versione] -
            #     [(5)Partita - #(2)SequenzaCarico] - [(10)Imballo]
            # Recycle product:
            #     recycle_code = 'R%s' % default_code[1:]
            code = wiz_proxy.product_id.default_code
            
            ref_lot_name = '%06d#%01d' % (int(mrp.name[3:]), sequence)
            product_code = '%-8s%-2s%-10s%-10s' % (
                code,
                wc.code[:2],
                ref_lot_name,
                wiz_proxy.package_id.code if package_id else '', # Package
                )
            load_pool.write(cr, uid, load_id, {
                'product_code': product_code,
                }, context=context)

            # Better: reload from dbmirror (but in real time)
            #product_pool.write(
            #    cr, uid, mrp.product_id.id,    
            #    # Update accounting_qty on db for speed up
            #    {'accounting_qty': 
            #        mrp.product_id.accounting_qty + \
            #            wiz_proxy.real_product_qty,
            #            }, context=context)

            # -----------------------------------------------------------------
            #                          Write Excel CL:
            # -----------------------------------------------------------------
            mrp_pool.write_excel_CL(cr, uid, lavoration_proxy, folder, 
                context=context)
                
            # -----------------------------------------------------------------
            # Workflow operation:    
            # -----------------------------------------------------------------
            # Check if it is the last lavoration:
            mrp_lavoration = lavoration_proxy.production_id.workcenter_lines
            last = True
            # Last if all lavoration done with 1 load 
            for lavoration in mrp_lavoration:
                if lavoration.state != 'done' or not lavoration.load_ids:
                    last = False
                    break

            if last:    
                wf_service.trg_validate(
                    uid, 'mrp.production', 
                    mrp.id,
                    'trigger_accounting_close',
                    cr)

        return {'type': 'ir.actions.act_window_close'}

    def default_list_unload(self, cr, uid, context=None):
        ''' Get default value, if load_confirmed so to_close is True
        '''
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        res = ''
        active_id = context.get('active_id', 0)
        if active_id:
            wc_browse = wc_pool.browse(cr, uid, active_id, context=context)
            res = _('Material:\n')
            for unload in wc_browse.bom_material_ids:
                res += '[%s %s] - %s [Ped. %s]\n' % (
                    unload.quantity,
                    unload.uom_id.contipaq_ref,
                    unload.product_id.name,
                    unload.pedimento_id.name if \
                        unload.pedimento_id else '/',
                    )
        return res

    # -------------------------------------------------------------------------
    # Onchange action (override)
    # -------------------------------------------------------------------------
    def onchange_package_id(self, cr, uid, ids, package_id, product_id, 
            real_product_qty, context=None):       
        ''' Integration on onchange for package (inser domain filter)
        '''
        res = super(ConfirmMrpProductionWizard, self).onchange_package_id(
            cr, uid, ids, package_id, product_id, real_product_qty, 
            context=context)
        if not package_id:
            return res
            
        # Update domain depend on package:
        ul_pool = self.pool.get('product.ul')
        ul_proxy = ul_pool.browse(cr, uid, package_id, context=context)        
        product_id = ul_proxy.linked_product_id.id

        if len(ul_proxy.linked_product_id.pedimento_ids) == 1:        
            package_pedimento_id = \
                ul_proxy.linked_product_id.pedimento_ids[0].id
        else:
            package_pedimento_id = False

        if 'value' not in res:
            res['value'] = {}        
        if 'domain' not in res:
            res['domain'] = {}
        
        res['value']['package_pedimento_id'] = package_pedimento_id
        res['domain']['package_pedimento_id'] = [
            ('product_id', '=', product_id)]
        return res    

    # -------------------------------------------------------------------------
    # Default function:
    # -------------------------------------------------------------------------
    def default_quantity(self, cr, uid, context=None):
        ''' Get default value
        '''
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        wc_proxy = wc_pool.browse(
            cr, uid, context.get('active_id', 0), context=context)

        # Production default is sum of material in this lavoration:        
        return sum(
            [material.quantity for material in wc_proxy.bom_material_ids])
            
    _columns = {
        'real_product_qty': fields.float(
            'Confirm production', digits=(16, 2), required=True),
        'use_mrp_package': fields.boolean('Usa solo imballi produzione', 
            help='Mostra solo gli imballaggi attivi nella produzione'),
        'package_pedimento_id': fields.many2one(
            'product.product.pedimento', 'Pedimento'),
        'waste_id': fields.many2one('product.product', 'Waste product',
            help='When there\'s some waste production this product is loaded'),
        'waste_qty': fields.float('Waste Qty', digits=(16, 2)),
        }
        
    _defaults = {
        'real_product_qty':  lambda s, cr, uid, c: s.default_quantity(
            cr, uid, context=c),
        'use_mrp_package': lambda *x: False,        
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
