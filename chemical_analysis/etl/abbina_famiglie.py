#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, ConfigParser, os, pdb
#from panchemicals import *

# Start main code *************************************************************
path=os.path.expanduser("~/ETL/minerals/")
cfg_file=path + "openerp.cfg"

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Function:
def prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def convert_caterogy_name(sock, dbname, uid, pwd, name): 
    item = sock.execute(dbname, uid, pwd, 'chemical.product.category', 'search', [('name', '=', name)])
    
    if item: 
       return item[0]
    return False

def get_or_create_symbol(sock, dbname, uid, pwd, symbol): 
    item = sock.execute(dbname, uid, pwd, 'chemical.element', 'search', [('symbol', '=', symbol)])
    
    if item: 
       return item[0]
    return sock.execute(dbname, uid, pwd, 'chemical.element', 'create', {'symbol': symbol, 'name': symbol,})
       
def get_symbol(sock, dbname, uid, pwd, chemical_symbol_list):
    res={}
    for item in chemical_symbol_list:
        res[item] = get_or_create_symbol(sock, dbname, uid, pwd, item)
    return res
    
def parse_element(sock, dbname, uid, pwd, item):
    ''' case: > 34 >>> (0.34, 1)
              < 5  >>> (0.0, 0.05)
              3/4  >>> (3.0, 4.0)
              or (0.0, 0.0)
    '''
    item=item.replace(",",".").replace(" ","")
    try: 
        if not item: # Vuoto
           return (0.0,0.0)
        if item[0]==">": # maggiore di
           return (float(item[1:]), 100.0)
        elif item[0]=="<": # minore di 
           return (0.0,float(item[1:]))
        elif len(item.split("/"))==2: # da / a
           range_items= item.split("/")
           return (float(range_items[0]),float(range_items[1]))
    except:
       print "Error parsing ", item
       
    return (0.0,0.0)

# Leggo i prodotti con 6 caratteri nel codice:
lines = csv.reader(open(path + "family.csv",'rb'), delimiter=separator)
counter=-1
    
# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
file_list= ('desolforanti',
            'diossidanti',
            'ferroleghe',
            'fluidificanti',
            'metalli',
            'polveri',
            'prefuse',
            'ricarburanti',
            'scorie',
            )

#convert_category={}
#convert_category['desolforanti']= convert_caterogy_name(sock, dbname, uid, pwd, 'Desolforanti') 
#convert_category['diossidanti']= False #= convert_caterogy_name(sock, dbname, uid, pwd, '') 
#convert_category['ferroleghe']= convert_caterogy_name(sock, dbname, uid, pwd, 'Ferroleghe') #= convert_caterogy_name(Metalli 	
#convert_category['fluidificanti']= convert_caterogy_name(sock, dbname, uid, pwd, 'Fluidificanti')
#convert_category['metalli']= convert_caterogy_name(sock, dbname, uid, pwd, 'Leghe Nobili ') #= convert_caterogy_name(Prodotti Siderurgici 	
#convert_category['polveri']= False #convert_caterogy_name(sock, dbname, uid, pwd, '') 
#convert_category['prefuse']= False #convert_caterogy_name(sock, dbname, uid, pwd, '') 
#convert_category['ricarburanti']=  convert_caterogy_name(sock, dbname, uid, pwd, 'Ricarburanti')# 	 = convert_caterogy_name(Materiali Vari 	
#convert_category['scorie']= False #convert_caterogy_name(Imballi             
	
lines = csv.reader(open(path + "family.csv",'rb'), delimiter=",")
counter=-1

family_id={}
for line in lines:
    if len(line): # jump empty lines
       counter+=1 
       name = line[0].title()
       family = "0" * (6-len(line[1])) + (line[1])

       # Creo la scheda col nome che rilevo
       model_data={ 
                  #'name':name,
                  #'chemical_category_id': convert_category[file_item],
                  'family': family,
                  }
       model_search_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'search', [('name', '=', name),])

       if model_search_id:
          family_id[family]=model_search_id[0]
          model_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'write', model_search_id, model_data)  
          print "[INFO] Update family", family
       else:   
          print "[ERR] Non trovato", name, family

product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [])  
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids):
    code=product['default_code'][:6]
    if code in family_id:
       product_update = sock.execute(dbname, uid, pwd, 'product.product', 'write', product['id'],{'model_id':family_id[code]})  
       

