#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib
import csv
import sys
import time
import string
from mx.DateTime import now
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
user = 'admin'
pwd = '30mcrt983'
dbname = 'laserbs60restore' 
server = '192.168.100.70'
port = '8069'
separator=';'

header_lines=1      # number of line to jump
domain='SC'
prefix=domain + '-T2.' # Letf part of the code (added to the code ID)
Current_Office="C.F.P."
Function_job="Docente"

# Start main code *************************************************************
def CheckParameters(total,error):
    if len(sys.argv)!=2 :
       print """
             *** Syntax Error! ***
             *  Use the command with this syntax: python ./nome_file.py nome_file.csv
             *********************
             """ 
    sys.exit()

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0} # tot negative (jump N lines)

error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               # CSV file data columns:
               csv_i=0
               ref = prefix + line[csv_i]         # ID ref with prefix
               csv_i+=1
               fiscal_id_code = Prepare(line[csv_i]).upper() or ''
               csv_i+=1
               last_name=Prepare(line[csv_i]).title()
               csv_i+=1
               first_name=Prepare(line[csv_i]).title()
               csv_i+=1
               birthdate=PrepareDate(line[csv_i])
               csv_i+=1
               birthplace=Prepare(line[csv_i]).title() 
               csv_i+=1
               birthprov=Prepare(line[csv_i]).upper() 
               csv_i+=1
               city = Prepare(line[csv_i]).title() or ''
               csv_i+=1
               prov = Prepare(line[csv_i]).upper() or ''
               csv_i+=1
               zipcode = Prepare(line[csv_i])
               csv_i+=1
               address = Prepare(line[csv_i]).title() or ''
               csv_i+=1
               address_number = Prepare(line[csv_i]) or ''
               csv_i+=1
               phone = Prepare(line[csv_i]) 
               csv_i+=1
               mobile = Prepare(line[csv_i]) 
               csv_i+=1
               email = Prepare(line[csv_i]).lower()

               # Calculated fields:    
               supplier=True
               customer=False # True
               street=address + ", " + address_number  
               name=last_name + " " + first_name
               birthplace+=" ("+ birthprov + ")"
               city+=" ("+ prov + ")"
               type_address='default'    # TODO decide if invoice or defaulf (even for update...)
               office_id=CreateOffice(sock,dbname,uid,pwd,Current_Office) # get ID of office
               lang_id=getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")
               # Country?

               # Default data dictionary (to insert / update)
               data={'active': True,
                     'name': name,
                     'fiscal_id_code': fiscal_id_code, 
                     'customer': customer,
                     'supplier': supplier,
                     'office_id': office_id,
                     'phone': phone,
                     'email': email, 
                     'lang_id': lang_id,
                     #'category_id': [(6,0,[category_id])], # m2m
                     #'comment': comment, # TODO create list of "province" / "regioni"
                     #'user_id': user_id_modify, 
                    }
               data_address={'city': city, # modify first import address
                             'zip': zipcode, 
                             #'country_id': country_id[0], 
                             'phone': phone,
                             'street': street, 
                             #'email': email
                             'type': type_address,
                            }    
               data_contact={'name': last_name,
                             'first_name': first_name,
                             'birthdate': birthdate,
                             'birthplace': birthplace,
                             'office_id': office_id, 
                             'mobile': mobile,
                             'email': email, 
                             'lang_id': lang_id,
                             #'gender': sex_id,    'fiscal_id_code': fiscalcode,'title_school_id':studysheet_id,'disadvantage': disadvantage,'title_profstatus_id': title_profstatus_id,
                             #'study_broken_year': study_broken_year,'study_broken': study_broken,'comment': comment,
                             }

               # CONTACT CREATION
               item_contact = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', [('import', '=', ref)])
               if item_contact: # test if partner already exists (import = ref) UPDATE:
                  sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', item_contact, data_contact)
                  item_contact_id=item_contact[0]
               else:           
                  data_contact['import'], data_contact['domain']= ref, domain  # Extra data (in insert but not in update)
                  item_contact_id=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data_contact)

               # PARTNER CREATION (Partner + Address updated or new)
               error="Searching partner with ref"
               item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('import', '=', ref)])
               if item: # test if partner already exists (import = ref) UPDATE:
                  counter['upd'] += 1  
                  error="Updating partner information"
                  try:
                      # Update partner                                         
                      item_partner=sock.execute(dbname, uid, pwd, 'res.partner', 'read', [item[0]])
                      if item_partner[0]['address']: # has almost one address
                         default_address_id=0    
                         for addr in sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', item_partner[0]['address']): # for all address of partner
                             if addr['type']==type_address:
                                default_address_id=addr['id'] # get ID of first default
                                # if not exist job with address + contact, create                                
                                item_job_id=sock.execute(dbname, uid, pwd, 'res.partner.job', 'search', [('address_id', '=', default_address_id),('contact_id', '=', item_contact_id),])
                                if item_job_id:
                                   update_job=sock.execute(dbname, uid, pwd, 'res.partner.job', 'write', item_job_id[0], {'function': Function_job,})  
                                else:  
                                   create_job=sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', {'address_id': default_address_id,'contact_id': item_contact_id, 'function': Function_job})  
                                break # choose the first default address
                         if default_address_id: # so job + contact already creater
                            data['address']=[(1,default_address_id,data_address)]    # Update first default address
                         else: 
                            data_address['job_ids']=[(0,0,{'contact_id': item_contact_id,'function': Function_job})] # add job to address with linked contact
                            data['address']=[(0,0,data_address)]                     # Create new default address (has other address)
                      else: # no address for this partner
                         data_address['job_ids']=[(0,0,{'contact_id': item_contact_id,'function': Function_job})]  # add link to contact (new)
                         data['address']=[(0,0,data_address)]                                # Generate new address
                      item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (updare partner, address it depends, so job)
                  except:
                      print "[ERROR] Modifing data, current record:", data
                      raise 
                  print "[INFO]", counter['tot'], "Already exist: ", ref, name
               else:           
                  counter['new'] += 1  
                  error="Creating partner"
                  try:
                      # Create Partner (address, job)
                      data['import'], data['domain']= ref, domain  # Extra data (in insert but not in update)
                      data_address['job_ids']=[(0,0,{'contact_id': item_contact_id,'function': Function_job})]  # Create job in address
                      data['address']=[(0,0,data_address)]         # Generate new address
                      create_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                  except:
                      print "[ERROR] Intert data, current record:", data
                      raise                
                  print "[INFO]",counter['tot'], "Insert: ", ref, name
               
               # Create jobs:
               #data={'address_id':ins_id_address,'contact_id':ins_id_contact,}
               #ins_job_id = sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', data)
except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
