#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# ETL import corsi
# use: add_corsi.py file_csv

# Modules required:
import xmlrpclib, csv, sys, ConfigParser

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) 
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator')   # verify if it's necessary: getint
 
# For final user: Do not modify nothing below this line (Python Code) *********
# Functions:
def Prepare(valore):  
    # For problems: input win output ubuntu; trim extra spaces
    #valore=valore.decode('ISO-8859-1')
    # N.B. Now files is in utf-8 
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def getCourseCategory(sock, dbname, uid, pwd, name):
    item = sock.execute(dbname, uid, pwd, 'training.course_category', 'search', [('name', 'ilike', name)])
    if item:
       return item[0] # return the first
    else:
       print "Non esiste la categoria corso col nome:",name
       return 

def getCourseType(sock, dbname, uid, pwd, name):
    item = sock.execute(dbname, uid, pwd, 'training.course_type', 'search', [('name', 'ilike', name)])
    if item:
       return item[0] # return the first
    else:
       print "Non esiste la categoria corso tipo (livello) col nome:",name
       return 

def getLang(sock, dbname, uid, pwd, name):
    item = sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name)])
    if item:
       return item[0] # return the first
    else:
       print "Non esiste la categoria corso tipo (livello) col nome:",name
       return 

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *   > Use the command with this syntax: python ./add_corsi.py name_file_csv.csv
         *********************
         """
   sys.exit()

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0}
start=1 
n_col=0
try:
    for line in lines:
        if start == 0:
            if line: 
                counter['tot'] += 1 
                if not n_col:
                   n_col=len(line)
                if len(line) != n_col:
                   print "Colonne discordanti: linea:", counter['tot'], "normalmente: " , n_col, "ora:", len(line)
                # CSV file data:
                # Campo/colonna del file:      # Campo nel DB tabella training.course:
                codice=line[0]                 # Codice
                tipologia=Prepare(line[1])
                settore=Prepare(line[2])       # Linea corso (in anagrafica)
                profilo=Prepare(line[3])
                contatto=Prepare(line[4])
                telefono=Prepare(line[5])
                mail=Prepare(line[6]).lower()
                fax=Prepare(line[7])
                titolo=Prepare(line[8])        # Nome breve, Nome Esteso
                descrizione=Prepare(line[9])   # Note
                ore=Prepare(line[10])          # Non usato sono tutti 40:00
                indirizzo=Prepare(line[11])
                ente=Prepare(line[12])

                # Campi calcolati:
                livello=getCourseType(sock, dbname, uid, pwd, "specialisti") # TODO  # Livello
                #import pdb; pdb.set_trace()
                #tipo="standard"       # TODO  # Tipo
                lingua=getLang(sock, dbname, uid, pwd, "Italian / Italiano")     # TODO  # Lingua
                durata=40.0           # TEST  # Durata
                diviso="1"            # TODO  # Splitted By
                
                item = sock.execute(dbname, uid, pwd, 'training.course', 'search', [('code', '=', codice)])
                data = {'code': codice,
                        'name': titolo,
                        'category_id': getCourseCategory(sock, dbname, uid, pwd, "settore"),
                        'course_type_id': getCourseType(sock, dbname, uid, pwd, "specialistici"), #  ???
                        #'kind': tipo, # default standard!
                        'lang_id': lingua,                              
                        'splitted_by': diviso,
                        #'duration_with_children':,
                        'duration_without_children': durata,
                        #'duration':, # Default 0.0
                        'internal_note': descrizione,
                        'state_course': 'validated', # WF action only test training.course.pending
                        #'complete_name':,'internal_note':,'type':,'description':,'quantity':,'currency_id':,
                        #'sequence':,'date_start':,'course_ids':,'quantity_max':,'contact_id':,'lecturer_ids':,
                        #'purchase_line_ids':,'id':,'analytic_account_id':,'user_id':,'attachment_ids':,
                        #'company_id':,'parent_id':,'state':,'debit':,'long_name':,'reference_type':,
                        #'price':,'pending_ids':,'child_reference_id':,'child_ids':,'with_children':,
                        #'has_support':,'child_complete_ids':,'theme_ids':,'p_id':'credit':,
                        #'reference_lang_id':,'line_ids':,'balance':,'reference_id':,'date':,'partner_id':,
                       }                  

                if item:  # Esiste il corso così codificato
                   counter['upd'] += 1  
                   try:                   
                      item_mod = sock.execute(dbname, uid, pwd, 'training.course', 'write', item, data) # update
                      course_id=item[0]    
                   except:
                      print "[ERROR] Modifing data, current record:", data
                      raise 
                   print "[INFO]", counter['tot'], "Already exist: ", codice, titolo
                else:    # Non esiste il corso con questo codice:      
                   counter['new'] += 1  
                   try:                   
                      course_id=sock.execute(dbname, uid, pwd, 'training.course', 'create', data) 
                   except:
                      print "[ERROR] Insert data, current record:", data
                      raise 
                   print "[INFO]",counter['tot'], "Insert: ", codice, titolo
                # Creazione / modifica del corso abbinato all'unico modulo standalone:
                
                ''''product_line_id' : fields.many2one('training.course_category', 'Product Line', select=1, required=True),
                'type_id' : fields.many2one('training.course_type', 'Livello'), # TODO Cambiare in qualcosa d'altro, ci sono 2 "tipi"
                'name' : fields.char('Name',
                'product_id' : fields.many2one('product.product',
                'course_ids' : fields.one2many('training.course.offer.rel', 'offer_id', 'Courses', help='An offer can contain some courses'), ### CASINO!!!
                'duration' : fields.function(_duration_compute,
                'objective' : fields.text('Objective',
                'description' : fields.text('Description',
                'requeriments' : fields.text('Requeriments',
                'management' : fields.text('Management',
                'sequence' : fields.integer('Sequence', help="Allows to order the offers by its importance"),
                'format_id' : fields.many2one('training.offer.format', 'Format', required=True, select=1,
                'state' : fields.selection([('draft', 'Draft'),
                'kind' : fields.selection(training_offer_kind_compute,
                'target_public_id' : fields.many2one('training.offer.public.target',
                'lang_id' : fields.many2one('res.lang', 'Language'),
                #'create_date' : fields.datetime('Create Date', readonly=True),
                'preliminary_offer_ids' : fields.many2many('training.offer','training_offer_pre_offer_rel','offer_id',
                'complementary_offer_ids' : fields.many2many('training.offer','training_offer_cpl_offer_rel','offer_id',
                'included_offer_ids' : fields.many2many('training.offer','training_offer_incl_offer_rel','offer_id',
                'is_standalone' : fields.function(_is_standalone_compute,
                'purchase_line_ids' : fields.one2many('training.offer.purchase.line','offer_id',
                'purchase_line_log_ids': fields.one2many('training.offer.purchase.line.log','offer_id',
                'theme_ids' : fields.many2many('training.course.theme', 'training_offer_them_rel', 'offer_id',
                'notification_note': fields.text('Notification Note', help='This note will be show on notification emails'),
                'is_certification': fields.boolean('Is a certification?', help='Indicate is this Offer is a Certification Offer'),
                'can_be_planned' : fields.function(_can_be_planned_compute, method=True,
                'is_planned': fields.function(is_planned_compute, method=True,'''

                '''data_offer={#'create_date':, 'sequence': 0, 
                            'course_ids': (2,0,[course_id,]), 
                            'is_planned': True, 
                            'duration': 40.0, 
                            #'purchase_line_ids': [], 'id': 30, 'management': False, 
                            'product_line_id': [10, 'SETTORE'], 
                            'type_id': [13, 'SPECIALISTICI'], 
                            'name': 'Il prodotto alimentare: caratteristiche dei prodotti e normativa', 
                            'state': 'draft', 
                            'lang_id': [2, 'Italian / Italiano'], 
                            #'objective': False, 'target_public_id': False, 
                            #'is_certification': False, 'complementary_offer_ids': [], 
                            #'description': False, 'requeriments': False, 'notification_note': False, 
                            'format_id': [1, 'in classe'], 
                            'is_standalone': 1, 
                            #'preliminary_offer_ids': [], 
                            'kind': 'standard', 
                            #'can_be_planned': False, 
                            'product_id': [1, 'Tutor'], 
                            #'theme_ids': [], 'purchase_line_log_ids': [], 'included_offer_ids': []
                           }'''
        else: # decrease start (Header line to jump)
             start-=1

except:
    print '>>> [ERROR] Error importing data!'
    raise # Scrivo l'errore per debug

print "[INFO]","Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
