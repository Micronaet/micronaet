#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Prima: " "  da sostituire con niente (per eliminare l'euro)
# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, string, ConfigParser, os, pdb, sys
from datetime import datetime
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))
verbose=False
error=True # Comunica gli errori
# TODO parametrize:
taxd="21a"
taxc="21b"

# Start main code *************************************************************
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value=1.0 # for problems in pricelist starting with cost price = 0 

# IVA per prodotti:
taxd="21a"
taxc="21b"
iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)

# Elenco unità di misura:
uom_todo=[]
uom_nr=getUOM(sock,dbname,uid,pwd,'PCE',{}) 
uom_kg=getUOM(sock,dbname,uid,pwd,'kg',{})
uom_m=getUOM(sock,dbname,uid,pwd,'m',{})
uom_hour=getUOM(sock,dbname,uid,pwd,'Hour',{})
uom_m2=getUOM(sock,dbname,uid,pwd,'M2',{})
uom_lt=getUOM(sock,dbname,uid,pwd,'LT',{})
uom_pk=getUOM(sock,dbname,uid,pwd,'PK',{})
uom_p2=getUOM(sock,dbname,uid,pwd,'P2',{})
uom_p10=getUOM(sock,dbname,uid,pwd,'P10',{})
uom_kw=getUOM(sock,dbname,uid,pwd,'KW',{})
uom_m3=getUOM(sock,dbname,uid,pwd,'M3',{})

# Carico i valori dell'IVA deb/cred
iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)
if not (iva_credito and iva_debito):
   print "[ERROR] Non è stata trovata l'IVA credito o debito da applicare:", data
errori_iva=[]

# 1. Importazione Fornitori (verificare che esiste il nome per ricavare l'id, se non esiste occorre correggere il codice)
# 2. Importazione Categorie dei prodotti (attualmente presenti in macro categorie: Prodotti, Materie Prime, Lavorazioni, Non Classificato; e tutte le sottocategorie)
# 3. Importazione Distinta (verifica presenta del codice articolo per ricavare l'ID - servirà a popolare i componenti)
# 4. Importazione Componenti (Verifica del codice utilzzato, inserimento prezzi in funzione del fornitore per ordinativo 1)
# 5. Importazione Relazione (Abbinamento vero e proprio prodotto con componente)
# 6. Importazione Storico (Importare vecchie variazioni di prezzo nella tabella degli storici componente) <<<<< Modulo a parte

# Problematiche: 
# 1. Unità di misura (ricavare e controllare che esista)
# 2. IVA del componente

