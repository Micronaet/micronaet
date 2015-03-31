#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules used for ETL customers/suppliers
# use: ETL.py file_csv_to_import

# Modules required:
import ConfigParser,xmlrpclib,csv,sys
import string,time
from mx.DateTime import now


# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test

trance='1' 

context={'lang':'it_IT','tz':False} #Set up an italian context 

# Create standard list:
partner_titles=("S.p.A.","S.n.C.","S.r.l.","Soc. Coop.","S.a.S.","S.d.f.")
contact_titles=("Sig.","Sig.ra","Ing.","Geom.","Rag.","Dott.","Dr.","Avv.to","Comm.")
region_list=("Valle D'Aosta","Piemonte","Liguria","Lombardia","Veneto","Trentino Alto Adige","Friuli Venezia Giulia","Emilia Romagna","Toscana","Lazio","Umbria","Marche","Abruzzo","Molise","Campania","Basilicata","Puglia","Calabria","Sicilia","Sardegna")
team_list=("Fiam - Gruppo Commerciale","G.P.B. - Gruppo Commerciale")

# TODO: Insert Stage of contact complete and set up partner leads to 1st value

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

def ShortCut(valore=''):
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore

def CreateTitle(dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

def getTeam(dbname,uid,pwd,team,code): 
    # get exist team or create it from campaign name <<< note
    team_id=sock.execute(dbname,uid,pwd,'crm.case.section','search',[('name','=',team)])
    if team_id:
       return team_id[0]
    return sock.execute(dbname,uid,pwd,'crm.case.section','create',{'name':team,'code':code})  
       
def CreateTeam(dbname,uid,pwd,team,team_list):
    if team:
       if team[0:3].lower()=="gpb": # The GPB team start from GPB, ex: "GPB - xxx"
          return getTeam(dbname,uid,pwd,team_list[1],"SaleGPB") # only this return GPB (verify return!)

    return getTeam(dbname,uid,pwd,team_list[0],"SaleFiam")    

def CreateCategories(dbname, uid, pwd, categorie):
    # Create standard structure of category for CRM 
    # Customer
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', 'Cliente')])
    if len(cat_id): 
       categorie['customer']=cat_id[0] 
    else:
       categorie['customer']=sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': 'Cliente',})  
    # Supplier
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', 'Fornitore')])
    if len(cat_id): 
       categorie['supplier']=cat_id[0] 
    else:
       categorie['supplier']=sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': 'Fornitore',})  
    # Customer / Potential
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', 'Potenziale'),('parent_id','=',categorie['customer'])])
    if len(cat_id):
       categorie['c_if']=cat_id[0]
    else:
       categorie['c_if']=sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': 'Potenziale','parent_id': categorie['customer'],})  
    # Customer / Potential
    cat_id = sock.execute(dbname, uid, pwd, 'res.partner.category', 'search', [('name', '=', 'Potenziale'),('parent_id','=',categorie['supplier'])])
    if len(cat_id): 
       categorie['s_if']=cat_id[0]
    else:
       categorie['s_if']=sock.execute(dbname,uid,pwd,'res.partner.category','create',{'name': 'Potenziale','parent_id': categorie['supplier'],})  
    return 

def GetUserMicronaet(dbname, uid, pwd):
    # Create username that own record created (set up admin permission)
    # User: Micronaet

    search_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('login', '=', 'admin')])
    read_id_admin = sock.execute(dbname, uid, pwd, 'res.users', 'read', search_id_admin[0])

    search_id = sock.execute(dbname, uid, pwd, 'res.users', 'search', [('name', '=', 'Micronaet')])
    if len(search_id): 
       user_id=search_id[0]
    else:
       user_id=sock.execute(dbname,uid,pwd,'res.users','create',{'name': 'Micronaet','login': 'Micronaet', 'groups_id': read_id_admin['groups_id'], 'password': pwd}) # Create user like admin (groups and pwd)
    return user_id

