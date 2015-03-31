#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, ConfigParser
from mic_ETL import *

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./articoli_ETL.py nome_file.csv 
         *********************
         """ 
   sys.exit()

cfg_file="/home/administrator/ETL/openerp.cfg"
   
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
percorso="/home/administrator/ETL/"
header_lines=0 # non header on CSV file

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create or get standard Items mandatory for program:
#  Product:
client_list={} # List of customer with particularity PL

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput=sys.argv[1]
lines = csv.reader(open(percorso + FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,'new':0,'upd':0,} # tot negative (jump N lines)

try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
            if len(line): # jump empty lines
               error="Importing line" 
               mexal_id = Prepare(line[1])
                
               if mexal_id not in client_list: # Collect list of client with particularity                  
                  counter['tot']+=1 
                  partner_ids = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', mexal_id)])
                  if partner_ids:
                    read_item = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_ids)[0]
                    client_list[mexal_id]=(read_item['property_product_pricelist'] and read_item['property_product_pricelist'][0],read_item['pricelist_model_id'] and read_item['pricelist_model_id'][0])
                  else:
                    print "Cliente non trovato: ", mexal_id   
except:
    print '>>> [ERROR] Searching client with particularity!'
    raise #Exception("Errore di importazione!")

print "[INFO]","Client with particolarity Pricelist:",counter['tot']
cPickleParticOutput(file_name_pickle,client_list)

