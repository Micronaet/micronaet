#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Modules required:
import xmlrpclib, ConfigParser, pdb

#if sys.argv[1][-3:]=="FIA":
cfg_file="../openerp.cfg"
#else: #"GPB"
#   cfg_file="openerp.gpb.cfg"
   
# Set up parameters (for connection to Open ERP Database) ********************************************
config = ConfigParser.ConfigParser()
config.read([cfg_file]) # if file is in home dir add also: , os.path.expanduser('~/.openerp.cfg')])
dbname=config.get('dbaccess','dbname')
user=config.get('dbaccess','user')
pwd=config.get('dbaccess','pwd')
server=config.get('dbaccess','server')
port=config.get('dbaccess','port')   # verify if it's necessary: getint
separator=config.get('dbaccess','separator') # test
verbose=eval(config.get('import_mode','verbose'))  # for info message

# Start main code *************************************************************
# FUNCTION:
def load_fiscal_position(sock, dbname, uid, pwd, fiscal_position_list):
    ''' get fiscal position for 3 states of openerp, from mexal the fields are: C, E, I 
        NOTA: il programma è cablato sul piano dei conti italiano perciò vediamo solo 
        le descrizioni italiane per i test
        TODO: parametrizzare con l'ID azienda!!
    '''
    #import pdb; pdb.set_trace()

    fiscal_element=sock.execute(dbname, uid, pwd, 'account.fiscal.position', 'search', [])
    fiscal_element_read=sock.execute(dbname, uid, pwd, 'account.fiscal.position', 'read', fiscal_element)
    for element in fiscal_element_read:
        if element['name']=='Regime Intra comunitario':
           fiscal_position_list['c']=element['id']
        elif element['name']=='Regime Extra comunitario':
           fiscal_position_list['e']=element['id']
        elif element['name']=='Italia':
           fiscal_position_list['i']=element['id']
    return

# XMLRPC connection for autentication (UID) and proxy 
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common', allow_none=True)
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object', allow_none=True)

# Rilevo gli ID per le 3 posizioni fiscali note: C E I 
fiscal_position_list={'c':0,'e':0,'i':0,}
load_fiscal_position(sock, dbname, uid, pwd, fiscal_position_list)

partner_ids = sock.execute(dbname, uid, pwd, 'res.partner', 'search', [])
partner_read = sock.execute(dbname, uid, pwd, 'res.partner', 'read', partner_ids, ('id', 'name', 'country', 'property_account_position', 'type_cei', 'import', 'lang'))

lang='it_IT'
for partner in partner_read:
    if partner['country'] and partner['country'][1]=="Italy":
       type_CEI='i' # TODO cercare regola per capirlo dal partner
       lang='it_IT'
    elif partner['country'] and partner['country'][1].lower() in ("austria", 
                                                          "belgium", "belgio"
                                                          "bulgaria",
                                                          "cyprus", "cipro",
                                                          "czech republic", "repubblica ceca", 
                                                          "denmark", "danimarca",
                                                          "estonia",
                                                          "finland", "finlandia",
                                                          "france", "francia",
                                                          "germany", "germania",
                                                          "greece", "grecia",
                                                          "hungary", "ungaria",
                                                          "ireland", "irlanda", 
                                                          "latvia", "lettonia",
                                                          "lithuania", "lituania",
                                                          "luxembourg", "lussemburgo",
                                                          "malta", "principato di malta",
                                                          "netherlands", "nederland", "olanda",
                                                          "poland", "polonia", "polland",
                                                          "portugal", "portogallo",
                                                          "united kingdom", "regno unito", "gran bretagna", "great britan",
                                                          "slovak republic", "repubblica slovacca", "slovacchia",
                                                          "spain", "spagna", 
                                                          "sweden", "svezia",
                                                          "yugoslavia", ):
       type_CEI= 'c'
       lang='en_US'
    else:
       type_CEI= 'e'
       lang='en_US'
          
    if type_CEI in ('c','e','i','v','r',):
       if type_CEI in ('v','r',):
          type_CEI='e' # Vaticano and RSM are extra CEE
       fiscal_position=fiscal_position_list[type_CEI]
    else:
       fiscal_position=False

    #pdb.set_trace()
    if (lang != partner['lang']) or (partner['type_cei'] != type_CEI) or (partner['property_account_position'] and (partner['property_account_position'][0] != fiscal_position)):
       data={#'fiscal_id_code': fiscal_code, 
          #'lang_id': lang_id,
          'property_account_position': fiscal_position,
          'type_cei': type_CEI,
          'lang': 'en_US',
          }
       item_mod = sock.execute(dbname, uid, pwd, 'res.partner', 'write', partner['id'], data) # (update partner) TODO ripristinarlo per la scrittura
       print "Partner (%s): %s (%s), CEI: %s > %s -- Pos. F.: %s > %s - Lang: %s > %s"%(partner['import'], partner['name'], partner['country'] and partner['country'][1], partner['type_cei'], type_CEI, partner['property_account_position'],  fiscal_position, partner['lang'], lang)

