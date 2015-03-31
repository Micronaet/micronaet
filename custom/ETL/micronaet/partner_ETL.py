#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# TODO LIST:
# Test numero of colums, there are some cases that separator char is present in fields, ex: email@soc1.it; email@soc2.it in email address
# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os
from posta import *
from mx.DateTime import now
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
# DB config read
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/ETL/micronaet/openerp.cfg')]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
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

# Function ********************************************************************
def raise_error(text, file_name,error_type="E"):
    status_list={"E":"ERROR","I":"INFO","W":"WARNING","C":"COLUMN ERROR"}
    error_type=error_type.upper()
    if error_type not in status_list.keys():
       error_type="E" # if status non present, default is Error!

    text= "["+status_list[error_type]+"] " + text 
    print text
    file_name.write(text + "\n")                          
    return

# Start main code *************************************************************
if len(sys.argv)!=3 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./partner_ETL.py nome_file.csv c|s
         *********************
         """ 
   sys.exit()
else:
   if sys.argv[2].lower() in ('c','s','cd', 'sd'):
      mexal_type=sys.argv[2][0]  # parameter for future use
      if len(sys.argv[2])==2: # = "*d"
         mexal_destination=True
      else:
         mexal_destination=False

      header_lines=config.getint('csv','header_' + mexal_type) # number of line to jump
   else:
      print """
            *** Syntax Error! ***
            *  Use the command with this syntax: python ./partner_ETL.py nome_file.csv c|s|cd|sd
                                                                           check this  ^^^^^^^^^    
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
counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} # tot negative (jump N lines)

# Open file log error (if verbose mail the file are sent to admin email)
try: 
   out_file = open(smtp_log,"w")
except:
   print "[WARNING]","Error creating log files:", smtp_log
   # No raise as it'a a warning

error=''
tot_colonne=0
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              raise_error("Colonne presenti: %d" % (tot_colonne),out_file,"I")
           if len(line): # jump empty lines
               if tot_colonne == len(line): # tot colums equal to column first line
                   counter['tot']+=1 
                   error="Importing line" 
                   # CSV file data columns:
                   # Mapping fields, from CVS to program variable
                   # res.partner data *********************
                   csv_id=0
                   ref = Prepare(line[csv_id])
                   csv_id+=1
                   name = Prepare(line[csv_id]).title()
                   csv_id+=1
                   first_name=Prepare(line[csv_id]).title() or ''
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
                   type_CEI = Prepare(line[csv_id]).upper()   #  C | E | I 
                   csv_id+=1
                   #website = Prepare(line[12]).lower()       # not present!!!!
                   code = Prepare(line[csv_id]).upper()       # Verify "IT" 
                   csv_id+=1
                   private = Prepare(line[csv_id]).upper()=="S"  # (non used) S | N (True if S)
                   csv_id+=1
                   parent=Prepare(line[csv_id]) # ID parent partner of this destination
                   csv_id+=1
                   ref_agente=Prepare(line[csv_id]) or '' # ID agente
                   csv_id+=1
                   name_agente=Prepare(line[csv_id]).title() or ''
                   csv_id+=1
                   # TODO verify for suppliers and destination!!!
                   csv_id+=1 # jump pricelist field
                   discount=Prepare(line[csv_id])       # Discount, string to parse

                   if mexal_destination:  # TODO with ^ XOR
                      if not parent: # Destination have parent field
                         if verbose: print "[INFO]", "JUMPED (not a destination)",ref,name
                         continue # jump if is destination and record is c or s
                   else: # c or s 
                      if parent: 
                         if verbose: print "[INFO]", "JUMPED (not a client / supplier)",ref,name
                         continue # jump if is c or s but parent is present
     
                   # Calculated fields:    
                   if first_name: name+=" " + first_name
                   if prov: city+=" ("+ prov + ")"
                   type_address='default'  # TODO decide if invoice or defaulf (even for update...)
                   type_address_destination='delivery'

                   lang_id=getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")    # TODO check in country (for creation not for update)

                   # Default data dictionary (to insert / update)
                   data_address={'city': city, # modify first import address
                                 'zip': zipcode, 
                                 #'country_id': country_id[0], 
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
                             #'property_product_pricelist': pricelist_id,
                             #'discount_value': discount_parsed['value'],
                             #'discount_rates': discount_parsed['rates'],
                            }
                       if mexal_type=='c': 
                          data['customer']=True
                          if not mexal_destination:
                             data['code']=ref # Code is mexal code only for customers
                       elif mexal_type=='s':
                          data['supplier']=True

                       data_address['type']=type_address             # default
                   else:  # destination
                       data_address['mexal_' + mexal_type]= ref      # ID in address
                       data_address['type']= type_address_destination # delivery
                   
                   # PARTNER CREATION ***************
                   if not mexal_destination:  # partner creation only for c or s
                       error="Searching partner with ref"
                       item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_' + mexal_type, '=', ref)]) # search if there is an import
                       if not item: 
                          item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('vat', '=', vat)]) # search if there is a partner with same vat (c or f)

                       error_print="Partner not %s: [%s] %s (%s)"
                       if item: 
                          counter['upd'] += 1  
                          error="Updating partner"
                          try:
                              item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # (update partner)
                              partner_id=item[0] # save ID for address creation
                          except:
                              raise_error(error_print % ("modified",data['mexal_' + mexal_type],data['name'],data['vat']),out_file,"E")
                              counter['err_upd']+=1  
                              #raise # << don't stop import process
                          if verbose: print "[INFO]", counter['tot'], "Already exist: ", ref, name
                       else:           
                          counter['new'] += 1  
                          error="Creating partner"
                          try:
                              partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data) 
                          #except ValidateError:
                          #    print "[ERROR] Create partner, (record not writed)", data                          
                          except:
                              raise_error(error_print % ("created",data['mexal_c'],data['name'],data['vat']),out_file,"E")
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
    raise_error ('>>> Import interrupted! Line:' + str(counter['tot']),out_file,"E")
    if verbose_mail: 
      send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Address:", "Total line: ",counter['tot_add']," (imported: ",counter['new_add'],") (updated: ", counter['upd_add'], ")"
if counter['err'] or counter['err_upd']:
   raise_error("Error updating: %d  -  Error adding: %d" %(counter['err_upd'],counter['err']),out_file,"I")
   out_file.close() # close before sending file
   if verbose_mail: 
      send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)
else:
   out_file.close() # clos log file in case of no error

