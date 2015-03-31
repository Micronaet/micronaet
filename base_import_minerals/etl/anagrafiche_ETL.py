#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# This module create or updare standard anagraphic list

# Modules required:
import xmlrpclib, sys, time, string, ConfigParser, os
from mx.DateTime import now
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
file_config = os.path.expanduser("~/ETL/minerals/") + 'openerp.cfg'

config = ConfigParser.ConfigParser()
config.read([file_config]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

# Create standard record:
partner_titles=("Sig.","Sig.ra","S.p.A.","S.n.C.","S.r.l.","Soc. Coop.","S.a.S.","S.d.f.",)
contact_titles=("Sig.","Sig.ra","Ing.","Geom.","Rag.","Dott.","Dr.","Avv.to","Comm.",) 
region_list=("Valle D'Aosta",
             "Piemonte",
             "Liguria",
             "Lombardia",
             "Veneto",
             "Trentino Alto Adige",
             "Friuli Venezia Giulia",
             "Emilia Romagna",
             "Toscana",
             "Lazio",
             "Umbria",
             "Marche",
             "Abruzzo",
             "Molise",
             "Campania",
             "Basilicata",
             "Puglia",
             "Calabria",
             "Sicilia",
             "Sardegna",
            )


context={'lang':'it_IT','tz':False} #Set up an italian context 

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

CreateTitle(sock,dbname,uid,pwd,partner_titles,'partner')                # Title partner
CreateTitle(sock,dbname,uid,pwd,contact_titles,'contact')                # Title contact
CreateAllRegion(sock,dbname,uid,pwd,region_list)                         # Region list

print "[INFO] Creation completed!"
