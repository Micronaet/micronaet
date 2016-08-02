# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
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
import logging
import csv
from openerp.osv import osv, fields

        
_logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
#                                     Utility
# -----------------------------------------------------------------------------

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime('%d/%m/%Y')

def PrepareFloat(valore):
    valore = valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(',', '.'))
    else:
       return 0.0   # for empty values
       
def Prepare(valore):  
    ''' For problems: input win output ubuntu; trim extra spaces
    '''
    valore = valore.decode('cp1252')
    valore = valore.encode('utf-8')
    return valore.strip()

def prepare_ascii(valore):  
    ''' Return only ascii char
    '''
    valore = valore.strip()
    res = ''
    for c in valore:
        if ord(c) < 128: # 256
            res += c
        else:
            res+= '#'                
    return res
            
class etl_bom_line(osv.osv):
    ''' ETL bom line imported from account program
    ''' 
    _name = 'etl.bom.line'
    _description = 'BOM line'
    _order = 'is_primary,name,seq'    

    # -------------------------------------------------------------------------
    #                                 Utility
    # -------------------------------------------------------------------------
    def generate_csv_file_from_bom(self, cr, uid, file_name, 
            context=None):
        ''' Generate file from BOM (variant)
        '''
        bom_pool = self.pool.get('mrp.bom')
        bom_ids = bom_pool.search(cr, uid, [
            ('bom_id', '=', False),
            ], context=context) 
            
        bom_f = open(file_name, 'w')
        # only parent elements:
        for bom in bom_pool.browse(cr, uid, bom_ids, context=context):
            sequence = 0
            for line in bom.bom_lines:
                sequence += 1
                row = '%s;%s;%s;%s;%s;%15.4f\n\r' % (
                    # Heeader:
                    bom.product_id.default_code,
                    prepare_ascii(bom.product_id.name),
                    
                    # Lines:
                    sequence,
                    line.product_id.default_code,
                    prepare_ascii(line.product_id.name),
                    line.product_qty or 0.0,
                    )
                row = row.replace('.', ',') # old account stype    
                bom_f.write(row)
        bom_f.close()            
        return True

    # -------------------------------------------------------------------------
    #                     Scheduled action (etl.bom.line)
    # -------------------------------------------------------------------------
    def schedule_etl_bom_line_import(self, cr, uid, path, file_name, 
            generate_from_bom=True, context=None):
        ''' ETL operations for import BOM in OpenERP (parameter setted up in
            scheduled action for file name)            
            Note: Only for report that compare BOM
            generate_from_bom: generate file before
        '''
        # TODO Migrate to mrp.bom
        counter = 1
        file_name = os.path.expanduser(os.path.join(path, file_name))
        
        # Generate file before from BOM
        if generate_from_bom:
            _logger.info('Generate file [%s] from BOM' % file_name)
            self.generate_csv_file_from_bom(
                cr, uid, file_name, context=context) 
            
        # Delete all:
        all_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, all_ids, context=context)
        
        # Create elements:
        try:
            lines = csv.reader(open(file_name,'rb'), delimiter = ';')
            
            tot_colonne=0
            for line in lines:
                if not counter:  # jump n lines of header 
                   counter += 1
                else: 
                   if not tot_colonne:
                       tot_colonne=len(line)
                       _logger.info('Start sync of BOM [cols=%s, file=%s]' % (
                           tot_colonne, file_name))
                      
                   if len(line): # jump empty lines
                       if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                           _logger.error('Colums not the same')
                           continue 
                       
                       counter += 1 
                       csv_id=0
                       code = Prepare(line[csv_id]).strip() # bom code (product)
                       csv_id+=1
                       name = Prepare(line[csv_id]).title() # product description
                       csv_id+=1
                       seq = Prepare(line[csv_id]) # sequence
                       csv_id+=1
                       component_code = Prepare(line[csv_id]) # bom code (material)
                       csv_id+=1
                       component_name = Prepare(line[csv_id]).title() # material description
                       csv_id+=1
                       quantity = PrepareFloat(line[csv_id]) # quantity         
                       
                       # Calculated fields:
                       is_primary = len(code) != 7
                       primary = code[:6].strip() # also for primary
                       name = name.replace(r'/', r'-')
                       component_name = component_name.replace(r'/', r'-')

                       data = {
                           'name': name,
                           'code': code,
                           'is_primary': is_primary,
                           'primary': primary,

                           # Line:
                           'seq': seq,
                           'component_name': component_name,
                           'component_code': component_code,
                           'quantity': quantity,
                           }
                            
                       # PRODUCT CREATION ***************
                       try:
                           product_id = self.create(cr, uid, data, 
                               context=context) 
                       except:
                           _logger.info(
                               "[ERROR] Create BOM line, current record:", 
                               counter)

            _logger.info('End importation: Total: %s' % counter)
        except:
            _logger.error('Error import BOM')
        return

    _columns = {
        # Header:
        'name': fields.char('BOM version', size=40, required=True),
        'code': fields.char('Product code', size=8, required=True),
        'is_primary': fields.boolean('is primary', required=False),
        'primary': fields.char('BOM primary', size=24, required=False),
 
        # Line:
        'seq': fields.integer('seq'),
        'component_name': fields.char('Component name', size=40, 
            required=True),
        'component_code': fields.char('Component code', size=8, 
            required=True),
        'quantity': fields.float('Q.', digits=(16, 6)),
        }
        
    _defaults = {
        'is_primary': lambda *a: False,
        #'sum_for_total': lambda *a: True, # TODO remove
        }                               