def CreateCRMcampaign(dbname, uid, pwd, campaign):
    # Create or get ID of campaign (for not empty values)
    # Campaign = crm.case.resource.type (ex. Fiera 1, Summer Mailing, New catalog 2009)
    # Note: case: "GPB - Spoga 2010)  GPB=team, Campaign=Spoga 2010
    
    if campaign[0:3].lower=="gpb":
       campaign=campaign[3:-1].replace("-","")
       campaign=campaign.strip()            
       
    if campaign:
       cat_id = sock.execute(dbname, uid, pwd, 'crm.case.resource.type', 'search', [('name', '=', campaign)])
       if len(cat_id): 
          return cat_id[0] 
       else:
          return sock.execute(dbname,uid,pwd,'crm.case.resource.type','create',{'name': campaign,})  
    else: 
       return # cannot create empty campaign (item present)

def CreateCRMcategory(dbname, uid, pwd, categ):
    # Create or get ID of category (for not empty values)
    # Category = crm.case.categ (ex. Arredamento, discoteca ecc.)
    # object_id must be: "crm.lead"
    if categ:
       object_id=sock.execute(dbname,uid,pwd,'ir.model','search',[('name','=','crm.lead')])[0]
       cat_id = sock.execute(dbname,uid,pwd,'crm.case.categ','search',[('name','=',categ),('object_id','=',[object_id])])
       if len(cat_id): 
          return cat_id[0] 
       else:
          return sock.execute(dbname,uid,pwd,'crm.case.categ','create',{'name': categ, 'object_id': object_id})  
    else:
       return # cannot create empty category

def CreateCRMdepartment(dbname, uid, pwd, department=None):
    # Create or get ID of sale department (if empty find or create Sales Dep.)
    # Department = crm.case.section (ex. Sales Deparment)
    if department:
       dep_id = sock.execute(dbname, uid, pwd, 'crm.case.section', 'search', [('name', '=', department.title())])
       if len(dep_id): 
          return dep_id[0] 
       else:
          return sock.execute(dbname,uid,pwd,'crm.case.section','create',{'name': department.title(),})  
    else: 
       dep_id = sock.execute(dbname, uid, pwd, 'crm.case.section', 'search', [('name', '=', 'Sales Department')])
       if len(dep_id):
          return dep_id[0] 
       else:
          return sock.execute(dbname,uid,pwd,'crm.case.section','create',{'name': 'Sales Department',})  

       return # cannot create empty campaign

def getRegion(dbname,uid,pwd,region):
    # Get region ID of passed name (use like for Trentino and Emilia)
    region=region.strip()       
    region=region.title()            
    return sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name','like',region)]) 

def getCountry(dbname, uid, pwd, country_parameter={},blacklist={}):
    # parse a text field to locate ID of country code
    # country dictionary: name=name passed, 
    #                     return in dic: 'region': name
    #                                    'region':id  
    #                     return with func: country_id
    country=country_parameter['name']
    if string.find(country.lower(),"italia")>=0: # For italy region fomat is, for ex. "ITALIA - LAZIO"
       lista=country.split("-")
       country="Italia"      
       if len(lista)==2:
          region_id=getRegion(dbname,uid,pwd,lista[1]) # seek region ID       
          if region_id:
             country_parameter['region_id']=region_id[0]
          else:
             if lista[1] not in blacklist: # add region to black list
                blacklist.append(lista[1])   
       else:
          print "Errore cercando la regione, dati:", lista    
    else:     
       country=country.title()
       #country_parameter['region_id']=0 # no region set up (default)
    
    country_id = sock.execute(dbname, uid, pwd, 'ir.translation', 'search', [('lang', '=', 'it_IT'),('name','=','res.country,name'),('value','like',country)]) 
    if len(country_id):
       country_id=sock.execute(dbname, uid, pwd, 'ir.translation', 'read', country_id[0])
       return country_id['res_id']
    else:
       if country not in blacklist:
          blacklist.append(country)
       return # no country code found

def CreateAllRegion(dbname,uid,pwd,regions):
    # Create region as a res.country.state linked to Italy
    country_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('name','=',"Italy")]) 
    for region in regions:
        region_id = sock.execute(dbname, uid, pwd, 'res.country.state', 'search', [('name', '=', region),('country_id','=',country_id)])
        if not len(region_id):            
           region_id=sock.execute(dbname,uid,pwd, 'res.country.state', 'create',{'name': region.title(), 
                                                                                 'country_id': country_id[0], 
                                                                                 'code': region[0:2].upper(), # first 2 char
                                                                                })  
    return region_id # if there is a list of one is usefull
    
