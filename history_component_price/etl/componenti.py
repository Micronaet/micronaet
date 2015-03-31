
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules used for ETL - Create User

# Modules required:
import xmlrpclib, sys, csv, ConfigParser, os

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([os.path.expanduser('~/ETL/fiam/openerp.cfg')]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# For final user: Do not modify nothing below this line (Python Code) *********
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

try:
    # test if record exists (basing on Ref. as code of Partner)
    item_ids = sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'search', [])
    
    #pricelist.partnerinfo
    a={'supplier_id': [4481, 'Polikart Imballaggi S.R.L.'],
     'has_bom': False, 
     'product_id': [12040, 'Scatola per sedia Semeraro 690x570x910'], 
     'product_supp_code': 'S031700049', 
     'price': 2.3500000000000001, 
     'suppinfo_id': [14236, '4481'], 
     'date_quotation': '2012-04-30', 
     #'product_supp_name': 'Scatola per sedia Semeraro 690x570x910', 
     'uom_id': [1, 'PCE'], 
     #'id': 14602, 
     'min_quantity': 322.0, 
     'product_name': 'Scatola per sedia Semeraro 690x570x910', 
     'name': False
     }

    #product.supplierinfo
    b={'pricelist_ids': [12262],
     'name': [5599, 'Gbm Components Srl'], 
     'product_uom': [1, 'PCE'], 
     'sequence': 1, 
     'product_name': 'Costruzione Rete Schienale Con Saldatura Su Vs Tel', 
     'company_id': [1, 'Fiam S.p.A.'], 
     'qty': 0.0, 
     'delay': 1, 
     'min_qty': 0.0, 
     'product_code': '', 
     'id': 12262, 
     'product_id': [10655, 'Schienale Gitter 80']}

    elenco={}
    lista_id={}
    if item_ids:
       print ">>> Archivio i dati"

       # Spunto tutti come default (poi togliero' quelli che non lo sono (per tenere compatiblita' 
       tutto_spuntato=sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'write', item_ids, {'is_active': True,})

       for item in sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'read', item_ids):
           if item['product_id'] and item['supplier_id']:
              key = (item['product_id'][0], item['supplier_id'][0], item['min_quantity'])

              if key not in elenco:
                 elenco[key] = []

              elenco[key].append(item['id']) # ricordo il solo ID
              lista_id[item['id']]=item
              print key, item
           else:
              print "[ERR] Non trovato prodotto o fornitore: product [ %s ] supplier [ %s ] min q. %s"%(item['product_id'], item['supplier_id'], item['min_quantity'])
           
       print ">>> Eliminazione"

       for key in elenco.keys():
           if len(elenco[key])>1:
              
              print "Elemento", elenco[key]
              max_value=max(elenco[key])
              
              print " > conservo %s lista: %s"%(max_value, lista_id[max_value])
              elenco[key].remove(max_value)
              
              #print " > elimino %s"%(elenco[key])
              #sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'unlink', elenco[key])

              print " > spunto default %s"%(elenco[key])
              sock.execute(dbname, uid, pwd, 'pricelist.partnerinfo', 'write', elenco[key], {'is_active': False,})
              
except:
    print '[ERROR] Error importing data!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

