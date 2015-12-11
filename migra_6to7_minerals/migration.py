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

from openerp.osv import osv, fields

class migration_server(osv.osv):
    ''' Migration server configuration
    ''' 
    _name = 'migration.server'
    _inherit = 'migration.server'
    
    # Scheduled action: ########################################################
    def schedule_etl_analysis_migrate(self, cr, uid, context=None):
        ''' Migrate all elements for Chemical Analysis
            Vers 6 >> Vers 7
            Case 1: 6 but not 7 > Create
            Case 2: 6 and 7     > Update
            Case 3: not 6 but 7 > Unlink
            Case 4: not present (not 6 and not 7) 
        '''
        import logging, sys, xmlrpclib
        _logger = logging.getLogger('migra_6to7_minerals')
        return True # TODO finire!                 
        mapper = self.pool.get('migration.mapping')
        
        #sock, v6_uid, parameters = self.get_xmlrpc(cr, uid, context=context)
        #elements_proxy = sock.execute(parameters.dbname, v6_uid, parameters.password, 'migration.agent', 'agent', query)
        try:
           # Elenco query da effettuare
           query = "select id, name, chemical_category_id, note, family from product_product_analysis_model;"
           query = "select name, symbol, model_id, min, max from product_product_analysis_line;"
           query = "select id, mode_id, need_analysis from product_product;"    
           query = """select name, date, quantity, quantity_lab1, quantity_lab2, quantity_lab3, code_lab1, code_lab2, code_lab3, prodlot_id, note, 
                      laboratory1_id, laboratory2_id, laboratory3_id from chemical_analysis;"""
           query = "select id, name, symbol, atomic from chemical_element;"
           
           
           import pdb; pdb.set_trace()           
           # chemical.product.category #########################################
           query = "select id, name, note from chemical_product_category;"
           pg_cursor = self.get_pg_cursor(cr, uid, context=context)
           pg_cursor.execute(query)      

           id_2_id = {}
           name_2_id = {}
           
           pool=self.pool.get('chemical.product.category')
           for item in pool.browse(cr, uid, pool.search(cr, uid, [])):
               name_2_id[item.name]=item.id
           
           for element in pg_cursor.fetchall(): # elements_proxy:
               try:
                   item_id = name_2_id.get(element[1],False)
                   if item_id:
                      pool.write(cr, uid, item_id, {'note': element[2]})
                      id_2_id[element[0]] = item_id
                   else:                     
                      id_2_id[element[0]] = pool.create(cr, uid, {'name': element[1],'note': element[2]})
               except:
                   _logger.error('Error import record in table: %s [%s]'%("chemical.product.category", sys.exc_info(),))
 
           return True
           # Create chemical.product.category.type #############################
           # Utility convert tables:
           item_v7_proxy=self.pool.get('chemical.product.category.type')
           chemical_product_category_type={}      # key=v6 value=v7
           map_chemical_product_category_type={}  # Conversion previous sync

           # get V.6 data from DB v6 via XMLRPC:
           mapper_ids=sock.execute(dbname, uid, pwd, 'chemical.product.category.type', 'search', [('name','=','chemical.product.category.type')])
           mapper_read = sock.execute(dbname, uid, pwd, 'chemical.product.category.type', 'read', mapper_ids)
           
           # get previous sync data with mapper for translation (and remove for delete element after)
           mapper_sync_ids = mapper.search(cr, uid, [('name','=','chemical.product.category.type')])
           for item in mapper.browse(cr, uid, mapperr_sync_ids):
               map_chemical_product_category_type[item.old_id] = map_chemical_product_category_type[item.new_id]
           
           # step 1. Update present element, Create new element from 6 to 7:
           for item in mapper_read:               
               if item['id'] in map_chemical_product_category_type: # Update
                  # Case 1:
                  # create item_v7_proxy
                  del map_chemical_product_category_type[item['id']] # remove element for test if in V6 is deleted
               else: # Create (and save mapped elements
                  # Case 2:
                  # update item_v7_proxy
                  pass
                  
           # delete extra elements:
           #Case 3:
           delete_list=[item.id for item in map_chemical_product_category_type]
           deletion=item_v7_proxy.unlink(cr, uid, delete_list)

           # Create Elements ###################################################
           
           # Create Model for Analysis #########################################
           
           # Create Lot product ################################################
           
           # Create Analysis form ############################################## 
           
           data = {'name': "",
                  }
                
           '''item = self.search(cr, uid, [('default_code', '=', ref)], context=context)
           if item: # update
              try:
                  modify_id = self.write(cr, uid, item, data, context=context)
                  product_id=item[0]
              except:
                  _logger.info("[ERROR] Modify product [%s]"%(sys.exc_info()[0],))

           else:           
               counter['new'] += 1  
               try:
                  product_id=self.create(cr, uid, data, context=context) 
               except:
                   _logger.info("[ERROR] Create product [%s]"%(sys.exc_info()[0],))


            _logger.info('End importation\n Counter: %s'%(counter))'''
        except:
            _logger.error('Error import analysis [%s]'%(sys.exc_info(),))
        return        
migration_server()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