# 00. Caricamento lista fornitori derivata da componenti:
print " " * 20, "[IMPORTAZIONE PREZZI COMPONENTI]"
lines = csv.reader(open('prezzi.csv','rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0,} # tot negative (jump N lines)
prezzi_componente={}
try:
  for line in lines:
      if counter['tot']<0:  # jump n lines of header 
         counter['tot']+=1
      else: 
        if len(line): # jump empty lines
           counter['tot']+=1 
           csv_id=0 
           code = Prepare(line[csv_id]).upper() # code
           csv_id+=1
           p1 = Prepare(line[csv_id]) # Prezzo1
           csv_id+=1
           p2 = Prepare(line[csv_id]) # Prezzo1
           csv_id+=1
           p3 = Prepare(line[csv_id]) # Prezzo1
           csv_id+=1
           p4 = Prepare(line[csv_id]) # Prezzo1
           csv_id+=1
           p5 = Prepare(line[csv_id]) # Prezzo1
           csv_id+=1
           prezzi_componente[code] = [p1,p2,p3,p4,p5]
except:
    print '[ERROR] *** Importing price!'
    raise 

# 0. Caricamento lista fornitori derivata da componenti:
print " " * 20, "[IMPORTAZIONE FORNITORI MICRONAET]"
lines = csv.reader(open('MicronaetFornitori.csv','rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0,} # tot negative (jump N lines)
micronaet_partner= {}
try:
    for line in lines:
        if len(line): # jump empty lines
           counter['tot']+=1 
           csv_id=0 
           ref = Prepare(line[csv_id]) # ID 
           csv_id+=1
           name = Prepare(line[csv_id]).title() # ID 
           csv_id+=1
           mexal_s = Prepare(line[csv_id])
           csv_id+=1
             
           # PRODUCT CREATION ***************
           if mexal_s: 
              item= sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_s', '=', mexal_s)]) # TODO supplier filter?
              if item: # update
                 micronaet_partner[name]=item[0]       # memorizzo gli ID del name partner
                 if verbose:
                    print "Fornitore trovato:", mexal_s
              else:
                 print "[ERRORE] *** Fornitore non trovato!:", mexal_s   
           else:
              print "[ERRORE] *** Manca il codice mexal nel file CSV!:", name
except:
    print '[ERROR] *** Importing partner!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

'''# 1. Importazione fornitori (ricerca di quelli presenti e lettura del codice)<< TODO vedere se serve
lines = csv.reader(open('Fornitori.csv','rb'),delimiter=separator)
header_lines = 1 # non header on CSV file
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               csv_id=0 
               ref = Prepare(line[csv_id]) # ID 
               csv_id+=1
               name = Prepare(line[csv_id]).title() # ID 
               csv_id+=1
                 
               item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('name', '=', name), ('import', '=', True)]) # TODO supplier filter?
               if item: # update
                  counter['upd'] += 1  
                  #if verbose: 
                  #   print "[INFO]", counter['tot'], "Trovato: ", ref, name
               else:           
                  counter['new'] += 1  
    print "[INFO]","Fornitori:", "Totale: ",counter['tot']," (non trovati: ",counter['new'],") (trovati: ", counter['upd'], ")"
except:
    print '[FINAL ERROR] Importing partner!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

if counter['new']>0:
   print "Non procedo con l'importazione finché non saranno corretti i file di input"'''

# 2. Importazione categorie (ricerca di quelli presenti e lettura del codice)
#### Per ora non create, solo un controllo per vedere quelle esistenti:
print " " * 20, "[VERIFICA CATEGORIE SE PRESENTI]"
lines = csv.reader(open('Categorie.csv','rb'),delimiter=separator)
header_lines = 1 # non header on CSV file
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               csv_id=0 
               ref = Prepare(line[csv_id]) # ID 
               csv_id+=1
               name = Prepare(line[csv_id]).title() # Categoria
               csv_id+=1
               description = Prepare(line[csv_id]).title() # Descrizione
                 
               error="Searching product with ref"
               parent_id = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('name', '=', "Materie Prime")]) 
               item = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('name', '=', name)]) #, ('parent_id', '=', parent_id)]) 
               if item: # update
                  item_distinta = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('name', '=', name)]) #, ('parent_id', '=', parent_id)]) 
                  counter['upd'] += 1  
               else:           
                  counter['new'] += 1  
                  error="Categoria da aggiungere: ", ref, name
                  if error: 
                     print "[INFO]",counter['tot'], "Non trovato: ", ref, name
    print "[INFO]","Categoria:", "Totale: ",counter['tot']," (non trovati: ",counter['new'],") (trovati: ", counter['upd'], ")"
except:
    print '[FINAL ERROR] Importing category!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
if counter['new']>0:
   print "Ci sono categorie ancora non presenti in openerp!"

