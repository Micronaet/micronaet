#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from posta import *
from mic_ETL import *
from panchemicals import *

# Set up parameters (for connection to Open ERP Database) ********************************************
# DB config read
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
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
def get_partner_id(sock, dbname, uid, pwd, partner_code):
    partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c','=', partner_code)]) 
    if partner_id:
       return partner_id[0]
    else:
       return False   
    

def get_product_id(sock, dbname, uid, pwd, product_code):
    product_id=sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id','=', product_code)]) 
    if product_id:
       return product_id[0]
    else:
       return False   

if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./invoice_line_ETL.py venduto.PAL
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
counter={'tot':0,}

# Delete all lines:
line_ids = sock.execute(dbname, uid, pwd, 'micronaet.invoice.line', 'search', []) 
delete_result = sock.execute(dbname, uid, pwd, 'micronaet.invoice.line', 'unlink', line_ids) 

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
               if tot_colonne == len(line): # tot # of colums must be equal to # of column in first line
                   counter['tot']+=1 #cliente; numero ft; data; articolo; quantità; prezzo
                   error="Importing line" 
                   csv_id=0
                   partner = Prepare(line[csv_id])
                   csv_id+=1
                   name = Prepare(line[csv_id])
                   csv_id+=1
                   date=Prepare(line[csv_id])
                   csv_id+=1
                   product = Prepare(line[csv_id])
                   csv_id+=1
                   quantity = Prepare(line[csv_id])
                   csv_id+=1
                   price = Prepare(line[csv_id])
        
                   # Import invoice line and price for price_quotation_history
                   data={'name': name,
                         'partner': partner, 
                         'price': price, 
                         'quantity': quantity,
                         'product': product,
                         'date': date, 
                        }    
                      
                   # CREATION ***************
                   item = sock.execute(dbname, uid, pwd, 'micronaet.invoice.line', 'create', data)
                   print "Record create micronaet.invoice.line:", line

                   # Import invoice line and price for chemical_application_product
                   partner_id = get_partner_id(sock, dbname, uid, pwd, partner)
                   product_id= get_product_id(sock, dbname, uid, pwd, product)
                   if partner_id and product_id:
                       data={'partner_id': partner_id,
                             'product_id': product_id, 
                            }                          
                       # CREATION ***************
                       item = sock.execute(dbname, uid, pwd, 'chemical.application', 'search', [('product_id','=',product_id),('partner_id','=',partner_id)])
                       if not item:
                          item = sock.execute(dbname, uid, pwd, 'chemical.application', 'create', data)
                          print "       Record create chemical.application:", line
                   else:
                      print "[ERR] Partner %s or product %s not found!"%(partner, product)
except:
    raise_error ('>>> Import interrupted! Line:' + str(counter['tot']),out_file,"E")
    raise # Exception("Errore di importazione!") # Scrivo l'errore per debug
print "[INFO]","Total line: ",counter['tot']
