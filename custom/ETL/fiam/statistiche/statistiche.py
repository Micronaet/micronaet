#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# TODO LIST:
# Test numero of colums, there are some cases that separator char is present in fields, ex: email@soc1.it; email@soc2.it in email address
# Modules ETL Partner Scuola
# use: partner.py file_csv_to_import

# Require: base_fiam

# Modules required:
import xmlrpclib, csv, ConfigParser, sys
from datetime import datetime, timedelta

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['../openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
#verbose=eval(config.get('import_mode','verbose'))  # for info message
verbose=False

# Start main code *************************************************************
# FUNCTION:
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def PrepareDate(valore):
    if valore: # TODO test correct date format
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def PrepareFloat(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

def PrepareInt(valore):
    valore=valore.strip() 
    if valore:
       return int(valore)
    else:
       return 0


# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *  Use the command with this syntax: python ./statistiche.py c|p    ( >>>current, precedent )
         *********************
         """          
   sys.exit()
else:
   year_char=sys.argv[1].lower()
   if year_char not in ['c', 'p']:
      print """
            *** Syntax Error! ***
            *  Use the command with this syntax: python ./statistiche.py c|p    ( >>>current, precedent )
            *********************
            """          
   
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char 
FileInput='../fatta' + year_char + 'oerp.FIA'  
header_lines=0

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':-header_lines,} 

tot_colonne=0
try:
    for line in lines:
        if counter['tot']<0:  # jump n lines of header 
           counter['tot']+=1
        else: 
           if not tot_colonne:
              tot_colonne=len(line)
              print "*** Colonne rilevate: %d" % (tot_colonne)
           if len(line): # jump empty lines
               if tot_colonne == len(line): # tot colums equal to column first line
                   counter['tot'] += 1 
                   error = "Importing line" 
                   csv_id = 0
                   ref = Prepare(line[csv_id])
                   csv_id+=1
                   fatturato = PrepareFloat(line[csv_id])
                   csv_id+=1
                   date_last = Prepare(line[csv_id]) 
                   csv_id+=1
                   days_left = PrepareInt(line[csv_id]) or 0

                   # color analisys: # hot, normal, cold
                   if days_left <= 180:
                      color="green"
                   elif days_left <= 365:
                      color="yellow"
                   else:
                      color="red"    
                   
                   # star analisys:
                   item_stars = sock.execute(dbname, uid, pwd, 'crm.partner.importance', 'search', [])
                   star_list={}
                   stars_id=False
                   if item_stars:
                      read_stars= sock.execute(dbname, uid, pwd, 'crm.partner.importance', 'read', item_stars)
                      for element in read_stars:
                          #star_list[element['sequence']]=[element['invoiced_less_than'],element['invoiced_over_than'],element['name']]
                          star_list[element['invoiced_over_than']]=element['id']
                          
                      #import pdb; pdb.set_trace()                      
                      star_invoice=star_list.keys()
                      star_invoice.sort()
                      star_invoice.reverse()
                      
                      for fatturato_annuo in star_invoice: #dall'ultimo al primo
                          if fatturato > fatturato_annuo:
                             stars_id=star_list[fatturato_annuo]
                             break
                   
                   if year_char=='c':
                       data = {
                              'day_left_ddt': days_left,              
                              'date_last_ddt': date_last,
                              'invoiced_current_year': fatturato,      
                              'partner_color': color,  
                              'partner_importance_id': stars_id,
                              }
                   else: # 'p'
                       data = {
                              'day_left_ddt': days_left,              
                              'date_last_ddt': date_last,
                              'invoiced_last_year': fatturato,      
                              'partner_color': color,  
                              #'partner_importance_id': stars_id,
                              }
                              
                   #try:
                   #values = {'vat': 'ZZ1ZZZ'} #data to update
                   #result = sock.execute(dbname, uid, pwd, 'res.partner', 'write', ids, values
                   #'invoiced_last_year': fatturato,
                   #'order_current_year': fields.float('Label', digits=(16, 2)),
                   #'order_last_year': fields.float('Label', digits=(16, 2)),                             
                   #'mexal_c'
                   #'import': True,                    

                   # PARTNER UPDATE ***************
                   item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('mexal_c', '=', ref), ('import','=', True)])                   
                   if item:
                      #import pdb; pdb.set_trace()
                      sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data)
                      if verbose:
                         print "[INFO]", counter['tot'], "Update statistic fields: ", ref
                   else:           
                      print "[WARN]", counter['tot'], "Not found: ", ref

except:
    raise 

print "[INFO]","Partner statistics:", "Total line: ", counter['tot']