# 3. Importazione Distinta (ricerca codici se sono presenti)
print " " * 20, "[IMPORTAZIONE DISTINTA E PRODOTTO]"
lines = csv.reader(open('Distinte.csv','rb'),delimiter=separator)
header_lines = 1 # non header on CSV file
counter={'tot':-header_lines,'new':0,'upd':0, 'no': 0,} # tot negative (jump N lines)
error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               csv_id=0 
               ref = Prepare(line[csv_id]).upper() # Codice
               csv_id+=1
               name = Prepare(line[csv_id]).title() # Nome prodotto
               csv_id+=1
               variant = Prepare(line[csv_id]).title() # Variante
                 
               error="Searching product with ref"
               data_distinta={'bom_id': False, 
                              'active': True, 
                              'product_uom': uom_nr, 
                              'product_qty': 1.0, 
                              'product_rounding': 0.0, 
                              'name': '[%s] %s'%(ref, name), 
                              'sequence': 0, 
                              }
               # Controllo l'esistenza del prodotto prima di creare la distinta:
               # Prodotto esistente:
               item  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)]) #, ('parent_id', '=', parent_id)]) 
               # Prodotto esistente creato da questa procedura (non importato)
               item_created  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref), ('import','=',False)]) 
               if not item or item_created: # non esiste il prodotto o è stato creato qui! (per le modifiche)
                  # code like 005PP, 005TW, 045TW ecc. (ovvero è un padre), negli altri casi
                  # è il programma di importazione che crea il prodotto precedentemente
                  # creato in mexal
                  if (len(ref)<=6) and (" " not in (ref)):
                     ref_name="[%s] %s"%(ref, name,)
                     data_product={'name': ref_name,
                           'mexal_id': ref,            #'import': True,
                           'sale_ok':True,
                           'purchase_ok': True,
                           'default_code': ref,
                           'uom_id': uom_nr,           # TODO test if it is NR
                           'uom_po_id': uom_nr,        # TODO test if it is NR
                           'type': 'product',          # TODO parametrize: product consu service
                           'supply_method': 'produce', # TODO parametrize: produce buy
                           'standard_price': 0.0,      # ex bug_start_value
                           'list_price': 0.0,
                           'procure_method': 'make_to_order', 
                           'q_x_pack': 1,  # ex. lot
                           'description_sale': ref_name, # preserve original name (not code + name)<<<<<<<<<
                           'name_template': ref_name,    
                           'taxes_id': [(6,0,[iva_debito])],    # TODO Tax always 20% ???
                           'supplier_taxes_id': [(6,0,[iva_credito])],
                           } # TODO Categorie da creare / modificare
                     if item_created: # modifico se è stato creato qui
                        mod_product_item = sock.execute(dbname, uid, pwd, 'product.product', 'write', item[0], data_product)
                        if verbose: 
                           print "[INFO]"," *** Aggiornamento prodotto creato da questa procedura: ", ref
                     else:
                        item = sock.execute(dbname, uid, pwd, 'product.product', 'create', data_product)
                        item=[item,]
                        if verbose: 
                           print "[INFO]"," *** Creazione prodotto da questa procedura: ", ref
               if item:
                  data_distinta['product_id']= item[0] # Only update (instead must exits product)!!
                  item_distinta = sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', [('product_id', '=', item[0]),('bom_id', '=', False)]) 
                  if item_distinta: # Esiste la distinta
                     mod_distinta = sock.execute(dbname, uid, pwd, 'mrp.bom', 'write', item_distinta[0], data_distinta)
                     counter['upd'] += 1  
                     if verbose: 
                        print "[INFO]",counter['tot'], "Aggiornato: ", ref
                  else: # Non esiste la distinta
                     counter['new'] += 1  
                     new_distinta = sock.execute(dbname, uid, pwd, 'mrp.bom', 'create', data_distinta)                     
                     if verbose: 
                        print "[INFO]",counter['tot'], "Nuovo: ", ref
               else:           
                  counter['no'] += 1  
                  error="[ERRORE] *** Prodotto da aggiungere prima della creazione distinta!: ", ref, name  # TODO rivedere la condizione!!!!!
                  if error: 
                     print "[INFO]",counter['tot'], " ************************* Non trovato: ", ref, name
    print "[INFO]","Prodotto:", "Totale: ", counter['tot']," (non trovati: ",counter['new'],") (trovati: ", counter['upd'], ")", " >>> No prod.:", counter['no']
except:
    print '[FINAL ERROR] Imporing BOM!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
if counter['new']>0:
   print "Non procedo con l'importazione finché non saranno corretti i file di input"
if uom_todo:
   print "[ERRORE] *** Unità di misura trovate non presenti e da creare:", uom_todo

# 4. Importazione Componenti come prodotti, con la corretta categorie e i prezzi relativi ai corretti fornitori
print " " * 20, "[IMPORTAZIONE COMPONENTI IN PRODOTTI]"
lines = csv.reader(open('Componenti.csv','rb'),delimiter=separator)
header_lines = 1 # non header on CSV file
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)
uom_todo=[] # riazzero il contatore errori uom

