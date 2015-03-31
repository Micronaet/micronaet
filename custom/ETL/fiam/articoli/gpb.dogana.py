#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL una tantum articoli-listino GPB
# use: gpb.articoli.py import.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, pdb
from mic_ETL import *

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./gpb.dogana.py dogana.csv
         *********************
         """ 
   sys.exit()

cfg_file="../openerp.gpb.cfg"

# Funzioni:
def prepare_float(valore):
    if not valore: 
       return 0.0
    try:
        valore=valore.replace(",",".")
        valore=valore.replace(" ","")
        valore=valore.replace("\n","")
        if valore: 
           return float(valore)
        else:
           return 0.0   # for empty values
    except:
       print ">>>> Errore conversione float:", originale, ">", valore 
       return 0.0       
       
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose')) #;verbose=True

header_lines=1 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

tot_col=0
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "[INFO] Colonne rilevate", tot_col
        if counter['tot'] < 0:  # salto le N righe di intestazione
           counter['tot'] += 1
        else:   
           if len(line) and (tot_col==len(line)): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               error="Importing line" 
               try:
                   csv_id=0       # codice  
                   item_id = Prepare(line[csv_id])
                   csv_id+=1      #  descrizione 
                   descrizione = Prepare(line[csv_id]).title()
               except:
                   print "[ERR] Riga:", item_id, "Errore di conversione:", sys.exc_info()[0]
               
               # product.custom.duty ********************************************
               data_duty = {'name': descrizione,
                            'code': '',
                            #'tax': 0.0,  
                           }
               #import pdb; pdb.set_trace()
               if descrizione:
                  item = sock.execute(dbname, uid, pwd, 'product.custom.duty', 'search', [('name', '=', descrizione)]) 
                  duty_id=0
                  if item: # update
                     try:
                         modify_id = sock.execute(dbname, uid, pwd, 'product.custom.duty', 'write', item, data_duty)
                         duty_id=item[0]
                     except:
                         print "[ERR] Riga:", item_id, "DOGANA", "Modificando record:", descrizione
                     if verbose: 
                        print "[INFO] Riga:", item_id, counter['tot'], "Dogana aggiornato:", descrizione
                                            
                  else: # nessun prodotto trovato!
                     try:
                         duty_id = sock.execute(dbname, uid, pwd, 'product.custom.duty', 'create', data_duty)
                     except:
                         print "[ERR] Riga:", item_id, "DOGANA", "Modificando record:", 
                     if verbose: 
                        print "[INFO] Riga:", item_id, counter['tot'], "Dogana aggiornato:", descrizione
               else:
                   print "[ERR] Riga:", item_id, counter['tot'], "Codice doganale inesistente!"                      


               # product.product ********************************************
               if duty_id: # se viene creata la tariffa doganale:
                  data={
                       'duty_id': duty_id,
                       }
                       
                  item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', item_id)]) 
                  if item: # update
                     try:
                         modify_id = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data)
                     except:
                         print "[ERR] Riga:", item_id, "PRODOTTI", "Modificando record:", item
                     if verbose: 
                         print "[INFO] Riga:", item_id, counter['tot'], "Prodotto aggiornato:", item
                                             
                  else: # nessun prodotto trovato!
                      print "[ERR] Riga:", item_id, counter['tot'], "Codice non trovato:", item_id, "<"*20
               else:         
                   print "[ERR] Riga:", item_id, counter['tot'], "Codice inesistente!"                      


           else:
               print "[ERR]Riga:", item_id, counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)
except:
    #pdb.set_trace()
    print '>>> [ERR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
print "Importazione terminata!"
