#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib, ConfigParser

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['../openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# Start main code *************************************************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

data = {
      'day_left_ddt': 0,              
      'invoiced_current_year': 0,      
      'partner_color': 'red',  
      'partner_importance_id': False,
      }
item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('import','=', True),])                   
if item:
  sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data)

print "Reset a rosso effettuato per i clienti importati!"

