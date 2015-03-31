#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# TODO LIST:
# Test numero of colums, there are some cases that separator char is present in fields, ex: email@soc1.it; email@soc2.it in email address
# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os
from mx.DateTime import now
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

verbose=eval(config.get('import_mode','verbose'))  # for info message

header_lines=1
domain="UD"
prefix=domain + '-T1.' # Letf part of the code (added to the code ID)
#actual_category=r"Ufficio doti / Apprendistato"
#actual_company="Laser"
Current_Office=r"Ufficio doti / Apprendistato"

# Function Override  (file is already UTF8)
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    #valore=valore.decode('cp1252')
    #valore=valore.encode('utf-8')
    return valore.strip()

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./partner_ETL.py nome_file.csv c|s
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
counter={'tot':-header_lines,'new':0,'upd':0,'err':0} # tot negative (jump N lines)

office_id=CreateOffice(sock,dbname,uid,pwd,Current_Office) 
            
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
               csv_id=0
               ref = Prepare(line[csv_id])
               csv_id+=1
               formation_type = Prepare(line[csv_id]).title()   # es.: formazione esterna
               csv_id+=1
               annuality=Prepare(line[csv_id])                  # es.: 1,2,3,4
               csv_id+=1
               pip_state = Prepare(line[csv_id]).title() or ''  # es.: Accettato, Bozza ...
               csv_id+=1
               pip_data = Prepare(line[csv_id]) or False        # format: dd/mm/yyyy
               csv_id+=1
               pip_number = Prepare(line[csv_id]).upper() or '' # LLNNNN
               csv_id+=1
               last_name = Prepare(line[csv_id]).title() or ''
               csv_id+=1
               first_name = Prepare(line[csv_id]).title() or ''
               csv_id+=1
               fiscal_code = Prepare(Prepare(line[csv_id])).upper() or ''  # Verify field
               csv_id+=1
               company = Prepare(line[csv_id]).title()
               csv_id+=1
               company_tutor = Prepare(line[csv_id]).title()   # referente aziendale >> remove (TUTOR)
               csv_id+=1
               phone = Prepare(line[csv_id])
               csv_id+=1
               fax = Prepare(line[csv_id]) 
               csv_id+=1
               email = Prepare(line[csv_id]).lower() 
               csv_id+=1
               street = Prepare(line[csv_id])  
               csv_id+=1
               zipcode = Prepare(line[csv_id])  
               csv_id+=1
               city = Prepare(line[csv_id])  
               csv_id+=1
               ccnl = Prepare(line[csv_id]).title()               # es.: Parrucchieri, Commercio    
               csv_id+=1
               recruitment_date = Prepare(line[csv_id]) or False   # format: dd/mm/yyyy 
               csv_id+=1
               mansione = Prepare(line[csv_id]).title()          
               csv_id+=1
               tutor = Prepare(line[csv_id]).title()              # Surname + Name      
               csv_id+=1
               tutor_cf = Prepare(line[csv_id]).upper() 
               csv_id+=1
               tutor_course = ("SI" == Prepare(line[csv_id]).upper())       #  SI | NO
               # MOD. BASE 1° ANNO - MODULO SPEC. 1° ANNO - MODULO SPEC. 1° ANNO - MOD. BASE 2° ANNO
               # MODULO SPEC. 2° ANNO - MODULO SPEC. 2° ANNO - MOD. BASE 3° ANNO - MOD. BASE 4° ANNO
               # Costo - Note
               csv_id+=9   # Attention + 10 <<<<
               cost = Prepare(line[csv_id])
               csv_id+=1
               comment = Prepare(line[csv_id])  # Contact comment

               # Calculated fields:    
               import_id= prefix + ref
               type_address='default'  # TODO decide if invoice or defaulf (even for update...)
               #if first_name: name=last_name + " " + first_name else: name=last_name 
               formation_id=CreateFormation(sock,dbname,uid,pwd,formation_type)      #res.partner.contact.formation 
               profile_id=CreateProfile(sock,dbname,uid,pwd,mansione)                #res.partner.contact.profile
               title_pip_state_id=CreatePIPstate(sock,dbname,uid,pwd,pip_state)      #res.partner.contact.pip
               title_ccnl_id=CreateCCNL(sock,dbname,uid,pwd,ccnl)                    #res.partner.contact.ccnl
               lang_id=getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")    # TODO check in country (for creation not for update)

               # Default data dictionary (to insert / update)
               data={'active': True,
                     'name': company,
                     'customer': True,              
                     'phone': phone,
                     'email': email, 
                     'lang_id': lang_id,       
                     'import': import_id,
                     'domain': domain,             
                     'number_employee': 0,   # fields not present in CSV
                     'pmi_company': False,   # fields not present in CSV
                     'office_id': office_id,
                    }

               data_address={'city': city, # modify first import address
                             'zip': zipcode, 
                             'street': street, 
                             #'country_id': country_id[0], 
                             'phone': phone,
                             'fax': fax,
                             #'email': email
                             #'type': type_address,
                             'type': type_address,
                             'domain': domain,             
                            }    

               data_contact={'name': last_name,
                             'first_name': first_name,
               #              'mobile': mobile,
               #              'email': email, 
                             'office_id': office_id,
                             'lang_id': lang_id,
                             'fiscal_id_code': fiscal_code, 
                             'import': import_id,
                             'domain': domain,             
                             'formation_id':formation_id,
                             'annuality': annuality,
                             'title_pip_state_id': title_pip_state_id,
                             'date': pip_data,
                             'pip_state': pip_number, 
                             'trainee_residence':'',
                             'trainee_location':'',
                             'title_ccnl_id': title_ccnl_id,
                             'recruitment_date': recruitment_date,
                             'cost': cost,
                             'tutor': tutor,
                             'tutor_fiscal_id_code' : tutor_cf,
                             'course_tutor': tutor_course,
                             'comment': comment,
                             'profile_id': profile_id,
                             'internal_ref': company_tutor,
                            }

               # PARTNER CREATION ***************
               item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('domain', '=', domain),('name','=',company),]) # search if there is an import
               if item: 
                  counter['upd'] += 1  
                  error="Updating partner"
                  try:
                      item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                      partner_id=item[0] # save ID for address creation
                      # Search address_id if there is a street with actual name
                      item_partner_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('partner_id', '=', partner_id),('street','=',street),])
                      if item_partner_address: 
                         address_id=item_partner_address[0] 
                      else: 
                         address_id=0   # Save ID for address creation / update
                  except:
                      print "[ERROR] Modify partner, (record not writed)", data                          
                      #raise  # for eliminate error creating partner with wrong VAT
                  if verbose: print "[INFO]", counter['tot'], "Update: ", ref, company
               else:           
                  counter['new'] += 1  
                  error="Creating partner"
                  try:
                      partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                      address_id=0 # for new record address is not yet created
                  except:
                      counter['err'] += 1  
                      print "[ERROR] Create partner, (record not writed)", data                          
                      #raise   # for eliminate error creating partner with wrong VAT
                  if verbose: print "[INFO]",counter['tot'], "Added: ", ref, company

               # ADDRESS CREATION ***************
               error="Searching address with ref" 
               if address_id:
                  error="Updating address"
                  try:
                      item_address_mod = sock.execute(dbname, uid, pwd, 'res.partner.address', 'write', address_id, data_address) # Update address data
                  except:
                      print "     [ERROR] Modifing address, current record:", data_address
                      raise 
               else:           
                  error="Creating address"
                  try:
                      data_address['partner_id']=partner_id # (only for creation)
                      address_id=sock.execute(dbname, uid, pwd, 'res.partner.address', 'create', data_address)                       
                  except:
                      print "     [ERROR] Insert data, current record:", data_address
                      raise                

               # CONTACT CREATION ***************
               error="Searching contact with ref"
               item_contact = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'search', [('import', '=', import_id),])
               if item_contact:
                  error="Updating contact"
                  try:
                      item_contact_mod = sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', item_contact, data_contact) 
                      contact_id=item_contact[0]
                  except:
                      print "     [ERROR] Modifing contact, current record:", data_contact
                      raise 
               else:           
                  error="Creating contact"
                  try:
                      contact_id=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data_contact) 
                  except:
                      print "     [ERROR] Insert contact, current record:", data_contact
                      raise                

               data_job={'address_id': address_id,
                         #'orientation','date_stop',
                         'contact_id': contact_id,
                         #'team_id','birthdate','contact_lastname','id','departments','date_start','state'
                         #'other','pricelist_id','email',
                         #'function', 'extension','external_matricule'
                         #'fax','contact_firstname','phone','sequence_partner','sequence_contact','name'                        
                        }

               # JOBS CREATION ***************
               error="Searching job ref"
               item_job = sock.execute(dbname, uid, pwd, 'res.partner.job', 'search', [('address_id', '=', address_id),('contact_id', '=', contact_id)])
               if item_job:
                  error="Updating job"
                  try:
                      item_job_mod = sock.execute(dbname, uid, pwd, 'res.partner.job', 'write', item_job, data_job) 
                  except:
                      print "     [ERROR] Modifing contact, current record:", data_job
                      raise 
               else:           
                  error="Creating job"
                  try:
                      job_id=sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', data_job) 
                  except:
                      print "     [ERROR] Insert contact, current record:", data_job
                      raise                

except:
    print '>>> [ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Partner importation:", "Total: ",counter['tot']," (updated: ",counter['upd'],"(new: ", counter['new'],"(errors: ", counter['err'], ")"
