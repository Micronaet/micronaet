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
import xmlrpclib
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class MrpProduction(osv.osv):
    ''' Utility for file operations
    '''
    _inherit = 'mrp.production'
    
    # -----------------------------------
    # Utility used also in forced module:
    # -----------------------------------    
    def get_sl_cl_parameter(self, cr, uid, context=None):
        ''' Get parameter browse obj for connection info
        '''
        try:
            parameter = self.pool.get('res.company').get_production_parameter(
                cr, uid, context=context)

            if not parameter:
                raise osv.except_osv(
                    _('Parameter error!'),
                    _('Problem reading parameters, test in Company window and setup '
                    'all parameters necessary!'))

            if not parameter.production_export:
                raise osv.except_osv(
                    _('Export non enabled!'),
                    _('The exportation of CL and SL is not enabled, check and fix in '
                    'Company window to setup parameters!'))

            if not all ((
                    parameter.production_host,
                    parameter.production_port,
                    parameter.production_path,
                    parameter.production_cl,
                    parameter.production_sl,
                    parameter.production_cl_upd,
                )):
                raise osv.except_osv(
                    _('Parameter error!'),
                    _('Problem reading parameters (someone is not present), '
                    'test in Company window and setup all parameters necessary!'),
                    )
        except:
            raise osv.except_osv(
                _('Parameter error!'),
                _('Problem reading parameters!'))
        return parameter        

    def get_interchange_files(self, cr, uid, parameter, context=None):
        ''' Return 3 interchange file name
        '''
        try:
            path_list = eval(parameter.production_path)
            path = os.path.expanduser(os.path.join(*path_list))

            if not parameter.production_demo and \
                    parameter.production_mount_mandatory and \
                    not os.path.ismount(path):
                # Test if the folder is mounted (here is a UNC mount)
                raise osv.except_osv(
                    _('Mount error!'),
                    _('Interchange path is not mount %s!') % path)

            file_cl = os.path.join(path, parameter.production_cl)
            file_cl_upd = os.path.join(path, parameter.production_cl_upd)
            file_sl = os.path.join(path, parameter.production_sl)
        except:
            raise osv.except_osv(
                _('Interchange file!'),
                _('Error create interchange file name!'))
        return file_cl, file_cl_upd, file_sl

    def get_xmlrpc_sl_cl_server(self, cr, uid, parameter, context=None):
        ''' Configure and retur XML-RPC server for accounting        
        '''
        try:
            mx_parameter_server = parameter.production_host
            mx_parameter_port = parameter.production_port

            xmlrpc_server = 'http://%s:%s' % (
                mx_parameter_server,
                mx_parameter_port,
                )
        except:
            raise osv.except_osv(
                _('Import CL error!'),
                _('XMLRPC for calling importation is not response'), 
                )
                
        return xmlrpclib.ServerProxy(xmlrpc_server)

    def create_unload_file(self, cr, uid, file_sl, lavoration_browse, 
            force_stock=False, context=None):
        ''' Procedure for save in fullname file passed the lavoration element
            used for pass file to import account procedure        
        '''
        # Pool used:
        product_pool = self.pool.get('product.product')
        
        try:
            f_sl = open(file_sl, 'w')
            for unload in lavoration_browse.bom_material_ids:
                default_code = unload.product_id.default_code
                if not default_code:
                    raise osv.except_osv(
                        _('Material code error:'),
                        _('No code for MP: %s') % unload.product_id.name,
                        )
                    
                # Export SL for material used for entire production:
                f_sl.write('%-10s%-25s%10.2f\r\n' % (
                    default_code,
                    lavoration_browse.name[4:],
                    unload.quantity,
                    ))
                
                if force_stock:
                    try:
                        # XXX Now update accounting_qty on db for speed up
                        product_pool.write(cr, uid, [unload.product_id.id],    
                            {'accounting_qty': 
                                (unload.product_id.accounting_qty or 0.0) - \
                                (unload.quantity or 0.0), 
                                },
                        context=context)
                    except:
                        pass # no error raise if problems
            f_sl.close()        
        except:
            raise osv.except_osv(
                _('Transit file SL:'),
                _('Problem accessing file: %s '
                    '(maybe open in accounting program or error'
                    ' during export)!') % file_sl,
            )
        return True

