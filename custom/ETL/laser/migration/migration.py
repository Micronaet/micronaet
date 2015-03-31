# -*- encoding: utf-8 -*-
# Migration from DB 1 to DB 2 (partner - address - job - contact + new inherit simple list m2o relationship)
import xmlrpclib, ConfigParser, sys, pdb
from mic_ETL import *

# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read(['openerp.cfg']) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])

# Connection Origin
dbname1=config.get('dbaccess1','dbname')
user1=config.get('dbaccess1','user')
pwd1=config.get('dbaccess1','pwd')
server1=config.get('dbaccess1','server')
port1=config.get('dbaccess1','port')   

# Connestion Destination
dbname2=config.get('dbaccess2','dbname')
user2=config.get('dbaccess2','user')
pwd2=config.get('dbaccess2','pwd')
server2=config.get('dbaccess2','server')
port2=config.get('dbaccess2','port')   

translation={'res.partner':{},'res.partner.address':{},'res.partner.contact':{},'res.partner.job':{}} # Dict for 4 table (new to old id)
totali={'res.partner':0,'res.partner.address':0,'res.partner.contact':0,'res.partner.job':0}
# Function:
def ReadAllO2Djob(sock1, dbname1, uid1, pwd1,sock2, dbname2, uid2, pwd2, translate_dict={}):  # dic is res.partner.job
    #pdb.set_trace()
    item1_ids = sock1.execute(dbname1, uid1, pwd1, 'res.partner.job', 'search', [])
    if item1_ids:
       origin_read_ids = sock1.execute(dbname1, uid1, pwd1, 'res.partner.job', 'read', item1_ids,['id','address_id','contact_id'])
       for origine in origin_read_ids: # read all origin job 
           if origine['address_id'] and origine['contact_id']: # if exist 
              # Transcode fields on new db ID 
              address_id= sock2.execute(dbname2, uid2, pwd2, 'res.partner.address', 'search', [('prev_id','=',origine['address_id'][0])])
              contact_id= sock2.execute(dbname2, uid2, pwd2, 'res.partner.contact', 'search', [('prev_id','=',origine['contact_id'][0])])
              if contact_id and address_id:
                 item2_ids = sock2.execute(dbname2, uid2, pwd2, 'res.partner.job', 'search', [('address_id','=',address_id[0]),('contact_id','=',contact_id[0])])
                 if item2_ids: # we suppose there's only one
                     translate_dict[origine['id']]=item2_ids[0]

def ReadAllO2D(sock, dbname, uid, pwd, table, translate_dict={}):  
    # Return dict with {[old_id]: new_id}
    item_ids = sock.execute(dbname, uid, pwd, table, 'search', [])
    if item_ids:
       read_ids = sock.execute(dbname, uid, pwd, table, 'read', item_ids, ['id', 'prev_id',])
       for item in read_ids:
           translate_dict[item['prev_id']]=item['id']
       #print "[INFO] %d Lines transcoded read in table %s!" % (i,table)
       return    
    else:
       print "[ERROR] Empty table: ", table
       return

def getID(sock, dbname, uid, pwd, table, name):
    # Get ID from table searching name
    if name and table:       
       element_id = sock.execute(dbname, uid, pwd, table, 'search', [('name', '=', name[1]),])
       if len(element_id): 
          return element_id[0] # take the first
       else:
          return False # There isn't a creation!
    else:
       return False

def getLangID(sock, dbname, uid, pwd, code):
    # Get ID from table searching name
    if code:       
       element_id = sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('code', '=', code),])
       if len(element_id): 
          return element_id[0] # take the first
       else:
          return False # There isn't a creation!
    else:
       return False
    
def CreateElement(sock, dbname, uid, pwd, table, name):
    # Create or get generic element by name (for standard anagraphic table with id, name, note)
    if name and table:
       element_id = sock.execute(dbname, uid, pwd, table, 'search', [('name', '=', name[1]),])
       if len(element_id): 
          return element_id[0] # take the first
       else:
          return sock.execute(dbname,uid,pwd,table,'create',{'name': name[1],})   
    else:
       return False

