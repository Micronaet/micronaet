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

class ResCompany(orm.Model):
    """ Model name: ResCompany
    """
    
    _inherit = 'res.company'
    
    _columns = {
        'contipaq_samba_folder': fields.char(
            'ContipaQ Samba folder', size=180),
        }

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
        excel_pool = self.pool.get('excel.writer')

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
                    contipaq_samba_folder, 'load', 'load.xlsx'),
                'history': os.path.join(
                    contipaq_samba_folder, 'load', 'history'),
                'log': os.path.join(
                    contipaq_samba_folder, 'log', 'load.log'),
                },
            'unload': {
                'data': os.path.join(
                    contipaq_samba_folder, 'unload', 'unload.xlsx'),
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

        # ---------------------------------------------------------------------
        #                      CL  (lavoration load)
        # ---------------------------------------------------------------------
        # Only if not to close have a partial or fully load:
        if wiz_proxy.state == 'product':
            # -----------------------------------------------------------------
            # Check operations:
            # -----------------------------------------------------------------
            # Last lavoration must all closed state:
            if not wiz_proxy.partial:
                for l in mrp.workcenter_lines:
                    if l.state not in ('done', 'cancel'): # not closed
                        raise osv.except_osv(
                            _('Last lavoration:'),
                            _('When is the last lavoration all lavoration must be in closed state!'),
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
                    _('If package is present quantity is mandatory!'))
                    
            if pallet and not wiz_proxy.pallet_qty:
                raise osv.except_osv(
                    _('Pallet error:'),
                    _('If pallet is present quantity is mandatory!'))

            # Create movement in list:
            product_qty = wiz_proxy.real_product_qty
            # TODO To be managed wrong and recycle load
            wrong = wiz_proxy.wrong
            recycle = wiz_proxy.recycle
            package_id = \
                wiz_proxy.package_id.id if wiz_proxy.package_id else False
            price = 0.0   
            load_id = load_pool.create(cr, uid, {
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
            
            ref_lot_id = False
            mrp_id = self.get_mrp_id(cr, uid, context=context)
            #if mrp_id:        
            #    lot_created_id = mrp_pool.get_account_yet_created_ul(
            #        cr, uid, mrp_id, wiz_proxy.package_id.id, context=context)
            #    if lot_created_id:
            #        ref_lot_id = '#%-9s' % lot_created_id
                
            ref_lot_name = '%06d#%01d' % (
                int(mrp.name[3:]),
                sequence,
                ) # Job <<< TODO use production (test, mrp is 5)

            # Written in CL info:                
            real_product_code = '%-8s%-2s%-10s%-10s' % (
                code,
                wc.code[:2],
                ref_lot_name,
                wiz_proxy.package_id.code if package_id else '', # Package
                )
                
            # Passed to account    
            product_code = '%-8s%-2s%-10s%-10s' % (
                code,
                wc.code[:2],
                ref_lot_id or ref_lot_name,
                wiz_proxy.package_id.code if package_id else '', # Package
                )
            load_pool.write(cr, uid, load_id, {
                'product_code_id': lot_created_id,
                'product_code': real_product_code,
                }, context=context)

            # Better: reload from dbmirror (but in real time)
            product_pool.write(
                cr, uid, mrp.product_id.id,    
                # Update accounting_qty on db for speed up
                {'accounting_qty': 
                    mrp.product_id.accounting_qty + \
                        wiz_proxy.real_product_qty,
                        }, context=context)

            # -----------------------------------------------------------------
            #                          Write Excel CL:
            # -----------------------------------------------------------------
            # A. Product load:
            f_cl.write('%-35s%10.2f%13.5f%16s\r\n' % (
                product_code, product_qty, price, ''))                
            convert_load_id = {} # list for convert CL code in load.id

            # -----------------------------------------------------------------
            #                          Write Excel SL:
            # -----------------------------------------------------------------
            # B. Unload package:
            if wiz_proxy.package_id and wiz_proxy.ul_qty:
                f_cl.write(
                    '%-10s%-25s%10.2f%-13s%16s\r\n' % ( # TODO 10 extra space
                        wiz_proxy.package_id.linked_product_id.default_code,
                        '', #lavoration_browse.name[4:],
                        - wiz_proxy.ul_qty,
                        lavoration_browse.accounting_sl_code,
                        '',
                        ))
            else:
                pass # TODO raise error if no package? (no if wrong!)

            # C. Unload pallet:
            if pallet and wiz_proxy.pallet_qty:
                f_cl.write(
                    '%-10s%-25s%10.2f%-13s%16s\r\n' % ( # TODO 10 extra space
                        pallet.default_code,
                        '', #lavoration_browse.name[4:],
                        - wiz_proxy.pallet_qty,
                        lavoration_browse.accounting_sl_code,
                        '',
                        ))
            else:
                pass

            # -----------------------------------------------------------------
            #                         Load CL for product
            # -----------------------------------------------------------------
            try:
                accounting_cl_code = 'CLXXX' # TODO counter for CL

                error = (
                    _('Update OpenERP with CL error!'),
                    _('Cannot write in OpenERP CL number for this load!'),
                    )
                load_pool.write(cr, uid, load_id, {
                    'accounting_cl_code': accounting_cl_code,
                    }, context=context)

                # --------------------------------
                # Update lavoration with new info:
                # --------------------------------
                total = 0.0 # net production total
                
                # Partial (calculated every load on all production)                
                for l in mrp.workcenter_lines:
                    for partial in l.load_ids:
                        total += partial.product_qty or 0.0

                # TODO togliere i commenti nei log e metterli magari nella
                # lavorazione per sapere come sono stati calcolati
                _logger.info(_('Production real total: %s') % (total, ))
                ######################### data = {'real_product_qty': total}

                # Last unload document (extra op. needed)
                if not wiz_proxy.partial: 
                    # TODO togliere il load_confirmed
                    # data['load_confirmed'] = True # No other loads are admit!
                    # ---------------------------------------------------------
                    #                     CL update price file
                    # ---------------------------------------------------------
                    try:        
                        f_cl_upd = open(file_cl_upd, 'w')
                    except:    
                        raise osv.except_osv(
                            _('Transit file!'),
                            _('Problem accessing file: %s (maybe open in accounting program)!') % (
                                file_cl_upd))
                    unload_cost_total = 0.0

                    # ------------------
                    # Lavoration K cost:
                    # ------------------
                    try:
                        cost_line = wc.cost_product_id.standard_price or 0.0
                    except:
                        cost_line = 0.0

                    if not cost_line:    
                        raise osv.except_osv(
                            _('Calculate lavoration cost!'),
                            _('Error calculating lavoration cost, verify if the workcenter has product linked'), )

                    unload_cost_total = cost_line * total
                    _logger.info(_('Lavoration %s [%s]') % (
                        cost_line, unload_cost_total, ))

                    # ----------------------------------------------
                    # All unload cost of materials (all production):
                    # ----------------------------------------------
                    for lavoration in mrp.workcenter_lines:
                        for unload in lavoration.bom_material_ids:
                            try:
                                unload_cost_total += \
                                    unload.product_id.standard_price * \
                                    unload.quantity
                            except:
                                _logger.error(
                                    _('Error calculating unload lavoration'))    
                    _logger.info(
                        _('With materials [%s]') % unload_cost_total)

                    # ------------------------------
                    # All unload package and pallet:
                    # ------------------------------
                    for l in mrp.workcenter_lines:                    
                        for load in l.load_ids:
                            try:
                                # Package:
                                if load.package_id: # there's pallet
                                    link_product = \
                                        load.package_id.linked_product_id
                                    unload_cost_total += \
                                        link_product.standard_price * \
                                        load.ul_qty
                                    _logger.info(_('Package cost %s [%s]') % (
                                        link_product.standard_price, 
                                        load.ul_qty,
                                    ))
                            except:
                                _logger.error(
                                    _('Error calculating package price'))    
                                
                            try:
                                # Pallet:
                                pallet_in = load.pallet_product_id
                                if pallet_in: # there's pallet
                                    unload_cost_total += \
                                        pallet_in.standard_price * \
                                        load.pallet_qty
                                    _logger.info(_('Pallet cost %s [%s]') % (
                                        pallet_in.standard_price,
                                        load.pallet_qty,
                                    ))
                            except:
                                _logger.error(
                                    _('Error calculating pallet price'))    
                                
                    unload_cost = unload_cost_total / total
                    _logger.info(_('With package  %s [unit.: %s]') % (
                        unload_cost_total, unload_cost, ))

                    # Update all production with value calculated: #TODO serve?
                    for l in mrp.workcenter_lines:                    
                        for load in l.load_ids:
                            load_pool.write(cr, uid, load.id, {
                                'accounting_cost': 
                                    unload_cost * load.product_qty,
                                }, context=context)

                            # Export CL for update product price:
                            if not load.accounting_cl_code:
                                raise osv.except_osv(
                                    _('CL list!'),
                                    _('Error CL without number finded!'), )
                                
                            accounting_cl_code = \
                                load.accounting_cl_code.strip()
                            f_cl_upd.write(
                                '%-6s%10.5f\r\n' % (
                                    accounting_cl_code,
                                    unload_cost, ), # unit
                                )
                            convert_load_id[accounting_cl_code] = load.id
                            # TODO problema con il file di ritorno !!!!!!!!!!!!

                    # Temporary update accounting_qty on db for speed up
                    # TODO Verificare perchè dovrebbe essere già stato 
                    # tolto alla creazione della CL!!
                    # product_pool.write(cr, uid, unload.product_id.id, 
                    # {'accounting_qty':(unload.accounting_qty or 0.0) - 
                    # (unload.quantity or 0.0),}, context=context)
                    # TODO Vedere per scarico imballaggi
                    f_cl_upd.close()

                    # ---------------------------------------------------------
                    #                   CL update for product cost
                    # ---------------------------------------------------------
                    error = (
                        _('Update CL error!'),
                        _('XMLRPC for calling update CL method'), 
                        )

                    if not parameter.production_demo: # Demo mode:
                        # testare per verificare i prezzi   
                        # >> list of tuple [(1000, True),(2000, False)] 
                        # >> (cl_id, updated)
                        res_list = mx_server.sprix('CLW') 
                        if not res_list:
                            raise osv.except_osv(
                                _('Update CL price error!'),
                                _('Error launchind update CL price command'),
                            )
                        error = (
                            _('Update loaded CL price error!'),
                            _('Error during confirm the load or price for product in accounting program!'),
                        )
                        for (key,res) in res_list:
                            load_id = convert_load_id[key]
                            if res: # if True update succesfully
                                load_pool.write(
                                    cr, uid, load_id,
                                    {'accounting_cost_confirmed': True},
                                    context=context)
                            else:
                                pass # TODO raise error?

                    wf_service.trg_validate(
                        uid, 'mrp.production', 
                        mrp.id,
                        'trigger_accounting_close',
                        cr)

            except:
                raise osv.except_osv(
                    _('Generic error'), 
                    '%s' % (sys.exc_info(), )
                    )

        else: # state == 'material' >> unload all material and package:
            # -----------------------------------------------------------------
            #                              SL Document
            # -----------------------------------------------------------------
            # extract XLSX file:
            accounting_sl_code = 'SLXXX' # TODO change
            # TODO load operation

            ws_name = 'unload'
            excel_pool.create_worksheet(ws_name)
            row = 0
            excel_pool.write_xls_line(ws_name, row, [
                    _('Code'),
                    _('Quantity'),
                    _('Cost'),
                    _('Pedimento'),
                    _('Lot'),
                    ])
            
            for unload in lavoration_browse.bom_material_ids:
                row += 1
                excel_pool.write_xls_line(ws_name, row, [
                    unload.product_id.default_code,
                    unload.quantity,
                    unload.product_id.standard_price,
                    unload.pedimento_id.name if \
                        unload.pedimento_id else '',
                    '', # lot
                    ])
            excel_pool.save_file_as(folder['unload']['data'])
            
            # TODO confirm load procedure
            unload_confirmed = True
            lavoration_pool.write(
                cr, uid, [current_lavoration_id], {
                    'accounting_sl_code': accounting_sl_code,
                    'unload_confirmed': unload_confirmed, 
                    },
                context=context)
            if unload_confirmed:
                try:  # If not error till now close WF for this lavoration:
                    wf_service.trg_validate(
                        uid, 'mrp.production.workcenter.line',
                        current_lavoration_id, 'button_done', cr)
                except:
                    error = (
                        _('Workflow error:'),
                        _('Error closing lavoration!'), 
                        )
        return {'type':'ir.actions.act_window_close'}

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
                    unload.uom_id.name,
                    unload.product_id.name,
                    unload.pedimento_id.name if \
                        unload.pedimento_id else '/',
                    )
        return res
        
    _columns = {
        'partial': fields.boolean('Partial', 
            help='If the product qty indicated is a partial load (not close lavoration)'),
        'use_mrp_package': fields.boolean('Usa solo imballi produzione', 
            help='Mostra solo gli imballaggi attivi nella produzione'),
        }
        
    _defaults = {
        'partial': lambda *a: False,        
        'use_mrp_package': lambda *x: False,        
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
