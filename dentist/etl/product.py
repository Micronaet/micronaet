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
if len(sys.argv) != 3 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./prdocut.py F_CATEGO.CSV F_LISTIN.CSV 
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

# Function ********************************************************************
def raise_log(text, file_name,error_type="E"):
    status_list={"E":"ERROR","I":"INFO","W":"WARNING","C":"COLUMN ERROR"}
    error_type=error_type.upper()
    if error_type not in status_list.keys():
       error_type="E" # if status non present, default is Error!

    text= "["+status_list[error_type]+"] " + text 
    print text
    file_name.write(text + "\n")                          
    return

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

def prepare_float(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(".","").replace(",","."))
    else:
       return 0.0   # for empty values
       
def prepare_telephone(valore):
    valore=valore.strip()
    #import pdb; pdb.set_trace()
    valore=valore.replace("-","/").replace("_","/").replace(" ","").replace(".","/").replace("//","/")
    return valore

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
file_categorie = sys.argv[1]
file_listino = sys.argv[2]

# Open file log error (if verbose mail the file are sent to admin email)
try: 
   out_file = open(smtp_log,"w")
except:
   print "[WARNING]","Error creating log files:", smtp_log
   # No raise as it'a a warning

try:
    # Importazione categorie:
    lines = csv.reader(open(file_categorie,'rb'),delimiter=separator)
    counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} 
    error=''
    tot_colonne = 0

    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              raise_log("Colonne presenti: %d" % (tot_colonne),out_file,"I")
           if len(line): # jump empty lines
               if tot_colonne == len(line): # tot colums equal to column first line
                   counter['tot']+=1 
                   error="Importing line" 
                   # product.category *********************
                   csv_id=0 # Categoria
                   ref = prepare(line[csv_id]) 
                   csv_id+=1 # Descrizione
                   name = prepare(line[csv_id]).title() or False

                   # Default data dictionary (to insert / update)
                   data_categ={'code': ref,
                               'name': name,
                               'type': 'normal',                   
                              }    
                   
                   # CATGEGORY CREATION ***************
                   error="Searching partner with ref"
                   item = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('code', '=', ref)])

                   if item: # UPDATE:
                      counter['upd'] += 1  
                      try:
                          item_mod = sock.execute(dbname, uid, pwd, 'product.category', 'write', item, data_categ) 
                          category_id=item[0] 
                      except:
                          raise_log("Errore aggiornando %s"%(ref,), out_file, "E")
                          counter['err_upd']+=1  
 
                      if verbose: print "[INFO]", counter['tot'], "Already exist: ", ref, name
                   else: # NEW:
                      counter['new'] += 1  
                      try:
                          partner_id=sock.execute(dbname, uid, pwd, 'product.category', 'create', data_categ) 
                      except:
                          raise_log("Errore creando %s"%(ref,), out_file, "E")
                          counter['err']+= 1  
                          
                      if verbose: print "[INFO]", counter['tot'], "New: ", ref, name

               else: # Errore totale colonne
                   counter['err']+=1
                   raise_log('Line %d (sep.: "%s"), %s)' % (counter['tot'] + 1 ,separator, line[0].strip() + " " +line[1].strip()),out_file,"C")

    # Importazione prodotti:
    #import pdb; pdb.set_trace()
    lines = csv.reader(open(file_listino,'rb'),delimiter=separator)
    counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} 
    error=''
    tot_colonne = 0
    
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              raise_log("Colonne presenti: %d" % (tot_colonne),out_file,"I")
           if len(line): # jump empty lines
               if tot_colonne == len(line): # tot colums equal to column first line
                   counter['tot']+=1 
                   error="Importing line" 
                   # product.product data *********************
                   csv_id=0 # Codice
                   ref = prepare(line[csv_id]) 
                   csv_id+=1 # Descrizione
                   name = prepare(line[csv_id]).title() or False
                   csv_id+=1 # IVA
                   iva = prepare(line[csv_id]) 
                   csv_id+=1 # Prezzo1
                   prezzo1 = prepare_float(line[csv_id]) 
                   csv_id+=1 # Prezzo2
                   prezzo2 = prepare(line[csv_id]) 

                   # Default data dictionary (to insert / update)
                   data_categ={'default_code': ref,
                               'name': name,
                               'list_price': prezzo1 or prezzo2 or 0.0,  
                               'supply_method': 'produce', 
                               'type': 'service', 
                               'procure_method': 'make_to_order', 
                              } 
                              
                   # PRODUCT CREATION ***************
                   error="Searching partner with ref"
                   item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', '=', ref)])

                   if item: # UPDATE:
                      counter['upd'] += 1  
                      try:
                          item_mod = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data_categ) 
                          category_id=item[0] 
                      except:
                          raise_log("Errore aggiornando %s"%(ref,), out_file, "E")
                          counter['err_upd']+=1  
 
                      if verbose: print "[INFO]", counter['tot'], "Product already exist: ", ref, name
                   else: # NEW:
                      counter['new'] += 1  
                      try:
                          partner_id=sock.execute(dbname, uid, pwd, 'product.product', 'create', data_categ) 
                      except:
                          raise_log("Errore creando %s"%(ref,), out_file, "E")
                          counter['err']+= 1  
                          
                      if verbose: print "[INFO]", counter['tot'], "Product new: ", ref, name

               else: # Errore totale colonne
                   counter['err']+=1
                   raise_log('Line %d (sep.: "%s"), %s)' % (counter['tot'] + 1 ,separator, line[0].strip() + " " +line[1].strip()),out_file,"C")

except:
    raise_log ('>>> Import interrupted! Line:' + str(counter['tot']),out_file,"E")
    if verbose_mail: 
      send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Address:", "Total line: ",counter['tot_add']," (imported: ",counter['new_add'],") (updated: ", counter['upd_add'], ")"
if counter['err'] or counter['err_upd']:
   raise_log("Error updating: %d  -  Error adding: %d" %(counter['err_upd'],counter['err']),out_file,"I")
   out_file.close() # close before sending file
   if verbose_mail: 
      send_mail(smtp_sender,[smtp_receiver,],smtp_subject,smtp_text,[smtp_log,],smtp_server)
else:
   out_file.close() # clos log file in case of no error

