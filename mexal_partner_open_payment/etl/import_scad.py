#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, ConfigParser
import datetime

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import.py file_to_import.csv
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
        return: ID partner, Name partner
    '''
    if mexal_id[:1] == '2': # cliente
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', mexal_id)])
    elif mexal_id[:1] == '4': # fornitore                      
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_s', '=', mexal_id)])
    else: # ne cliente ne fornitore
       print "[ERR] Non trovato questo codice:", mexal_id
       return False, "Non trovato"

    if item_id:
       item_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', item_id[0],)
       return item_id[0], item_read['name']
    return False, "Non trovato"

FileInput=sys.argv[1]
cfg_file="/home/administrator/ETL/openerp.cfg"

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

# Elimino tutti gli elementi della tabella prima di procedere all'importazione:
deadline_ids = sock.execute(dbname, uid, pwd, 'statistic.deadline', 'search', []) 
response =  sock.execute(dbname, uid, pwd, 'statistic.deadline', 'unlink', deadline_ids) 

partner_ids= sock.execute(dbname, uid, pwd, 'res.partner', 'search', []) 
partner_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', partner_ids, {'pendent': False,})

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
               try:
                   csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                   mexal_id = prepare(line[csv_id])
                   csv_id+=1      # Data: YYYYMMDD
                   deadline = prepare_date(line[csv_id])
                   csv_id+=1      # Importo
                   total = prepare_float(line[csv_id]) 
                   csv_id+=1      # Tipo
                   type_id = prepare(line[csv_id]).lower()

                   if deadline < datetime.date.today().strftime("%Y-%m-%d"): # solo quelle scadute                                      
                       # Calculated field:                   
                       if total > 0:
                          total_in = total
                          total_out = 0.0
                       else:
                          total_in = 0.0
                          total_out = -total

                       partner_id, partner_name = get_partner_id(sock, uid, pwd, mexal_id)

                       if not partner_id:
                          print "[ERR] Riga:", counter['tot'], "Partner non trovato:", mexal_id
                       else: # Se il partner esiste registro la pendenza! 
                          partner_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', partner_id, {'pendent': True,})
                       
                       # Importazione dato: statistic.order
                       data={'name': "%s [%s]: %s (%s €)"%(partner_name, mexal_id, deadline, total),
                             'partner_id': partner_id,
                             'deadline': deadline,
                             'in': total_in,
                             'type': type_id,
                             }
                       try:
                          deadline_id = sock.execute(dbname, uid, pwd, 'statistic.deadline', 'create', data)
                       except:
                          print "[ERR] Riga:", counter['tot'], "Errore creando scadenza:", deadline
                       if verbose: 
                         print "[INFO] Riga:", counter['tot'], "Scadenza inserita:", deadline, mexal_id                  
                             
               except:
                   print "[ERR] Riga:", counter['tot'], "Errore di importazione:", sys.exc_info()[0]
           else:
               print "[ERR] Riga:", counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)               
except:
    print '>>> [ERR] Errore importando gli deadline!'
    raise 
