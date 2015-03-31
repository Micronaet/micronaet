#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os, pdb
from posta import *

# Parameters:
cfg_file="/home/administrator/ETL/ambulatorio/openerp.cfg"
   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))  # for info message

# SMTP config read
smtp_server=config.get('smtp','server') 
verbose_mail=eval(config.get('smtp','verbose_mail'))  # for info mail
smtp_log=config.get('smtp','log_file') 
smtp_sender=config.get('smtp','sender') 
smtp_receiver=config.get('smtp','receiver') 
smtp_text=config.get('smtp','text') 
smtp_subject=config.get('smtp','subject') 

# Start main code *************************************************************
# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)
sock_wiz = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/wizard')

for item in sock.execute(dbname, uid, pwd, 'dentist.operation', 'search', [('import', '=', True)]):
    import pdb; pdb.set_trace()
    print "Esito:", sock_wiz.execute(dbname, uid, pwd, 'trg_validate', 'dentist.operation', item)
#wf_service.trg_validate
# workflow.trg_validate(uid, 'training.subscription.line', new_sl_id, 'signal_confirm', cr)


