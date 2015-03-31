#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import xmlrpclib, ConfigParser, os, pdb

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['../openerp.gpb.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
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

image_path = "/home/administrator/photo/" #tools.config['addons_path'] + '/product_extra_photo/images/photo/200/' # default: /home/administrator/photo
for root, dirs, files in os.walk(image_path):
    for f in files:
        file_name=f.lower().split(".")
        #pdb.set_trace()
        if len(file_name)==2 and (file_name[0]!="0") and (file_name[1] in ("png","tif","jpg","jpeg","tiff",)): # like "code.png"
           old="%s%s.%s"%(image_path, file_name[0].strip(), file_name[1].strip(),)
           new="%s%s.%s.%s.%s"%(image_path, file_name[0].strip(), "a", "01", file_name[1].strip(),)           
           try:
               os.rename(old,new)
           except IOError: # if exist new file:
               #os.unlink(new)
               #os.rename(old,new)
               print "Errore rinominando:%s in %s"%(old,new)  # do nothing
print "Elementi rinominati!"
