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


from osv import osv, fields
# Utility: #####################################################################

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def PrepareFloat(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values
       
def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()

def getCountryFromCode(sock,dbname,uid,pwd,code):
    if code: 
       find_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('code', '=', code),]) 
       if find_id: 
          return find_id[0] 
       else: 
          return False # TODO segnalare la mancanza della sigla
    else:
       return False # no code


def ShortCut(valore=''): 
    # used for code the title (partner or contact), ex.: Sig.ra > SIGRA
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore

def getTaxID(sock,dbname,uid,pwd,description):
    # get ID of tax from description value
    return sock.execute(dbname, uid, pwd, 'account.tax', 'search', [('description', '=', description),])[0]

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

# PRODUCT
def getUomCateg(sock,dbname,uid,pwd,categ):
    # Create categ. for UOM
    cat_id = sock.execute(dbname, uid, pwd, 'product.uom.categ', 'search', [('name', '=', categ),]) 
    if len(cat_id): 
       return cat_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom.categ','create',{'name': categ,})  

def getUOM(sock,dbname,uid,pwd,name,data):
    # Create if not exist name: 'name' UOM with data: data{}
    uom_id = sock.execute(dbname, uid, pwd, 'product.uom', 'search', [('name', '=', name),]) 
    if len(uom_id): 
       return uom_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom','create',data)  