class confirm_mrp_production_wizard(osv.osv_memory):
    ''' Wizard that confirm production/lavoration
    '''
    _name = 'mrp.production.confirm.wizard'

    # ---------------
    # Onchange event:
    # ---------------
    def onchange_use_mrp_package(self, cr, uid, ids, use_mrp_package, 
            package_id, context=None):
        ''' Change package domain filter
        '''
        res = {
            'domain': {
                'package_id': False,
                },
            }    
                
        if not use_mrp_package:
            return res

        
        # Read info in 
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        wc_id = context.get('active_id', 0)
        if not wc_id:
            raise osv.except_osv(
                _('Errore'), 
                _('Non trovato lavorazione corrente'),
                )
            
        wc_browse = wc_pool.browse(
            cr, uid, wc_id, context=context)
        package_ids = []
        import pdb; pdb.set_trace()
        for ul in wc_browse.production_id.product_packaging_ids:
            package_ids.append(ul.ul_id.id)
        
        if package_id not in package_ids:
            package_id = False # reset package
            
        return {
            'domain': {
                'package_id': [('id', 'in', package_ids)],
                },
            'value': {
                'package_id': package_id,
                }
            }
        
    def onchange_package_id(self, cr, uid, ids, package_id, product_id, total, 
            context=None):
        ''' Get selected package_id and calculate total package
        '''
        res = {}
        res['value'] = {}

        if package_id and product_id and total:
            pack_pool = self.pool.get('product.packaging')
            pack_ids = pack_pool.search(cr, uid, [
                ('product_id','=',product_id),
                ('ul','=',package_id)], context=context)
            if pack_ids:
                pack_proxy=pack_pool.browse(
                    cr, uid, pack_ids, context=context)[0]
                q_x_pack = pack_proxy.qty or 0.0
                res['value']['ul_qty'] = total // q_x_pack + \
                    (0 if total % q_x_pack == 0 else 1)
                return res
        res['value']['ul_qty'] = 0
        return res

    def onchange_pallet_id(self, cr, uid, ids, pallet_product_id, 
            real_product_qty, pallet_max_weight, context=None):
        ''' Get total pallet with real qty and pallet selected
        '''
        res = {}
        res['value'] = {}
        res['value']['pallet_qty'] = 0.0
        res['value']['pallet_max_weight'] = 0.0

        product_pool = self.pool.get('product.product')
        try:
            if pallet_product_id and real_product_qty:
                if not pallet_max_weight:
                    pallet_max_weight = product_pool.browse(
                        cr, uid, pallet_product_id, context=context
                        ).pallet_max_weight or 0.0
                res['value'][
                    'pallet_qty'] = real_product_qty // pallet_max_weight + (
                        0 if real_product_qty % pallet_max_weight == 0 else 1)
                res['value']['pallet_max_weight'] = pallet_max_weight
        except:
            pass # set qty to 0.0
        return res
        
    # --------------
    # Wizard button:
    # --------------
    def action_confirm_mrp_production_order(self, cr, uid, ids, context=None):
        ''' Write confirmed weight (load or unload documents)
        '''
        if context is None:
            context = {}

        # Pool used:
        mrp_pool = self.pool.get('mrp.production')
        lavoration_pool = self.pool.get('mrp.production.workcenter.line')
        product_pool = self.pool.get('product.product')
        load_pool = self.pool.get('mrp.production.workcenter.load')

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        current_lavoration_id = context.get('active_id', 0)

        # ---------------------------------------------------------------------
        #                          Initial setup:
        # ---------------------------------------------------------------------
        # get parameters
        parameter = mrp_pool.get_sl_cl_parameter(cr, uid, context=context)
        wf_service = netsvc.LocalService('workflow')
        error_prefix = '#' # TODO configuration area?

        # Interchange file:
        file_cl, file_cl_upd, file_sl = mrp_pool.get_interchange_files(
            cr, uid, parameter, context=context)
        
        # XMLRPC server:
        mx_server = mrp_pool.get_xmlrpc_sl_cl_server(
            cr, uid, parameter, context=context)

        lavoration_browse = lavoration_pool.browse(
            cr, uid, current_lavoration_id, context=context)
            
        # readability:
        mrp = lavoration_browse.production_id # Production reference
        pallet = wiz_proxy.pallet_product_id or False  
        wc = lavoration_browse.workcenter_id or False

        # Only if not to close have a partial or fully load:
        # 1. First close: all material are unloaded from stock accounting
        # 2. From second to last: all product are loaded with unload package
        # 3. Last: also correct product price
        if wiz_proxy.state == 'product':
            # -----------------------------------------------------------------
            #                      CL  (lavoration load)
            # -----------------------------------------------------------------
            
            # -----------
            # Init check:
            # -----------            
            # Verify thet if is the last load no lavoration are open:
            if not wiz_proxy.partial:
                for l in mrp.workcenter_lines:
                    if l.state not in ('done', 'cancel'): # not closed
                        raise osv.except_osv(
                            _('Last lavoration:'),
                            _('When is the last lavoration all lavoration must be in closed state!'),
                            )
                            
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
            product_qty = wiz_proxy.real_product_qty or 0.0
            wrong = wiz_proxy.wrong
            recycle = wiz_proxy.recycle
            #recycle_product_id = wiz_proxy.recycle_product_id
            package_id = \
                wiz_proxy.package_id.id if wiz_proxy.package_id else False
            # TODO create a function for compute: sum ( q. x std. cost)    
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
                
            # TODO create sequence depend on production
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
            product_code = '%-8s%-2s%-10s%-10s' % (
                code,
                wc.code[:2],
                '%06d#%01d' % (
                    int(mrp.name[3:]),
                    sequence,
                    ), # Job <<< TODO use production (test, mrp is 5)
                wiz_proxy.package_id.code if package_id else '', # Package
                )
            load_pool.write(cr, uid, load_id, {
                'product_code': product_code}, context=context)

            ### Write load on accounting: 
            # XXX potrebbe generare problemi se annullassero carichi o simili!
            # Better: reload from dbmirror (but in real time)
            product_pool.write(
                cr, uid, mrp.product_id.id,    
                # XXX Now update accounting_qty on db for speed up
                {'accounting_qty': 
                    (mrp.product_id.accounting_qty or 0.0) + \
                    (wiz_proxy.real_product_qty or 0.0),
                    }, context=context)

            # Export CL for product with new generated code:
            try:
                f_cl = open(file_cl, 'w')
                _logger.info('Open CL file: %s' % file_cl)    
            except:
                raise osv.except_osv(
                    _('Transit file problem accessing!'),
                    _('%s (maybe open in accounting program)!') % file_cl,
                    )

            # wrong > new code = (recycle code = code with R in 8th position)
            # NOTE remove wrong part, no more used!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #if wrong:
            #    f_cl.write('%-35s%10.2f%13.5f%16s\r\n' % (
            #        '%sR%s' % (
            #            product_code[:7],
            #            product_code[8:],
            #            ),
            #        product_qty,
            #        price,
            #        '', 
            #        ))
            #else:
            f_cl.write('%-35s%10.2f%13.5f%16s\r\n' % (
                product_code, product_qty, price, ''))                

            # TODO mode in product (end movement)
            convert_load_id = {} # list for convert CL code in load.id
            #for load in lavoration_browse.load_ids:

            # -----------------------------------------------------
            # Export SL form package/pallet used in loaded products
            # -----------------------------------------------------
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
            f_cl.close()

            # -----------------------------------------------------------------
            #                         Load CL for product
            # -----------------------------------------------------------------
            try:
                if parameter.production_demo: # Demo mode:
                    accounting_cl_code = 'DEMOCL000'
                else:
                    try:
                        accounting_cl_code = mx_server.sprix('CL')
                    except:    
                        raise osv.except_osv(
                            _('Import CL error!'),
                            _('XMLRPC error calling import CL procedure'), )

                    # test if there's an error during importation:
                    if accounting_cl_code.startswith(error_prefix):
                        raise osv.except_osv(
                            _('Import CL error!'),
                            _('Error from accounting:\n%s') % (
                                accounting_cl_code[len(error_prefix):], ),
                        )

                error = (
                    _('Update OpenERP with CL error!'),
                    _('Cannot write in OpenERP CL number for this load!'),
                )
                load_pool.write(cr, uid, load_id, {
                    'accounting_cl_code': accounting_cl_code}, context=context)

                # --------------------------------
                # Update lavoration with new info:
                # --------------------------------
                # TODO portare l'informazione sulla produzione qui non ha
                # più senso con i carichi sballati
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
                    # (till new synd for product state with correct value)
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

                    # ---------------------------------------------------------
                    #            Real workflow operation (only last load)
                    # ---------------------------------------------------------
                    # TODO Non occorre più verificare togliee questa parte:
                    # Close production order:
                    #if mrp.accounting_state in ('draft', 'production'):
                    #    if mrp.accounting_state in ('production'):
                    #        all_closed = True
                    #        for lavoration in mrp.workcenter_lines:
                    #            if lavoration.state not in ('done','cancel'):
                    #                all_closed = False
                    #                break
                    #        if all_closed:
                    wf_service.trg_validate(
                        uid, 'mrp.production', 
                        mrp.id,
                        'trigger_accounting_close',
                        cr)

                # togliere: scriveva il totale carico e il load_confirmed
                # lavoration_pool.write(cr, uid, [lavoration_browse.id], data, 
                # context=context)
            except:
                raise osv.except_osv(
                    _('Generic error'), 
                    '%s' % (sys.exc_info(), )
                    ) #error[0], '%s [%s]' % (error[1], sys.exc_info()) )

        else: # state == 'material' >> unload all material and package:
            # -----------------------------------------------------------------
            #                              SL Document
            # -----------------------------------------------------------------
            mrp_pool.create_unload_file(
                cr, uid, file_sl, lavoration_browse, force_stock=True, 
                context=context)

            # -----------------------------------------------------------------
            #                      XMLRPC call for import SL 
            # -----------------------------------------------------------------
            try:
                error = (
                    _('Generic error!'),
                    _('Startup error'),
                    )
                # an error here could mean that the document is created in 
                # accounting program 
                # TODO manage this problem
                if parameter.production_demo:
                    accounting_sl_code = 'DEMOSL000'
                else:
                    # ---------------------------------------------------------
                    #               SL for material and package
                    # ---------------------------------------------------------
                    try:
                        accounting_sl_code = mx_server.sprix('SL')
                    except:
                        error = (
                            _('Import SL error!'),
                            _('XMLRPC error calling import SL procedure'), 
                            )
                        raise osv.except_osv(*error)

                    # Test if there's an error during importation:
                    if accounting_sl_code.startswith(error_prefix):
                        error = (
                            _('Import SL error!'),
                            _('Error from accounting:\n%s') % \
                                accounting_sl_code[len(error_prefix):],
                            )
                        raise osv.except_osv(*error)

                error = (
                    _('Update SL error!'),
                    _('Error updating yet created SL link in OpenERP'),
                    )
                lavoration_pool.write(
                    cr, uid, [current_lavoration_id], {
                        'accounting_sl_code': accounting_sl_code,
                        'unload_confirmed': True, 
                        # TODO non dovrebbe più servire 
                        # Next 'confirm' is for prod.
                        },
                    context=context)

                try:  # If not error till now close WF for this lavoration:
                    wf_service.trg_validate(
                        uid, 'mrp.production.workcenter.line',
                        current_lavoration_id, 'button_done', cr)
                except:
                    error = (
                        _('Workflow error:'),
                        _('Error closing lavoration!'), 
                        )
                    raise osv.except_osv(*error)
            except:
                raise osv.except_osv(*error)                
        return {'type':'ir.actions.act_window_close'}

    # -----------------
    # default function:
    # -----------------
    def default_quantity(self, cr, uid, context=None):
        ''' Get default value
        '''
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        wc_browse = wc_pool.browse(
            cr, uid, context.get('active_id', 0), context=context)
        
        total = 0.0
        try:
            for l in wc_browse.production_id.workcenter_lines:
                total += l.product_qty - sum(
                    [load.product_qty for load in l.load_ids])
        except:
            total = 0.0  
        return total


    #def default_mode(self, cr, uid, context=None):
    #    ''' Setup open mode of wizard depend of status check
    #    '''
    #    wc_pool = self.pool.get('mrp.production.workcenter.line')
    #    active_id = context.get('active_id', 0)
    #    if active_id:
    #        wc_browse = wc_pool.browse(
    #            cr, uid, context.get('active_id', 0), context=context)
    #        if wc_browse.unload_confirmed:
    #            return 'product'
    #        else:
    #            return 'material'
    #    return 'matarial' # default

    #def default_to_close(self, cr, uid, context=None):
    #    ''' Get default value, if load_confirmed so to_close is True
    #    '''
    #    wc_pool = self.pool.get('mrp.production.workcenter.line')
    #    if context.get('active_id', 0):
    #        wc_browse = wc_pool.browse(
    #            cr, uid, context.get('active_id', 0), context=context)
    #        return wc_browse.load_confirmed
    #    return False # not launched during wizard

    def default_list_unload(self, cr, uid, context=None):
        ''' Get default value, if load_confirmed so to_close is True
        '''
        wc_pool = self.pool.get('mrp.production.workcenter.line')
        res = ''
        active_id = context.get('active_id', 0)
        if active_id:
            wc_browse = wc_pool.browse(cr, uid, active_id, context=context)
            res = 'Material:\n'
            for unload in wc_browse.bom_material_ids:
                res += '[%s %s] - %s\n' % (
                    unload.quantity,
                    unload.uom_id.name,
                    unload.product_id.name,
                )

            # TODO Manage in production load
            #res += '\nPackage:\n'
            #for load in wc_browse.load_ids:
            #    if load.package_id:
            #        res += 'Load %s. [%s] - %s%s\n' % (
            #            load.sequence,
            #            load.ul_qty,
            #            load.package_id.name,
            #            '\t\t<<<< No q.ty (not exported in SL)! <<<<<' if (
            #                load.package_id and not load.ul_qty) else '')
            #    else:
            #        res += 'Load %s. Wrong product is without package '
        #                   '(not exported in SL)\n' % (
            #            load.sequence)
        return res

    def default_product(self, cr, uid, context=None):
        ''' Get default value for product (get from product order)
        '''
        wc_pool = self.pool.get('mrp.production.workcenter.line')

        if context.get('active_id', 0):
            wc_browse = wc_pool.browse(
                cr, uid, context.get('active_id', 0), context=context)
            return wc_browse.product.id if wc_browse.product else False
        return False

    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product', required=True),
        'real_product_qty': fields.float(
            'Confirm production', digits=(16, 2), required=True),
        'partial': fields.boolean('Partial', 
            help='If the product qty indicated is a partial load (not close lavoration)'),
        'confirm_material': fields.boolean('Confirm material', 
            help='This confirm update of material on account program and close definitively the lavoration!'),

        'use_mrp_package': fields.boolean('Usa solo imballi produzione', 
            help='Mostra solo gli imballaggi attivi nella produzione'),
        'package_id': fields.many2one('product.ul', 'Package'),
        'ul_qty': fields.integer(
            'Package q.', help='Package quantity to unload from accounting'),
        'linked_product_id': fields.related(
            'package_id', 'linked_product_id', type='many2one', 
            relation='product_product', string='Linked product'),

        'pallet_product_id': fields.many2one(
            'product.product', 'Pallet', required=False),
        'pallet_max_weight': fields.float(
            'Max weight', digits=(16, 2), help='Max weight per pallet'),
        'pallet_qty': fields.integer('Pallet q.', help='Pallet total number'),

        #'to_close': fields.boolean('To close', required=False, help='If the load is set ad not partial'), # TODO remove
        'list_unload': fields.text('List unload'),

        'recycle': fields.boolean('Recycle', help='Recycle product'),
        'recycle_product_id': fields.many2one('product.product', 'Product'),

        'wrong': fields.boolean('Wrong', 
            help='Wrong product, coded with a standard code'),
        'wrong_comment': fields.text('Wrong comment'),
        # there's not a WF, only a check
        'state': fields.selection([
                ('material', 'Unload materials'),
                ('product', 'Load product (unload package')
                ], 'Mode', readonly=True),
        }

    _defaults = {
        'product_id': lambda s, cr, uid, c: s.default_product(
            cr, uid, context=c),
        'real_product_qty':  lambda s, cr, uid, c: s.default_quantity(
            cr, uid, context=c),
        'partial': lambda *a: True,
        'list_unload': lambda s, cr, uid, ctx: s.default_list_unload(
            cr, uid, context=ctx),
        'use_mrp_package': lambda *x: True,    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
