#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib, csv, sys, ConfigParser, os, pdb
from mic_ETL import *
from panchemicals import *

# Set up parameters (for connection to Open ERP Database) ********************************************
file_config = os.path.expanduser("~/ETL/minerals/") + 'openerp.cfg'

config = ConfigParser.ConfigParser()
config.read([file_config]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
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

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py ERPanagrart.csv 
         *********************
         """ 
   sys.exit()

# Function:
def get_chemical_category(sock, dbname, uid, pwd, contropartita):
    item_id = sock.execute(dbname, uid, pwd, 'chemical.product.category', 'search', [('name', '=', contropartita),]) 
    if len(item_id): 
       return item_id[0] 
    else:
       return sock.execute(dbname, uid, pwd,'chemical.product.category','create',{'name': contropartita, })  

def getProductGroup(sock,dbname,uid,pwd,name, parent_id=False):
    # Create or get Group
    item_id = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('name', '=', name), ('parent_id', '=', parent_id)]) 
    if len(item_id): 
       return item_id[0] # take the first
    else:
       return sock.execute(dbname, uid, pwd,'product.category','create',{'name': name, 'parent_id': parent_id,})  

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

print "[INFO] Lettura creazione UOM:"       
# Create or get standard Items mandatory for program:
#  Product:
uom_todo=[]
ID_uom_categ_unit=getUomCateg(sock,dbname,uid,pwd,'Unit')    # Category Unit

# Nuove:
ID_uom_categ_area=getUomCateg(sock,dbname,uid,pwd,'Area')    # Category Area 
ID_uom_categ_capacity=getUomCateg(sock,dbname,uid,pwd,'Capacity')    # Category Capacità 
#ID_uom_categ_peso=getUomCateg(sock,dbname,uid,pwd,'Weight')    # Category Peso

uom_nr=getUOM(sock,dbname,uid,pwd,'PCE',{}) 
uom_kg=getUOM(sock,dbname,uid,pwd,'kg',{})
uom_m=getUOM(sock,dbname,uid,pwd,'m',{})
uom_hour=getUOM(sock,dbname,uid,pwd,'Hour',{})
uom_t=getUOM(sock,dbname,uid,pwd,'tonne',{})

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

FileInput=sys.argv[1]
print "[INFO] Importazione prodotti da file" + FileInput
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
header_lines=0
counter={'tot':-header_lines,'new':0,'upd':0,} 

iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)
errori_iva=[]

if not (iva_credito and iva_debito):
   print "[ERROR] Non è stata trovata l'IVA credito o debito da applicare:", data
error=''
try:
    for line in lines: #line in []:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               error="Importing line" 
               csv_id=0
               ref = Prepare(line[csv_id])                      # codice
               csv_id+=1
               name = Prepare(line[csv_id]).title()             # descrizione prodotto
               name=name.replace(r"/",r"|")
               csv_id+=1
               #name_eng1 = Prepare(line[csv_id]).title()
               #csv_id+=1
               #name_eng2 = Prepare(line[csv_id]).title()
               #csv_id+=1
               uom = Prepare(line[csv_id]).upper()              # UOM
               csv_id+=1
               taxes_id = Prepare(line[csv_id])                 # IVA
               csv_id+=1
               # descrizione aggiuntiva
               csv_id+=1
               # numero 3 decimali??
               csv_id+=1
               cost_std = PrepareFloat(line[csv_id])            
               csv_id+=1
               cost_ult = 0.0 #PrepareFloat(line[csv_id])  
               csv_id+=1
               #has_bom = "S" == Prepare(line[csv_id]).upper()
               csv_id+=1

               csv_id+=1

               csv_id+=1

               csv_id+=1

               csv_id+=1

               csv_id+=1
               contropartita = Prepare(line[csv_id]).upper()              # Contropartita
               
               # Calculated field:
               contropartita=contropartita.strip()
               if contropartita not in ("",
                                        "RICAVI DA PRESTAZIONI DI SERVIZIO",
                                        "MERCI C/VENDITE", 
                                        "TRASPORTI ADDEBITATI A CLIENTI",
                                        "AFFITTI ATTIVI", 
                                        "TRASPORTI SU VENDITE",
                                        "NS. LAVORAZIONI PER TERZI", 
                                        "RIMBORSO SPESE BOLLI",
                                        "COMPARTECIPAZIONE SPESE RECUPERI", 
                                        "MERCI C/VENDITE             (C.AUTO)"):
                  contropartita=contropartita.replace("VENDITA","")
                  contropartita=contropartita.title()
                  contropartita=contropartita.strip()
                  chemical_category_id=get_chemical_category(sock, dbname, uid, pwd, contropartita)
               else:
                  chemical_category_id=False
               
               sale_name = name
               category_id= False
               
               if uom in ['NR', 'N.', 'AC']: # PCE
                  uom_id=uom_nr 
               elif uom in ["M2", "MQ"]: 
                  uom_id=uom_m2 
               elif uom in ["M", "MT"]: # note: after M2!! 
                  uom_id=uom_m
               elif uom == "HR": 
                  uom_id=uom_hour
               elif uom in ["KG", "KK", "GK"]:  # UM inserita errata KK
                  #uom_id=uom_kg   # NOTE: su richiesta di Alberto tutti i prodoti vengono importati da Kg a Tonnellate
                  uom_id=uom_t
               elif uom in ["TN", "T"]: 
                  uom_id=uom_t 
               elif uom == "LT": 
                  uom_id=uom_lt
               else: 
                  if uom not  in uom_todo:
                     uom_todo.append(uom)
                  uom_id=uom_nr # for now is NR till introduce of new uom
 

               data={'name': sale_name,
                     'name_template': sale_name, 
                     #'partner_ref': sale_name,
                     'mexal_id': ref,
                     'code': ref, 
                     'import': True,
                     'sale_ok':True,
                     'purchase_ok': True,
                     'default_code': ref,
                     #'uos_id': uom_id,          # TODO test if it is NR
                     'uom_id': uom_id,           # TODO test if it is NR
                     'uom_po_id': uom_id,        # TODO test if it is NR
                     'type': 'product',          # TODO parametrize: product consu service <<<<<<<<<<
                     'supply_method': 'produce', # TODO parametrize: produce buy
                     'standard_price': cost_ult or cost_std or 0, #cost_std or 0, 
                     'list_price': 0.0,     
                     'procure_method': 'make_to_order', 
                     'description_sale': sale_name, # preserve original name (not code + name)
                     'description': sale_name,
                     #'categ_id': category_id,
                     'chemical_category_id': chemical_category_id,
                     'need_analysis': True,
                     }
                    
               if taxes_id and taxes_id=='21':
                  data['taxes_id']= [(6,0,[iva_debito])]
                  data['supplier_taxes_id']= [(6,0,[iva_credito])]
               else:
                  errori_iva.append("articolo: %s" % (name))                                       
 
               # PRODUCT CREATION ***************
               error="Searching product with ref"
               item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)])
               if item: # update
                  try:
                      modify_id = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data)
                      product_id=item[0]
                  except:
                      print "[ERROR] Modify product, current record:", data
                      #raise  # TODO ripristinare??
                  if verbose: 
                     print "[INFO]", counter['tot'], "Already exist: ", ref, name
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
                     
    print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
except:
    print '>>> [ERROR] Error importing articles!'
    raise # Genero l'errore 

if uom_todo:
   print "Unita' di misura da aggiungere:\n", uom_todo

if errori_iva:
   print "Errori IVA:\n", errori_iva
