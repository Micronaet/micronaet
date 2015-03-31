# -*- encoding: utf-8 -*-
# Tolgo le city, es: Brescia (BS)
# Aggiorna tutte le province, zip, region basandosi sul campo city (portato in title!) 

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
 
# Funzioni:
def CasiParticolati(s_city):
    # Transcodifica alcuni casi particolari scritti male:
    s_city=s_city.title()
    if s_city == "Castelmella":
       return "Castel Mella"     
    elif s_city == "Cazzago S. Martino":
       return "Cazzago San Martino"
    elif s_city == "Desenzano D/G" or s_city == "Desenzano":
       return "Desenzano Del Garda"
    elif s_city == "Gardone V/T":
       return "Gardone Val Trompia"     
    elif s_city == "Palazzolo S/O":
       return "Palazzolo Sull'Oglio"     
    elif s_city == "Rodengo Saiano":
       return "Rodengo-Saiano"
    elif s_city == "S. Felice D/B" or s_city == "S. Felice Del Benaco":
       return "San Felice Del Benaco"     
    elif s_city == "S. Zeno" or s_city == "S. Zeno Sul Naviglio" or s_city == "S. Zeno S/N" or s_city == "Zeno Naviglio":
       return "San Zeno Naviglio"     
    return s_city

# For final user: Do not modify nothing below this line (Python Code) ********************************
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/common')
uid = sock.login(dbname ,user ,pwd)
sock = xmlrpclib.ServerProxy('http://' + server + ':' + port + '/xmlrpc/object')

# Aggiorno le province con la parentesi (la elimino!)
address_id = sock.execute(dbname, uid, pwd, "res.partner.address", 'search', [('city','ilike','('),('city','ilike',')')]) 
if address_id:
    address_read=sock.execute(dbname, uid, pwd, "res.partner.address", 'read', address_id)
    for indirizzo in address_read:
        city_prov=indirizzo['city'].split("(")
        s_city=city_prov[0].strip()
        s_city=s_city.title() 
        s_city=CasiParticolati(s_city)
        if not s_city: # città vuota (ma che contiene " ()"
            t_city_mod=sock.execute(dbname, uid, pwd, "res.partner.address", 'write', indirizzo['id'], {'city': False,})
        else:     
            t_city_ids = sock.execute(dbname, uid, pwd, "res.city", 'search', [('name', '=', s_city)]) 
            if t_city_ids: # è presente la città nel database:
               t_city_read=sock.execute(dbname, uid, pwd, "res.city", 'read', t_city_ids)
               # aggiorno l'elemento cambiandogli i campi ricavati:
               data_mod={'province': t_city_read[0]['province_id'][0],  # ID
                         'region': t_city_read[0]['region'][0],         # ID
                         'zip': t_city_read[0]['zip'],  
                         'city': s_city,                             # in title() form
                        }
               t_city_mod=sock.execute(dbname, uid, pwd, "res.partner.address", 'write', indirizzo['id'], data_mod)
            else: # provincia non trovata:
               print "NON TROVATA:", s_city, " >>", "Indirizzo:", indirizzo['city']
           
# Aggiorno le province partendo dalla city attuale (portata a title)           
address_id = sock.execute(dbname, uid, pwd, "res.partner.address", 'search', []) 
if address_id:
    address_read=sock.execute(dbname, uid, pwd, "res.partner.address", 'read', address_id)
    for indirizzo in address_read:      
        if indirizzo['city']: # esiste la città:
           s_city=indirizzo['city'].strip()
           s_city=s_city.title() # la porto con l'iniziale maiuscola
           s_city=CasiParticolati(s_city)
           t_city_ids = sock.execute(dbname, uid, pwd, "res.city", 'search', [('name', '=', s_city)]) 
           if t_city_ids: # è presente la città nel database:
              t_city_read=sock.execute(dbname, uid, pwd, "res.city", 'read', t_city_ids)
              # aggiorno l'elemento cambiandogli i campi ricavati:
              data_mod={'province': t_city_read[0]['province_id'][0],  # ID
                        'region': t_city_read[0]['region'][0],         # ID
                        'zip': t_city_read[0]['zip'],  
                        'city': s_city,                             # in title() form
                       }
              t_city_mod=sock.execute(dbname, uid, pwd, "res.partner.address", 'write', indirizzo['id'], data_mod)
           else: # provincia non trovata:
              print "NON TROVATA:", s_city, " >>", "Indirizzo:", indirizzo['city']
               
               
                  
