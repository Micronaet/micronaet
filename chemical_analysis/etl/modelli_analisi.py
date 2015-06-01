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
lines = csv.reader(open(path + "ERPanagrart.MMI",'rb'),delimiter=separator)
counter=-1
parent_item={}
parent_item_id={}
try:
    for line in lines:
        if counter<0: 
           counter+=1
        else:
            if len(line): # jump empty lines
               counter+=1 
               code = prepare(line[0]).strip()
               name = prepare(line[1]).title()
               if len(code)==6:                  
                  #print "%s;%s"%(code, name)
                  parent_item[name]=code
                  parent_item_id[name]=0
except:
   print "Error parsing "
    
# TODO: attenzione, se hanno già fatto associazioni o aggiunte di informazioni non è possibile fare questi due comandi:
print "Attenzione, se hanno già fatto associazioni o aggiunte di informazioni non è possibile fare questi due comandi:"
import pdb; pdb.set_trace()               
remove_ids = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'search', [])                
remove_unlink = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'unlink', remove_ids)                

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

convert_category={}
convert_category['desolforanti']= convert_caterogy_name(sock, dbname, uid, pwd, 'Desolforanti') 
convert_category['diossidanti']= False #= convert_caterogy_name(sock, dbname, uid, pwd, '') 
convert_category['ferroleghe']= convert_caterogy_name(sock, dbname, uid, pwd, 'Ferroleghe') #= convert_caterogy_name(Metalli 	
convert_category['fluidificanti']= convert_caterogy_name(sock, dbname, uid, pwd, 'Fluidificanti')
convert_category['metalli']= convert_caterogy_name(sock, dbname, uid, pwd, 'Leghe Nobili ') #= convert_caterogy_name(Prodotti Siderurgici 	
convert_category['polveri']= False #convert_caterogy_name(sock, dbname, uid, pwd, '') 
convert_category['prefuse']= False #convert_caterogy_name(sock, dbname, uid, pwd, '') 
convert_category['ricarburanti']=  convert_caterogy_name(sock, dbname, uid, pwd, 'Ricarburanti')# 	 = convert_caterogy_name(Materiali Vari 	
convert_category['scorie']= False #convert_caterogy_name(Imballi             
	
for file_item in file_list:
    file_input=file_item
    lines = csv.reader(open(path + "modelli/" + file_input + ".csv",'rb'),delimiter=separator)
    counter=-1
    try:
        for line in lines:
            if counter==-1:  # jump n lines of header
               cols=len(line)                
               chemical_symbol_list=line[1:]
               # ricavo gli ID eventualmente creandoli dal simbolo chimico
               chemical_symbol_id=get_symbol(sock, dbname, uid, pwd, chemical_symbol_list)
               counter+=1
               # ricavo la lista elementi da header
            else: # inizio l'importazione delle schede
                if len(line): # jump empty lines
                   counter+=1 
                   name = line[0].title()
                   # Creo la scheda col nome che rilevo
                   model_data={ 
                              'name':name,
                              'chemical_category_id': convert_category[file_item],
                              #family
                              }                   
                   model_search_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'search', [('name', '=', name),])                
                   if model_search_id:
                      model_id=model_search_id[0]
                   else:   
                      model_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'create', model_data)  
                   if name in parent_item:
                      parent_item_id[parent_item[name]]=model_id # associare manualmente la categoria del modello
                   else:
                      print "[ERR] Categoria di modello non trovata:", name
                     
                   
                   for i in range(1,cols):  # leggo tutti gli elementi:
                       (min_value,max_value) = parse_element(sock, dbname, uid, pwd, line[i])
                       if min_value or max_value:
                           # Creo tutti i sottoelementi con gli ID delle colonne
                           model_line_data={
                                           'name': chemical_symbol_id[chemical_symbol_list[i-1]],
                                           'min': min_value,
                                           'max':max_value,
                                           'model_id':model_id,
                                           }
                           item_line = sock.execute(dbname, uid, pwd, 'product.product.analysis.line', 'search', [('model_id','=','model_id'),
                                                                                                              ('name','=',chemical_symbol_id[chemical_symbol_list[i-1]])])                
                           if item_line: # update
                              item_mod = sock.execute(dbname, uid, pwd, 'product.product.analysis.line', 'write', model_line_data)
                           else:                
                              item_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.line', 'create', model_line_data) 
    except:
        print '>>> [ERROR] Error importing articles! File: %s, Riga: %s'%(file_item, counter,)
        raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

product_ids=sock.execute(dbname, uid, pwd, 'product.product', 'search', [])                
for product in sock.execute(dbname, uid, pwd, 'product.product', 'read', product_ids):
    if product['default_code'][:6] in parent_item_id and parent_item_id[product['default_code'][:6]]:
       modify_category=sock.execute(dbname, uid, pwd, 'product.product', 'write', product['id'], {'model_id': parent_item_id[product['default_code'][:6]]})                
       model_modify_id = sock.execute(dbname, uid, pwd, 'product.product.analysis.model', 'write', parent_item_id[product['default_code'][:6]], {'family': product['default_code'][:6],})

