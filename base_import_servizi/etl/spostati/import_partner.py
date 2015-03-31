#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
#from pyExcelerator import *
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from parse_function import *

# Parameters:
path_file=os.path.expanduser("~/ETL/servizi/")
file_csv=os.path.expanduser("~/ETL/servizi/partner.csv")

cfg_file=path_file + "openerp.cfg"
header_lines = 0 # riga di intestazione

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

# Start main code *************************************************************
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

lines = csv.reader(open(file_csv,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} 

error=''
tot_colonne=0
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              print "Colonne presenti: %d" % (tot_colonne)
           if len(line): # jump empty lines
               if tot_colonne == len(line):
                   counter['tot']+=1 
                   error="Importing line" 
                   csv_id=0
                   ref = prepare(line[csv_id])
                   csv_id+=1
                   name = prepare(line[csv_id]).title()
                   csv_id+=1
                   first_name=prepare(line[csv_id]).title() or ''
                   csv_id+=1
                   street = prepare(line[csv_id]).title() or ''
                   csv_id+=1
                   zipcode = prepare(line[csv_id])
                   csv_id+=1
                   city = prepare(line[csv_id]).title() or ''
                   csv_id+=1
                   prov = prepare(line[csv_id]).upper() or ''
                   csv_id+=1
                   phone = prepare(line[csv_id])
                   csv_id+=1
                   fax = prepare(line[csv_id])
                   csv_id+=1
                   email = prepare(line[csv_id]).lower() or ''
                   csv_id+=1
                   fiscal_code = prepare(line[csv_id]).upper() or ''  # Verify field
                   csv_id+=1
                   vat = prepare(line[csv_id]).upper()        # IT* format   (checked ??)
                   csv_id+=1
                   type_CEI = prepare(line[csv_id]).lower()   #  C | E | I 
                   csv_id+=1
                   #website = prepare(line[12]).lower()       # not present!!!!
                   code = prepare(line[csv_id]).upper()       # Verify "IT" 
                   csv_id+=1
                   private = prepare(line[csv_id]).upper()=="S"  # (non used) S | N (True if S)
                   csv_id+=1
                   parent=prepare(line[csv_id]) # ID parent partner of this destination
                   csv_id+=1
                   ref_agente=prepare(line[csv_id]) or '' # ID agente
                   csv_id+=1
                   name_agente=prepare(line[csv_id]).title() or ''
                   csv_id+=1
                   # TODO verify for suppliers and destination!!!
                   if (mexal_type.lower()=='c') and (not mexal_destination): # Pricelist only present for client TODO not destination
                      if prepare(line[csv_id]):
                         pricelist_mexal_id=eval(prepare(line[csv_id]))   # ID of mexal pricelist
                         if type(pricelist_mexal_id)!=type(0):
                            pricelist_mexal_id=0
                            print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Error converting",prepare(line[csv_id])
                      else:
                         pricelist_mexal_id=0 
                   else:
                      pricelist_mexal_id=0
                   csv_id+=1
                   discount=prepare(line[csv_id])       # Discount, string to parse
                   if discount: # per problemi nella stampa del modulo!
                      discount=discount.replace("+", "+ ") # Metto uno spazio dopo il più
                      discount=discount.replace("  ", " ") # Se c'era già tolgo il doppio spazio 
                   csv_id+=1
                   esention_code=prepare(line[csv_id])    # Codice esenzione IVA (se presente allora è esente)
                   csv_id+=1
                   country_international_code=prepare(line[csv_id]).upper()    # Codice Nazione
                   # Fido:
                   csv_id+=1
                   fido_total = prepareFloat(line[csv_id])   # Importo fido
                   csv_id+=1
                   fido_date = prepare_date(line[csv_id])    # Data ottenimento fido
                   csv_id+=1
                   fido_ko=('x' == prepare(line[csv_id]))    # X se ha perso il fido
                   csv_id+=1
                   # ID Zona
                   csv_id+=1
                   zone = prepare(line[csv_id])              # zona del cliente
                   zone_id=get_zona(sock, dbname, uid, pwd, zone)
                   if azienda=="fiam":  # solo per fiam la gestione della categoria
                       csv_id+=1
                       # ID Categoria
                       csv_id+=1
                       category = prepare(line[csv_id])              # categoria statistica cliente
                       category_id=get_statistic_category(sock, dbname, uid, pwd, category)                    
                       csv_id+=1
                       ddt_e_oc = PrepareFloat(line[csv_id])              # saldo contabile OC + DDT aperti
                       
                   if pricelist_mexal_id in range(1,10): # mexal ID go from 1 to 9
                      if ref in client_list: # Create Particular PL for client (or update)
                         result={} 
                         GetPricelist(sock, dbname, uid, pwd, ref, pricelist_mexal_id, pricelist_fiam_id[pricelist_mexal_id], result) # 2 returned values in dict
                         pricelist_id=result['pricelist']
                      else: # Link to standard PL version
                         pricelist_id=pricelist_fiam_id[pricelist_mexal_id]
                   else:
                      pricelist_id=0
     
                   discount_parsed=ParseDiscount(discount)               
                      
                   if mexal_destination:  # TODO with ^ XOR
                      if not parent: # Destination have parent field
                         if verbose: print "[INFO]", "JUMPED (not a destination)",ref,name
                         continue # jump if is destination and record is c or s
                   else: # c or s 
                      if parent: 
                         if verbose: print "[INFO]", "JUMPED (not a client / supplier)",ref,name
                         continue # jump if is c or s but parent is present
     
                   if type_CEI in ('c','e','i','v','r',):
                      if type_CEI in ('v','r',):
                         type_CEI='e' # Vaticano and RSM are extra CEE
                      fiscal_position=fiscal_position_list[type_CEI]
                   else:
                      fiscal_position=False
                      raise_error("Campo C, E, I contiene dati non conformi:" + ref, out_file, "E")

                   # Calculated fields:    
                   if first_name: name+=" " + first_name
                   if prov: city+=" ("+ prov + ")"
                   type_address='default'  # TODO decide if invoice or defaulf (even for update...)
                   type_address_destination='delivery'

                   lang_id=getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")    # TODO check in country (for creation not for update)

                   # Default data dictionary (to insert / update)
                   data_address={'city': city, # modify first import address
                                 'zip': zipcode, 
                                 'country_id': getCountryFromCode(sock,dbname,uid,pwd,country_international_code), 
                                 'phone': phone,
                                 'fax': fax,
                                 'street': street, 
                                 #'email': email
                                 #'type': type_address,
                                 'import': True,
                                }    
                   if not mexal_destination: # create partner only with c or s
                       data={'name': name,
                             'fiscal_id_code': fiscal_code, 
                             'phone': phone,
                             'email': email, 
                             'lang_id': lang_id,
                             'vat': vat,
                             #'category_id': [(6,0,[category_id])], # m2m
                             #'comment': comment, # TODO create list of "province" / "regioni"
                             'mexal_' + mexal_type : ref,
                             'discount_value': discount_parsed['value'],
                             'discount_rates': discount_parsed['rates'],                             
                             'import': True,                    
                             'fido_total': fido_total,
                             'fido_date': fido_date,
                             'fido_ko': fido_ko,  
                             'zone_id': zone_id, 
                             }
                       if azienda=="fiam" and mexal_type=='c':  # Per ora solo per la fiam
                          data['statistic_category_id']= category_id
                       if mexal_type=='c': # and not destination!                       
                          data['property_product_pricelist']= pricelist_id  
                          data['property_account_position']= fiscal_position
                          data['customer']=True
                          data['ref']=ref
                          data['type_cei']=type_CEI
                          data['ddt_e_oc_c']=ddt_e_oc
                       if mexal_type=='s': 
                          data['supplier']=True
                          data['ddt_e_oc_s']=ddt_e_oc

                       data_address['type']=type_address  # default
                   else:  # destination
                       data_address['mexal_' + mexal_type]= ref      # ID in address
                       data_address['type']= type_address_destination # delivery
                   
                   # PARTNER CREATION ***************
                   if not mexal_destination:  # partner creation only for c or s
                       error="Searching partner with ref"
                       item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + mexal_type, '=', ref)]) # search if there is an import
                       if (not item): # partner not found with mexal_c, try with vat  <<<< TODO problem 2 client with same vat!!!
                          if vat:
                             item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('vat', '=', vat),('mexal_' + mexal_type, '=', False)]) # search if there is a partner with same vat (c or f)
                             if not item and mexal_type=="s":
                                data['customer']=False
                          else:
                             if mexal_type=="s":
                                data['customer']=False

                       error_print="Partner not %s: [%s] %s (%s)"
                       if item: # modify
                          counter['upd'] += 1  
                          error="Updating partner"
                          try:
                              item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                              partner_id=item[0] # save ID for address creation
                          except:
                              try: 
                                 del data['vat']    
                                 item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                                 partner_id=item[0] # save ID for address creation
                              except: 
                                 raise_error(error_print % ("modified", data['mexal_' + mexal_type], data['name'], ""), out_file, "E")
                                 counter['err_upd']+=1  
                                 #raise # << don't stop import process

                          if verbose: print "[INFO]", counter['tot'], "Already exist: ", ref, name
                       else: # create
                          counter['new'] += 1  
                          error="Creating partner"
                          try:
                              partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                              #except ValidateError:
                              #   print "[ERROR] Create partner, (record not writed)", data                          
                          except:
                              try: 
                                 del data['vat']    
                                 partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                              except: 
                                 raise_error(error_print % ("created",data['mexal_' + mexal_type],data['name'], ""), out_file, "E")
                                 counter['err']+= 1  
                                 #raise # << don't stop import process

                          if verbose: print "[INFO]", counter['tot'], "Insert: ", ref, name
                   else: # destination
                       partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + mexal_type, '=', parent),])
                       if partner_id: 
                          #print "**", partner_id
                          partner_id=partner_id[0] # only the first
                          
                   
                   if not partner_id:  
                      raise_error('No partner [%s] rif: "%s" << [%s] ' % (mexal_type, ref, parent),out_file,"E")
                      continue # next record

                   # ADDRESS CREATION ***************
                   error="Searching address with ref"
                   if mexal_destination:   
                      item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('import', '=', 'true'),('type', '=', type_address_destination),('mexal_' + mexal_type, '=', ref)]) # TODO error (double dest if c or s)
                   else:   
                      item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('import', '=', 'true'),('type', '=', type_address),('partner_id','=',partner_id)])
                   counter['tot_add']+=1

                   if item_address:
                      counter['upd_add'] += 1  
                      error="Updating address"
                      try:
                          item_address_mod = sock.execute(dbname, uid, pwd, 'res.partner.address', 'write', item_address, data_address) 
                      except:
                          print "     [ERROR] Modifing address, current record:", data_address
                          raise # eliminate but raise log error
                      if verbose: print "     [INFO]", counter['tot_add'], "Already exist address: ", ref, name
                   else:           
                      counter['new_add'] += 1  
                      error="Creating address"
                      try:
                          data_address['partner_id']=partner_id # (only for creation)
                          item_address_new=sock.execute(dbname, uid, pwd, 'res.partner.address', 'create', data_address) 
                      except:
                          raise_error("Insert data, current record:" + str(data),out_file,"E")
                      if verbose: print "     [INFO]",counter['tot_add'], "Insert: ", ref, name
               else: # wrong column number
                   counter['err']+=1
                   raise_error('Line %d (sep.: "%s"), %s)' % (counter['tot'] + 1 ,separator, line[0].strip() + " " +line[1].strip()),out_file,"C")
except:
    print '>>> Import interrupted! Line:' + str(counter['tot'])
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Address:", "Total line: ",counter['tot_add']," (imported: ",counter['new_add'],") (updated: ", counter['upd_add'], ")"

if counter['err'] or counter['err_upd']:
   print "Error updating: %d  -  Error adding: %d" %(counter['err_upd'],counter['err'])

