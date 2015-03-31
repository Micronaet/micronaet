#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib, csv, sys, ConfigParser, os, pdb
from mic_ETL import *
from panchemicals import *

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

list_group={'A': 'Materie prime', 'B': 'Imballaggi', 'C': 'Lubrificanti', 
            'L': 'Lavorazioni', 'M': 'Macchinari', 'P': 'Componenti', 'S': 'Spese', 
            'V': 'Acqua', '': 'Non classificati',}

list_C_subgroups=['Calcio','Sodio','Calcio-Sodio','Prodotti speciali','Olii emulsionabili e grassi',
                 'Olii interi e grassi (da usarsi tal quali)','Prodotti per non ferrosi: Rame Alluminio (Fili,Tubi,Barre)',
                 'Non reactive coatings: Lubricant carriers','Reactive coatings: Phosphating product','Prodotti ausiliari',
                 'Prodotti eliminati da listino','Prodotti fuori produzione'
                 ]            
                 
list_prodotti_ausiliari_subgroups=['Decapanti','Additivi per calce e borace','Protettivi, anticorrosivi',
                                   'Inibitori decapaggio','Additivi per fosfatazione-Trattamenti superficiali',
                                   'Fosfosgrassanti','Sgrassanti','Antibatterici','Antischiuma',
                                   'Additivi per zincatura a caldo','Flussi','Additivi zootecnici'
                                  ]
                                  
list_group_id={}

# TODO parametrize:
taxd="21a"
taxc="21b"

