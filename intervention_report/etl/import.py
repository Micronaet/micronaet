#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# use: import.csv rapportini.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, os

path_file=os.path.expanduser("~/ETL/micronaet/")

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./import.py rapportini.csv
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
    item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', mexal_id)])
    if item_id:
       return item_id[0]
    return 0   

def parse_intervent(date, da1, a1, da2, a2, viaggio_pre, totale_pre):
    ''' get: date,      from 1, to 1,      from 2, to 2,  
             trip,      total intervent
             
        return 
             date_start,               duration,              total,
             manual_total,              trip_hour,              trip_require,
             break_hour,              break_require, 
             mode,   >> 'customer', 'company', 'connection', 'phone' 
    '''    
    from datetime import datetime, timedelta
    data_iniziale = datetime(int(date[:4]),int(date[5:7]),int(date[8:10]),0,0,0)
    break_require = False
    break_hour = 0.0
    duration = 0.0
    total = totale_pre # TODO verify
    trip_hour = viaggio_pre / 60.0 # trip in hour
    if da1:
        date_start = data_iniziale + timedelta(hours=int(da1[0:2]), minutes=int(da1[3:5]))
        if da2:
            date1_end = data_iniziale + timedelta(hours=int(a1[0:2]), minutes=int(a1[3:5]))
            date2_start = data_iniziale + timedelta(hours=int(da2[0:2]), minutes=int(da2[3:5]))
            date_end = data_iniziale + timedelta(hours=int(a2[0:2]), minutes=int(a2[3:5]))
            duration_interval = date_end - date_start
            break_require = True
            duration_break_interval = date2_start - date1_end           
            break_hour = duration_break_interval.days * 24.0 + duration_break_interval.seconds / 3600.0
            duration = duration_interval.days * 24.0 + duration_interval.seconds / 3600.0
            
        else: # yes da1 no da2
            date_end = data_iniziale + timedelta(hours=int(a1[0:2]), minutes=int(a1[3:5]))
            duration_interval = date_end - date_start
            duration = duration_interval.days * 24.0 + duration_interval.seconds / 3600.0 
            
    else: # no da1
        if da2:
            date_start = data_iniziale + timedelta(hours=int(da2[0:2]), minutes=int(da2[3:5]))
            date_end = data_iniziale + timedelta(hours=int(a2[0:2]), minutes=int(a2[3:5]))
            duration_interval = date_end - date_start
            # duration   # TODO convert interval
            
        else:  # no da1 no da2       
            date_start = data_iniziale + timedelta(hours=8, minutes=30) # default hour (8.00)
            duration = total

    if break_require:
       duration -= break_hour

    if trip_hour:
       trip_require = True
       mode='customer'
       duration += trip_hour
    else:
       trip_require=False
       mode='company'
    
    if duration == total: 
       manual_total = False
    else:
       manual_total = True   
    
    return (date_start.strftime('%Y-%m-%d %H:%M:%S'),
            duration,
            total,
            manual_total,
            trip_hour,
            trip_require,
            break_hour,
            break_require,
            mode)

FileInput=sys.argv[1]
cfg_file=path_file + "openerp.cfg"
    
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
counter={'tot':-header_lines,'riga': 0, 'new':0,'upd':0,} # tot negative (jump N lines)

#tech_name = {'631.00001':'Mazzo','631.00002':'nicola','631.00006':'laura'}
tech_ids = {'631.00001':3,'631.00002':4,'631.00006':5} # ID utenti 
sector_ids = {'IIP':1, 'IIT':3, 'IIO':2, 'IIA':4} # gestionale, tecnico, gestionale # TODO Valutare poi con IIT, IIO, IIP

tipologia_ids = {1:1,   # vendita ??
                 #2:,   # reso riparato
                 #3:,   # c/visione
                 #4:,   # c/lavorazione
                 #5:,   # acquisto
                 #6:,   # c/sostituzione
                 #7:,   # acconto
                 #8:,   # reso non riparato
                 #9:,   # c/riparazione
                 #10:,   # per accredito
                 11:1,   # int. pagamento
                 12:2,   # int. commessa  > no san flaviano
                 13:3,   # int. garanzia
                 14:4,   # int. gratuito
                 15:5,   # int. contratto
                 #16:,   # svendita
                 #17:,   # reso fornitore
                 #18:,   # eliminazione merce
                 #19:,   # c/prestito
                 #20:,   # reso non conforme
                 #21:,   # reso c/visione
                 25:6,   # intervento non a pagamento
                 26:7,   # analisi
                }