class mrp_bom_extra_fields(osv.osv):
    ''' Add extra field to manage mrp.bom
    ''' 
    _inherit = 'mrp.bom'

    # -------------------------------------------------------------------------
    #                      Scheduled action (mrp.bom)
    # -------------------------------------------------------------------------
    def schedule_etl_bom_line_import(self, cr, uid, path, file_name, 
            delete_before=False, context=None):
        ''' ETL operations for import BOM in OpenERP (parameter setted up in
            scheduled action for file name)
        '''
        # TODO Da rimuovere: creato bom_csv_import per fare solo questo
        # -----------------
        # Utility function:
        # -----------------        
        def get_product_uom(self, cr, uid, name, context=None):
            ''' get product uom for create product
            '''
            try:
                uom_pool = self.pool.get("product.uom")

                uom_ids = uom_pool.search(cr, uid, [
                    ('name', '=', name)], context=context)
                if len(uom_ids):
                    return uom_ids[0]
                return False # there will be problems...
            except:
                return False
        
        def create_update_product(self, cr, uid, default_code, data, _logger, 
                context=None):
            ''' Search default_code an decide to create / update record
                logging error >1 record are present            
                return product_id
            '''
            try:
                product_pool = self.pool.get("product.product")
                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                if len(product_ids) >= 1:  # TODO update
                    if len(product_ids) > 1:
                        _logger.error('Too much product with code: %s' % (
                            code,))
                        
                    mod = product_pool.write(cr, uid, [product_ids[0]], data, 
                        context=context)  # only first
                    return product_ids[0] # no update (it's not this import procedure
                else:
                    return product_pool.create(cr, uid, data, context=context)                   
            except:
                _logger.error('Error creating product: -<[%s]>-' % (
                    sys.exc_info(), ))
                return False       

        def create_update_bom(self, cr, uid, domain, data, _logger, 
                context=None):
            ''' Search domain list an decide to create / update record
                logging error >1 record are present            
                return list of bom lines (for check the line to delete at the 
                end                
            '''
            try:
                bom_ids = self.search(cr, uid, domain, context=context)
                if len(bom_ids) >= 1:  # too many bom                
                    if len(bom_ids) > 1:  # too many bom
                        _logger.error('Too many bom with this code: [%s] (take first)' % (
                            domain,))
                        
                    bom_id = bom_ids[0]
                    mod = self.write(cr, uid, [
                        bom_id, ], data, context=context), []# no list if news!                                                  
                    bom_read = self.read(cr, uid, [bom_id], context=context) # save bom_lines for test the deleted items
                    return bom_id, bom_read[0].get('bom_lines',[])
                else:              # no bom (create)
                    return self.create(cr, uid, data, context=context), [] # no list if news!                                                  
            except:
                _logger.error('Error creating BOM: -<[%s]>-' % (
                    sys.exc_info(),))                
                return False       
        
        # ------------------
        # MAIN SCHEDULE CODE 
        # ------------------
        counter = 1 # no header!
        bom_id_lines = {} # array that get all (value) bom_lines, key: bom_id 
        try:
            # Array for remove headers or component BOM:
            bom_pool = self.pool.get('mrp.bom')
            header_bom_to_delete = bom_pool.search(cr, uid, [
                ('bom_id', '=', False),
            ], context=context)
            
            component_bom_to_delete = bom_pool.search(cr, uid, [
                ('bom_id', '!=', False),
            ], context=context)

            uom_id = get_product_uom(
                self, cr, uid, 'kg', context=context) # always kg
            # Get file name and read all lines 
            file_name = os.path.expanduser(os.path.join(path, file_name))
            lines = csv.reader(open(file_name,'rb'), delimiter = ";")
            
            tot_colonne = 0            
            for line in lines:
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
                       
                        try: # jump line if error:
                            counter += 1 
                            code = Prepare(line[0]).strip() # bom code (product)
                            name = Prepare(line[1]).title() # product description
                            sequence = Prepare(line[2]) # sequence
                            component_code = Prepare(line[3]) # bom code (material)
                            component_name = Prepare(line[4]).title() # material description
                            quantity = PrepareFloat(line[5]) # quantity         

                            if not quantity: # tot # of colums must be equal to # of column in first line
                                _logger.error('Quantity empty, component: %s, product: %s' % (
                                    component_code, code))
                                continue
                           
                            # Calculated fields:
                            is_primary = len(code) != 7
                            primary = code[:6].strip() # also for primary  (not user for now)
                            name = name.replace(r"/", r"-")
                            component_name = component_name.replace(r'/', r'-')

                            # --------------------------------
                            # 1. Create or get product.product
                            # --------------------------------
                            product_data = {
                                'name': name,
                                'default_code': code,
                                'sale_ok': True,
                                'purchase_ok': True,
                                'type': 'product',
                                'supply_method': 'produce', # 'buy'
                                #'uos_id': uom_id,     # TODO tolti per errore durante l'update
                                #'uom_po_id': uom_id,
                                #'uom_id': uom_id,
                                
                                #'taxes_id':,
                            }
                            product_id = create_update_product(
                                self, cr, uid, code, product_data, _logger, 
                                context=context)
                                        
                            # -----------------------------------
                            # 2. Create or get mrp.bom > [header]
                            # -----------------------------------
                            # TODO  save list of lines for delete
                            bom_data = {
                                'name': name,
                                'code': code,
                                'active': True,
                                'type': 'normal',
                                'bom_id': False,
                                'product_id': product_id,
                                'product_qty': 1.0, # normal is one (TODO test if there's some total problems here!!)
                                'is_primary': is_primary,                                                                              
                                'product_uos': uom_id,
                                'product_uom': uom_id,
                            }
                            bom_id, bom_id_lines[bom_id] = create_update_bom(
                                self, cr, uid, [
                                    ('code', '=', code),
                                    ('bom_id', '=', False),
                                    ], bom_data, _logger, context=context)
                                
                            if bom_id in header_bom_to_delete: # Present
                                header_bom_to_delete.remove(bom_id)

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
                                'uos_id': uom_id,
                                'uom_po_id': uom_id,
                                'uom_id': uom_id,
                                #'taxes_id'?
                                }
                            product_id = create_update_product(
                                self, cr, uid, component_code, component_data,
                                _logger, context=context)
                                
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
                                'is_primary': False,
                                'product_uos': uom_id,
                                'product_uom': uom_id,
                                #'date_start': fields.date('Valid From', help="Validity of this BoM or component. Keep empty if it's always valid."),
                                #'date_stop': fields.date('Valid Until', help="Validity of this BoM or component. Keep empty if it's always valid."),
                                }
                            mp_bom_id, temp = create_update_bom(self, cr, uid, [
                                ('code', '=', component_code),
                                ('bom_id', '=', bom_id),
                                ], component_data, _logger, context=context)

                            if mp_bom_id in component_bom_to_delete: # Present
                                component_bom_to_delete.remove(mp_bom_id)

                            # todo temp??
                            # 4. TODO problem for product in lines!!!
                            
                            # End of importation
                            _logger.info('%s. Line imported: {%s}' % (
                                counter, line))
                        except: 
                            _logger.error('Error importing line mrp.bom, jumped %s [%s]' % (
                                line,sys.exc_info()))       
                            continue # not necessary
                            
            # --------------------------
            # 4. Delete bom not present:
            # --------------------------
            ''' TODO debug
            for item_id in header_bom_to_delete:
                try:
                    bom_pool.unlink(cr, uid, item_id, context=context)
                except:
                    pass # error deleting bom

            for item_id in component_bom_to_delete:
                try:
                    bom_pool.unlink(cr, uid, item_id, context=context)
                except:
                    pass # error deleting bom
            '''

            _logger.info('End importation: Total: %s'%(counter))
        except:
             _logger.error('Error import mrp.bom [%s]'%(sys.exc_info(),)) 
             return #raise
        

        return

    _columns = {
        'is_primary': fields.boolean('is primary'),
        # override:
        'product_qty': fields.float('Product Quantity', digits=(8,6)),  
        #dp.get_precision('Product Unit of Measure')),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