def CreateChannel(dbname, uid, pwd, channel):
    # parse a text field to locate canal or partner
    # Actual rule: Ricerca or, if not empty: Fiera
    if channel:
       if channel.title()=="Ricerca":
          can_id = sock.execute(dbname, uid, pwd, 'res.partner.canal', 'search', [('name', '=', 'Ricerca')])
          if len(can_id): 
             return can_id[0] 
          else:
             return sock.execute(dbname,uid,pwd,'res.partner.canal','create',{'name': 'Ricerca',})
       else:
          can_id = sock.execute(dbname, uid, pwd, 'res.partner.canal', 'search', [('name', '=', 'Fiera')])
          if len(can_id): 
             return can_id[0] 
          else:
             return sock.execute(dbname,uid,pwd,'res.partner.canal','create',{'name': 'Fiera',})
    else:
       return # nessun canale se non è indicata la campagna

# Initialize variables
categorie={'customer':0, 'supplier':0, 'c_if':0, 's_if':0}
user_id_modify=0

# Start main code *************************************************************
if len(sys.argv)!=2 :
   print """
         *** Syntax Error! ***
         *   > Use the command with this syntax: python ./ETL_contact.py name_file_csv.csv
         *********************
         """
   sys.exit()

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

CreateCategories(dbname, uid, pwd, categorie) 
user_id_modify=GetUserMicronaet(dbname, uid, pwd) # create user Micronaet or get it

CreateTitle(dbname,uid,pwd,partner_titles,'partner') # Create standard partner title
CreateTitle(dbname,uid,pwd,contact_titles,'contact') # Create standard contact title
                  
country_not_found=[] # list of county not found

# Open CSV passed file (see arguments) mode: read / binary, delimiation char ";"
FileInput=sys.argv[1]

# CreateCRMcampaign
lines = csv.reader(open(FileInput,'rb'),delimiter=separator)
counter={'tot':0,'new':0,'upd':0}

