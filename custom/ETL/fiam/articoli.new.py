#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from mx.DateTime import now
from mic_ETL import *
from fiam import *

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py nome_file.csv 
         *********************
         """ 
   sys.exit()

if sys.argv[1][-3:]=="FIA":
   cfg_file="openerp.cfg"
   azienda="fia"
else:
   cfg_file="openerp.gpb.cfg"
   azienda="gpb"
   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))

# TODO parametrize:
taxd="21a"
taxc="21b"

header_lines=0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value=1.0 # for problems in pricelist starting with cost price = 0 

# Gestione unità di misura:
uom_todo=[]
ID_uom_categ_unit=getUomCateg(sock,dbname,uid,pwd,'Unit')    # Category Unit
# Nuove:
ID_uom_categ_area=getUomCateg(sock,dbname,uid,pwd,'Area')    # Category Area 
ID_uom_categ_capacity=getUomCateg(sock,dbname,uid,pwd,'Capacity')    # Category Capacità 
ID_uom_categ_power=getUomCateg(sock,dbname,uid,pwd,'Electric Power')    # Category potenza elettrica
ID_uom_categ_volume=getUomCateg(sock,dbname,uid,pwd,'Volume')    # Category Volume

uom_nr=getUOM(sock,dbname,uid,pwd,'PCE',{}) 
uom_kg=getUOM(sock,dbname,uid,pwd,'kg',{})
uom_m=getUOM(sock,dbname,uid,pwd,'m',{})
uom_hour=getUOM(sock,dbname,uid,pwd,'Hour',{})
# Nuove:
uom_m2=getUOM(sock,dbname,uid,pwd,'M2',{'name': 'M2', 
                                        'factor_inv': 1.0, 
                                        'rounding': 0.01, 
                                        'uom_type': 'reference', 
                                        'factor': 1.0, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_area,
                                        })
uom_lt=getUOM(sock,dbname,uid,pwd,'LT',{'name': 'LT', 
                                        'factor_inv': 1.0, 
                                        'rounding': 0.01, 
                                        'uom_type': 'reference', 
                                        'factor': 1.0, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_capacity,
                                        })
uom_pk=getUOM(sock,dbname,uid,pwd,'PK',{'name': 'PK', 
                                        'factor_inv': 1000.0, 
                                        'rounding': 1.0, 
                                        'uom_type': 'bigger', 
                                        'factor': 0.001, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_unit,
                                        })
uom_p2=getUOM(sock,dbname,uid,pwd,'P2',{'name': 'P2', # Paia
                                        'factor_inv': 2.0, 
                                        'rounding': 1.0, 
                                        'uom_type': 'bigger', 
                                        'factor': 0.5, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_unit,
                                        })
uom_p10=getUOM(sock,dbname,uid,pwd,'P10',{'name': 'P10', # Decine
                                        'factor_inv': 10.0, 
                                        'rounding': 1.0, 
                                        'uom_type': 'bigger', 
                                        'factor': 0.1, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_unit,
                                        })
uom_kw=getUOM(sock,dbname,uid,pwd,'KW',{'name': 'KW', 
                                        'factor_inv': 1.0, 
                                        'rounding': 0.01, 
                                        'uom_type': 'reference', 
                                        'factor': 1.0, 
                                        'active': True, 
                                        'category_id': ID_uom_categ_power,
                                        })                                        
uom_m3=getUOM(sock,dbname,uid,pwd,'M3',{'name': 'M3', 
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
pl_pricelist=[0,0,0,0,0,0,0,0,0,]   # Pricelist for Mexal 4 pricelist  ex. 0,0,0,0,
pl_fiam=[0,0,0,0,0,0,0,0,0,]         # Version of price list (Mexal 4 pricelist) ex 0,0,0,0,
CreateAllPricelist(sock, dbname, uid, pwd, ('1', '4', '5', '9','2','3','6','7','8',), ('EUR','EUR','CHF','EUR','EUR','EUR','EUR','EUR','EUR',), pl_pricelist, pl_fiam)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)
errori_iva=[]

if not (iva_credito and iva_debito):
   print "[ERROR] Non è stata trovata l'IVA credito o debito da applicare:", data
error=''
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               '''FIELDS: warranty ean13 supply_method uos_id list_price weight track_production incoming_qty standard_price variants active price_extra mes_type
               uom_id code description_purchase default_code type name_template property_account_income qty_available location_id id uos_coeff 
               property_stock_procurement virtual_available sale_ok purchase_ok product_manager track_outgoing company_id name product_tmpl_id state
               loc_rack uom_po_id pricelist_id price_margin property_stock_account_input description
               valuation price property_stock_production seller_qty supplier_taxes_id volume outgoing_qty loc_row
               description_sale procure_method property_stock_inventory cost_method 
               partner_ref track_incoming seller_delay weight_net packaging seller_id sale_delay loc_case property_stock_account_output
               property_account_expense categ_id lst_price taxes_id produce_delay seller_ids rental
               '''
               price=[0.0,0.0,0.0,0.0,]
               csv_id=0
               ref = Prepare(line[csv_id])
               csv_id+=1
               name = Prepare(line[csv_id]).title()
               csv_id+=1
               uom = Prepare(line[csv_id]).title()
               csv_id+=1
               taxes_id = Prepare(line[csv_id])
               csv_id+=1
               ref2 = Prepare(line[csv_id]) # TODO where put it?
               csv_id+=1
               lot_str = Prepare(line[csv_id])  # No prepara (art x pack)
               if lot_str:
                  lot=eval(lot_str.replace(',','.'))
               else:
                  lot=0
               csv_id+=1
               price[0] = PrepareFloat(line[csv_id])   # Price pricelist 1 EUR
               csv_id+=1
               price[1] = PrepareFloat(line[csv_id])   # Price pricelist 4 EUR
               csv_id+=1
               price[2] = PrepareFloat(line[csv_id])   # Price pricelist 5 CHF
               csv_id+=1
               price[3] = PrepareFloat(line[csv_id])   # Price pricelist 9 EUR
               csv_id+=1
               # Language:
               Lang_EN = Prepare(line[csv_id]).title()  # Article EN
               csv_id+=1               
               Lang_2 = Prepare(line[csv_id]).title()  # TODO Lingua 1
               csv_id+=1               
               Lang_3 = Prepare(line[csv_id]).title()  # TODO Lingua 2
               csv_id+=1               
               Lang_4 = Prepare(line[csv_id]).title()  # TODO Lingua 3
               # Parte dimensioni:
               csv_id+=1          
               linear_length = PrepareFloat(line[csv_id])   # Lunghezza lineare
               csv_id+=1
               volume = PrepareFloat(line[csv_id])   # Volume M3
               csv_id+=1
               weight = PrepareFloat(line[csv_id])   # Peso (lordo?) TODO vedere se e' netto
               
                 
               # Calculated field:
               #    Blocco unità di misura
               if uom.upper() in ['NR', 'N.', "PZ"]: # PCE
                  uom_id=uom_nr 
               elif uom.upper() in ["M2", "MQ"]: 
                  uom_id=uom_m2 
               elif uom.upper() in ["M", "MT", "ML",]: # note: after M2!! 
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

               #    Blocco lingua  
               name="[" + (ref[0:6].replace(' ','')) + "] " + name
               if Lang_EN:
                  Lang_EN="[" + (ref[0:6].replace(' ','')) + "] " + Lang_EN
                  data_lang={'lang': 'it_IT', 
                             'src': Lang_EN, # Nome scritto in inglese
                             'xml_id': False, 
                             'name': 'product.template,name',
                             'type': 'model', 
                             'module': False, 
                             'value': name, # Nome in italiano
                             #'res_id': 2, # when created
                                       }
                  name=Lang_EN # Nel prodotto rimane invece il nome in inglese               
                  insert_lang=True
               else:
                  insert_lang=False
                 
               data={'name': name,
                     'mexal_id': ref,
                     'import': True,
                     'sale_ok':True,
                     'purchase_ok': True,
                     'default_code': ref,
                     'uom_id': uom_id,           # TODO test if it is NR
                     'uom_po_id': uom_id,        # TODO test if it is NR
                     'type': 'product',          # TODO parametrize: product consu service
                     'supply_method': 'produce', # TODO parametrize: produce buy
                     'standard_price': bug_start_value,
                     'list_price': 0.0,
                     'procure_method': 'make_to_order', 
                     'q_x_pack': lot,
                     'description_sale': name, # preserve original name (not code + name)<<<<<<<<<
                     'name_template': name,    
                     #'description': description,
                     #'description_spurchase'
                     #'lst_price' 
                     #'seller_qty'   
                    }
               if azienda=='fia':# TODO veder se attivarla anche per la GPB
                  data['volume']=volume
                  data['linear_length']=linear_length
                  data['weight']= weight

               if taxes_id and taxes_id=='21':
                  data['taxes_id']= [(6,0,[iva_debito])]
                  data['supplier_taxes_id']= [(6,0,[iva_credito])]
               else:
                  errori_iva.append("articolo: %s" % (name))                                       
 
               # PRODUCT CREATION ***************
               error="Searching product with ref"
               item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)]) 
               ''' non filtro per import che viene utilizzato per capire se è arrivata da qui l'importazione
                   in caso contrario di creazione con script modifico solo mexal_id per permettere così
                   l'aggiornamento di lingua ecc.
               '''
               #if item: # update
               #   try:
               #       modify_id = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data)
               #       product_id=item[0]
               #   except:
               #       print "[ERROR] Modify product, current record:", data
               #       #raise  # TODO ripristinare??
               #   if verbose: 
               #      print "[INFO]", counter['tot'], "Already exist: ", ref, name
               if item: # update
                  continue
               else:           
                  counter['new'] += 1  
                  error="Creating product"
                  try:
                      product_id=sock.execute(dbname, uid, pwd, 'product.product', 'create', data) 
                  except:
                      print "[ERROR] Create product, current record:", data
                      #raise  # TODO ripristinare??
                  if verbose: 
                     print "[INFO]",counter['tot'], "Insert: ", ref, name
               
               # TRANSLATION UPDATE:
               if insert_lang:  # Only if present lang EN terms in Mexal
                   if product_id:
                      error="Searching product lang"
                      item_lang = sock.execute(dbname, uid, pwd, 'ir.translation', 'search', [('lang', '=', 'it_IT'),
                                                                                              ('name', '=', 'product.template,name'),
                                                                                              ('res_id', '=', product_id),
                                                                                              ('value','=', data_lang['value'])
                                                                                             ]) # if english is present it translation is made!
                      data_lang['res_id']=product_id # add product_id for reference!
                      if item_lang: # update
                         try:
                             modify_id_lang = sock.execute(dbname, uid, pwd, 'ir.translation', 'write', item_lang, data_lang)
                             lang_id=item[0]
                         except:
                             print "[ERROR] Modify product lang, current record:", data_lang
                             #raise  # TODO ripristinare??
                         if verbose: 
                            print "   [INFO]", "Lang modify:",data_lang['value']
                      else:           
                         error="Creating product lang"
                         try:
                             lang_id=sock.execute(dbname, uid, pwd, 'ir.translation', 'create', data_lang) 
                         except:
                             print "[ERROR] Create product lang, current record:", data_lang
                             #raise  # TODO ripristinare??
                         if verbose: 
                            print "   [INFO]","Lang insert: ", data_lang['value']
               if verbose:  # Print only if aren't print info importation TODO?? tolto il "not verbose"
                  if insert_lang:
                     print ref,"\t", name, "\t>>>\t", data_lang['value']   

               # PRICE LIST CREATION/UPDATE:               
               for j in range(0,4):
                   if price[j]: # if exist price prepare PL item                        
                      item_data={#'price_round':
                                 #'price_min_margin':
                                 #'price_discount':
                                 #'base_pricelist_id': pl_pricelist[j],  # Price list
                                 'price_version_id': pl_fiam[j],   # Price list version (4 pl) # TODO erase cost=1 PL=PL-1
                                 'sequence':10,                    # Sequence for article 4 pl (for partic is less)
                                 #'price_max_margin':
                                 #'company_id
                                 'name':'%s [%s]' % (name,ref),
                                 #'product_tmpl_id':
                                 'base': 2,    # base price (product.price.type) TODO parametrize: 1 pl 2 cost
                                 'min_quantity':1,
                                 'price_surcharge': price[j] - bug_start_value, # Recharge on used base price 
                                 #'categ_id':
                                 'product_id': product_id,
                                 }
                      item_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('price_version_id', '=', pl_fiam[j]),('product_id','=',product_id)])                
                      try:
                         if item_item: # update
                             modify_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'write', item_item, item_data)                                    
                         else:           
                             new_item_id=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', item_data) 
                      except:
                          print "[ERROR] Creating / Modifying item in pricelist", item_data
                          #raise # RIPRISTINARE??
except:
    print '>>> [ERROR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

if errori_iva:
   print errori_iva
print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"

if uom_todo:
   print "Unita' di misura da aggiungere!", uom_todo