# ad hoc procedure:
def CreateTitle(sock, dbname, uid, pwd, table, name):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    if table=='partner':
       domain='partner'
    else:
       domain='contact' 
    title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', name),('domain','=',domain)])

    if title_id:             
       return title_id[0]
    else:
       return sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': name, 
                                                              'domain': domain, 
                                                              'shortcut': name.upper(),
                                                             })  

def TranscodeIDfromTable(sock, dbname, uid, pwd, ids, table, translation={}):
    # Transcode address ids in table with translation dictionary of values
    result=[]
    for element in ids:
        if element in translation.keys():
           result.append(translation[element])  
    return result

def TranscodeSingleIDfromTable(sock, dbname, uid, pwd, element, table, translation={}):
    if element: # integer
        if element in translation.keys():
           return translation[element]
    return

def PrepareDictionary(sock, dbname, uid, pwd, table, item, dizionario={}):
    # Modify dict for create element in DB 2 (with creation of m2o element and get id)
    # Default set up 
    item['prev_id']=item['id'] # Rename field id
    del item['id']       
          
    # Prepare item for write:
    if table=='res.partner':
       # Erase (updated with default values)
       del item['company_id']     # sembra compilata

       del item['ref_companies']  # Verify if filled with default
       del item['property_product_pricelist'] # Verificare con la lingua impostata
       del item['property_product_pricelist_purchase']
       del item['property_account_payable']
       del item['property_account_receivable']       
       del item['property_stock_customer']
       del item['property_stock_supplier']
       del item['address'] # linked from Address to Partner

       # Empty
       del item['events'] 
       del item['bank_ids'] 
       del item['child_ids']
       del item['category_id']  
       del item['invoice_ids']
       del item['contract_ids']

       # Filled:
       item['notif_participant']=True # TODO (vanno messi per default)
       del item['country'] # campo related (visualizza quello presente nell'address)
       item['lang']='it_IT'
       item['title_dimension_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.dimension',item['title_dimension_id']) # Verify [0] (and if not exist)
       item['title_sector_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.sector', item['title_sector_id'])                 
       item['office_id']=CreateElement(sock, dbname, uid, pwd, 'base.laser.office', item['office_id'])
       if 'notif_contact_id' in item.keys():  # TODO correggere questa parte (andrebbe remmata la prima esecuzione e poi ripristinata
          if item['notif_contact_id']: 
             item['notif_contact_id']=dizionario['res.partner.job'][item['notif_contact_id'][0]]
       if 'title' in item.keys(): 
          if item['title']:
             item['title']=CreateTitle(sock, dbname, uid, pwd, 'partner', item['title'][1])

       if 'property_account_position' in item.keys(): 
          del item['property_account_position']  # correggere e mettere [1, Italia] 
       if 'property_payment_term' in item.keys(): 
          del item['property_payment_term']  # (correggere 30 fine mese)
          
    elif table=='res.partner.address':
       item['country_id']=getID(sock, dbname, uid, pwd, 'res.country', [0,'Italy']) # set up all Italy (require [] fields)
       if item['partner_id']:
          item['partner_id']=TranscodeSingleIDfromTable(sock, dbname, uid, pwd, item['partner_id'][0], table, translation['res.partner']) 
       #del item['country_id'] # Verify
       del item['company_id'] # Verify [1, 'Laser'],
       del item['job_id']
       del item['job_ids']
    elif table=='res.partner.contact':
       #'gender' # Verify
       item['title_school_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.schoolsheet', item['title_school_id'])
       item['title_profpos_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.profposition', item['title_profpos_id'])
       item['title_contract_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.contract', item['title_contract_id'])
       item['title_prioritycat_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.prioritycat', item['title_prioritycat_id'])
       item['title_profstatus_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.profstatus', item['title_profstatus_id'])
       item['title_currentprof_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.currentprof', item['title_currentprof_id'])
       item['formation_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.contact.formation', item['formation_id'])
       item['profile_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.contact.profile', item['profile_id'])
       item['title_pip_state_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.contact.pip', item['title_pip_state_id'])
       item['title_ccnl_id']=CreateElement(sock, dbname, uid, pwd, 'res.partner.contact.ccnl', item['title_ccnl_id'])
       item['office_id']=CreateElement(sock, dbname, uid, pwd, 'base.laser.office', item['office_id'])

       item['lang_id']=getLangID(sock, dbname, uid, pwd, 'it_IT') # Filled as italian per default
       item['country_id']=getID(sock, dbname, uid, pwd, 'res.country', [0,'Italy']) # set up all Italy (require [] fields)
       if 'title' in item.keys(): 
          if item['title']:
             item['title']=CreateTitle(sock, dbname, uid, pwd, 'contact', item['title'][1])

       del item['course_ids']
       del item['partner_id'] 
       del item['job_id']
       del item['linguistic_skill_ids']
       del item['job_ids']
       del item['technical_skill_ids']

    elif table=='res.partner.job':
       if item['address_id']:
          item['address_id']=TranscodeSingleIDfromTable(sock, dbname, uid, pwd, item['address_id'][0], table, translation['res.partner.address'])  #es [2, 'Via Gammara,23 91011 Alcamo (Tp)']
       if item['contact_id']:
          item['contact_id']=TranscodeSingleIDfromTable(sock, dbname, uid, pwd, item['contact_id'][0], table, translation['res.partner.contact']) #es [1, 'Ida Mirrione']
       del item['name'] #'name': [2, 'Bridor Bridor Srl'], # calculated
       del item['pricelist_id'] # 1, public pricelist
       #try:
       if item['team_id']:
          print item
       del item['team_id']     
       #except:
       #    pdb.set_trace()
           
    else:
       print "[ERRORE] Tabella inwww.technotizie.it/esistente!"

