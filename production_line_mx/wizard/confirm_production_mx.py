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

class ResCompany(orm.Model):
    """ Model name: ResCompany
    """
    
    _inherit = 'res.company'
    
    _columns = {
        'contipaq_samba_folder': fields.char(
            'ContipaQ Samba folder', size=180),
        }

class MrpProduction(osv.Model):
    ''' MRP production
    '''
    _inherit = 'mrp.production'

    _columns = {    
        'accounting_sl_code': fields.char('Accounting SL code', size=16, 
            help='SL Code assigned during importation in accounting program'),
        'accounting_cl_code': fields.char('Accounting CL code', size=16, 
            help='CL Code assigned during importation in accounting program'),
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

        ws_name = 'load'
        excel_pool.create_worksheet(ws_name)

        # Readability:
        mrp = lavoration.production_id
        wc = lavoration.workcenter_id

        # ---------------------------------------------------------------------
        #                          Cost calculation:
        # ---------------------------------------------------------------------
        # Lavoration K cost (for line):
        try:
            # Check if forced during production
            cost_line = mrp.force_production_rate or \
                wc.cost_product_id.standard_price or 0.0
        except:
            cost_line = 0.0
        if not cost_line:    
            raise osv.except_osv(
                _('Calculate lavoration cost!'),
                _('Error calculating lavoration cost, verify if '
                    'the workcenter has product linked'))

        # ---------------------------------------------------------------------
        # Unloaded material, package and pallet:
        # ---------------------------------------------------------------------
        unload_cost_total = total = 0.0 
        for l in mrp.workcenter_lines: # All lavoration in MRP:
            mrp = l.production_id

            # -----------------------------------------------------------------
            # Master MRP Materials:
            # -----------------------------------------------------------------
            for unload in mrp.bom_material_ids:
                # Q:
                total += unload.quantity or 0.0
                
                # Cost for material:
                try:
                    unload_cost_total += \
                        unload.product_id.standard_price * unload.quantity
                except:
                    _logger.error(
                        _('Error calculating unload material (missed cost'))

            # -----------------------------------------------------------------
            # Package and pallet:
            # -----------------------------------------------------------------
            for load in mrp.load_ids:
                # -------------------------------------------------------------
                # Package:
                # -------------------------------------------------------------
                package = load.package_id
                link_product = package.linked_product_id
                
                if not package:
                    raise osv.except_osv(
                        _('Calculate lavoration cost!'),
                        _('No package in load'))
                if not link_product:
                    raise osv.except_osv(
                        _('Calculate lavoration cost!'),
                        _('No package product in load'))    
                
                # Package cost:
                unload_cost_total += \
                    link_product.standard_price * load.ul_qty

                # -------------------------------------------------------------
                # Pallet:
                # -------------------------------------------------------------
                pallet = load.pallet_product_id
                # Pallet cost:
                if pallet: # There's pallet
                    unload_cost_total += \
                        pallet.standard_price * load.pallet_qty

        # ---------------------------------------------------------------------
        # Total cost of MRP production:
        # ---------------------------------------------------------------------
        # Add also Lavoration cost:
        unload_cost_total += (cost_line * total) # K of Line (medium cost)
        # Calculate unit cost:
        unit_cost = unload_cost_total / total

        # ---------------------------------------------------------------------
        # Update all loads with total (master):
        # ---------------------------------------------------------------------
        for load in mrp.load_ids:        
            load_pool.write(cr, uid, [load.id], {
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
        for load in mrp.load_ids:
            row += 1
            product = load.product_id
            excel_pool.write_xls_line(ws_name, row, [
                product.default_code,
                load.product_qty,
                product.uom_id.contipaq_ref,
                unit_cost,
                load.product_code, # Lot code
                ])
        excel_pool.save_file_as(folder['load']['data'] % lavoration.id)
        
        # After creating CL write SL document
        del(excel_pool) 
        self.write_excel_SL(lavoration, folder)
        
        # Lavoration is done now:
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

        mrp = lavoration.production_id
        
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

        for l in mrp.workcenter_lines:
            # For every load product:
            for load in l.load_ids:
                # -------------------------------------------------------------
                # Unload package:
                # -------------------------------------------------------------
                product = load.package_id.linked_product_id
                row +=1 
                excel_pool.write_xls_line(ws_name, row, [
                    product.default_code,
                    load.ul_qty,
                    product.uom_id.contipaq_ref,
                    product.standard_price,
                    '', # pedimento
                    '', # lot
                    ])

                # -------------------------------------------------------------
                # Unload Palled:
                # -------------------------------------------------------------
                if load.pallet_product_id:
                    product = load.pallet_product_id
                    row +=1 
                    excel_pool.write_xls_line(ws_name, row, [
                        product.default_code,
                        load.pallet_qty,
                        product.uom_id.contipaq_ref,
                        product.standard_price,
                        '', # pedimento
                        '', # lot
                        ])

        # ---------------------------------------------------------------------
        # Explode materials:
        # ---------------------------------------------------------------------
        # All lavoratoin in master MRP:
        for l in mrp.workcenter_lines:
            # -----------------------------------------------------------------
            # All material in lavoration:
            # -----------------------------------------------------------------
            for unload in l.bom_material_ids:
                row += 1
                
                # Check:                
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
        excel_pool.save_file_as(folder['unload']['data'] % mrp.id)        
        return True
    
    # -------------------------------------------------------------------------    
    # TODO Procedure to update accounting_sl_code
    # -------------------------------------------------------------------------    
    
class ConfirmMrpProductionWizard(osv.osv_memory):
    ''' Wizard that confirm production/lavoration
    '''
    _inherit = 'mrp.production.confirm.wizard'

    # --------------
    # Wizard button:
    # --------------
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
        wf_service = netsvc.LocalService('workflow')

        # ---------------------------------------------------------------------
        # Get parameters
        # ---------------------------------------------------------------------
        contipaq_samba_folder = company_pool.browse(
            cr, uid, 1, context=context).contipaq_samba_folder

        if not contipaq_samba_folder:
            raise osv.except_osv(
                _('Setup parameter'), 
                _('No root folder setted up in company management'),
                )
        contipaq_samba_folder = os.path.expanduser(contipaq_samba_folder)
        folder = {
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

        # ---------------------------------------------------------------------
        # Check mount test file:
        # ---------------------------------------------------------------------
        if not os.path.isfile(folder['whoami']):
            raise osv.except_osv(
                _('Mount error'),
                _('Windows server not mounted!'),
                )
        
        lavoration_browse = lavoration_pool.browse(
            cr, uid, current_lavoration_id, context=context)
            
        # Readability:
        mrp = lavoration_browse.production_id # Production reference
        pallet = wiz_proxy.pallet_product_id
        wc = lavoration_browse.workcenter_id
        partial = wiz_proxy.partial

        # ---------------------------------------------------------------------
        #                      CL  (lavoration load)
        # ---------------------------------------------------------------------
        # Only if not to close have a partial or fully load:
        if wiz_proxy.state == 'product':
            # -----------------------------------------------------------------
            # Check operations before CL:
            # -----------------------------------------------------------------
            #TODO Manage partial ?? if not wiz_proxy.partial:
            # Last lavoration must all closed state:
            for l in mrp.workcenter_lines:
                if l.state not in ('done', 'cancel'): # not closed
                    raise osv.except_osv(
                        _('Last lavoration:'),
                        _('When is the last lavoration all lavoration '
                            'must be in closed state!'),
                        )

            # MRP in cancel:                            
            if mrp.accounting_state in ('cancel'):
                raise osv.except_osv(
                    _('Production error:'),
                    _('Could not add other extra load (production cancelled)!')
                    )
            
            if wiz_proxy.package_id and not wiz_proxy.ul_qty:
                raise osv.except_osv(
                    _('Package error:'),
                    _('If package is present quantity is mandatory [%s]!') % (
                        wiz_proxy.package_id.name,
                        ))
                    
            if pallet and not wiz_proxy.pallet_qty:
                raise osv.except_osv(
                    _('Pallet error:'),
                    _('If pallet is present quantity is mandatory! [%s]' % (
                        pallet.name,
                        )))

            # -----------------------------------------------------------------
            # Create movement in list:
            # -----------------------------------------------------------------
            #accounting_cl_code = 'CLXXX' # TODO counter for CL
            product_qty = wiz_proxy.real_product_qty
            # TODO To be managed wrong and recycle load
            wrong = wiz_proxy.wrong
            recycle = wiz_proxy.recycle
            package_id = \
                wiz_proxy.package_id.id if wiz_proxy.package_id else False
            price = 0.0   
            load_id = load_pool.create(cr, uid, {
                #'accounting_cl_code': accounting_cl_code,
                'product_qty': product_qty, # only the wrote total
                'line_id': lavoration_browse.id,
                'partial': wiz_proxy.partial,
                'package_id': package_id,
                'ul_qty': wiz_proxy.ul_qty,
                'pallet_product_id': pallet.id if pallet else False,
                'pallet_qty': wiz_proxy.pallet_qty or 0.0,
                'recycle': recycle,
                'recycle_product_id': False,
                #    recycle_product_id.id if recycle_product_id else False,
                'wrong': wrong,
                'wrong_comment': wiz_proxy.wrong_comment,
                })
                
            # Reload record for get sequence value:
            sequence = load_pool.browse(
                cr, uid, load_id, context=context).sequence 

            # TODO manage recycle product!!!!! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
            # Code for product, syntax:
            # [(1)Famiglia - (6)Prodotto - (1).Pezzatura - (1)Versione] -
            # [(5)Partita - #(2)SequenzaCarico] - [(10)Imballo]
            if recycle:
                # Pass product with R + code without first char:
                code = 'R%s' % wiz_proxy.product_id.default_code[1:]
            else:    
                code = wiz_proxy.product_id.default_code
            
            #ref_lot_id = False
            ref_lot_name = '%06d#%01d' % (
                int(mrp.name[3:]),
                sequence,
                ) # Job <<< TODO use production (test, mrp is 5)

            product_code = '%-8s%-2s%-10s%-10s' % (
                code,
                wc.code[:2],
                ref_lot_name,
                wiz_proxy.package_id.code if package_id else '', # Package
                )
            load_pool.write(cr, uid, load_id, {
                #'product_code_id': lot_created_id,
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
            if not partial:
                # Export Excel file and complete production:
                mrp_pool.write_excel_CL(cr, uid, lavoration_browse, folder, 
                    context=context)
                wf_service.trg_validate(
                    uid, 'mrp.production', 
                    mrp.id,
                    'trigger_accounting_close',
                    cr)

        else: # state == 'material' >> unload all material and package:
            # -----------------------------------------------------------------
            #                              SL Unload material
            # -----------------------------------------------------------------
            # Now go ahead only:
            #accounting_sl_code = 'SLXXX' # TODO change when confirmed
            unload_confirmed = True
            lavoration_pool.write(
                cr, uid, [lavoration_browse.id], {
                    #'accounting_sl_code': accounting_sl_code,
                    'unload_confirmed': unload_confirmed,
                    },
                context=context)
            if unload_confirmed:
                wf_service.trg_validate(
                    uid, 'mrp.production.workcenter.line',
                    lavoration_browse.id, 'button_done', cr)                        
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
        
    _columns = {
        #'partial': fields.boolean('Partial', 
        #    help='If the product qty indicated is a partial load (not close lavoration)'),
        'use_mrp_package': fields.boolean('Usa solo imballi produzione', 
            help='Mostra solo gli imballaggi attivi nella produzione'),
        }
        
    _defaults = {
        #'partial': lambda *a: False,        
        'use_mrp_package': lambda *x: False,        
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
