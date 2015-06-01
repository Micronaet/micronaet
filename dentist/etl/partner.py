#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from posta import *
#from micronaet import *
#from ambulatorio import *

# Parameters:
cfg_file="/home/administrator/ETL/ambulatorio/openerp.cfg"
header_lines = 1 # riga di intestazione

# Start main code *************************************************************
if len(sys.argv) != 2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./partner.py F_ANAGRA.CSV
         *********************
         """ 
   sys.exit()
   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))  # for info message

# SMTP config read
smtp_server=config.get('smtp','server') 
verbose_mail=eval(config.get('smtp','verbose_mail'))  # for info mail
smtp_log=config.get('smtp','log_file') 
smtp_sender=config.get('smtp','sender') 
smtp_receiver=config.get('smtp','receiver') 
smtp_text=config.get('smtp','text') 
smtp_subject=config.get('smtp','subject') 

#file_name_pickle=config.get('dbaccess','file_name_pickle') # Pickle file name

# Start main code *************************************************************
# FUNCTION:
def prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:
       if valore: # TODO test correct date format
          return valore[:4] + "/" + valore[4:6] + "/" + valore[6:8]
    return False #time.strftime("%d/%m/%Y") (per gli altri casi)

def prepare_telephone(valore):
    valore=valore.strip()
    #import pdb; pdb.set_trace()
    valore=valore.replace("-","/").replace("_","/").replace(" ","").replace(".","/").replace("//","/")
    return valore

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

def getGID(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.groups', 'search', [('name', '=', name),])[0]

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} 

error=''
tot_colonne = 0

lang_id=getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")    # TODO check in country (for creation not for update)
#import pdb; pdb.set_trace()
gid=getGID(sock,dbname,uid,pwd,"Poliambulatory / Dentist annotation")
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              print "Colonne presenti: %d" % (tot_colonne)
           if len(line): # jump empty lines
               if tot_colonne == len(line): # tot colums equal to column first line
                   note_list={1:'',2:'',3:'',4:'',5:'',6:'',7:'',8:'',9:'',10:'',11:'',12:'',13:'',14:'',15:'',16:'',17:'',18:'',19:'',20:'',21:'',22:'',}
                   counter['tot']+=1 
                   error="Importing line" 
                   # res.partner data *********************
                   csv_id=0 #Codice
                   ref = prepare(line[csv_id]) 
                   csv_id+=1 # Datacompil
                   date_creation = prepare_date(line[csv_id]) or False
                   csv_id+=1 #Titolo
                   title = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Sesso
                   sex = prepare(line[csv_id]).lower() or False 
                   csv_id+=1 # Cognome
                   name = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Nome
                   first_name = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Genitore
                   parent= prepare(line[csv_id]).title() or False                
                   csv_id+=1 # Indirizzo
                   street = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Cap
                   zipcode = prepare(line[csv_id]) or False  
                   csv_id+=1 # Residenza
                   city = prepare(line[csv_id]).title() or False  
                   csv_id+=1 # Telefono
                   phone = prepare_telephone(line[csv_id]) or False  
                   csv_id+=1 # Codfisc
                   fiscal_id_code = prepare(line[csv_id]).upper() or False  # Verify field
                   csv_id+=1 # Datanasc
                   birth_date = prepare_date(line[csv_id]) or False
                   csv_id+=1 # Luogonasc
                   birth_city = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Provincia
                   birth_prov = prepare(line[csv_id]).upper() or False # TODO verificare
                   csv_id+=1 # Inviato (da)
                   send_from = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Codmedic
                   medic_code = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Assist
                   
                   csv_id+=1 # Listino
                   
                   csv_id+=1 # Odont
                   
                   csv_id+=1 # Nuovo
                   
                   csv_id+=1 # Annotaz1
                   note_list[1] = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Annotaz2
                   note_list[2] = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Annotaz3
                   note_list[3] = prepare(line[csv_id]).title() or False
                   csv_id+=1 # Annotaz4
                   note_list[4] = prepare(line[csv_id]).title() or False                   
                   csv_id+=1 # Gs
                   
                   # Allergie   ************* SPUNTE ***************************
                   csv_id+=1 
                   disease_allergie = prepare(line[csv_id]).upper()=="S"  # S/N o False
                   csv_id+=1 # Malapres
                   disease_pressure = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Malcardio
                   disease_cardio = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Malemo
                   disease_emo = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Malricamb
                   disease_ricamb = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Malnervose
                   disease_nerve = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Gravidan
                   disease_pregnant = prepare(line[csv_id]).upper()=="S" # S/N o False
                   csv_id+=1 # Malinfett 
                   disease_infectious = prepare(line[csv_id]).upper()=="S" # S/N o False                   
                   # ***********************************************************
                   csv_id+=1 # Note1
                   note_list[5] = prepare(line[csv_id]).title() or False                   
                   csv_id+=1 # Note2
                   note_list[6] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Note3
                   note_list[7] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Note4
                   note_list[8] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Farminsom1
                   note_list[9] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Farminsom2
                   note_list[10] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Farminsom3
                   note_list[11] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Contro1
                   note_list[12] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Contro2
                   note_list[13] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Contro3
                   note_list[14] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Annota1
                   note_list[15] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Annota2
                   note_list[16] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Annota3
                   note_list[17] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Annota4
                   note_list[18] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Annocrea
                   
                   csv_id+=1 # Imp prev  ***********  SALDI CALCOLATI  *********
                   
                   csv_id+=1 # Imp eseg
                   
                   csv_id+=1 # Imp acco
                   
                   csv_id+=1 # Imp sald
                   
                   csv_id+=1 # Imp scon
                   
                   csv_id+=1 # Imp res  ****************************************
                   
                   csv_id+=1 # Professio
                   professione = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Tipo viso  ********** CAMPI VUOTI ***************
                   
                   csv_id+=1 # Colordent
                   
                   csv_id+=1 # Superfdent
                   
                   csv_id+=1 # Lucentezza
                   
                   csv_id+=1 # Altridisp1
                   
                   csv_id+=1 # Altridisp2
                   
                   csv_id+=1 # Allegati1
                   
                   csv_id+=1 # Allegati2
                   
                   csv_id+=1 # Allerg acc
                   
                   csv_id+=1 # Allerg pre
                   
                   csv_id+=1 # Malattinf
                   
                   csv_id+=1 # Problemi
                   
                   csv_id+=1 # Difficolta
                   
                   csv_id+=1 # Noteagg1
                   note_list[19] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Noteagg2
                   note_list[20] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Noteagg3
                   note_list[21] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Noteagg4
                   note_list[22] = prepare(line[csv_id]).title() or False                                      
                   csv_id+=1 # Multilist  **************************************
                   
                   # Campi calcolati:
                   # TODO identificare il telefono se è un cellulare per portarlo direttamente nel campo giusto
                   type_address='default'  # TODO decide if invoice or defaulf (even for update...)
                   if zipcode:
                      zipcode= "0"*(5-len(zipcode)) + zipcode

                   # Default data dictionary (to insert / update)
                   data_address={'city': city, # modify first import address
                                 'zip': zipcode, 
                                 #'country_id': getCountryFromCode(sock,dbname,uid,pwd,country_international_code), 
                                 'phone': phone,
                                 #'fax': fax,
                                 'street': street, 
                                 #'email': email,
                                 #'type': type_address,
                                 #'import': True,
                                 'type': type_address,
                                 }    
                                 
                   data={'first_name': first_name, # Nome
                         'last_name': name,  # Cognome
                         'ref':ref,
                         'fiscal_id_code': fiscal_id_code, 
                         'phone': phone,
                         #'email': email, 
                         'lang_id': lang_id,
                         #'vat': vat,
                         #'property_product_pricelist': pricelist_id,
                         #'property_account_position': fiscal_position,
                         'customer': True,
                         'supplier':False,
                         'is_patient': True, # per questa importazione per forza
                         'sex': sex,
                         'send_from': send_from,
                         'profession': professione,
                         # Birth 
                         'dob': birth_date,
                         'lob': birth_city,
                         'pob': birth_prov,
                         'date_creation': date_creation,
                         
                         # Disease checkbox:
                         'disease_allergie': disease_allergie,
                         'disease_pressure': disease_pressure,
                         'disease_cardio': disease_cardio,
                         'disease_emo': disease_emo,
                         'disease_ricamb': disease_ricamb,
                         'disease_nerve': disease_nerve,
                         'disease_pregnant': disease_pregnant,
                         'disease_infectious': disease_infectious,
                         }
                   
                   # PARTNER CREATION ***************
                   error="Searching partner with ref"
                   item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', ref)]) # search if there is an import

                   error_print="Partner not %s: [%s] %s (%s)"
                   if item: # UPDATE:
                      counter['upd'] += 1  
                      error="Updating partner"
                      try:
                          item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                          partner_id=item[0] # save ID for address creation
                      except:
                          print "[ERR] modified", ref, data['last_name']
                          counter['err_upd']+=1  
                          #raise # << don't stop import process
 
                      if verbose: print "[INFO]", counter['tot'], "Already exist: ", ref, name
                   else: # NEW:
                      counter['new'] += 1  
                      error="Creating partner"
                      try:
                          partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                      except:
                          print "[ERR] created", ref, data['last_name']
                          counter['err']+= 1  

                      if verbose: 
                         print "[INFO]", counter['tot'], "Insert: ", ref, name
                   
                   if not partner_id:  
                      print 'No partner [%s] rif: "%s" << [%s] ' % (mexal_type, ref, parent)
                      continue # next record

                   # ADDRESS CREATION ***************
                   error="Searching address with ref"
                   item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('type', '=', type_address),('partner_id','=',partner_id)])
                   counter['tot_add']+=1
                   if item_address: # UPDATE
                      counter['upd_add'] += 1  
                      error="Updating address"
                      try:
                          item_address_mod = sock.execute(dbname, uid, pwd, 'res.partner.address', 'write', item_address, data_address) 
                      except:
                          print "     [ERROR] Modifing address, current record:", data_address
                          raise # eliminate but raise log error
                      if verbose: 
                         print "     [INFO]", counter['tot_add'], "Already exist address: ", ref, name
                         
                   else: # NEW
                      counter['new_add'] += 1  
                      error="Creating address"
                      try:
                          data_address['partner_id']=partner_id # (only for creation)
                          item_address_new=sock.execute(dbname, uid, pwd, 'res.partner.address', 'create', data_address) 
                      except:
                          print "[ERR] Insert data, current record:", str(data)
                      if verbose: 
                         print "     [INFO]", counter['tot_add'], "Insert: ", ref, name

                   # ANNOTATION CREATION ***************
                   error="Creating notes"
                   
                   for i in range(1,23): 
                       if not note_list[i]:
                          continue
                          
                       #import pdb; pdb.set_trace()                          
                       # se invece esiste:   
                       data_note={'name': note_list[i],
                                  'user_id': 1, # admin
                                  'import': i,
                                  'partner_id': partner_id,
                                  'group_id': gid,
                                 }
                       if i in range(9,12): # Farmaci
                          data_note['type']='farmacology'
                       elif i in range(12,15): # Controindicazioni
                          data_note['type']='controindications'
                       else:   
                          data_note['type']='info'
                          
                       note_item = sock.execute(dbname, uid, pwd, 'dentist.annotation', 'search', [('import', '=', i),('partner_id','=',partner_id)])
                          
                       if note_item: # update: # TODO only for initials import!!!
                          try:
                             write_note_item = sock.execute(dbname, uid, pwd, 'dentist.annotation', 'write', note_item[0], data_note)
                             print "[INFO] Modify annotation, current record:", str(data_note)
                          except:
                             print "     [ERROR] Modifing annotation, current record:", name, data_note
                             raise # eliminate but raise log error
                       else: #new
                          try:
                             create_note_item = sock.execute(dbname, uid, pwd, 'dentist.annotation', 'create', data_note)
                             print "[INFO] Insert annotation, current record:", str(data_note)
                          except:
                             print "     [ERROR] Creating annotation, current record:", name, data_note
                             raise # eliminate but raise log error
                          

               else: # Errore totale colonne
                   counter['err']+=1
                   print '[ERR] Line %d (sep.: "%s"), %s)'%(counter['tot'] + 1 ,separator, line[0].strip() + " " +line[1].strip())
except:
    print '[ERR] >>> Import interrupted! Line:' + str(counter['tot'])
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Address:", "Total line: ",counter['tot_add']," (imported: ",counter['new_add'],") (updated: ", counter['upd_add'], ")"