# Carico gli elementi da file CSV:
tot_col=0
actual_id=0
try:
    for line in lines:
        if tot_col==0: # memorizzo il numero colonne la prima volta
           tot_col=len(line)
           print "[INFO] Colonne rilevate", tot_col
        if counter['tot']<0:  # salto le N righe di intestazione
           counter['tot']+=1
        else:
           if len(line) != 1 and len(line) != tot_col: # righe con ; (2)
              if len(line)==2:
                 line=[line[0]]
                    
           if len(line) and (len(line)==1 or (tot_col==len(line))): # salto le righe vuote e le righe con colonne diverse
               try:
                   counter['riga'] += 1                    
                   if len(line)==1: # parte della descrizione rapportino
                       data['intervention'] += prepare(line[0]) + "\n"
                       continue
                       
                   if counter['riga']!=1: # jump first record
                       
                       if actual_id: # *******************************************
                          int_test1_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('ref','=', False),('imported','=',False),('partner_id','=',partner_id),('user_id','=',tech_id),('date_start','=',date_start),]) #('duration','=',duration)])
                          if int_test1_id: # manually inserted (before import)
                             #add_info= sock.execute(dbname, uid, pwd, 'intervention.report', 'write', int_test1_id, {'ref' : "BC2/%s"%(intervento_id)})
                             print "[WAR] Riga:" , counter['riga'], "Già nel programma, aggiornato con rif:", "BC2/%s"%(intervento_id)
                             print "NOT UPDATE: ", data, "Riga:", counter['riga'] , "Intervento:" , intervento_id
                             
                          int_test2_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('ref','=', "BC2/%s"%(intervento_id)),('import_id','=',False)])
                          if int_test1_id or int_test2_id: # manually inserted (before import)
                             print "[ERR] Riga:" , counter['riga'], "Già nel programma, inserita manualmente! Rif.: ", intervento_id
                             print "NOT UPDATE: ", data, "Riga:", counter['riga'] , "Intervento:" , intervento_id
                             # TODO update??
                          else:   
                             int_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('import_id','=', actual_id)])
                             if len(int_id) == 1:
                                mod_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'write', int_id[0], data)
                                print "[INF] Riga:" , counter['riga'], "Modificato rapportino esistente, aggiornato con rif:", "BC2/%s"%(intervento_id)
                                print "UPDATE: ", data, "Riga:", counter['riga'] , "Intervento:" , intervento_id
                                
                             else:  # Creo
                                create_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'create', data)
                                print "[INF] Riga:" , counter['riga'], "Creato rapportino rif: %s", "BC2/%s"%(intervento_id)
                                print  "CREATE: ", data, "Riga:", counter['riga'] , "Intervento:" , intervento_id
                       else: 
                          print "[ERR] Riga:", counter['riga'], "L'ID rapportino importato è vuoto!"
                       # *******************************************************   

                   counter['tot'] += 1 
                   csv_id=0                                                      # ID rapportino
                   intervento_id = prepare(line[csv_id])
                   actual_id= int(intervento_id) # per gli aggiornamenti successivi

                   if intervento_id >= 614 and intervento_id <= 630:
                      import pdb; pdb.set_trace()
                      
                   csv_id+=1                                                     # Scadenza OC formato: YYYYMMDD
                   int_date = prepare_date(line[csv_id]) 
                   csv_id+=1                                                     # ID tecnico xxx.xxxxx                       
                   tech_code = prepare(line[csv_id]) 
                   csv_id+=1                                                     # ID cliente xxx.xxxxx                       
                   customer_id = prepare(line[csv_id]) 
                   csv_id+=1                                                     # Cliente descrizione
                   cliente = prepare(line[csv_id]) 
                   csv_id+=1                                                     # Da (1)
                   da1 = prepare(line[csv_id]) 
                   csv_id+=1                                                     # A (1)
                   a1 = prepare(line[csv_id]) 
                   csv_id+=1                                                     # Da (2)
                   da2 = prepare(line[csv_id]) 
                   csv_id+=1                                                     # A (2)
                   a2 = prepare(line[csv_id]) 
                   csv_id+=1                                                     # Viaggio in minuti
                   viaggio_pre = prepare_float(line[csv_id]) 
                   csv_id+=1                                                     # Durata totale
                   totale_pre = prepare_float(line[csv_id]) 
                   csv_id+=1                                                     # Mettere se l'intervento è a pagamento (ID tipologia da mexal)
                   tipologia = prepare(line[csv_id])                                    
                   csv_id+=1                                                     # Tipo intervento (IIT, IIO, IIP, IIA)
                   intervent_category = prepare(line[csv_id]).upper()                                    
                   csv_id+=1                                                     # Mettere se l'intervento è a pagamento (ID tipologia da mexal)
                   price = prepare_float(line[csv_id]) 
                   
                   # Calculated field:
                   date_start, duration, total, manual_total, trip_hour, trip_require, break_hour, break_require, mode = parse_intervent(int_date,da1,a1,da2,a2,viaggio_pre,totale_pre)
                   #mode= 'customer' # 'company', 'connection', 'phone'

                   partner_id = get_partner_id(sock, uid, pwd, customer_id)
                   if not partner_id:
                      print "[ERR] Riga:", counter['riga'], "Partner non trovato:", intervento_id, "Cliente:", cliente
                      partner_id=1 # TODO correggere poi segnalando l'errore!!!

                   # Trovo l'id della tipologia
                   if tipologia and tipologia in tipologia_ids:
                      type_id = tipologia_ids[tipologia]
                   else:
                      if price:
                         type_id = 1
                      else:  # test customer (gratuito o contratto?)  # TODO lista clienti con contratto
                         type_id = 4 # TODO test intervent price for default!
                         #print "[ERR] Riga:", counter['riga'], "Tipologia non trovata, codice:", tipologia
               
                   # Trovo l'id del tecnico
                   if tech_code in tech_ids:
                      tech_id = tech_ids[tech_code]
                   else:
                      tech_id = 1 # administrator!
                      print "[ERR] Riga:", counter['riga'], "Tecnico non trovato, codice:", tech_code, " intervento:", intervento_id

                   # Trovo l'id del settore
                   if intervent_category in sector_ids:
                      sector_id = sector_ids[intervent_category]
                   else:
                      sector_id = 0
                      print "[ERR] Riga:", counter['riga'], "Categoria intervento non trovata, codice:", intervent_category

                   data={
                        'import_id': intervento_id,
                        'imported': True,
                        'ref': "BC2/%s"%(intervento_id),
                        'name': 'Richiesta intervento generica',
                        'date_start': date_start, 
                        'duration': duration,
                        'trip_hour': trip_hour,
                        'break_hour': break_hour,
                        'trip_require': trip_require,
                        'break_require': break_require,
                        'total': total, 
                        'manual_total': manual_total,
                        
                        #'date_end': '', # calculated
                        'partner_id': partner_id,
                        'intervention_request': 'Richiesta intervento generica', 
                        'intervention': "", # non necessario (aggiornato quando è completo)
                        'internal_note': False,
                        
                        'type_id': type_id, #fields.many2one('intervention.type', 'Type', required=False),
                        'user_id': tech_id, #fields.many2one('res.users', 'User', required=True),
                        'tipology': 'work',#  'mode': '','phone','customer','connection','company'
                        'state': 'close',                             
                        'sector_id': sector_id, # intervention.sector (1 gestionale, 2 openerp, 3 tecnico)
                        'mode': mode, # customer, company, connection, phone
                        }             
               except:
                   print "[ERR] Riga:", counter['tot'], "Errore di importazione:", sys.exc_info()[0]
                   import pdb; pdb.set_trace()
           else:
               print "[ERR] Riga:", counter['riga'], "Riga vuota o con colonne diverse", tot_col, len(line)
    
    # write last record:
    if actual_id: # *******************************************
       int_test1_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('ref','=', False),('imported','=',False),('partner_id','=',partner_id),('user_id','=',tech_id),('date_start','=',date_start),]) #('duration','=',duration)])
       if int_test1_id: # manually inserted (before import)
          #add_info= sock.execute(dbname, uid, pwd, 'intervention.report', 'write', int_test1_id, {'ref' : "BC2/%s"%(intervento_id)})
          print "[WAR] Riga:" , counter['riga'], "Già nel programma, aggiornato con rif:", "BC2/%s"%(intervento_id)
          
       int_test2_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('ref','=', "BC2/%s"%(intervento_id)),('import_id','=',False)])
       if int_test1_id or int_test2_id: # manually inserted (before import)
          print "[ERR] Riga:" , counter['riga'], "Già nel programma, inserita manualmente! Rif.: ", intervento_id
          # TODO update??
       else:   
          int_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('import_id','=', actual_id)])
          if len(int_id) == 1:
             mod_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'write', int_id[0], data)
             print "[INF] Riga:" , counter['riga'], "Modificato rapportino esistente, aggiornato con rif:", "BC2/%s"%(intervento_id)
             
          else:  # Creo
             create_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'create', data)
             print "[INF] Riga:" , counter['riga'], "Creato rapportino rif: %s", "BC2/%s"%(intervento_id)
    else: 
       print "[ERR] Riga:", counter['riga'], "L'ID rapportino importato è vuoto!"
   # *******************************************************   
               
except:
    print '>>> [ERR] Errore importando i rapportini!'
    raise 

to_close_id = sock.execute(dbname, uid, pwd, 'intervention.report', 'search', [('import_id','!=', False)])
to_close = sock.execute(dbname, uid, pwd, 'intervention.report', 'write', to_close_id, {'state': 'close'})

print "Importazione terminata! Totale rapportini %s" %(counter['tot'],)
