#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Modules required:
import xmlrpclib, csv, sys, time, string, ConfigParser, os

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
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

item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '!=', '')]) 
item_erase=sock.execute(dbname, uid, pwd, 'res.partner', 'unlink', item) 
item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_s', '!=', '')]) 
item_erase=sock.execute(dbname, uid, pwd, 'res.partner', 'unlink', item) 

item_address = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', [('import', '=', 'true')])
item_address_erase = sock.execute(dbname, uid, pwd, 'res.partner.address', 'unlink', item_address)
