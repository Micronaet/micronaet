#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules Listini 
# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os
from mx.DateTime import now
from mic_ETL import *
from fiam import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

header_lines=0 # non header on CSV file

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./listini.py nome_file.csv 
         *********************
         """ 
   sys.exit()

 
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

ID_pricelist_type=getPricelistType(sock,dbname,uid,pwd,'sale',{'name': 'Sale Pricelist', 'key': 'sale'})
#cur_EUR=getCurrency(sock,dbname,uid,pwd,'EUR')
#cur_CHF=getCurrency(sock,dbname,uid,pwd,'CHF')

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
               ref = Prepare(line[csv_id])
               csv_id+=1
 
               data={'name': name,
                     'mexal_id': ref,
                    }
               
               # PRICELIST CREATION ***************
               error="Searching product with ref"
               item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)])
               if item: # update
                  try:
                      article_mod = sock.execute(dbname, uid, pwd, 'product.product', 'write', item, data) 
                  except:
                      print "[ERROR] Modify product, current record:", data
                      raise 
                  print "[INFO]", counter['tot'], "Already exist: ", ref, name
               else:           
                  counter['new'] += 1  
                  error="Creating product"
                  try:
                      article_new=sock.execute(dbname, uid, pwd, 'product.product', 'create', data) 
                  except:
                      print "[ERROR] Create product, current record:", data
                      raise                
                  print "[INFO]",counter['tot'], "Insert: ", ref, name
      
except:
    print '>>> [ERROR] Error importing articles!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "[INFO]","Articles:", "Total: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