CreateAllRegion(dbname,uid,pwd,region_list)
try:
    for line in lines:
        if line[0] != '':
          if line[0] !='ID':  
            # Mapping fields, from CVS to program variable
            # CSV file data:
            ref = "I" + trance + "." + Prepare(line[0])  # Import tranche 1, ex. for ref: I1.41 
            name = Prepare(line[1]).title()  # Title for Camel Case
            contact=Prepare(line[2]).title()
            date = PrepareDate(line[3])           # date of contact
            street = Prepare(line[4]).title()
            city = Prepare(line[5]).title()
            zipcode = line[6]         # contact?
            country = Prepare(line[7])
            phone = line[8]
            fax = line[9]
            note = Prepare(line[10])
            campaign = Prepare(line[11]).title() #Fiera or Internet (Note: Team GPB o FIAM)
            email = Prepare(line[12]).lower()
            website = Prepare(line[13]).lower()
            category = Prepare(line[14]).title() # sector
            has_cat = line[15]  # catalog send
            has_pl = line[16]   # price list send
            has_off = line[17]  # offer send
            document = line[18] # name of document send
            senddate = PrepareDate(line[19]) # date of send ...
     
            # calculated field:
            team_id = CreateTeam(dbname,uid,pwd,campaign,team_list) # If begin with GPB is GPB, else FIAM
            descrizione = "Contattare"
            # Contacting for... Check box 
            if has_cat.lower()=='false':
               descrizione += '(no cat.)'
            else:
               descrizione += "(cat. ok)"

            if has_pl.lower()=='false':
               descrizione += "(no list.)"
            else:
               descrizione += "(list. ok)"

            if has_off.lower()=='false':
               descrizione += "(no offerta)"
            else:     
               descrizione += "(offerta ok)"
            descrizione +="[data: %s] "%(senddate or now) 

            if ref: # test country id there is an ID
               parameter= {'name':country,'region_id':0,}
               country_id = getCountry(dbname, uid, pwd, parameter,country_not_found)
               region_id=parameter['region_id']
               counter['tot'] += 1  

            # test if record exists (basing on Ref. as code of Partner)
            item = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [('ref', '=', ref)])

            # Create lead for this client, values for update/create (without client_id > only for updade) 
            data_lead = {'name': note or descrizione[0:63], # max 64
                        #'partner_id': ins_id_partner, # Only for new records
                        #'create_date': senddate,
                        'description': descrizione + (note or '') ,
                        'date_action_last': senddate,     
                        'fax': fax,
                        'phone': phone,
                        'zip': zipcode,
                        'email_from': email,
                        'type_id': CreateCRMcampaign(dbname,uid,pwd,campaign),  #Occasione
                        'categ_id': CreateCRMcategory(dbname,uid,pwd,category), #Settore 
                        'channel_id': CreateChannel(dbname,uid,pwd,campaign),   #Macro Canale (parte di occasione/campaign)
                        # 'stage_id': , #Nuovo
                        'optin': email or False,
                        'contact_name': contact[0:63] or name[0:63], # max 64
                        'partner_name': name[0:63], # max 64     
                        'section_id': team_id,
                        'country_id': country_id, 
                        }
         
            if item:  # partner already exist
               counter['upd'] += 1  
               try:                   
                  data = {'name': name,
                          'customer': 1,
                          'date':date,
                          #'section_id': team_id,
                          #'category_id':[(6,0,[categorie['c_if']])],
                         }                  
                  item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', item, data) # update only name

                  # ** TODO ** complete analisys of address, contact, leads, jobs
                  #id_address=sock.execute(dbname,uid,pwd,'res.partner.address','search',[('partner_id','=',item[0])])                  
                  #if id_address:
                  #   mod_id_address=sock.execute(dbname,uid,pwd,'res.partner.address','write',id_address[0],{'state_id': region_id})
                  # Creo il contatto:                                 
                  #id_contact=sock.execute(dbname,uid,pwd,'res.partner.contact','search',[('partner_id','=',item[0])]) 
                  #if id_contact:
                  #   ins_id_contact=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'write', id_contact[0],{'name':contact or name})

                  # Update lead for this client
                  id_lead=sock.execute(dbname,uid,pwd,'crm.lead','search',[('partner_id','=',item)]) # NOTE: use only for single batch import
                  ins_id_lead=sock.execute(dbname,uid,pwd,'crm.lead','write',id_lead, data_lead)
               except:
                  print "Current record data:", data
                  raise 
               print counter['tot'], "Already exist: ", ref, name
            else:           
               counter['new'] += 1  
               try:   
                  # Creo il contatto:                                 
                  data={'name':contact or name,
                        'email':email,                        
                       }
                  ins_id_contact=sock.execute(dbname, uid, pwd, 'res.partner.contact', 'create', data)
                  # Creo il partner:
                  data={'ref': ref,
                        'name': name,
                        'customer': 1,
                        'website': website,
                        'comment': note,
                        'section_id': team_id,
                        'category_id':[(6,0,[categorie['c_if']])],
                        }
                  ins_id_partner = sock.execute(dbname,uid,pwd,'res.partner','create', data)
                  # Creo l'indirizzo:
                  data={'city': city, 
                        'country_id': country_id,
                        'street': street,
                        'zip' : zipcode, 
                        'phone': phone, 
                        'fax': fax,
                        'email': email,
                        'partner_id': ins_id_partner,
                        'state_id': region_id
                        }
                  ins_id_address=sock.execute(dbname,uid,pwd,'res.partner.address','create',data)
                  # Creo il lavoro:
                  data={'address_id':ins_id_address,
                        'contact_id':ins_id_contact,
                       }
                  ins_job_id = sock.execute(dbname, uid, pwd, 'res.partner.job', 'create', data)
                  # Create lead for this client
                  data_lead['partner_id']=ins_id_partner # extra field for create lead
                  ins_id_lead=sock.execute(dbname,uid,pwd,'crm.lead','create',data_lead)
                  print counter['tot'], "Insert: ", ref, name
               except:
                  print "****************************************"
                  print "Error writing: ", data
                  print "****************************************"
                  raise  # normal text of error

except:
    print '>>> Errore importando i dati!'
    raise #Exception("Errore di importazione!") # Scrivo l'errore per debug

print "Total line: ",counter['tot']," (imported: ",counter['new'],") (updated: ", counter['upd'], ")"
if country_not_found:
   print "Country non found:", country_not_found