try:
    sock1 = xmlrpclib.ServerProxy('http://' + server1 + ':' + port1 + '/xmlrpc/common')
    uid1 = sock1.login(dbname1,user1,pwd1)
    sock1 = xmlrpclib.ServerProxy('http://' + server1 + ':' + port1 + '/xmlrpc/object', allow_none=True)

    sock2 = xmlrpclib.ServerProxy('http://' + server2 + ':' + port2 + '/xmlrpc/common')
    uid2 = sock2.login(dbname2,user2,pwd2)
    sock2 = xmlrpclib.ServerProxy('http://' + server2 + ':' + port2 + '/xmlrpc/object', allow_none=True)

    # Linked anagraphic:
    ReadAllO2Djob(sock1, dbname1, uid1, pwd1,sock2, dbname2, uid2, pwd2, translation['res.partner.job'])
    if not translation['res.partner.job']: 
       print "Rilanciare l'applicativo dopo che l'esecuzione è terminata!(per caricare i contatti di riferimento)"
    j=[]
    tables=('res.partner','res.partner.address','res.partner.contact','res.partner.job') # order is important
    for table in tables:
       recordO_ids = sock1.execute(dbname1, uid1, pwd1, table, 'search', []) 
       if recordO_ids:
          itemO_ids=sock1.execute(dbname1, uid1, pwd1, table,'read',recordO_ids)
          for itemO in itemO_ids:
              PrepareDictionary(sock2, dbname2, uid2, pwd2, table, itemO, translation) # DB is for creation of m2o list
              recordD_ids = sock2.execute(dbname2, uid2, pwd2, table, 'search', [('prev_id','=',itemO['prev_id'])])  # id is deleted
              totali[table] +=1
              if recordD_ids: # Update
                 modD_ids=sock2.execute(dbname2, uid2, pwd2, table, 'write', recordD_ids, itemO) # no [0] is only one
                 print "[INFO] Modify", table, itemO['prev_id']
              else: # New
                 if table=='res.partner.job':
                    j.append(itemO)                     
                 else:      
                    insD_ids=sock2.execute(dbname2, uid2, pwd2, table, 'create', itemO)
                 print "[INFO] Created", table, itemO['prev_id']
       if table!='res.partner.job':
          ReadAllO2D(sock2, dbname2, uid2, pwd2, table, translation[table]) # After write all previous table, read old=new dict

    cPickleParticOutput('contatti.pkl',j)     
    print "Totali", totali 

    # NOTA: appena finito le varie importazioni creare uno scritp per mettere almeno l'address di default 
    # controllare che le contropartite dare e avere siano correttamente impostate nel piando dei conti italiano
    # Anche per le ditte senza nazione ovvero address
except:
   pdb.set_trace()
   raise

