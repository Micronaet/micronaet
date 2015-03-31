#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# ETL. import csv file with preformatted data comes from Mexal orders
# use: import.csv mexal_file_csv.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, datetime

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import_product.py fatmesartoerp.FIA
         *********************
         """ 
   sys.exit()

# Funzioni:
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
    return '' #time.strftime("%d/%m/%Y") (per gli altri casi)

def prepare_float(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values
       
def get_partner_id(sock, uid, pwd, mexal_id):
    ''' Ricavo l'ID del partner dall'id di mexal
    '''
    item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', mexal_id)])
    if item_id:
       return item_id[0]
    return 0   

def get_partner_name(sock, uid, pwd, partner_id):
    ''' Ricavo il nome del partner
    '''
    partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_id)
    if partner_read:
       return partner_read['name']
    return ''

FileInput=sys.argv[1]
if FileInput:
   sigla_azienda=FileInput[-3:].lower()
else:
   print "[ERR] File input non presente!"
   sys.exit()   
cfg_file="openerp.cfg"
    
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname = config.get('dbaccess','dbname')
user = config.get('dbaccess','user')
pwd = config.get('dbaccess','pwd')
server = config.get('dbaccess','server')
port = config.get('dbaccess','port')   # verify if it's necessary: getint
separator = config.get('dbaccess','separator') # test
verbose = eval(config.get('import_mode','verbose')) #;verbose=True

header_lines = 0 # mai da mexal

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

# Elimino tutto
print "Elimino vecchio archivio invoice!"
invoice_item_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'search', [])
result_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'unlink', invoice_item_ids)

print "Inizio importazione"
# Carico gli elementi da file CSV:
tot_col=0
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "[INFO] Colonne rilevate", tot_col
        if counter['tot']<0:  # salto le N righe di intestazione
           counter['tot']+=1
        else:   
           if (len(line) and (tot_col==len(line))) or (len(line)==5): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               try:
                   csv_id=0       # Famiglia
                   name = prepare(line[csv_id])
                   csv_id+=1      # Mese
                   month = int(prepare(line[csv_id]) or 0 )
                   csv_id+=1      # Anno
                   year = prepare(line[csv_id])
                   csv_id+=1      # Totale
                   total_invoice = prepare_float(line[csv_id]) or 0.0
                   if len(line)==5:
                      csv_id+=1      # Tipo (OC o FT< comprende BC)
                      type_document = prepare(line[csv_id]).lower()
                   else:
                      type_document = 'ft'   
                                                              
                   # Calculated field:
                   if type_document not in ('ft', 'bc', 'oc'):
                      print "Tipo di documento non riconosciuto! Sigla:", type_document
                      type_document=False
                   data = {"name": name, 
                           "month": month, 
                           "type_document":type_document,
                          }
         
                   # Calcolo in quale anno inserire il fatturato (specchio di 3)
                   #import pdb; pdb.set_trace()
                   if not (year or month): 
                      print "[ERR] Linea %s: Mese [%s] o anno [%s] non trovati!"%(counter['tot'], month, year)
                      
                   anno_mese = "%s%02d"%(year, month) 
                   anno_attuale = int(datetime.datetime.now().strftime("%Y"))
                   # TODO: inserire anche gli OC ###############################
                   # Periodo settembre - anno attuale >> agosto - anno prossimo
                   if anno_mese >= "%s09"%(anno_attuale,) and anno_mese <= "%s08"%(anno_attuale + 1,): # current
                      data['total'] = total_invoice
                   elif anno_mese >= "%s09"%(anno_attuale -1,) and anno_mese <= "%s08"%(anno_attuale,): # anno -1
                      data['total_last'] = total_invoice
                   elif anno_mese >= "%s09"%(anno_attuale -2,) and anno_mese <= "%s08"%(anno_attuale -1,): # anno -2
                      data['total_last_last'] = total_invoice
                   else:                      
                      print "[ERR] Riga:", counter['tot'], "Anno non trovato", year

                   try:                      
                      invoice_id = sock.execute(dbname, uid, pwd, 'statistic.invoice.product', 'create', data)
                   except:
                      print "[ERR] Riga:", counter['tot'], "Errore creando fatturato prodotto:", name
                   if verbose: 
                      print "[INFO] Riga:", counter['tot'], "Fatturato prodotto inserito:", name
                         
               except:
                   print "[ERR] Riga:", counter['tot'], "Errore di importazione:", sys.exc_info()[0]
           else:
               print "[ERR] Riga:", counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)
except:
    print '>>> [ERR] Errore importando gli ordini!'
    raise 
print "Importazione terminata! Totale elementi %s" %(counter['tot'],)
