#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib
import csv
import sys
import time
import string
import ConfigParser
import os
import shutil
from mx.DateTime import now
from mic_ETL import *
from fiam import *

# Start main code *************************************************************
if len(sys.argv) != 2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py nome_file.csv 
         *********************
         """ 
   sys.exit()

if sys.argv[1][-3:] == "FIA":
   cfg_file = "openerp.cfg"
   azienda = "fia"
else:
   cfg_file = "openerp.gpb.cfg"
   azienda = "gpb"
   
# Set up parameters (for connection to Open ERP Database) *********************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint
separator = config.get('dbaccess', 'separator') # test
verbose = eval(config.get('import_mode', 'verbose'))

file_transcode_log = "transcode.log"
#if azienda == 'gpb'
#    try:
#        convert_file = config.get('convert', 'list')
#        convert_log = config.get('convert', 'log')
#        file_transcode = os.path.expanduser(convert_file)
#        file_transcode_log = os.path.expanduser(convert_log)
#        
#    except:
#        print "Log file not found in openerp.gpb.cfg file!!"
#        sys.exit()

# TODO parametrize:
taxd = "21a"
taxc = "21b"

header_lines = 0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname, user, pwd)
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value = 1.0 # for problems in pricelist starting with cost price = 0 

# Gestione unità di misura:
uom_todo = []
ID_uom_categ_unit = getUomCateg(sock, dbname, uid, pwd, 'Unit') # Category Unit

# Nuove:
ID_uom_categ_area = getUomCateg(sock, dbname, uid, pwd, 'Area') # Category Area 
ID_uom_categ_capacity = getUomCateg(sock, dbname, uid, pwd, 'Capacity') # Category Capacità 
ID_uom_categ_power = getUomCateg(sock, dbname, uid, pwd, 'Electric Power') # Category potenza elettrica
ID_uom_categ_volume = getUomCateg(sock, dbname, uid, pwd, 'Volume') # Category Volume

uom_nr = getUOM(sock, dbname, uid, pwd, 'Pz', {}) 
uom_kg = getUOM(sock, dbname, uid, pwd, 'kg', {})
uom_m = getUOM(sock, dbname, uid, pwd, 'm', {})
uom_hour = getUOM(sock, dbname, uid, pwd, 'Hour', {})

# Nuove:
uom_m2 = getUOM(sock, dbname, uid, pwd, 'M2', {
    'name': 'M2', 
    'factor_inv': 1.0, 
    'rounding': 0.01, 
    'uom_type': 'reference', 
    'factor': 1.0, 
    'active': True, 
    'category_id': ID_uom_categ_area,
    })
uom_lt = getUOM(sock, dbname, uid, pwd, 'LT', {
    'name': 'LT', 
    'factor_inv': 1.0, 
    'rounding': 0.01, 
    'uom_type': 'reference', 
    'factor': 1.0, 
    'active': True, 
    'category_id': ID_uom_categ_capacity,
    })
uom_pk = getUOM(sock, dbname, uid, pwd, 'PK', {
    'name': 'PK', 
    'factor_inv': 1000.0, 
    'rounding': 1.0, 
    'uom_type': 'bigger', 
    'factor': 0.001, 
    'active': True, 
    'category_id': ID_uom_categ_unit,
    })
uom_p2 = getUOM(sock, dbname, uid, pwd, 'P2', {
    'name': 'P2', # Paia
    'factor_inv': 2.0, 
    'rounding': 1.0, 
    'uom_type': 'bigger', 
    'factor': 0.5, 
    'active': True, 
    'category_id': ID_uom_categ_unit,
    })
uom_p10 = getUOM(sock, dbname, uid, pwd, 'P10', {
    'name': 'P10', # Decine
    'factor_inv': 10.0, 
    'rounding': 1.0, 
    'uom_type': 'bigger', 
    'factor': 0.1, 
    'active': True, 
    'category_id': ID_uom_categ_unit,
    })
uom_kw = getUOM(sock, dbname, uid, pwd, 'KW', {
    'name': 'KW', 
    'factor_inv': 1.0, 
    'rounding': 0.01, 
    'uom_type': 'reference', 
    'factor': 1.0, 
    'active': True, 
    'category_id': ID_uom_categ_power,
    })                                        
uom_m3 = getUOM(sock, dbname, uid, pwd,'M3', {
    'name': 'M3', 
    'factor_inv': 1.0, 
    'rounding': 0.01, 
    'uom_type': 'reference', 
    'factor': 1.0, 
    'active': True, 
    'category_id': ID_uom_categ_volume,
    })
    
'''
PR (LASCIA PERDERE, ERA UNA PROVA) 
KN LASCIA PERDERE 
KS CONI FILATO (UNITA0 DI MISURA VECCHIA) 

MN MANODOPERA 
CN CONI FILATO 
RT ROTOLI 
CM COMPLETO (SET COMPOSTO DA + PEZZI) 
'''

#  Pricelist
pl_pricelist = [0, 0, 0, 0, 0, 0, 0, 0, 0] # Pricelist for Mexal 4 pricelist  ex. 0,0,0,0,
pl_fiam = [0, 0, 0, 0, 0, 0, 0, 0, 0]    # Version of price list (Mexal 4 pricelist) ex 0,0,0,0,
CreateAllPricelist(sock, dbname, uid, pwd, 
    ('1', '4', '5', '9', '2', '3', '6', '7', '8',), 
    ('EUR', 'EUR', 'EUR', 'EUR', 'EUR', 'EUR', 'EUR', 'EUR', 'EUR',), 
    pl_pricelist, pl_fiam)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput = sys.argv[1]

lines = csv.reader(open(FileInput, 'rb'), delimiter=separator)
counter = {'tot': -header_lines, 'new':0, 'upd':0} # tot negative (jump N lines)

iva_credito = getTaxID(sock, dbname, uid, pwd, taxc)
iva_debito = getTaxID(sock, dbname, uid, pwd, taxd)
errori_iva = []

if not (iva_credito and iva_debito):
   print "[ERROR] Non è stata trovata l'IVA credito/debito da applicare:", data
error = ''

# --------------------------
# Load transcode dictionary:
# --------------------------
transcode_log = open(file_transcode_log, 'a')        
transcode = {}
new_code = {}

if azienda == 'gpb': # Preload transcode
    i = 0
    image_path = os.path.expanduser("~/photo/gpb/product/default")
    extension_image = "jpg"
    for code_line in csv.reader(open(file_transcode, 'rb'), delimiter=";"):
        i += 1
        if len(code_line) != 2 or code_line[0] == 'old': 
            transcode_log.write("[WARN] %s. Riga anomala in convert.txt: '%s'\r\n" % (
                i, code_line))
            continue
        transcode[Prepare(code_line[0])] = Prepare(code_line[1])
        
        # Copio il file dell'immagine
        new_image = os.path.join(image_path, "%s.%s" % (
            code_line[1], extension_image))

        if not os.path.isfile(new_image): # non esiste nuova immagine
            try:
                shutil.copy(
                    os.path.join(image_path, "%s.%s" % (
                        code_line[0], extension_image), ),
                    new_image,    
                    )
            except:
                transcode_log.write("[ERR] %s. Impossibile creare file immagine '%s'\r\n" % (
                    i, code_line))

# TODO GPB: update product_product set active='t'; # set all product active
try:
    for line in lines:
        if counter['tot'] < 0:  # jump n lines of header 
           counter['tot'] += 1
        else: 
            if len(line): # jump empty lines
               counter['tot'] += 1 
               error = "Importing line" 
               price = [0.0, 0.0, 0.0, 0.0]
               ref = Prepare(line[0])
               name = Prepare(line[1]).title()
               uom = Prepare(line[2]).title()
               taxes_id = Prepare(line[3])
               ean = Prepare(line[4])
               try: # Q per pack
                  lot = eval(Prepare(line[5]).replace(',', '.'))
               except:
                  lot = 1

               if lot > 0 and lot < 1:
                   import pdb; pdb.set_trace()
                   colls = 1 / lot
               else:
                   colls = 1

               price[0] = PrepareFloat(line[6])   # Price pricelist 1 EUR
               price[1] = PrepareFloat(line[7])   # Price pricelist 4 EUR
               price[2] = PrepareFloat(line[8])   # Price pricelist 5 CHF
               price[3] = PrepareFloat(line[9])   # Price pricelist 9 EUR

               # Language:
               Lang_EN = Prepare(line[10]).title()  # Article EN
               Lang_2 = Prepare(line[11]).title()  # TODO Lingua 1
               Lang_3 = Prepare(line[12]).title()  # TODO Lingua 2
               Lang_4 = Prepare(line[13]).title()  # TODO Lingua 3
               # Parte dimensioni:
               linear_length = PrepareFloat(line[14])   # Lunghezza lineare
               volume = PrepareFloat(line[15])   # Volume M3
               weight = PrepareFloat(line[16])   # Peso (lordo?) TODO vedere se e' netto

               if azienda == 'fia':
                   active = True
               elif azienda == 'gpb' and Prepare(line[17]).strip() == 'C01':
                   active = True 
               else:    
                   active = False
               
               colour = Prepare(line[18])   
                
                   
               item = sock.execute( # search current ref
                   dbname, uid, pwd, 'product.product', 'search', [
                       ('mexal_id', '=', ref)])
                       
               # ---------------------------
               # Test if to transcode (GPB):
               # ---------------------------
               if azienda == 'gpb' and ref in transcode: # Exist transcode
                   new_ref = transcode[ref]
                   item_new = sock.execute( # Search new code (if yet created)
                       dbname, uid, pwd, 'product.product', 'search', [
                           ('mexal_id', '=', new_ref)])
                   if item: # old present
                       if item_new: # old and new present
                           if len(item_new) > 1:
                               transcode_log.write(
                                   "[ERR] Più di uno nuovi (non fatto nulla): %s > %s\r\n" % (
                                       ref, new_ref))
                           else: # delete new
                               sock.execute(
                                   dbname, uid, pwd, 'product.product',
                                   'unlink', item_new) # Delete new record 
                               transcode_log.write("[WAR] Delete new code: %s (vecchio: %s)\r\n" % (
                                      new_ref, ref))
                       ref = new_ref # for rename

                   elif item_new: # new only present
                       #transcode_log.write("[WAR] Salto vecchio codice: %s (nuovo: %s)\n" % (
                       #       ref, new_ref))
                       continue # jump 

               # Calculated field:
               #    Blocco unità di misura
               if uom.upper() in ['NR', 'N.', "PZ"]: # PCE
                  uom_id = uom_nr 
               elif uom.upper() in ["M2", "MQ"]: 
                  uom_id = uom_m2 
               elif uom.upper() in ["M", "MT", "ML",]: # note: after M2!! 
                  uom_id = uom_m
               elif uom.upper() == "HR": 
                  uom_id = uom_hour
               elif uom.upper() == "KG": 
                  uom_id = uom_kg
               elif uom.upper() == "LT": 
                  uom_id = uom_lt
               elif uom.upper() == "KW": 
                  uom_id = uom_kw
               elif uom.upper() in ["M3", "MC"]: 
                  uom_id = uom_m3
               elif uom.upper() in ["PA", "CO", "CP"]: 
                  uom_id = uom_p2
               elif uom.upper() == "PC": 
                  uom_id = uom_p10
               else: 
                  if uom not in uom_todo:
                     uom_todo.append(uom)
                  uom_id = uom_nr # for now is NR till introduce of new uom

               # Blocco lingua  
               name = "[%s] %s" % (ref[0:6].replace(' ', ''), name)
               if Lang_EN:
                  Lang_EN = "[%s] %s" % (ref[0:6].replace(' ', ''), Lang_EN)
                  data_lang = {
                      'lang': 'it_IT', 
                      'src': Lang_EN, # Nome scritto in inglese
                      'xml_id': False, 
                      'name': 'product.template,name',
                      'type': 'model', 
                      'module': False, 
                      'value': name, # Nome in italiano
                      #'res_id': 2, # when created
                      }
                  name = Lang_EN # Nel prodotto rimane invece il nome in inglese               
                  insert_lang = True
               else:
                  insert_lang = False
                 
               data = {
                   'active': active, # for GPB purpose
                   'name': name,
                   'mexal_id': ref,
                   'ean13': ean,
                   'import': True,
                   'sale_ok': True,
                   'purchase_ok': True,
                   'default_code': ref,
                   'uom_id': uom_id,           # TODO test if it is NR
                   'uom_po_id': uom_id,        # TODO test if it is NR
                   'type': 'product',          # TODO parametrize: product consu service
                   'supply_method': 'produce', # TODO parametrize: produce buy
                   #'standard_price': bug_start_value,
                   'list_price': 0.0,
                   'procure_method': 'make_to_order', 
                   'q_x_pack': lot,
                   'description_sale': name, # preserve original name (not code + name)<<<<<<<<<
                   'name_template': name,    
                   'colour': colour,
                   #'description': description,
                   #'description_spurchase'
                   #'lst_price' 
                   #'seller_qty'   
                   }
               if azienda == 'fia':# TODO veder se attivarla anche per la GPB
                  data['volume'] = volume
                  data['linear_length'] = linear_length
                  data['weight'] = weight
                  data['colls'] = colls

               if taxes_id and taxes_id == '21':
                  data['taxes_id'] = [(6, 0, [iva_debito])]
                  data['supplier_taxes_id'] = [(6, 0, [iva_credito])]
               else:
                  errori_iva.append("articolo: %s" % name)                                       
 
               # PRODUCT CREATION ***************
               error = "Searching product with ref"
               ''' non filtro per import che viene utilizzato per capire se è arrivata da qui l'importazione
                   in caso contrario di creazione con script modifico solo mexal_id per permettere così
                   l'aggiornamento di lingua ecc.
               '''
               # -------------------------------------
               # Searched before for trancode problem:
               # -------------------------------------
               if item: # update
                   try:
                       sock.execute(
                           dbname, uid, pwd, 'product.product', 'write', 
                           item, data)
                       product_id = item[0]
                   except:
                       print ("[ERROR] Modify product, current record:", data, 
                           sys.exc_info())
                       #raise  # TODO ripristinare??
                   if verbose: 
                       print "[INFO]", counter['tot'], "Already exist: ", ref, name
               else: # create
                   if not active:
                       if verbose:
                           print "[WARN]", counter['tot'], "Not active, jumped: ", ref, name
                       continue # no recreate if not active
                       
                   counter['new'] += 1  
                   error = "Creating product"
                   try:
                       product_id = sock.execute(
                           dbname, uid, pwd, 'product.product', 'create', data) 
                   except:
                       print ("[ERROR] Create product, current record:", data,
                           sys.exc_info())
                       
                       #raise  # TODO ripristinare??
                   if verbose: 
                       print "[INFO]", counter['tot'], "Insert: ", ref, name
               
               # TRANSLATION UPDATE:
               if insert_lang:  # Only if present lang EN terms in Mexal
                   if product_id:
                      error = "Searching product lang"
                      item_lang = sock.execute(
                          dbname, uid, pwd, 'ir.translation', 'search', [
                              ('lang', '=', 'it_IT'),
                              ('name', '=', 'product.template,name'),
                              ('res_id', '=', product_id),
                              ('value','=', data_lang['value'])  # TODO può dare problemi con traduzione [nuova] [vecchio] descrizione
                              ]) # if english is present it translation is made
                      data_lang['res_id'] = product_id # add product_id for reference!
                      if item_lang: # update
                         try:
                             modify_id_lang = sock.execute(
                                 dbname, uid, pwd, 'ir.translation', 'write', 
                                 item_lang, data_lang)
                             lang_id = item[0]
                         except:
                             print "[ERROR] Modify product lang, record:", data_lang
                             #raise  # TODO ripristinare??
                         if verbose: 
                            print "   [INFO]", "Lang modify:", data_lang['value']
                      else:           
                         error = "Creating product lang"
                         try:
                             lang_id = sock.execute(
                                 dbname, uid, pwd, 'ir.translation', 'create',
                                 data_lang) 
                         except:
                             print "[ERROR] Create product lang, record:", data_lang
                             #raise  # TODO ripristinare??
                         if verbose: 
                            print "   [INFO]","Lang insert: ", data_lang['value']
               if verbose:  # Print only if aren't print info importation TODO?? tolto il "not verbose"
                  if insert_lang:
                     print ref, "\t", name, "\t>>>\t", data_lang['value']   

               # PRICE LIST CREATION/UPDATE:               
               for j in range(0, 4):
                   if price[j]: # if exist price prepare PL item                        
                      item_data = {
                          #'price_round':
                          #'price_min_margin':
                          #'price_discount':
                          #'base_pricelist_id': pl_pricelist[j],  # Price list
                          'price_version_id': pl_fiam[j],   # Price list version (4 pl) # TODO erase cost=1 PL=PL-1
                          'sequence': 10,                    # Sequence for article 4 pl (for partic is less)
                          #'price_max_margin':
                          #'company_id
                          'name': '%s [%s]' % (name, ref),
                          #'product_tmpl_id':
                          'base': 2,    # base price (product.price.type) TODO parametrize: 1 pl 2 cost
                          'min_quantity': 1,
                          'price_surcharge': price[j] - bug_start_value, # Recharge on used base price 
                          #'categ_id':
                          'product_id': product_id,
                          }
                      item_item = sock.execute(
                          dbname, uid, pwd, 'product.pricelist.item', 'search', [
                              ('price_version_id', '=', pl_fiam[j]),
                              ('product_id', '=', product_id)])                
                      try:
                         if item_item: # update
                             modify_item = sock.execute(
                                 dbname, uid, pwd, 'product.pricelist.item', 
                                 'write', item_item, item_data)                                    
                         else:           
                             new_item_id=sock.execute(
                                 dbname, uid, pwd, 'product.pricelist.item', 
                                 'create', item_data) 
                      except:
                          print "[ERROR] Creating/Modifying item in pricelist", item_data
                          #raise # RIPRISTINARE??
except:
    print '>>> [ERROR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

if errori_iva:
   print errori_iva
print "[INFO]","Articles:", "Total: ", counter['tot'], " (imported: ", counter['new'], ") (updated: ", counter['upd'], ")"

if uom_todo:
   print "Unita' di misura da aggiungere!", uom_todo

