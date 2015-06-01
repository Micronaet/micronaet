# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys
import os
from openerp.osv import osv, fields
import logging
import csv
from openerp.tools.translate import _ 


_logger = logging.getLogger(__name__)

class product_product_bom(osv.osv):
    ''' Add extra function for button event
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    
    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------
    def force_bom_import(self, cr, uid, ids, context=None):
        ''' Create a BOM and the lines using the current product_id 
        '''
        bom_pool = self.pool.get('mrp.bom')
        (path, file_name) = bom_pool._get_args_cron(cr, uid, context=context)
        if not path or not file_name:
            raise osv.except_osv(
                _('Error!'), 
                _("There's no cron element (or more than one) with function named: schedule_mrp_bom_production_line_import!"))

        bom_pool.schedule_mrp_bom_production_line_import(
            cr, uid, path, file_name,
            delete_before=False, 
            force_bom_id=False, 
            force_product_id=ids[0], # current
            context=context)
        return True
        
    
class mrp_bom_extra_fields(osv.osv):
    ''' Add extra field to manage mrp.bom
    ''' 
    _name = 'mrp.bom'
    _inherit = 'mrp.bom'

    # ------------------------------------------------------------------------- 
    # Private methods (utility):
    # ------------------------------------------------------------------------- 
    def _get_args_cron(self, cr, uid, context=None):
        ''' Read scheduled action and return path and filename
        '''
        cron_pool = self.pool.get("ir.cron")
        cron_ids = cron_pool.search(cr, uid, [
            ('function', '=', 'schedule_mrp_bom_production_line_import')
            ], context=context)
        if not cron_ids or len(cron_ids) > 1:
            return (False, False)
        cron_args = eval(cron_pool.browse(
            cr, uid, cron_ids, context=context)[0].args)
        return (cron_args[0], cron_args[1])
    
    # -------------------------------------------------------------------------
    # Button events:
    # -------------------------------------------------------------------------    
    def force_code_import(self, cr, uid, ids, context=None):
        ''' Force importation from file but only for current product
            deleting bom lines before
        '''
        try:    
            (path, file_name) = self._get_args_cron(cr, uid, context=context)
            if not path or not file_name:
                raise osv.except_osv(
                    _('Error!'), 
                    _("There's no cron element (or more than one) with function named: schedule_mrp_bom_production_line_import!"))

            self.schedule_mrp_bom_production_line_import(
                cr, uid, path, file_name, 
                delete_before=True, 
                force_bom_id=ids[0], 
                context=context)
            return True    
        except:
            raise osv.except_osv(
                _('Error!'), 
                _("Error reload BOM: [%s-%s-%s]" % sys.exc_info()))
            return False

    # -------------------------------------------------------------------------
    #                             Scheduled action 
    # -------------------------------------------------------------------------
    def schedule_mrp_bom_production_line_import(self, cr, uid, path, file_name,
        delete_before=True, force_bom_id=False, force_product_id=False, 
        context=None):
        ''' ETL operations for import BOM in OpenERP (parameter setted up in
            scheduled action for file name)
            delete_before: delete elements before import (used for sync 
               correctly when element are deletef in accounting program
            force_bom_id: Bom ID to import (BOM parent present)
            force_product_id: Create new BOM for product before import element
        '''
        # -----------------
        # Utility function:
        # -----------------
        def PrepareDate(valore):
            if valore: # TODO test correct date format
               return valore
            else:
               return time.strftime("%d/%m/%Y")

        def PrepareFloat(valore):
            valore=valore.strip() 
            if valore: # TODO test correct date format       
               return float(valore.replace(",", "."))
            else:
               return 0.0   # for empty values
               
        def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()

        def get_product_uom(self, cr, uid, name, context=None):
            ''' get product uom for create product
            '''
            try:
                uom_pool = self.pool.get("product.uom")

                uom_ids = uom_pool.search(cr, uid, [
                    ('name', '=', name)
                ], context=context)
                if len(uom_ids):
                    return uom_ids[0]
                return False # there will be problems...
            except:
                return False
        
        def create_update_product(self, cr, uid, default_code, data, _logger, context=None):
            ''' Search default_code an decide to create / update record
                logging error >1 record are present            
                return product_id
                if data is empty search only
            '''
            try:
                product_pool = self.pool.get("product.product")

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                if len(product_ids) >= 1:  # TODO update
                    if len(product_ids) > 1:
                        _logger.error('Too much product with code: %s' % (code, ))
                    if data:
                        mod = product_pool.write(
                            cr, uid, [product_ids[0]], data, context=context)  # only first
                    return product_ids[0] # no update (it's not this import procedure
                else:
                    if data:
                        return product_pool.create(cr, uid, data, context=context)                   
                    else:
                        _logger.error("No product found %s!" % (code, ))
                        return False 
            except:
                _logger.error('Error creating product: -<[%s]>-' % (sys.exc_info(),))                
                return False       

        def create_update_bom(self, cr, uid, domain, data, _logger, context=None):
            ''' Search domain list an decide to create / update record
                logging error >1 record are present            
                return list of bom lines (for check the line to delete at the end                
            '''
            try:
                bom_ids = self.search(cr, uid, domain, context=context)
                if len(bom_ids) >= 1:  # too many bom                
                    if len(bom_ids) > 1:  # too many bom
                        _logger.error(
                            'Too many bom with this code: [%s] (take first)' % (
                                domain, ))
                        
                    bom_id = bom_ids[0]
                    mod = self.write(cr, uid, [bom_id,],data, context=context), [] # no list if news!                                                  
                    bom_read = self.read(cr, uid, [bom_id], context=context) # save bom_lines for test the deleted items
                    return bom_id, bom_read[0].get('bom_lines', [])
                else:              # no bom (create)
                    return self.create(cr, uid, data, context=context), [] # no list if news!                                                  
            except:
                _logger.error('Error creating BOM: -<[%s]>-' % (sys.exc_info(), ))                
                return False       

        # -------------------
        # MAIN SCHEDULE CODE:
        # -------------------
        counter = 1 # no header!
        bom_id_lines = {} # array that get all (value) bom_lines, key: bom_id 
        product_to_produce = [] # update the supply_method to 'produce'
        
        # Delete only lines (for scheduled or for bom force only):
        force_product_code = False
        if delete_before:
            domain = [('etl', '=', True)]

            # Test if is in forced call:
            if force_bom_id:
                domain.append(('bom_id', '=', force_bom_id))
                bom_proxy = self.browse(cr, uid, force_bom_id, context=context)                
                force_product_code = bom_proxy.product_id.default_code
            else:                
                domain.append(('bom_id', '!=', False))    

            all_line_bom_ids = self.search(cr, uid, domain, context=context)
            self.unlink(cr, uid, all_line_bom_ids, context=context)
        
        uom_id = get_product_uom(self, cr, uid, 't', context=context) # default

        # Get file name and read all lines
        file_name = os.path.expanduser(os.path.join(path, file_name))
        lines = csv.reader(open(file_name,'rb'), delimiter = ";")
        
        tot_colonne = 0  
        for line in lines:
            try: # error manager for each line (not master error)
                if not counter:  # jump n lines of header 
                    counter += 1
                else: 
                    if not tot_colonne:
                        tot_colonne=len(line)
                        _logger.info('Start sync of mrp.bom [cols=%s, file=%s]' % (
                            tot_colonne, file_name))
                      
                    if len(line): # jump empty lines
                        if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                            _logger.error('Colums not the same (line jumped)')
                            continue
                       
                        counter += 1 
                        
                        # Read elements in CSV file:
                        code = Prepare(line[0]).strip()             # bom code (product)
                        if force_product_code and code != force_product_code:
                            continue # jump line

                        name = Prepare(line[1]).title()             # product description
                        sequence = Prepare(line[2])                 # sequence
                        component_code = Prepare(line[3])           # bom code (material)
                        component_name = Prepare(line[4]).title()   # material description
                        quantity = PrepareFloat(line[5])            # quantity         

                        if not quantity: # tot # of colums must be equal to # of column in first line
                            _logger.error('Quantity empty, component: %s, product: %s' % (
                                component_code, code))
                            continue
                       
                        # Calculated fields:
                        name = name.replace(r"/", r"-")
                        component_name = component_name.replace(r"/", r"-")

                        product_id = create_update_product(
                            self, cr, uid, code, False, _logger, context=context) # data empty for not create (UM problem)
                        if not product_id or force_product_id and product_id != force_product_id:
                            continue # jump line)

                        # -----------------------------------
                        # 2. Create or get mrp.bom > [header]
                        # -----------------------------------
                        # (save list of lines for delete)
                        bom_data = {
                            'name': name,
                            'code': code,
                            'active': True,
                            'type': 'normal',
                            'bom_id': False,
                            'product_id': product_id,
                            'product_qty': 1.0, # normal is one (TODO test if there's some total problems here!!)
                            'product_uos': uom_id,   # TODO può generare errore?
                            'product_uom': uom_id,
                            'etl': True,
                        }
                            
                        if product_id not in product_to_produce:
                            product_to_produce.append(product_id)
                            
                        (bom_id, bom_id_lines[bom_id]) = create_update_bom(
                            self, cr, uid, [
                                ('etl', '=', True), 
                                ('code', '=', code), 
                                ('bom_id', '=', False)],
                                    bom_data, _logger, context=context)
    
                        # ----------------------------------
                        # 3. Get or create component product
                        # ----------------------------------
                        component_data = {
                            'name': component_name,
                            'default_code': component_code,
                            'sale_ok': True,
                            'purchase_ok': True,
                            'type': 'product',
                            'supply_method': 'buy', # not produce!
                            #'uos_id': uom_id, # TODO come sopra
                            #'uom_po_id': uom_id,
                            #'uom_id': uom_id,
                            #'taxes_id':
                        }
                        product_id = create_update_product(self, cr, uid, component_code, component_data, _logger, context=context)

                        # ---------------------------------------------
                        # 4. Create or get mrp.bom line (from csv line)
                        # ---------------------------------------------
                        component_data = {
                            'name': component_name,
                            'code': component_code,
                            'active': True,
                            'type': 'normal',
                            'sequence': sequence,
                            'bom_id': bom_id,
                            'product_id': product_id, # MP
                            'product_qty': quantity, 
                            'product_uos': uom_id,
                            'product_uom': uom_id,
                            'etl': True,
                            #'date_start': fields.date('Valid From', help="Validity of this BoM or component. Keep empty if it's always valid."),
                            #'date_stop': fields.date('Valid Until', help="Validity of this BoM or component. Keep empty if it's always valid."),
                        }
                        (mp_bom_id, temp) = create_update_bom(self, cr, uid, [
                            ('etl', '=', True), ('code', '=', component_code), ('bom_id', '=', bom_id)], component_data, _logger, context=context)

                        # todo temp??
                        # 4. TODO problem for product in lines!!!
                        
                        # End of importation
                        _logger.info('%s. Line imported: {%s}'%(counter, line))
            except: # for every line (not master error)
                _logger.error('Error import line of mrp.bom [%s]' % (sys.exc_info(), )) 
        
        try:        
            self.pool.get('product.product').write(cr, uid, product_to_produce, {
                'supply_method': 'produce',
            }, context=context)
        except:
            _logger.error('Error updating product supply method')

        _logger.info('End importation: Total: %s' % (counter))
        return

    _columns = {
        'etl': fields.boolean('Import ETL'),
    }    
    
    _defaults = {
        'etl': lambda *x: False,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