# Start main code *************************************************************
if len(sys.argv)!=3 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py ERPanagrart.csv ERPricettepan.csv
         *********************
         """ 
   sys.exit()

# Function:
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

print "[INFO] Eliminazione BOM e componenti:"
# Eliminazione BOM:
tabella_campi=sock.execute(dbname, uid, pwd, 'mrp.bom', 'unlink', 
              sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', []) )

print "[INFO] Creazione gruppi per prodotti:"
# 1. Create group:
for item in list_group.values():
    item_id=getProductGroup(sock,dbname,uid,pwd,item)
    list_group_id[item]=item_id
    if item == 'Lubrificanti':
       item_lubrificanti=item_id
       
#     2. Per i lubrificanti:      
for item in list_C_subgroups:
    item_id=getProductGroup(sock,dbname,uid,pwd,item,item_lubrificanti)
    list_group_id[item]=item_id
    if item == 'Prodotti ausiliari':
       item_prodotti_ausiliari=item_id

#        3. Per i Prodotti ausiliari:      
for item in list_prodotti_ausiliari_subgroups:
    item_id=getProductGroup(sock,dbname,uid,pwd,item,item_prodotti_ausiliari)
    list_group_id[item]=item_id
    if item == 'Prodotti ausiliari':
       item_prodotti_ausiliari=item_id
       
print "[INFO] Lettura creazione UOM:"       
# Create or get standard Items mandatory for program:
#  Product:
uom_todo=[]
ID_uom_categ_unit=getUomCateg(sock,dbname,uid,pwd,'Unit')    # Category Unit

# Nuove:
ID_uom_categ_area=getUomCateg(sock,dbname,uid,pwd,'Area')    # Category Area 
ID_uom_categ_capacity=getUomCateg(sock,dbname,uid,pwd,'Capacity')    # Category Capacità 

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

FileInput=sys.argv[1]
print "[INFO] Importazione prodotti (e distinte base primarie) da file" + FileInput
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
header_lines=0
counter={'tot':-header_lines,'new':0,'upd':0,} 

iva_credito=getTaxID(sock,dbname,uid,pwd,taxc)
iva_debito=getTaxID(sock,dbname,uid,pwd,taxd)
errori_iva=[]

# Carico i prodotti importati in una lista per velocizzare l'import BOM:
product_imported={}  # dict for speed up bom creation loading product during importation
item_bom_todo=[]     # ref id for check bom creation

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
               ref = Prepare(line[csv_id])
               csv_id+=1
               name = Prepare(line[csv_id]).title()
               csv_id+=1
               name_eng1 = Prepare(line[csv_id]).title()
               csv_id+=1
               name_eng2 = Prepare(line[csv_id]).title()
               csv_id+=1
               uom = Prepare(line[csv_id]).upper()
               csv_id+=1
               taxes_id = Prepare(line[csv_id])
               csv_id+=1
               cost_std = PrepareFloat(line[csv_id])
               csv_id+=1
               cost_ult = PrepareFloat(line[csv_id])  
               csv_id+=1
               has_bom = "S" == Prepare(line[csv_id]).upper()
               # Calculated field:
               sale_name = name
               iniziale=ref[0].upper()
               if iniziale=="A" and not cost_ult:               
                   print "[ERROR] Materia prima %s con costo ultimo inesistente:" % (ref,)
               #else:
               #    cost_ult=0 # Viene calcolato per tutte le altri prodotti eccetto "A*"   # TODO verificare se è vero
               if iniziale in list_group.keys():
                  category_id= list_group_id[list_group[ref[0].upper()]]
               else:
                  category_id=list_group_id['Non classificati']   

               if uom in ['NR', 'N.',]: # PCE
                  uom_id=uom_nr 
               elif uom in ["M2", "MQ"]: 
                  uom_id=uom_m2 
               elif uom in ["M", "MT"]: # note: after M2!! 
                  uom_id=uom_m
               elif uom == "HR": 
                  uom_id=uom_hour
               elif uom in ["KG", "KK"]:  # UM inserita errata KK
                  uom_id=uom_kg
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
                     'standard_price': cost_ult or 0, #cost_ult or cost_std or 0, #cost_std or 0, 
                     'list_price': 0.0,     
                     'procure_method': 'make_to_order', 
                     'description_sale': sale_name, # preserve original name (not code + name)
                     'description': sale_name,
                     'categ_id': category_id,
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
               product_imported['mexal_id']=[product_id, ref, sale_name, uom_id, has_bom]
               if has_bom: # Creo già la BOM base
                  item_bom_todo.append(ref)
                  item_bom = sock.execute(dbname, uid, pwd, 'mrp.bom', 
                                          'create',{'product_id': product_id,
                                                    'bom_id': False,
                                                    'name': sale_name,
                                                    'product_uom': uom_id,
                                                   })                  
                     
    print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
    
    # Import BOM:
    FileInput=sys.argv[2]
    
    print "[INFO] Importazione componenti da file" + FileInput
    lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
    header_lines=1
    error=''
    counter={'tot':-header_lines,'new':0,'upd':0,'no': 0,} 

    #pdb.set_trace()
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               counter['tot']+=1 
               #c.ult MPrima;c.stand M.Prima;costo ultimo;costo standard;RG
               csv_id=0
               ref = Prepare(line[csv_id]).upper()             # Codice articolo
               csv_id+=1
               child_ref = Prepare(line[csv_id]).upper()       # Codice componente
               csv_id+=1                                       # Descrizione componente (non importata)
               csv_id+=1                                       # UM (non importata)
               csv_id+=1
               q = PrepareFloat(Prepare(line[csv_id]).replace("@",""))                  # Quantità
               csv_id+=1                                       # Costo ultimo materia prima    
               csv_id+=1                                       # Costo standard materia prima
               csv_id+=1                                       # Costo ultimo prodotto
               csv_id+=1                                       # Costo standard prodotto
               csv_id+=1
               sequence=Prepare(line[csv_id])                  # Numero riga ricetta

               # Controllo esistenza prodotto e componente:
               # TODO: sostituire con: product_imported['mexal_id']=[id, ref, sale_name, uom_id, has_bom]
               item_product  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref),]) 
               item_component  = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', child_ref),]) 

               if item_product and item_component and q: # campi necessari a procedere
                  if ref[0] in ["A", "B", "C", "V",]: # test first char of parent code
                      prod_id = item_product[0]
                      comp_id = item_component[0]
                      # Leggo i dati relativi al prodotto e componente
                      item_product_data = sock.execute(dbname, uid, pwd, 'product.product', 'read', prod_id)
                      item_component_data = sock.execute(dbname, uid, pwd, 'product.product', 'read', comp_id) 
                      # Cerco se esiste la distinta prodotto:
                      item_bom  = sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', [('product_id', '=', prod_id), ('bom_id','=',False) ]) 
                      if ref in item_bom_todo:   # remove only the first time
                         item_bom_todo.remove(ref)
                      if item_bom: # Read data BOM
                         item_bom=item_bom[0] # prendo il primo (e unico)
                      else: # Create BOM # TODO eliminare, non dovrebbe passare!!
                         print "[ERROR] Creazione BOM!! NON DEVE PASSARE DA QUI !!!!!!!!", item_product_data['name']
                         bom_data={'product_id': prod_id,
                                   'bom_id': False,
                                   'name': item_product_data['name'],
                                   'product_uom': item_product_data['uom_id'][0],
                                  }
                         item_bom = sock.execute(dbname, uid, pwd, 'mrp.bom', 'create', bom_data)                  
                         
                      if child_ref[0] != "Z": # salto i componenti che iniziano con Z
                         item_bom_comp = sock.execute(dbname, uid, pwd, 'mrp.bom', 'search', [('product_id', '=', comp_id), ('bom_id','=', item_bom)])
                         data_component= {'product_qty': q, 
                                          'product_id': comp_id,
                                          'bom_id': item_bom, 
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
                         if item_bom_comp: # Esiste già il componente per questa distinta
                            mod_bom_comp = sock.execute(dbname, uid, pwd, 'mrp.bom', 'write', item_bom_comp[0], data_component)
                            if verbose: 
                                print "[INFO]"," *** Modifica componente distinta: ", ref, child_ref, q
                            counter['upd'] += 1  
                         else: 
                            item = sock.execute(dbname, uid, pwd, 'mrp.bom', 'create', data_component)
                            if verbose: 
                                print "[INFO]"," *** Creazione componente distinta: ", ref, child_ref, q
                            counter['new'] += 1  
                  else:
                     if verbose: 
                        print "[WARN] *** Prodotto saltato:", ref, child_ref, q
               else:           
                  counter['no'] += 1  # counter errors
                  print "[ERRORE] *** Padre: %s Componente: %s, Quant.: %s non trovate: " % (ref, child_ref, q,)
except:
   print '>>> [ERROR] Error importing articles!'
   raise # Genero l'errore 

if uom_todo:
   print "Unita' di misura da aggiungere!", uom_todo

if errori_iva:
   print errori_iva

if item_bom_todo:
   print "[ERROR] Trovate distinte base non create:", item_bom_todo
print "[INFO]","BOM e components:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ") (error: ", counter['no'], ")"

# Calcolo prezzi prodotti finiti:
esito=sock.execute(dbname, uid, pwd, 'product.product', 'compute_price_from_bom') #  TODO riabilitare!!
