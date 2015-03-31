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
         *  Use the command with this syntax: python ./import_fatturato.py fatmeseoerp.FIA
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
    if mexal_id[:1]=="2": # cliente
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', mexal_id)])
    elif mexal_id[:1]=="4": # fornitore
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_s', '=', mexal_id)])

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
cfg_file= "openerp.cfg"
    
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
invoice_item_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'search', [])
result_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'unlink', invoice_item_ids)

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
           if len(line) and (tot_col==len(line)): # salto le righe vuote e le righe con colonne diverse
               counter['tot']+=1 
               #import pdb; pdb.set_trace()
               try:
                   csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                   mexal_id = prepare(line[csv_id])
                   csv_id+=1      # Mese
                   month = int(prepare(line[csv_id]) or 0 )
                   csv_id+=1      # Anno
                   year = prepare(line[csv_id]) 
                   csv_id+=1      # Totale
                   total_invoice = prepare_float(line[csv_id]) or 0.0
                   #csv_id+=1      # Type (oc or ft)
                   type_document = "ft" #prepare(line[csv_id]).lower()
                   
                   # Calculated field:
                   partner_id = get_partner_id(sock, uid, pwd, mexal_id)
                   if not partner_id:
                      print "[ERR] Riga:", counter['tot'], "Partner non trovato, codice:", mexal_id
                      partner_name=">> Partner non trovato %s"%(mexal_id or "")
                   else:
                      partner_name = get_partner_name(sock, uid, pwd, partner_id)
   
                   if not total_invoice: 
                      print "[ERR] Importo non trovato!", line
                      continue # passo alla riga successiva
                         
                   if not (month or year): # lo importo lo stesso così si vede nei non class.
                      print "[ERR] Mese o anno non trovato!", line
                         
                   data = {"name": "%s [%s]"%(partner_name, mexal_id,), 
                           "partner_id": partner_id,
                           "month": month, 
                           "type_document": type_document, # TODO era commentato!
                          }
                   anno_attuale = datetime.datetime.now().strftime("%Y")

                   if year == anno_attuale: # current
                      data['total'] = total_invoice 
                   elif year == str(int(anno_attuale) -1): # anno -1
                      data['total_last'] = total_invoice
                   elif year == str(int(anno_attuale) -2): # anno -2
                      data['total_last_last'] = total_invoice 
                   else:                      
                      print "[ERR] Riga:", counter['tot'], "Anno non trovato", year
                         
                   try:
                      invoice_id = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'create', data)
                   except:
                      print "[ERR] Riga:", counter['tot'], "Errore creando fatturato:", mexal_id
                   if verbose: 
                      print "[INFO] Riga:", counter['tot'], "Fatturato inserito:",  mexal_id
                         
               except:
                   print "[ERR] Riga:", counter['tot'], "Errore di importazione:", sys.exc_info()[0]
           else:
               print "[ERR] Riga:", counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)
except:
    print '>>> [ERR] Errore importando gli ordini!'
    raise 
print "Importazione terminata! Totale elementi %s" %(counter['tot'],)

#import pdb; pdb.set_trace()
for documento in ['oc', 'ft', 'bc',]:
    print "Ricavo i dati per statistic.trend" + documento # Fatture e OC+FAtture
    if documento=="ft": # Solo fatture
       invoice_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'search', [('type_document','=','ft')])
    else: # tutto oc + ft + bc
       invoice_ids = sock.execute(dbname, uid, pwd, 'statistic.invoice', 'search', [])

    if invoice_ids:
       # Elimino precedenti
       if documento=="ft":
          trend_ids = sock.execute(dbname, uid, pwd, 'statistic.trend', 'search', [])
          remove_trend = sock.execute(dbname, uid, pwd, 'statistic.trend', 'unlink', trend_ids)
       else:
          trend_ids = sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'search', [])
          remove_trend = sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'unlink', trend_ids)
       
       # Carico nella lista tutti i valori divisi per partner:
       item_list={}
       total_invoiced=[0.0, 0.0, 0.0] # year -2, year -1, year 0       
       for item in sock.execute(dbname, uid, pwd, 'statistic.invoice', 'read', invoice_ids): # in funzione del documento
           partner_id=(item['partner_id'] and item['partner_id'][0]) or 0
           
           if partner_id not in item_list:
              item_list[partner_id]=[0.0,0.0,0.0] # year -2, year -1, year 0

           if item['total']: # anno attuale
              item_list[partner_id][2] += item['total']
              total_invoiced[2] += item['total']
           if item['total_last']: # anno attuale
              item_list[partner_id][1] += item['total_last']
              total_invoiced[1] += item['total_last']
           if item['total_last_last']: # anno attuale
              item_list[partner_id][0] += item['total_last_last']
              total_invoiced[0] += item['total_last_last']

    print "Inserisco i dati nell'archivio statistico per " + documento 
    for elemento_id in item_list.keys(): # passo tutti gli elementi inserendoli in archivio col calcolo perc.
        data={'name': "cliente: %d" % (elemento_id,), #"%s [%d €]" % (number, total) ,
              'partner_id': elemento_id,
              'total': item_list[elemento_id][2],
              'total_last': item_list[elemento_id][1],
              'total_last_last': item_list[elemento_id][0],
              'percentage': (total_invoiced[2]) and (item_list[elemento_id][2] * 100 / (total_invoiced[2])), # current year
              'percentage_last': (total_invoiced[1]) and (item_list[elemento_id][1] * 100 / (total_invoiced[1])), # current year
              'percentage_last_last': (total_invoiced[0]) and (item_list[elemento_id][0] * 100 / (total_invoiced[0])), # current year
              }
        try:
           if documento=="ft":
              trend_id = sock.execute(dbname, uid, pwd, 'statistic.trend', 'create', data)
           else:
              trend_id = sock.execute(dbname, uid, pwd, 'statistic.trendoc', 'create', data)
              
        except:
           print "[ERR] Riga:", "Errore creando ordine id_partner:", elemento_id
        if verbose: 
           print "[INFO] Riga:", "Fatturato del partner %d inserito:"%(elemento_id,)