error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            supplier_id={}; unit_price={}; date={}; lot={} #; unit_price_old={}
            
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               csv_id=0 
               ref = Prepare(line[csv_id]).upper() # ID 
               csv_id+=1
               name = Prepare(line[csv_id]).title() 
               csv_id+=1
               s_name = Prepare(line[csv_id]).title() 
               csv_id+=1
               s_ref = Prepare(line[csv_id]).upper()  
               csv_id+=1
               fatto = Prepare(line[csv_id]).upper()  
               csv_id+=1
               category = Prepare(line[csv_id]).title()  
               csv_id+=1
               #pdb.set_trace()
               uom = Prepare(line[csv_id]).upper()  
               if uom in  ['KN', 'CN', 'KS', 'PK', 'MN', 'CM', 'RT', 'PR']: # trasformo in NR le UM strane
                  uom = "NR"
               csv_id+=1

               supplier_id[0]=Prepare(line[csv_id])
               csv_id+=1
               unit_price[0] = prezzi_componente[ref][0] # Prepare(line[csv_id])
               csv_id+=1
               #unit_price_old[0] = Prepare(line[csv_id])
               csv_id+=1
               date[0] = Prepare(line[csv_id])
               csv_id+=1
               #lot[0] = Prepare(line[csv_id])
               csv_id+=1
               
               #weight = Prepare(line[csv_id])
               csv_id+=1

               supplier_id[1] = Prepare(line[csv_id])
               csv_id+=1
               unit_price[1] = prezzi_componente[ref][1] #Prepare(line[csv_id])
               csv_id+=1
               #unit_price_old[1] = Prepare(line[csv_id])
               csv_id+=1
               date[1] = Prepare(line[csv_id])
               csv_id+=1
               #lot[1] = Prepare(line[csv_id])
               csv_id+=1

               supplier_id[2] = Prepare(line[csv_id])
               csv_id+=1
               unit_price[2] = prezzi_componente[ref][2] #Prepare(line[csv_id])
               csv_id+=1
               #unit_price_old[2] = Prepare(line[csv_id])
               csv_id+=1
               date[2] = Prepare(line[csv_id])
               csv_id+=1
               #lot[2] = Prepare(line[csv_id])
               csv_id+=1

               supplier_id[3] = Prepare(line[csv_id])
               csv_id+=1
               unit_price[3] = prezzi_componente[ref][3] #Prepare(line[csv_id])
               csv_id+=1
               #unit_price_old[3] = Prepare(line[csv_id])
               csv_id+=1
               date[3] = Prepare(line[csv_id])
               csv_id+=1
                 
               supplier_id[4] = Prepare(line[csv_id])
               csv_id+=1
               unit_price[4] = prezzi_componente[ref][4] #Prepare(line[csv_id])
               csv_id+=1
               #unit_price_old[4] = Prepare(line[csv_id])
               csv_id+=1
               date[4] = Prepare(line[csv_id])
               csv_id+=1

               lost = Prepare(line[csv_id])
               csv_id+=1

               # Campi calcolati:
               #    Blocco unità di misura
               if uom.upper() in ['NR', 'N.', 'PZ']: # PCE
                  uom_id=uom_nr 
               elif uom.upper() in ["M2", "MQ"]: 
                  uom_id=uom_m2 
               elif uom.upper() in ["M", "MT", "ML"]: # note: after M2!! 
                  uom_id=uom_m
               elif uom.upper() == "HR": 
                  uom_id=uom_hour
               elif uom.upper() == "KG": 
                  uom_id=uom_kg
               elif uom.upper() == "LT": 
                  uom_id=uom_lt
               elif uom.upper() == "KW": 
                  uom_id=uom_kw
               elif uom.upper() in ["M3", "MC"]: 
                  uom_id=uom_m3
               elif uom.upper() in ["PA", "CO", "CP"]: 
                  uom_id=uom_p2
               elif uom.upper() == "PC": 
                  uom_id=uom_p10
               else: 
                  if uom not in uom_todo:
                     uom_todo.append(uom)
                  uom_id=uom_nr # for now is NR till introduce of new uom

               error="Searching product with ref"
               # Cerco quelli che possono essere presenti con il codice di mexal
               # Prodotto/Componente già presente:
               item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)]) 
               # Prodotto/Componente già presente e creato da questa procedura:
               item_created  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref), ('import','=',False)])
               if item: 
                  item_product_id_prec=item[0]
               if not item or item_created: # non esiste il prodotto (o è stato creato qui!)
                  ref_name= name
                  data_product={'name': ref_name,
                       'mexal_id': ref,
                       'sale_ok':True,
                       'purchase_ok': True,
                       'default_code': ref,
                       'uom_id': uom_id,         
                       'uom_po_id': uom_id,
                       #'code': ref,      
                       'type': 'product',          # TODO parametrize: product consu service
                       'supply_method': 'produce', # TODO parametrize: produce buy
                       'standard_price': 0.0,      # ex bug_start_value
                       'list_price': 0.0,
                       'procure_method': 'make_to_order', 
                       'q_x_pack': 1,  
                       'description_sale': ref_name, # preserve original name (not code + name)<<<<<<<<<
                       'name_template': ref_name,    
                       'taxes_id': [(6,0,[iva_debito])],    # TODO Tax always 20% ???
                       'supplier_taxes_id': [(6,0,[iva_credito])],
                       } # TODO Categorie da creare / modificare
                  if item_created: # modifico se è stato creato qui
                     mod_product_item = sock.execute(dbname, uid, pwd, 'product.product', 'write', item[0], data_product)
                     if verbose: 
                         print "[INFO]"," *** Aggiornamento componente: ", ref
                     counter['upd'] += 1              
                  else:
                     item = sock.execute(dbname, uid, pwd, 'product.product', 'create', data_product)
                     item_product_id_prec=item
                     item=[item,]
                     if verbose: 
                         print "[INFO]"," *** Creazione componente: ", ref
                     counter['new'] += 1      
               else: # esiste il prodotto e non è stato creato qui!
                  item_read = sock.execute(dbname, uid, pwd, 'product.product', 'read', item) 
                  if item_read[0]['uom_id'][0]!=uom_id:
                     print "[ERRORE] *** Discordanza tra unità di misura (1: %s 2: %s) per prodotto: %s (uniformata a quella presente nel prodotto!)" % (item_read[0]['uom_id'][0], uom_id, ref,) 
                     uom_id=item_read[0]['uom_id'][0]
                     
               # PREZZI PER FORNITORE ***************
               if item: # Creo i prezzi se esiste l'articolo   
                  # Carico quello con il prezzo migliore
                  ultima_data=""
                  for i in range(0,1): #,5): # Eliminato blocchi successivi TODO cercare il migliore per data!
                      if supplier_id[i]=="0": # per eliminare controlli inutili
                         supplier_id[i]=""
                      if not supplier_id[i]:
                         supplier_id[i]="FIAM"
                      if supplier_id[i]: # solo se esiste!
                          if supplier_id[i].title() in micronaet_partner: # (se esiste nella lista caricata al punto 0)
                             item_partner_id= micronaet_partner[supplier_id[i].title()]
                          else:
                             item_partner_id=''   # Manca il codice del fornitore in openerp
                          #item_partner_id = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('name', '=', supplier_id[i])])                       
                          if item_partner_id:   
                             supplierinfo_data= { # PRODUCT.SUPPLIERINFO
                                     #'pricelist_ids': [1], 
                                     'name': item_partner_id,
                                     'product_uom': uom_id, # arriva da prima 
                                     #'sequence': 1, 
                                     #'company_id': [1, 'Fiam'], 
                                     'qty': 0.0, 
                                     'delay': 1, 
                                     'min_qty': 0.0, 
                                     'product_id': item_product_id_prec, # product_id #_partner_id,
                                     'product_name': s_name,  # del fornitore
                                     'product_code': s_ref,   # del fornitore
                                     }

                             item_supplierinfo = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'search', 
                                                 [('name', '=', item_partner_id), ('product_id', '=', item_product_id_prec)])
                             if item_supplierinfo:
                                #try:
                                item_supplierinfo_mod = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'write', item_supplierinfo, supplierinfo_data)
                                #except:
                                #   import pdb; pdb.set_trace()   
                                item_supplierinfo=item_supplierinfo[0] 
                             else:
                                item_supplierinfo = sock.execute(dbname, uid, pwd, 'product.supplierinfo', 'create', supplierinfo_data)
                             if item_supplierinfo:
                                if not unit_price[i]:
                                   print "[ERRORE] *** Prezzo non trovato! %s - %s > %s - € %s" % (ref, name, supplier_id[i], unit_price[i])
                                
                                partnerinfo_data= {
                                      'min_quantity': 1.0, # TODO vedere per il lotto!
                                      'price': float(unit_price[i].replace(".","").replace(",",".") or '0'), 
                                      'suppinfo_id': item_supplierinfo, # link
                                      #'name': False,
                                      }
                                if date[i]:
                                   partnerinfo_data['date_quotation']= date[i]
                                item_partnerinfo = sock.execute(dbname, uid, pwd, 
                                                   'pricelist.partnerinfo', 
                                                   'search', 
                                                   [('suppinfo_id', '=', item_supplierinfo)]) # Faccio solo un prezzo!
                                if item_partnerinfo:
                                   item_partnerinfo_mod = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'write', item_partnerinfo , partnerinfo_data)
                                else:
                                   item_partnerinfo = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'create', partnerinfo_data)
                             else:
                                 if error:
                                    print "*** No Supplier info" + " " * 40, supplierinfo_data
                          else:           
                              if error:
                                 print "*** No partner" + " " * 20, supplier_id[i] 
    print "[INFO]","Prodotto:", "Totale: ",counter['tot']," (non trovati: ",counter['new'],") (trovati: ", counter['upd'], ")"
