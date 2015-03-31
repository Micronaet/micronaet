#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL una tantum articoli-listino GPB
# use: gpb.articoli.py import.csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser, pdb
from mic_ETL import *
#from fiam import *

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./gpb.articoli.py import.csv
         *********************
         """ 
   sys.exit()

cfg_file="../openerp.gpb.cfg"

# Funzioni:
def prepare_float(valore):
    originale=valore
    if not valore: # ''
       return 0.0
    if valore == "#DIV/0!" or valore == "#RIF!" or valore == "??" or valore == "#VALORE!":
       return 0.0
    #print valore
       
    try:
        valore=valore.replace(",",".")
        valore=valore.replace("cbm","")   
        valore=valore.replace("kg","")   
        valore=valore.replace("Kg","")   
        valore=valore.replace(" ","")
        valore=valore.replace("\n","")
        
        valore_array=valore.split(".")
        # if valore=="1.337,53": 
        #    import pdb; pdb.set_trace()
        if len(valore_array)==3:
           #import pdb; pdb.set_trace()
           valore=valore_array[0] + valore_array[1] + "." + valore_array[2] 
        
        if valore: # TODO test correct date format 
           return float(valore)
        else:
           return 0.0   # for empty values
    except:
       print ">>>> Errore conversione float:", originale, ">", valore 
       return 0.0       
       
def getSupplier_id(supplier):
    '''Get short name, return supplier ID
    '''
    lista = {'DOLCEVITA':'20.00803',
             'EVERGREEN':'20.00855',
             'GREAT': '20.00711',
             'GREENLINE':'20.00805',
             'HOMMAX':'20.00693',
             'JINHUA UNIVERSE':'20.00528',
             'OTION':'20.00709',
             'MEIGU':'20.00724',
             'PCA':'20.00387',
             'TOPHINE':'20.00797',
             'TONGY':'20.07002',
             'SUNSHINE':'20.01085',
             'UNIVERSE': '20.00528', # come JINHUA UNIVERSE
             'UNIVERS':'20.00909', # UNIVERSE? NON USATO PER ORA
             'WEILING':'20.00710',
             'WUJI SUNSHINE': '20.07001',
             'YADA':'20.00392',
             'XINYA':'20.00688',
             'YONGQING':'20.00707',
             'YATAI':'20.00762',  
             'SIESTA':           
             }
    codice = lista.get(supplier.upper(), "")
    if codice:
       item_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_s', '=', codice)])
       if item_id:
          return item_id[0]                 
    return 0   

def getMargin(pricelist_calc, total_cost):
    if total_cost:
       return round((100.0 * pricelist_calc / total_cost) - 100, 0)
    return 0   

def getContainer_id(transport, q_x_container):
    ''' Calcolo il totale del costo container e recupero il dato dall'archivio
    '''
    totale=(round(transport * q_x_container/100, 0) *100) or 0.0
    item_id = sock.execute(dbname, uid, pwd, 'base.container.type', 'search', [('cost', '=', totale)])
    if item_id:
       return item_id[0]
    return 0   
    
def getEAN(codice):
    ''' calculate check digit and return hole code'''    
    if len(codice)!= 12:
       return ""
    
    somma = (int(codice[0]) + int(codice[2]) + int(codice[4]) + int(codice[6]) + int(codice[8]) + int(codice[10])) + \
            3*(int(codice[1]) + int(codice[3]) + int(codice[5]) + int(codice[7]) + int(codice[9]) + int(codice[11]))
    check = str(somma)[-1:]
    if check != "0":
       check = str(10 - int(check))  
    return codice + str(check)
    
def getMeasure(dimension, misure):
    ''' Riceve una stringa e una lista [0.0, 0.0, 0.0] e scorpora gli elementi nelle 3 dimensioni
    '''
    if not dimension:
       return False   
    dimension = dimension.lower()   
    dimension = dimension.replace('**', '*')
    dimension = dimension.replace('*', 'x')
    dimension = dimension.replace('xx', 'x') # errore doppia x
    dimension = dimension.replace('cm', '')
    dimension = dimension.replace(' ', '')
    dimension = dimension.replace(',', '.')    
    valori=dimension.split('x')
    try:
        if len(valori)!=3:
           return False
        for i in range(0,3):   
           if type(eval(valori[i])) in (type(0.0), type(0)):
              misure[i]=eval(valori[i])
           else:
              return False       
    except:
       return False          
    return True
    
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
# TODO parametrize:
taxd="21a"
taxc="21b"
#import pdb; pdb.set_trace()
header_lines=1 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)

tot_col=0
if not (iva_credito and iva_debito):
   print "[ERR] Non è stata trovata l'IVA credito o debito da applicare:", data
error=''
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
               error="Importing line" 
               storico_anni=['2008', '2009', '2010', '2011', '2012']
               pricelist = [0.0, 0.0, 0.0, 0.0, 0.0]   # 2008, 2009, 2010, 2011, 2012
               var_perc =  [0.0, 0.0, 0.0, 0.0, 0.0]   # 2008, 2009, 2010, 2011, 2012
               fob_cost =  [0.0, 0.0, 0.0, 0.0, 0.0]   # 2008, 2009, 2010, 2011, 2012
               errore=False
               try:
                   csv_id=0       # id  
                   item_id = Prepare(line[csv_id])
                   csv_id+=1      #  % 2008         <<<<< Calcolare non importare
                   var_perc[0] = prepare_float(line[csv_id])
                   csv_id+=1      # listino 2008  
                   pricelist[0] = prepare_float(line[csv_id])                  
                   csv_id+=1      # listino 2009
                   pricelist[1] = prepare_float(line[csv_id])                  
                   csv_id+=1      # listino 2010
                   pricelist[2] = prepare_float(line[csv_id])                  
                   csv_id+=1      # listino % 2010  <<<<< Calcolare non importare
                   var_perc[2] = prepare_float(line[csv_id])
                   csv_id+=1      # listino 2011
                   pricelist[3] = prepare_float(line[csv_id])                  
                   csv_id+=1      # listino % 2011  <<<<< Calcolare non importare ************************
                   var_perc[3] = prepare_float(line[csv_id])
                   csv_id+=1      # listino 2012 *********************************************************
                   pricelist[4] = prepare_float(line[csv_id])                  
                   csv_id+=1      # immagine

                   csv_id+=1      # tipo o materiale
                   type_of_material = Prepare(line[csv_id]) 
                   csv_id+=1      # barcode
                   
                   csv_id+=1      # codice fiam
                   ref = Prepare(line[csv_id])   #prima era code

                   csv_id+=1      # descrizione
                   description = Prepare(line[csv_id])
                   csv_id+=1      # codice fornitore
                   supplier_code = Prepare(line[csv_id])
                   csv_id+=1      # descrizione in inglese
                   description_eng = Prepare(line[csv_id])
                   csv_id+=1      # colore
                   colour = Prepare(line[csv_id])
                   csv_id+=1      # tessuto - vetro
                   fabric = Prepare(line[csv_id])
                   csv_id+=1      # dimensioni articolo
                   dimension = Prepare(line[csv_id])
                   csv_id+=1      # volume imballo
                   volume = prepare_float(line[csv_id])
                   csv_id+=1      # pezzi x imballo
                   pezzi_x_imballo = prepare_float(line[csv_id])
                   csv_id+=1      # dimensione imballo cm.  0,0 x 0,0 x 0,0
                   dimension_pack = Prepare(line[csv_id])
                   csv_id+=1      # costo fob 2012 USD
                   fob_cost[4] = prepare_float(line[csv_id])
                   fob_cost[3] = fob_cost[4] # utilizzato il prezzo 2012 anche per anno 2011
                   csv_id+=1      # costo fob 2012 EUR
                   fob_cost_2012_eur = prepare_float(line[csv_id])
                   csv_id+=1      # ----- calcolo 30 CBM

                   csv_id+=1      # ----- calcolo 68 CBM

                   csv_id+=1      # q. per container               
                   q_x_container = prepare_float(line[csv_id])
                   csv_id+=1      # ???????????

                   csv_id+=1      # Trasporto
                   transport = prepare_float(line[csv_id])
                   csv_id+=1      # Dazi USD
                   dazi = prepare_float(line[csv_id])
                   csv_id+=1      # Prezzo listino 2011 non arrot
                   pricelist_calc = prepare_float(line[csv_id])
                   csv_id+=1      # Costo EUR trasporto compreso
                   total_cost = prepare_float(line[csv_id])
                   csv_id+=1      # Peso art. Kg.
                   weight = prepare_float(line[csv_id])
                   csv_id+=1      # Peso imballo Kg.
                   weight_pack = prepare_float(line[csv_id])
                   csv_id+=1      # Fornitore
                   supplier = Prepare(line[csv_id])
                   csv_id+=1      # Costo fob 2008 USD
                   fob_cost[0] = prepare_float(line[csv_id])
                   csv_id+=1      # Costo fob 2009 USD
                   fob_cost[1] = prepare_float(line[csv_id])
                   csv_id+=1      # ----- Costo fob 2009 EUR
                   
                   csv_id+=1      # Costo fob 2010 USD
                   fob_cost[2] = prepare_float(line[csv_id])
                   csv_id+=1      # ----- Costo fob 2010 EUR
                   
                   csv_id+=1      # ----- Incidenza trasporto
               except:
                   print "[ERR] Riga:", item_id, "Errore di conversione:", sys.exc_info()[0]
                   errore=True
               # Calculated field:
               # dimensioni articolo:
               misure=[0.0, 0.0, 0.0]
               if len(ref)<5:
                  ref = "0" * (5-len(ref)) + ref
                  print ">> Riga:", item_id, "Aggiustamento codice con zeri:", ref
                  
               #import pdb; pdb.set_trace()
               ean13 = getEAN("8004467" + ref)
               
               # controllo se il prezzo di listino l'anno precedente era maggiore e tengo quello
               # Parte da eliminare per gestione errori dimensione: ************
               error_import = False
               error_dimension = False
               dimension_text = ""
               error_dimension_pack = False
               dimension_text_pack = ""
               # ***************************************************************
               
               if pricelist[4] < pricelist[3]:
                  print ">>> Riga:", item_id, "Conservato prezzo precedente, riga %s > codice: %s (prec. %s, nuovo %s)"%(item_id, ref, pricelist[3], pricelist[4])
                  pricelist[4] =  pricelist[3]
               if not getMeasure(dimension, misure):               
                  if dimension:
                     print "[ERR] Riga:", item_id, "", "DIMENSIONI" , ref,  "Dimensione errata!", dimension
                  else:
                     print "[ERR] Riga:", item_id, "", "DIMENSIONI" , ref,  "Dimensione nulla!", dimension
                        
                  height = 0.0
                  width = 0.0
                  length = 0.0

                  # Parte da eliminare per gestione errori dimensione: *********
                  error_import = True
                  dimension_text = dimension
                  error_dimension = True
                  # ************************************************************

               else:   
                  height = misure[0]
                  width = misure[1]
                  length = misure[2]

               # dimensioni imballaggio:
               misure=[0.0, 0.0, 0.0]
               if not getMeasure(dimension_pack, misure):
                  if dimension_pack:
                     print "[ERR] Riga:", item_id, "","DIMENSIONI PACK" ,  ref, "Dimensione imballaggio errata:", dimension_pack
                  else:   
                     print "[ERR] Riga:", item_id, "","DIMENSIONI PACK" ,  ref, "Dimensione imballaggio nullo:", dimension_pack
                  height_pack = 0.0
                  width_pack = 0.0
                  length_pack = 0.0
                  
                  # Parte da eliminare per gestione errori dimensione: *********
                  error_import = True
                  dimension_text_pack = dimension_pack
                  error_dimension_pack = True
                  # ************************************************************
               else:   
                  height_pack = misure[0]
                  width_pack = misure[1]
                  length_pack = misure[2]
                  
               # tipo di container:
               container_id = getContainer_id(transport, q_x_container)
               uom_id = getUOM(sock,dbname,uid,pwd,'PCE',{}) 
               
               fixed_margin = getMargin(pricelist_calc, total_cost) # TODO calcolo del margine!
               margin = getMargin(pricelist[4], total_cost) # TODO calcolo del margine effettivo!
               
               supplier_id = getSupplier_id(supplier)  
               if not supplier_id:
                  print "[ERR] Riga:", item_id, "", "FORNITORE " + ">"*20, ref, "Fornitore non trovato:", supplier
               
               if not errore:  
                  data={'dazi': dazi,
                        'description': description,
                        'description_purchase': description_eng,
                        'colour': colour,
                        'fabric': fabric,
                        'type_of_material': type_of_material,
                        'weight_net': weight,
                        'weight': weight_pack,
                        'volume': volume,
                        'in_pricelist': True,
                        'manual_pricelist': False,
                        'ean13': ean13,
                        'margin': margin,
                        'fixed_margin': fixed_margin,
                        'standard_price': fob_cost_2012_eur, #total_cost,
                        'list_price': pricelist[4],

                        # Tolti perchè Roberta inizia a modificarli ************
                        #'dimension_text': dimension,
                        #'height': height,
                        #'width': width,
                        #'length': length,                        
                        #'error_import': error_import,
                        #'dimension_text': dimension_text,
                        #'error_dimension': error_dimension,
                        }

                  # product.product ********************************************
                  error="Searching product with ref"
                  #import pdb; pdb.set_trace()
                  if ref:
                     errore=False
                     item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)]) 
                     if item: # update
                        try:
                            modify_id = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data)
                            product_id=item[0]
                        except:
                            print "[ERR] Riga:", item_id, "PRODOTTI", "Modificando record:", ref
                            errore=True
                            #raise  # TODO ripristinare??
                        if verbose: 
                           print "[INFO]Riga:", item_id, counter['tot'], "Prodotto aggiornato:", ref
                        # product.packaging ************************************   
                        if not errore:                           
                           data_packaging = {#'code': False, 
                                             #'name': False, 
                                             #'rows': 1, 
                                             #'sequence': 1, 
                                             #'ul_qty': 0, 
                                             #'ean': False, 
                                             'weight': 0.0, 
                                             'ul': 1,  #[1, 'Scatolone'], Messo fisso per velocizzare TODO vedere se parametrizzare
                                             'qty': pezzi_x_imballo, 
                                             'q_x_container': q_x_container, 
                                             'weight_ul': 0.0, 
                                             'container_id': container_id, # [1, "HQ 40''"],   TODO fare funzione per ricavare 
                                             'product_id': product_id,
                                             
                                             # Tolti perchè Roberta inizia a modificarli *****************
                                             #'height': height_pack, 
                                             #'length': length_pack, 
                                             #'width': width_pack, 
                                                               
                                             #'dimension_text': dimension_text_pack,
                                             #'error_dimension_pack': error_dimension_pack,
                                             }   
                                             
                           item_pack = sock.execute(dbname, uid, pwd, 'product.packaging', 'search', [('product_id', '=', product_id)]) 
                           if item_pack:
                              try:
                                  modify_id = sock.execute(dbname, uid, pwd, 'product.packaging', 'write', item_pack, data_packaging)
                                  packaging_id=item_pack[0]
                              except:
                                  print "[ERR] Riga:", item_id, ">>>> PACK: Modificando il packaging per:", ref
                           else: # da creare
                              try:
                                  packaging_id = sock.execute(dbname, uid, pwd, 'product.packaging', 'create', data_packaging)
                              except:
                                  print "[ERR] Riga:", item_id, ">>>> PACK:  Creando il packaging per: ", ref
                           # product.supplierinfo ******************************
                           data_supplierinfo = {#'pricelist_ids': [1], 
                                                'name': supplier_id, # TODO mettere la ditta corretta (per ora GPB) [2321, 'Abc Autotrasporti'], 
                                                'product_uom': uom_id, #[1, 'PCE'], 
                                                #'sequence': 1, 
                                                #'product_name': False, 
                                                'qty': 1.0, 
                                                'delay': 1, 
                                                'min_qty': 1.0, 
                                                'product_code': supplier_code, #'GLA 6386-110', 
                                                'product_id': product_id, #[10187, 'SEDIA NUMERO 123123']
                                                }
                           item_supplierinfo = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'search', [('product_id', '=', product_id)]) 
                           if item_supplierinfo:
                              try:
                                  modify_id = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'write', item_supplierinfo, data_supplierinfo)
                                  supplierinfo_id=item_supplierinfo[0]
                              except:
                                  print "[ERR] Riga:", item_id, ">>>> SUPPL: Modificando il supplierinfo per:", ref
                           else: # da creare
                              try:
                                  supplierinfo_id = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'create', data_supplierinfo)
                              except:
                                  print "[ERR] Riga:", item_id, ">>>> SUPPL:  Creando il supplierinfo per: ", ref
                           # pricelist.partnerinfo *****************************       
                           if supplierinfo_id:
                              data_pricelist = {
                                                'price_usd': fob_cost[4], 
                                                #'name': False, 
                                                'price': fob_cost_2012_eur, # TODO vedere il calcolo in euro perchè è discordante!
                                                'suppinfo_id': supplierinfo_id, #[1, '2321'], 
                                                #'date_quotation': False, 
                                                #'id': 1, 
                                                #'supplier_id': [2321, 'Abc Autotrasporti'], 
                                                'min_quantity': 1.0, 
                                                #'product_name': 'SEDIA NUMERO 123123', 
                                                #'product_id': product_id, #[10187, 'SEDIA NUMERO 123123']
                                                }
                              item_pricelist = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'search', [('suppinfo_id', '=', supplierinfo_id)]) 
                              if item_pricelist:
                                 try:
                                     modify_id = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'write', item_pricelist, data_pricelist)
                                     pricelist_id=item_pricelist[0]
                                 except:
                                     print "[ERR] Riga:", item_id, ">>>> PRICELIST: Modificando il listino per:", ref
                              else: # da creare
                                 try:
                                     pricelist_id = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'create', data_pricelist)
                                 except:
                                     print "[ERR] Riga:", item_id, ">>>> PRICELIST:  Creando il listino per: ", ref
                           # product.product.history.cost **********************                           
                           for i in range(0,4): # da 0 a 4 per: 2008,2009,2010,2011                           
                               #pdb.set_trace()                           
                               if fob_cost[i] or pricelist[i]: # almeno uno dei due
                                  data_history = {'name': "Anno " + storico_anni[i],
                                                  'fob_cost': fob_cost[i], # USD
                                                  'fob_pricelist': pricelist[i], # USD
                                                  'date': storico_anni[i] + "-12-31",
                                                  'product_id': product_id,
                                                  'usd_exchange': 0.0, # TODO vedere se è necessario calcolarlo                                           
                                                  }
                                  item_history = sock.execute(dbname, uid, pwd, 'product.product.history.cost', 'search', [('name', '=', "Anno " + storico_anni[i]),('product_id','=',product_id)]) 
                                  if item_history:
                                     try:
                                        modify_id = sock.execute(dbname, uid, pwd, 'product.product.history.cost', 'write', item_history, data_history)
                                     except:
                                        print "[ERR] Riga:", item_id, ">>>> HISTORY: Modificando lo storico per:", ref, sys.exc_info()[0]
                                  else: # da creare
                                     try:
                                        history_id = sock.execute(dbname, uid, pwd, 'product.product.history.cost', 'create', data_history)
                                     except:
                                        print "[ERR] Riga:", item_id, ">>>> HISTORY:  Creando lo storico per: ", ref, sys.exc_info()[0]
                                               
                     else: # nessun prodotto trovato!
                        print "[ERR]Riga:", item_id, counter['tot'], "Codice non trovato:", ref, "<"*20
                  else:         
                      print "[ERR]Riga:", item_id, counter['tot'], "Codice inesistente!"                      
           else:
               print "[ERR]Riga:", item_id, counter['tot'], "Riga vuota o con colonne diverse", tot_col, len(line)
except:
    #pdb.set_trace()
    print '>>> [ERR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
print "Importazione terminata!"
