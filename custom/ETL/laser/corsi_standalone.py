# -*- encoding: utf-8 -*-
import xmlrpclib,ConfigParser,sys

# Set up parameters (for connection to Open ERP Database) ********************************************
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
 
# For final user: Do not modify nothing below this line (Python Code) ********************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

tabella_id = sock.execute(dbname, uid, pwd, 'training.offer', 'search', [('is_standalone','=','1')]) 
tabella_offerte = sock.execute(dbname, uid, pwd, 'training.offer', 'read', tabella_id) 
i=0
for corso in tabella_offerte:
    if corso['is_standalone']==1 and len(corso['course_ids'])==1: # standalone ed esiste solo 1 corso collegato!
          tabella_corsi_rel = sock.execute(dbname, uid, pwd, 'training.course.offer.rel', 'read', corso['course_ids']) 
          if tabella_corsi_rel:
             tabella_corsi = sock.execute(dbname, uid, pwd, 'training.course', 'read', tabella_corsi_rel[0]['course_id'][0]) # not [id] but id
             if tabella_corsi['code']: # esiste il codice (sono stati importati)
                i+=1
                print i, ")", corso['name'].encode('cp1252'), corso['course_ids'], tabella_corsi['code'], "Stato corso:", corso['state']
                tabella_corsi = sock.execute(dbname, uid, pwd, 'training.offer', 'write', corso['id'], {'state': 'validated',}) # Imposto il corso come convalidato!

