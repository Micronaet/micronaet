#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib, ConfigParser, pdb
import re
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['../openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

def validate_email(email):

	if len(email) > 7:
		if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
			return 1
	return 0

# Start main code *************************************************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

condizione=[('email','!=',False),('mexal_c','!=',False)] 
ids0 = sock.execute(dbname, uid, pwd, 'res.partner', 'search', condizione)                   
items_read0 = sock.execute(dbname, uid, pwd, 'res.partner', 'read', ids0, ['email',])                   

ids1 = sock.execute(dbname, uid, pwd, 'res.partner.address', 'search', condizione)                   
items_read1 = sock.execute(dbname, uid, pwd, 'res.partner.address', 'read', ids1, ['email',])                   

items_read=items_read1 + items_read0
lista_mail=[]
lista_fake_mail=[]
#pdb.set_trace()
for item in items_read:
   email=item['email']
   if email: 
      #email=email.encode('cp1252') #    valore=valore.decode('cp1252')
      #valore=valore.encode('utf-8')
      email=email.replace("e-mail: ","")
      email=email.replace("  ","")
      email=email.replace(" ","")
      
      if validate_email(email):
         if email not in lista_mail:
            lista_mail.append(email)
      else:   
         lista_fake_mail.append(email)

email_file = open("email.txt", "w")
for indirizzo in lista_mail:
    try: 
       mail=indirizzo.replace(",",";")
       email_file.write(mail + ";")
    except:
       #pdb.set_trace()
       lista_fake_mail.append(indirizzo) 
email_file.close() 

print lista_fake_mail
#fake_file = open("fake.txt", "w")
#fake_file.write(";".join(lista_fake_mail))                          
#fake_file.close() 