# PARTNER & CONTACT
def CreateTitle(sock,dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

class res_partner_extra_fields(osv.osv):
    ''' Import procedure for partner
    '''
    _name='res.partner'
    _inherit ='res.partner'

    # Scheduled action: ########################################################
    def schedule_etl_partner_import(self, cr, uid, path, file_name, file_name_supplier, log_file, context=None):
        ''' ETL operations for import partner in OpenERP (parameter setted up in
            scheduled action for file name
        '''
        import logging, os, csv
        
        import pdb; pdb.set_trace()
        verbose = True # TODO setup by program
        _logger = logging.getLogger('base_syncro_ecologia')
        
        def log(logger_funct, message_type, message, log_file):
            ''' Log function on OpenERP and on file
            '''
            logger_funct(message)
            log_file.write("[%s] %s\n"%(message_type, message))
            
        def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()
        # Create pool
        partner_pool=self.pool.get("res.partner")
        address_pool=self.pool.get("res.partner.address")

        # Init counter
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}
        mexal_types={'c': file_name, 'cd': file_name, 's': file_name_supplier,}

        # Log file
        log_file_name = os.path.expanduser(os.path.join(path, log_file))
        log_file=open(log_file_name,'w')
        
        try:
            for type_partner in mexal_types:
                row = 0 # reset counter row
                mexal_type=type_partner[:1]
                mexal_destination = (len(type_partner)==2) # 2 char=>destination
                
                file_name = os.path.expanduser(os.path.join(path, mexal_types.get(mexal_type)))
                lines = csv.reader(open(file_name,'rb'), delimiter = ";")

                tot_colonne=0
                for line in lines:
                    row += 1
                    if counter['tot'] < 0:  # jump n lines of header 
                       counter['tot'] += 1
                    else: 
                       if not tot_colonne:
                           tot_colonne=len(line)
                           log(_logger.info, 'info', "*"*100, log_file)
                           log(_logger.info, 'info', 'Start sync of partners type: %s [cols=%s, file=%s] %s'%(mexal_type, tot_colonne, file_name, "*"*5), log_file)
                           log(_logger.info, 'info', "*"*100, log_file)
                           
                       if len(line): # jump empty lines
                           if tot_colonne == len(line): # tot # of colums must be equal to # of column in first line
                               counter['tot'] += 1 
                               csv_id=0
                               ref = Prepare(line[csv_id])
                               csv_id+=1
                               name = Prepare(line[csv_id]).title()
                               csv_id+=1
                               first_name = Prepare(line[csv_id]).title() or ''
                               csv_id+=1
                               street = Prepare(line[csv_id]).title() or ''
                               csv_id+=1
                               zipcode = Prepare(line[csv_id])
                               csv_id+=1
                               city = Prepare(line[csv_id]).title() or ''
                               csv_id+=1
                               prov = Prepare(line[csv_id]).upper() or ''
                               csv_id+=1
                               phone = Prepare(line[csv_id])
                               csv_id+=1
                               fax = Prepare(line[csv_id])
                               csv_id+=1
                               email = Prepare(line[csv_id]).lower() or ''
                               csv_id+=1
                               fiscal_code = Prepare(Prepare(line[csv_id])).upper() or ''  # Verify field
                               csv_id+=1
                               vat = Prepare(line[csv_id]).upper()        # IT* format   (checked ??)
                               csv_id+=1
                               type_CEI = Prepare(line[csv_id]).lower()   #  C | E | I 
                               csv_id+=1
                               #website = Prepare(line[12]).lower()       # not present!!!!
                               code = Prepare(line[csv_id]).upper()       # Verify "IT" 
                               csv_id+=1
                               private = Prepare(line[csv_id]).upper()=="S"  # S | N (True if S)
                               csv_id+=1
                               parent=Prepare(line[csv_id]) # ID parent partner of this destination
                               csv_id+=1
                               ref_agente=Prepare(line[csv_id]) or '' # ID agente
                               csv_id+=1
                               name_agente=Prepare(line[csv_id]).title() or ''
                               csv_id+=1
                               csv_id+=1
                               discount=Prepare(line[csv_id])       # Discount, string to parse
                               csv_id+=1
                               esention_code= 0 #Prepare(line[csv_id])    # Codice esenzione IVA (se presente allora è esente)
                               csv_id+=1
                               country_international_code=code #Prepare(line[csv_id]).upper()    # Codice Nazione
                               csv_id+=1
                               # ID Categoria
                               csv_id+=1
                               category = Prepare(line[csv_id])              # categoria statistica cliente
                               #category_id=get_statistic_category(sock, dbname, uid, pwd, category)                    
       
                               if mexal_destination:  # TODO with ^ XOR
                                  if not parent: # Destination have parent field                       if verbose: print "[INFO]", "JUMPED (not a destination)",ref,name
                                     log(_logger.warning, 'warning', '[%s] Not a destination, jumped %s [File: %s]!'%(row, name, file_name,), log_file)                                     
                                     continue # jump if is destination and record is c or s
                               else: # c or s 
                                  if parent: 
                                     log(_logger.warning, 'warning', '[%s] Not a customer/supplier, type: %s, (no destination but parent setted up) [File: %s]!'%(row,mexal_type,file_name), log_file)                                     
                                     continue # jump if is c or s but parent is present
                 
                               if type_CEI in ('c','e','i','v','r',):
                                  if type_CEI in ('v','r',):
                                      type_CEI='e' # Vaticano and RSM are extra CEE
                                      
                               if type_CEI == "i":
                                   lang = "it_IT" #getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")   
                                   property_account_position = 1
                               else:
                                   lang = "en_US" #getLanguage(sock,dbname,uid,pwd,"English")
                                   if type_CEI == "c":
                                       property_account_position = 3
                                   elif type_CEI == "e":
                                       property_account_position = 2
                                   else:
                                       property_account_position = False
                                   
                               # Calculated fields:    
                               if first_name:
                                   name+=" " + first_name
                               if prov: 
                                   city+=" ("+ prov + ")"
                                   
                               if mexal_destination:
                                   type_address='delivery'
                               else:    
                                   type_address='default'  # TODO decide if invoice or defaulf (even for update...)
                               # supplier????
                               
                               if not mexal_destination: # Create partner 
                                   data={'name': name,
                                         'active': True,
                                         #'property_account_position': property_account_position,  # TODO parametrizzare
                                         #'phone': phone,
                                         #'email': email, 
                                         #'street': street,
                                         #'street2': street,
                                         #'zip': zipcode,
                                         #'city': city,
                                         #'is_company': True,
                                         #'employee': False,
                                         #'parent_id': False,
                                         'website': '',
                                         #'lang': lang,
                                         'vat': vat,
                                         #'vat_subject': not private,
                                         #'type_cei': type_CEI,
                                         #'category_id': [(6,0,[category_id])], # m2m
                                         #'comment': comment, # TODO create list of "province" / "regioni"
                                         'mexal_' + mexal_type : ref,
                                         #'discount_value': discount_parsed['value'],
                                         #'discount_rates': discount_parsed['rates'],                             
                                         'import': True,
                                        }
                                        
                                   if mexal_type=='c': # and not destination!
                                      data['ref']=ref
                                      data['customer']=True
                                      #data['property_account_position']= fiscal_position
                                   if mexal_type=='s':
                                      data['supplier']=True
                                  
                                   item = partner_pool.search(cr, uid, [('mexal_' + mexal_type, '=', ref)], context=context) # search if there is an import
                                   if not item: 
                                      if vat:
                                         item = partner_pool.search(cr, uid, [('vat', '=', vat)], context=context) # search if there is a partner with same vat (c or f)
                                      if not item and mexal_type=="s":
                                         data['customer']=False # If pass from here is: supplier and not customer
                                         
                                   if item: # update
                                      counter['upd'] += 1  
                                      try:
                                          item_mod = partner_pool.write(cr, uid, item, data, context=context) 
                                          partner_id=item[0] # save ID (remove?)
                                          if verbose:
                                              log(_logger.info, 'info', '[%s] Partner updated: [%s] %s! >> ID: %s'%(row, ref, name, partner_id), log_file)                                     
                                      except:
                                          try: # Riprovo a scrivere rimuovendo la vat
                                              del data['vat']    
                                              item_mod = partner_pool.write(cr, uid, item, data, context=context)
                                              partner_id=item[0] # save ID (remove?)
                                              if verbose:
                                                  log(_logger.warning, 'warning', '[%s] Partner updated (without vat): [%s] %s! >> ID: %s'%(row, ref, name, partner_id), log_file)                                                                                       
                                          except: 
                                              log(_logger.error, 'error', '[%s] Error update partner [%s] %s'%(row, ref, name), log_file)
                                              counter['err_upd']+=1
                                   else: # new
                                      counter['new'] += 1  
                                      try:
                                          partner_id = partner_pool.create(cr, uid, data)
                                          if verbose:
                                              log(_logger.info, 'info', '[%s] Partner created: [%s] %s! >> ID: %s'%(row, ref, name, partner_id), log_file)
                                      except:
                                          try: # Riprovo a scrivere rimuovendo la vat
                                              del data['vat']
                                              partner_id = partner_pool.create(cr, uid, data)
                                              if verbose:
                                                  log(_logger.warning, 'warning', '[%s] Partner created (without vat): [%s] %s! >> ID: %s'%(row, ref, name, partner_id), log_file)
                                          except: 
                                              log(_logger.error, 'error', '[%s] Error create partner ref: %s'%(row, ref), log_file)
                                              counter['err']+= 1  

                               if mexal_destination: # search partner_id for create address
                                   partner_id = partner_pool.search(cr, uid, [('mexal_' + mexal_type, '=', parent),])
                                   if partner_id: 
                                      partner_id=partner_id[0] # only the first
                                   else: # non necessary (yet tested)
                                       log(_logger.error, 'error', '[%s] No partner parent: %s for this destination: %s'%(row, parent, ref), log_file)
                                       continue
                                   
                               address_data = {
                                            'partner_id': partner_id,
                                            'type': type_address,
                                            #'function': fields.char('Function', size=64),
                                            #'title': fields.many2one('res.partner.title','Title'),
                                            #'name': fields.char('Contact Name', size=64, select=1),
                                            'street': street,
                                            #'street2': fields.char('Street2', size=128),
                                            'zip': zipcode,
                                            'city': city,
                                            #'state_id': fields.many2one("res.country.state", 'Fed. State', domain="[('country_id','=',country_id)]"),
                                            #'country_id': fields.many2one('res.country', 'Country'),
                                            'email': email,
                                            'phone': phone,
                                            'fax': fax,
                                            #'mobile': mobile
                                            #'birthdate': fields.char('Birthdate', size=64),
                                            #'is_customer_add': fields.related('partner_id', 'customer', type='boolean', string='Customer'),
                                            #'is_supplier_add': fields.related('partner_id', 'supplier', type='boolean', string='Supplier'),
                                            'active': True,                               
                                             }
                               address_data['mexal_' + mexal_type]= ref      # ID in address

                               if not partner_id:  
                                  log(_logger.error, 'error', '[%s] Error no partner ID: [%s] %s'%(row,ref, name), log_file)                                  
                                  continue # next record
                               try:
                                   address_id = address_pool.search(cr, uid, [('mexal_' + mexal_type,'=',ref),('type','=',type_address)])
                                   if address_id: # modify
                                       address_modify=address_pool.write(cr, uid, ids,  address_data)
                                       address_id=address_id[0]
                                       if verbose:
                                           log(_logger.info, 'info', "[%s]  >>  Address type '%s' updated: [%s] %s! >> ID: %s"%(row, type_address, ref, name, address_id), log_file)                                  
                                   else:
                                       address_id=address_pool.create(cr, uid,  address_data)
                                       if verbose:
                                           log(_logger.info, 'info', "[%s]  >>  Address type '%s' created: [%s] %s! >> ID: %s"%(row, type_address, ref, name, address_id), log_file)                                                                             
                               except:
                                   log(_logger.error, 'error', "[%s]  >>  Error creating address type '%s', ref: [%s] %s!"%(row, type_address, ref, name), log_file)
    
                           else: 
                               log(_logger.error, 'error', "[%s] Column error for line: %s"%(row, line,), log_file)
                               counter['err']+=1
                               
                log(_logger.info, 'info', '[%s] End sync of partner type of import: %s - Counter:%s'%(row, type_partner, counter), log_file)                 
            log_file.close()    
        except:
            log(_logger.error, 'error', 'Error scheduler operation during!', log_file)                                              

        return True
res_partner_extra_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