except:
    print '[FINAL ERROR] Importing category!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
if uom_todo:
   print "[ERRORE] *** UM Mancanti nei componenti:",uom_todo

# 5. Abbinamento componenti con elemento distinta base:
print " " * 20, "[CREAZIONE ABBINAMENTI COMPONENTI DISTINTA]"
lines = csv.reader(open('Relazione.csv','rb'), delimiter=separator)
header_lines = 1 # non header on CSV file
counter={'tot':-header_lines,'new':0,'upd':0, 'no': 0,} # tot negative (jump N lines)
error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               # Jumped ID access
               csv_id=1
               padre = Prepare(line[csv_id]).upper()       # Codice padre
               csv_id+=1
               componente = Prepare(line[csv_id]).upper()  # Codice componente
               csv_id+=1
               q = PrepareFloat(line[csv_id])              # Quantità
                 
               item_product  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', padre), ]) 
               item_component  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', componente), ]) 

               if item_product and item_component and q:
                  item_bom  = sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', [('product_id', '=', item_product[0]), ('bom_id','=',False) ]) 
                  item_component_data  = sock.execute(dbname, uid, pwd, 'product.product', 'read', item_component[0])  # for get name and uom_id
                  if item_bom: 
                     data_component= {'product_qty': q, 
                                      'product_id': item_component[0], #[9434, '[TWH044] [TWH044] Tessuto Twh H.44'], 
                                      'bom_id': item_bom[0], #[1, '[127] Fiesta'], 
                                      #    Da ricavare:
                                      'name': item_component_data['name'], 
                                      'product_uom': item_component_data['uom_id'][0], 
                                      'product_uos': item_component_data['uom_id'][0], 
                                      #    Default:
                                      #'type': 'normal', 'method': 'order', 
                                      #    Non necessari:
                                      #'product_uos': False, #'active': True,                                
                                      #'product_uos_qty': 0.0,'product_efficiency': 1.0, 
                                      #'product_rounding': 0.0,'code': False, 
                                      #'revision_ids': [], 'date_start': False, 'company_id': [1, 'Fiam'], 
                                      #'routing_id': False, 'bom_lines': [], property_ids': [], 'date_stop': False, 
                                      #'sequence': 0, 'child_complete_ids': [], 'position': False
                                     }
                  item_bom_comp = sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', [('product_id', '=', item_component[0]), ('bom_id','=', item_bom[0])])
                  if item_bom_comp: 
                     mod_bom_comp = sock.execute(dbname, uid, pwd, 'mrp.bom', 'write', item_bom_comp[0], data_component)
                     if verbose: 
                         print "[INFO]"," *** Modifica componente distinta: ", padre, componente, q
                     counter['upd'] += 1  
                  else: 
                     item = sock.execute(dbname, uid, pwd, 'mrp.bom', 'create', data_component)
                     if verbose: 
                         print "[INFO]"," *** Creazione componente distinta: ", padre, componente, q
                     counter['new'] += 1  
               else:           
                  counter['no'] += 1  
                  print "[ERRORE] *** Padre: %s Componente: %s, Quant.: %s non trovate: " % (padre, componente, q,)
    print "[INFO]","Componenti Distinta base:", "Totale: ", counter['tot']," (non trovati: ",counter['new'],") (trovati: ", counter['upd'], ")", " >>> No prod.:", counter['no']
except:
    print '[FINAL ERROR] Global import!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug
