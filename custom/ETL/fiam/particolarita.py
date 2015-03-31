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
         *  Use the command with this syntax: python ./particolarita.py partoerp.csv 
         *********************
         """ 
   sys.exit()

if sys.argv[1][-3:]=="FIA":
   cfg_file="openerp.cfg"
else: #"GPB"
   cfg_file="openerp.gpb.cfg"
   
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
 
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
bug_start_value=1.0 # for problems in pricelist starting with cost price = 0 
client_list=[] # List of customer with particularity PL

#ID_uom_categ=getUomCateg(sock,dbname,uid,pwd,'Unit')    # Category Unit
#uom_nr=getUOM(sock,dbname,uid,pwd,'PCE',{'name': 'PCE', # Create new UOM PCE
#                                        'factor_inv': 1.0, 
#                                        'rounding': 1.0, 
#                                        'uom_type': 'reference', 
#                                        'factor': 1.0, 
#                                        'active': True, 
#                                        'category_id': ID_uom_categ,
#                                        })
#

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
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
               article_id = Prepare(line[csv_id])
               csv_id+=1
               customer_id = Prepare(line[csv_id]).title()
               csv_id+=1
               price = PrepareFloat(line[csv_id])   # Price pricelist 1 EUR
                
               if customer_id not in client_list: # Collect list of client with particularity
                  client_list.append(customer_id) 

                 
               # PRICE LIST CREATION/UPDATE:               
               if price: # if exist price prepare PL item  
                  price_version_id=GetVersionPricelist(sock, dbname, uid, pwd, customer_id)     
                  if not price_version_id:                    
                      print "[ERROR] Could not find price list for customer:", customer_id
                  else:
                      item_data={#'price_round':
                                 #'price_min_margin':
                                 #'price_discount':
                                 #'base_pricelist_id': pl_pricelist[j],  # Price list
                                 'price_version_id':  price_version_id,   # Price list version (4 pl) # TODO erase cost=1 PL=PL-1
                                 'sequence':5,  #less than pl defaulf version
                                 #'price_max_margin':
                                 #'company_id
                                 'name':'%s (Particolarità art)' % (article_id),
                                 #'product_tmpl_id':
                                 'base': 2,    # base price (product.price.type) TODO parametrize: 1 pl 2 cost
                                 'min_quantity':1,
                                 'price_surcharge': price - bug_start_value, # Recharge on used base price 
                                 #'categ_id':
                                 'product_id': GetProductID(sock, dbname, uid, pwd, article_id),
                                 }
                      item_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('price_version_id', '=', item_data['price_version_id']),('product_id','=',item_data['product_id'])])                
                      if item_item: # update
                         modify_item = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'write', item_item, item_data)
                         counter['upd']+=1
                         print "[INFO]",counter['tot'], "Updated: ", article_id, customer_id, price 
                      else:           
                         new_item_id=sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'create', item_data) 
                         counter['new']+=1
                         print "[INFO]",counter['tot'], "Insert: ", article_id, customer_id, price 
except:
    print '>>> [ERROR] Error importing articles!'
    pdb.set_trace()
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Particolarity:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
cPickleParticOutput(file_name_pickle,client_list)

