#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from posta import *

# Parameters:
cfg_file="/home/administrator/ETL/ambulatorio/openerp.cfg"
header_lines = 1 # riga di intestazione

# Start main code *************************************************************
if len(sys.argv) != 2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./operation.py F_SCHEOP.CSV
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

def prepare_date_ISO(valore):
    valore=valore.strip()
    if len(valore)==8:  #"aaaammgg"  # aa in 00 - 12
       if valore: # TODO test correct date format          
          return valore[:4] + "/" + valore[4:6] + "/" + valore[6:]
    return False #time.strftime("%d/%m/%Y") (per gli altri casi)

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:  #"gg-mm-aa"  # aa in 00 - 12
       if valore: # TODO test correct date format          
          if valore[-2:-1]=="9":
             anno="19"
          else:
             anno="20"
          return anno + valore[-2:] + "/" + valore[3:5] + "/" + valore[:2]
    return False #time.strftime("%d/%m/%Y") (per gli altri casi)

def get_partner_id(sock, dbname, uid, pwd, ref):
    partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', ref),])
    return (partner_id and partner_id[0]) or False

def get_product_id(sock,dbname,uid,pwd,code):
    product_id = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('default_code', '=', code),])
    return (product_id and product_id[0]) or False

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,'err':0,'err_upd':0,'tot_add':0,'new_add':0,'upd_add':0,} 

# Open file log error (if verbose mail the file are sent to admin email)
try: 
   out_file = open(smtp_log,"w")
except:
   print "[WARNING]","Error creating log files:", smtp_log
   # No raise as it'a a warning

tooth_list=['11','12','13','14','15','16','17','18','21','22','23','24','25','26','27','28',
            '31','32','33','34','35','36','37','38','41','42','43','44','45','46','47','48',
            '51','52','53','54','55','61','62','63','64','65','71','72','73','74','75','81','82','83','84','85',
            '*','n']
            
# setto tutto il workflow a done!
operation_ids = sock.execute(dbname, uid, pwd, 'dentist.operation', 'search', [('import', '=', True)]) # TODO mettere il campo per cambiare solo quelli con stato E ??
operation_esit = sock.execute(dbname, uid, pwd, 'dentist.operation', 'wkf_operation_done', operation_ids)

if verbose: print "[INFO] Total line: ", counter['tot'], "Error creating:", counter['err_upd']

# *************************** Importazione preventivi come operazioni da effettuare se non sono state appena importate ***********************************************
error=''
tot_colonne = 0

operation_ids = sock.execute(dbname, uid, pwd, 'dentist.todo', 'search', [('import', '=', True)])
operation_esit = sock.execute(dbname, uid, pwd, 'dentist.todo', 'unlink', operation_ids)

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
                   counter['tot']+=1 
                   error="Importing line" 
                   # res.partner data *********************
                   csv_id=0 # Cognome
                   last_name = prepare(line[csv_id]) 
                   csv_id+=1 # Nome
                   first_name = prepare(line[csv_id]) 
                   csv_id+=1 # Ref
                   ref = prepare(line[csv_id]) 
                   csv_id+=1 # Dente
                   tooth = prepare(line[csv_id]).lower() or "n" # note if null
                   csv_id+=1 # Product code
                   product_code = prepare(line[csv_id])
                   csv_id+=1 # Product description
                   product_description = prepare(line[csv_id])
                   csv_id+=1 # Quantity
                   quantity = prepare(line[csv_id])
                   csv_id+=1 # Price
                   price = prepare(line[csv_id])
                   csv_id+=1 # State 
                   state = prepare(line[csv_id]).upper() # E(ffettuato), A(), N() TODO capire se sfruttarlo per vedere l'import <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                   csv_id+=1 # Quotation date
                   date = prepare_date_ISO(line[csv_id]) or False # formato AAAAMMGG
                   csv_id+=1 # Pricelist
                   pricelist = prepare_date(line[csv_id]) or False
                   
                   if state!="E": # oppure controllare da operazioni con una lista se esiste già
                       # calculed fields:
                       name=""
                       if tooth not in tooth_list:
                          print "[ERR] ", counter['tot'] ,"Dente non trovato:", tooth
                          #import pdb; pdb.set_trace()
                          #operation_ids = sock.execute(dbname, uid, pwd, 'dentist.operation', 'search', [('import', '=', True)])
                          #operation_esit = sock.execute(dbname, uid, pwd, 'dentist.operation', 'wkf_operation_done', operation_ids)
                          continue # salto la scrittura
                          
                       if tooth=="n": # only for note fields
                          name=product_description
                       product_id= get_product_id(sock, dbname, uid, pwd, product_code)
                       partner_id= get_partner_id(sock, dbname, uid, pwd, ref)
                       
                       product_data = {
                                      'name': name,
                                      'partner_id': partner_id,
                                      'product_id': product_id,
                                      'tooth': tooth,
                                      'note': '',
                                      #'urgency': 'a', 
                                      'date': date,
                                      'import': True,
                                      }
                       
                       # OPERATION CREATION ***************
                       try:
                           item_id = sock.execute(dbname, uid, pwd, 'dentist.todo', 'create', product_data) 
                       except:
                           print "[ERR] Create",  counter['tot']
                           counter['err_upd']+=1  
                       if verbose: print "[INFO]", counter['tot'], "Insert: ", ref, last_name
except:
    print '[ERR] >>> Import interrupted! Line:', (counter['tot'])
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug

if verbose: print "[INFO] Total line: ", counter['tot'], "Error creating:", counter['err_upd']

