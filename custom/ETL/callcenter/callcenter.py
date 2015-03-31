#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, ConfigParser, sys

# Parameters:
cfg_file="openerp.cfg"

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

# Open file log error (if verbose mail the file are sent to admin email)
for i in range(int(sys.argv[1]), 9000000):
   print "record", i
   data={'name': "Cliente %d"%(i,),
         'phone': "+39 030 %d"%(i,),
         'customer': True,
         'supplier': False,
         'city': 'City %d'%(i,),
         'mobile': '+39 337 %d'%(i,),
         'ref': i,
         }
   partner_id=sock.execute(dbname, uid, pwd, 'res.partner', 'create', data)

   data_address={'city': 'City %d'%(i,), # modify first import address
                 'zip': "25100",
                 #'country_id': getCountryFromCode(sock,dbname,uid,pwd,country_international_code), 
                 'phone': "+39 030 %d"%(i,),
                 'fax': "+39 035 %d"%(i,),
                 'street': 'Via n %d'%(i,),
                 'email': "info@%d"%(i,),
                 'type':  'default',
                 'partner_id': partner_id,
                 }
   item_address_new=sock.execute(dbname, uid, pwd, 'res.partner.address', 'create', data_address)




