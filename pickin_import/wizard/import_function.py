# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#    ########################################################################
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import os
from openerp import tools


# General methods used in import function:
def _get_default_folder(history):
    ''' Return default document folder depend on type of document            
    '''
    # TODO parametrize folder path on company 
    if history: 
       return tools.config['addons_path'] + "/pickin_import/files/parsed/bf/"
    else:   
       return tools.config['addons_path'] + "/pickin_import/files/"

def _is_document_file(path, file_name, direction_in):
    ''' Return test if the file name is to import
                                    TypeYear Customer  N.doc.Company
        direction_in = True >>  file=  BF 2012 501.000001 0701.MMI
        direction_in = False >> file=  BC 2012 501.000001 0701.MMI
                  
    '''
    # TODO parametrize file name extension/code doc.
    if direction_in:
       start_from = "BF"
    else:
       start_from = "BC"
    # TODO extra test for syntax??       
    return os.path.isfile(os.path.join(path, file_name)) and file_name[:2].upper() == start_from and file_name[-3:].upper() == "MMI"        

def _parse_file_name_saved(file_name):
    ''' Check if file is syntactically correct with this format:
                                    TypeYear Customer  N.doc.Company
        direction_in=True >>  file=  BF 2012 501.000001 0701.MMI
        direction_in=False >> file=  BC 2012 501.000001 0701.MMI
        
        Return file name in this format (number/year):
           NNNNN/YYYY  ex.: 12341/2012
           
        '''
    import parse_function
    
    parsed = file_name[3:-4].split(" ")
    if len(parsed) == 3:
       return "%s/%s" % (parsed[2], parsed[0])        
    return False

def _parse_file_name(self, cr, uid, file_name):
    ''' Check if file is syntactically correct with this format:
                                    TypeYear Customer  N.doc.Company
        direction_in = True >>  file=  BF 2012 501.000001 0701.MMI
        direction_in = False >> file=  BC 2012 501.000001 0701.MMI
        
        Return 3 extra information:
        year, partner_id, doc_number '''
    import parse_function
    
    direction_in = file_name[:2].upper()=='BF'
    parsed = file_name[3:-4].split(" ")
    if len(parsed) == 3:
       parsed[1] = parse_function.get_partner_supplier(self, cr, uid, parsed[1], direction_in)
       return parsed 
       
    return False,False,False # error

def is_product_coal(self, cr, uid, product_id, context=None):
    ''' Return test on product passed, True if is a coal else false
    '''    
    return self.pool.get("product.product").browse(cr, uid, product_id).is_coal
    
def _exist_openerp_document(self, cr, uid, ids, direction_in, file_name, context=None):
    ''' Test if there's a store.picking with same partner, year, number and type
        return True or False depends on this test (True=Exists)
    '''
    year, partner_id, doc_number = _parse_file_name(self, cr, uid, file_name)
    
    # TODO manage error parsing file!
    pick_ids=self.pool.get("stock.picking").search(cr,uid,[
        ('type', '=', 'in' if direction_in else 'out'),
        ('partner_id', '=', partner_id),
        ('import_document', '=', _parse_file_name_saved(file_name)),
    ])
    if pick_ids: # exist document
        return True
    return False 
        
def load_file_2_field(self, cr, uid, ids, context=None):
    ''' Procedure that read default folder parse file name and select, depend on
        direction, the correct file and create record line in the wizard for
        future import
    '''
    import os, time

    wiz_proxy = self.browse(cr, uid, ids[0])
    direction_in = wiz_proxy.direction_in

    # delete lines if presents (for change in and out)
    line_ids = self.pool.get("picking.import.wizard.file").search(cr,uid,[('wizard_id','=',ids[0])])            
    line_delete = self.pool.get("picking.import.wizard.file").unlink(cr,uid,line_ids)            
    
    path =_get_default_folder(False)
    path_history =_get_default_folder(True)
    
    for file_name in os.listdir(path):
        full_name = os.path.join(path, file_name)
        if _is_document_file(path, file_name, direction_in):
           # Create record line of the wizard
           exist = _exist_openerp_document(self, cr, uid, ids, direction_in, file_name, context=None) # TODO test the DB for this BF
           line_delete=self.pool.get("picking.import.wizard.file").unlink(cr,uid,line_ids)           

           try:
              month = {"Gen":1, "Feb":2, "Mar":3, "Apr":4, "Mag":5, "Giu":6, "Lug":7, "Ago":8, "Set":9, "Ott":10, "Nov":11, "Dic":12,
                       "Jan":1                           , "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}
              c_date = time.ctime(os.path.getctime(full_name))
              c_date_string = "%4d-%02d-%02d %02d:%02d:%02d" % (
                  int(c_date[-4:]), month[c_date[4:7]], int(c_date[8:10]), int(c_date[11:13]), int(c_date[14:16]), int(c_date[17:19]),)
           except: # RAISE error?
              create_date_string =  False # NOTE problem for test BC document!!
              
           record_data={
               'name': file_name,
               'path': path,
               'path_history': path_history,
               'full_name': full_name,
               'to_import': not exist,
               'exist': exist, 
               'date': c_date_string,
               'import_document': _parse_file_name_saved(file_name),
               'wizard_id': ids[0],
           }
           self.pool.get("picking.import.wizard.file").create(cr, uid, record_data)            
    return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

