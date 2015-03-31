#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, ConfigParser, os, pdb
from mic_ETL import *
#from panchemicals import *

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./particolarita.py partoerp.csv 
         *********************
         """ 
   sys.exit()

cfg_file="openerp.cfg"

def getCurrency(sock,dbname,uid,pwd,name):
    # get Currency from code, ex. EUR, CHF
    currency_id = sock.execute(dbname, uid, pwd, 'res.currency', 'search', [('name', '=', name),]) 
    if len(currency_id): 
       return currency_id[0] # take the first
    else:
       return #sock.execute(dbname,uid,pwd,'res.currency','create',data)  # TODO create ??

def GetPricelist(sock, dbname, uid, pwd, customer_id, model_pricelist): # 2 returned values in dict
    #item_currency_id=sock.execute(dbname,uid,pwd,'product.pricelist', 'read', model_pricelist, []) # get currency from default PL base
    #if item_currency_id:
    #   currency_id=item_currency_id['currency_id'][0]
    #else:
    #   currency_id=0
    currency_id = 0   
    pricelist_version_id=0
    pricelist_id=0
    #import pdb; pdb.set_trace()
    if not currency_id:
       currency_id=getCurrency(sock,dbname,uid,pwd,"EUR") # TODO parametrize like model one's

    # Create Pricelist base per client:   
    name="Listino cliente: [%s]" %(customer_id)
    pl_id = sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', customer_id)]) 
    if pl_id: 
       pricelist_id= pl_id[0]  
    else:
       pricelist_id=sock.execute(dbname,uid,pwd,'product.pricelist','create',{'name':name,
                                                                              'currency_id': currency_id, # getCurrency(sock,dbname,uid,pwd,currency),
                                                                              'type': 'sale',  # Sale already exist, created from first base importation of PL
                                                                              'mexal_id': customer_id, # << extra fields
                                                                              })  
    if pricelist_id: # Abbino il listino al partner
       partner_ids = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', customer_id)]) 
       mod_partner_pricelist = sock.execute(dbname, uid, pwd, 'res.partner', 'write', partner_ids, {'property_product_pricelist': pricelist_id,})
       
    # Create Pricelist version base per client:
    version="Versione cliente: [%s]"  % (customer_id)
    version_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', customer_id)])
    if version_id:
       pricelist_version_id= version_id[0] 
    else:
       pricelist_version_id=sock.execute(dbname,uid,pwd,'product.pricelist.version','create',{'name':version,
                                                                                           'pricelist_id': pricelist_id,  # TODO verify relation field
                                                                                           'mexal_id': customer_id, # << extra fields
                                                                                           })
    item_based_data={#'price_round': 0.0,  #'price_discount': 0.0, 
                     'base_pricelist_id': model_pricelist,
                     'sequence': 10000, 
                     #'price_max_margin': 0.0, #'company_id': False,  #'product_tmpl_id': False, #'product_id': False, 
                     'base': -1,  # Price list
                     'price_version_id': pricelist_id, 
                     'min_quantity': 1, 
                     #'price_surcharge': 0.0,   #'price_min_margin': 0.0, #'categ_id': False, 
                     'name': "Listino modello del partner",
                     'mexal_id': customer_id, # << extra fields
                    }
    item_based_id = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('mexal_id', '=', customer_id,)]) 
    if item_based_id: # update
       upd_item_based=sock.execute(dbname,uid,pwd,'product.pricelist.item','write',item_based_id[0],item_based_data)
    else:
       cr_item = sock.execute(dbname,uid,pwd,'product.pricelist.item','create',item_based_data)
       
    return pricelist_id, pricelist_version_id
       
def GetVersionPricelist(sock, dbname, uid, pwd, customer_id): 
    version_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', customer_id,)]) 
    if len(version_id): 
       return version_id[0] 
    else:
       print "Errore searching Client version price list! *******************" 
       return 0 # Generate an error? *******
       
def GetProductID(sock, dbname, uid, pwd, ref): 
    item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)])
    if item: 
       return item[0]
    else:
       print "Errore searching Client particularity product from code! ******************"
       return 0 # ERROR!   
       
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
file_name_pickle=config.get('dbaccess','file_name_pickle') # Pickle file name
header_lines=0 # non header on CSV file
percorso="/home/administrator/ETL/"
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value=0.0 # for problems in pricelist starting with cost price = 0 

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(percorso + FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

client_list=cPickleParticInput(file_name_pickle)
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
               article_id = Prepare(line[csv_id])
               csv_id+=1
               mexal_id = Prepare(line[csv_id]).title()
               csv_id+=1
               price = PrepareFloat(line[csv_id])   # Price pricelist 1 EUR
               
               # Controllo se esiste un listino base per il cliente 
               if mexal_id not in client_list: # Create Particular PL for client (or update)
                  print "[ERR] Non trovato: ", mexal_id
                  continue # Prossima riga
               
               if price: # if exist price prepare PL item  
                  pricelist_id, price_version_id=GetPricelist(sock, dbname, uid, pwd, mexal_id, client_list[mexal_id][1])
                  if not price_version_id:                    
                      print "[ERROR] Could not find price list for customer:", mexal_id
                  else:
                      product_id=GetProductID(sock, dbname, uid, pwd, article_id)
                      if not product_id:
                         print "[ERR] Prodotto non trovato:", article_id
                         
                      item_data={'price_round':0.01,  #'price_min_margin': #'price_discount': #'base_pricelist_id': pl_pricelist[j],  # Price list
                                 'price_version_id':  price_version_id,   # Price list version (4 pl) # TODO erase cost=1 PL=PL-1
                                 'sequence':5,  #less than pl defaulf version
                                 #'price_max_margin': #'company_id
                                 'name':'%s (Particolarità art)' % (article_id),
                                 #'categ_id': #'product_tmpl_id':
                                 'base': 1,    # base price (product.price.type) TODO parametrize: 1 pl 2 cost
                                 'min_quantity': 1,
                                 'price_surcharge': price - bug_start_value, # Recharge on used base price 
                                 'product_id': GetProductID(sock, dbname, uid, pwd, article_id),
                                 }
                      item_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('price_version_id', '=', price_version_id),('product_id','=',product_id)])                
                      if item_item: # update
                         modify_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'write', item_item, item_data)
                         counter['upd']+=1
                         print "[INFO]",counter['tot'], "Updated: ", article_id, mexal_id, price 
                      else:           
                         new_item_id=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', item_data) 
                         counter['new']+=1
                         print "[INFO]",counter['tot'], "Insert: ", article_id, mexal_id, price 
except:
    print '>>> [ERROR] Error importing articles!'
    #pdb.set_trace()
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Particolarity:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
