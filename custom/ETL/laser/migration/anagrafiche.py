#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# This module add standard anagraphic list

# Modules required:
import xmlrpclib, sys, time, string, ConfigParser
from mx.DateTime import now

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess2','dbname')
user=config.get('dbaccess2','user')
pwd=config.get('dbaccess2','pwd')
server=config.get('dbaccess2','server')
port=config.get('dbaccess2','port')   # verify if it's necessary: getint


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

category_list={"Laser":("Scuola","Servizi alle imprese",),
               "Tipologia":("Cliente","Fornitore",),
               "Training":("Studente","Docente","Tutor","Stagista","Genitore/Tutore",),}

office_list=(r"C.F.P.",
             r"Servizi alle imprese",
             r"Ufficio doti / Apprendistato",)

study_sheet_list=(#r"Nessun titolo o licenza elementare!",
                  r"Licenza media inferiore",
                  r"Diploma di qualifica professionale (tramite istituto professionale)",
                  r"Qualifica professionale di I livello",
                  #r"Qualifica acquisita tramite apprendistato!",
                  #r"Diploma di maturità e diploma di scuola superiore!",
                  r"Qualifica professionale post diploma",
                  r"Certificato di specializzazione tecnica superiore (IFTS)",
                  r"Diploma universitario o laurea triennale",
                  #r"Master post laurea triennale!",
                  r"Laurea di durata superiore ai 3 anni",
                  #r"Dottorato, master, o specializzazione post laurea!",
                 )

contract_list=(r"Contratto a tempo determinato",
               r"Contratto a tempo indeterminato",
               r"Contratto di lavoro intermittente",
               r"Contratto di lavoro ripartito",
               r"Contratto di lavoro a tempo parziale",
               r"Contratto di apprendistato",
               r"Contratto di inserimento",
               r"Tipologie contrattuali a progetto o occasionale",
               r"Cassa integrazione guadagni ordinaria o straordinaria",
              )

priority_categories = (r"Lavoratori di imprese private con meno di quindici dipendenti",
                       r"Lavoratori inseriti nelle tipologie contrattuali previste dal \
                        titolo V, VI e VII previsto dal D.Lgs. 276/03",
                       r"Lavoratori di imprese private con CIGO e CIGS",
                       r"Persone iscritte nelle liste di mobilità",
                       r"Lavoratori over 45",
                       r"Donne over 40",
                       r"Lavoratori in possesso del solo titolo di licenza elementare o \
                        di istruzione obbligatoria",
                       r"Lavoratori disoccupati in attesa di ristrutturazione aziendale \
                        nonché aree e settori in crisi",
                       r"Persone provenienti da paesi non appartenenti all'unione Europea \
                        o di recente ammissione", 
                       r"Altri non prioritari",
                      )

professional_position=("Dirigente",
                       "Direttivo – Quadro",
                       "Impiegato – Intermedio",
                       "Operaio – Subalterno – Assimilati",
                       "Apprendista",
                       "Lavoratore presso il proprio domicilio per conto di imprese",
                       "Socio di cooperative di produzione lavoro",
                       )   

context={'lang':'it_IT','tz':False} #Set up an italian context 

# For final user: Do not modify nothing below this line (Python Code) *********
# Functions:
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

# Title (partner / contact) block #########################
def ShortCut(valore=''): 
    # used for code the title (partner or contact), ex.: Sig.ra > SIGRA
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore


def CreateTitle(dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

# Generic element block #########################
def CreateElement(dbname,uid,pwd,name,table):
    # Create or get generic element by name
    if name and table:
       element_id = sock.execute(dbname, uid, pwd, table, 'search', [('name', '=', name),])
       if len(element_id): 
          return element_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,table,'create',{'name': name,})   
    else:
       return 

def CreateAllElements(dbname,uid,pwd,value_list,table,title=False):
    # generic function for create elements in a table from tupla (element are stored in field: name)
    for element in value_list:
        if title:
           element_id=CreateElement(dbname,uid,pwd,element.title(),table)
        else: # as is
           element_id=CreateElement(dbname,uid,pwd,element,table)
 
    return # nothing is a procedure


# Category block #########################
def CreateCategory(dbname,uid,pwd,name,parent_id=0):
    # create Category and return ID, if exist return only ID (we suppose that name are in right case)
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', name),]) # TODO filter for parent_id
    if len(cat_id): 
       return cat_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': name,'parent_id': parent_id or False})  

def CreateAllCategories(dbname, uid, pwd, category_list):
    # Create standard structure of category based on dictionary + tuple for parent-child structure
    for parent in category_list.keys():
        parent_id=CreateCategory(dbname,uid,pwd,parent) # Create parent category with name of keys
        for child in category_list[parent]:   # Loop for child value of keys               
            CreateCategory(dbname,uid,pwd,child,parent_id) # Create child name with parent link ID
    return # nothing, is a procedure!
        
# Region block #########################
def getRegion(dbname,uid,pwd,region):
    # Get region ID of passed name (use "like" operator for Trentino and Emilia)
    region=region.strip()       
    region=region.title()            
    return sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name','like',region)]) 

def CreateAllRegion(dbname,uid,pwd,regions):
    # Create region as a res.country.state linked to Italy nation
    country_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('name','=',"Italy")]) 
    for region in regions:
        region_id = sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name', '=', region),('country_id','=',country_id)])
        if not len(region_id):            
           region_id=sock.execute(dbname,uid,pwd, 'res.country.state', 'create',{'name': region.title(), 
                                                                                 'country_id': country_id[0], 
                                                                                 'code': region[0:2].upper(), # first 2 char
                                                                                })  
    return 

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Create standard value for initial start up of DB
#CreateAllRegion(dbname,uid,pwd,region_list)                         # Region
#CreateAllCategories(dbname,uid,pwd,category_list)                   # Category structure
CreateTitle(dbname,uid,pwd,partner_titles,'partner')                # Title partner
CreateTitle(dbname,uid,pwd,contact_titles,'contact')                # Title contact
CreateAllElements(dbname,uid,pwd,office_list,"base.laser.office")   # Office
CreateAllElements(dbname,uid,pwd,priority_categories,"res.partner.prioritycat",True) # Categorie prioritarie
CreateAllElements(dbname,uid,pwd,contract_list,"res.partner.contract",True)  # Descrizione contratto
CreateAllElements(dbname,uid,pwd,professional_position,"res.partner.profposition",True) # Posizione professionale
CreateAllElements(dbname,uid,pwd,study_sheet_list,"res.partner.schoolsheet",True) # Titolo di studio
#Titolo di studio: res.partner.schoolsheet
#Professional Position res.partner.profposition
#Current Profession Status res.partner.profstatus'
#Current Profession res.partner.currentprof

print "[INFO] Creation completed!"
