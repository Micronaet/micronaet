#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import xmlrpclib, sys
# Parent group
list_parent_group=('Prodotti', 'Materie prime', 'Lavorazioni', 'Non classificati',)

# Raw material list
list_product_group=[{},{},{}]
list_product_group[0]={"Amaca": ("Amaca","Amache",),
                       "Appendiabiti": ("Appendiabito", "Appendiabiti",),
                       "Bauli": ("Baule","Bauli",),
                       "Birrerie": ("Birreri",),
                       "Brandine": ("Brandin",),
                       "Cantinette": ("Cantinett", " Botte", " Botti","Botti ", "Botte "),
                       "Carrelli": ("Carrell",),
                       "Chaise Longue": ("Chaise Longue",),
                       "Cuscini": ("Cuscin", "Poggiatest",),
                       "Copriruota": ("Copriruota",),
                       "Divani": ("Divan",), # C'è dondolina che è una sdraio
                       "Dondoli": (" Dondol", "Dondolo", "Dondoli "), # C'è dondolina che è una sdraio
                       "Fioriere": ("Fiorier",),
                       "Gazebo": ("Gazebo",),
                       "Lettini": ("Lettin",),
                       "Materassini": ("Materassin",),
                       "Ombrelloni": ("Ombrellon","Ombr.",),
                       "Ottomane": ("Ottoman",),
                       "Panca": ("Panca","Panche","Cassapanc",),
                       "Parasole": ("Parasole "," Parasole"),
                       "Paraventi": ("Paravent",),         #Pergole, Pergolina, Pergoline, Pergolato
                       "Pergole": ("Pergol",),         #Pergole, Pergolina, Pergoline, Pergolato
                       "Porta-Cd": ("Porta-Cd",),
                       "Poltrone": ("Poltron",),      #Poltrone, Poltroncina
                       "Prolunghe": ("Prolung",),
                       "Sofa'": ("Sofa'", ),
                       "Schienali": ("Schienal",),
                       "Sedie": ("Sedia", "Sedie", ),
                       "Sdraio": ("Sdraio", "Sedia Sdraio",),
                       "Sedili": ("Sedile", "Sedili",),
                       "Separe'": ("Separe'",),
                       "Sgabelli": ("Sgabell", "Poggiapied",),
                       "Spiaggine": ("Spiaggin",),
                       "Strutture": ("Struttur",),
                       "Tavoli": ("Tavol",),
                      }
list_product_group[1]={"Accessori": ("Accessori",),
                       "Aghi": ("Aghi",),
                       "Angolari": ("Angolar",),
                       "Aste": ("Aste", "Asta", "Astin",),
                       "Barre": ("Barra","Barre",),
                       "Banner": ("Banner",),
                       "Blocchetti": ("Blocchett",),
                       "Braccioli": ("Braccioli ","Bracciolo "), # "Sedia con b."
                       "Bussoline": ("Bussolin",),
                       "Bobine": ("Bobina","Bobine"),
                       "Bordini": ("Bordin",),
                       "Bussole": ("Bussol",),
                       "Cartoni": ("Carton",),
                       "Cavalletti": ("Cavallett",),
                       "Cavallotti": ("Cavallott",),
                       "Cellophane": ("Cellophane",),
                       "Cinghie": ("Cinghi",),
                       "Confezioni": ("Confezion",),
                       "Cremagliere": ("Cremaglier",),
                       "Dadi": ("Dadi ","Dado ",),
                       "Distanziali": ("Distanzial",),
                       "Elastici": (" Elastic", "Elastico ", "Elastici "),
                       "Etichette": ("Etichett",),
                       "Finta pelle": ("Finta pelle",), 
                       "Fondelli": ("Fondell",),
                       "Gambe": ("Gambe", "Gamba", "Gambetta",),
                       "Ganci": ("Ganci",),
                       "Manopole": ("Manopole","Manopola",),
                       "Molle": ("Molle","Molla",),
                       "Monoblocchi": ("Monoblocc",),
                       "Morsetti": ("Morsett",),
                       "Nastro": ("Nastro","Nastri",),
                       "Perni": ("Perni","Perno",),
                       "Piastre": ("Piastr",),
                       "Pinze": ("Pinze","Pinza"),
                       "Picchetti": ("Picchett",),
                       "Piani": ("Piani ","Piano ",),
                       "Piatti": ("Piatto ","Piatti ",),
                       "Piedini": ("Piedin",),
                       "Polistirolo": ("Polistirol",),
                       "Polveri": ("Polver",),
                       "Profili": ("Profil",),
                       "Puntali": ("Puntali","Puntale",),
                       "Rettangoli": ("Rettangoli","Rettangolo"),
                       "Ribattini": ("Ribattin",),
                       "Rivetti": ("Rivett",), 
                       "Rondelle": ("Rondell",),
                       "Sacchi": ("Sacchi","Sacco",),
                       "Saldature": ("Saldatur",),
                       "Scatole": ("Scatol",),
                       "Snodi": ("Snodo","Snodi",),
                       "Spugne": ("Spugne", "Spugna",),
                       "Staffe": ("Staffe", "Staffa",),
                       "Supporti": ("Support",),
                       "Tappi": ("Tappi", "Tappo",),
                       "Telai": ("Telai", "Telaio",),
                       "Teli": ("Tela ","Teli ", "Tele ","Telo "),
                       "Tende": ("Tende", "Tendaggi",),
                       "Tessuti": ("Tessuti","Tessuto", "Texplast", "Texfil", "Canapone", "Juta",),
                       "Tondini": ("Tondin",),
                       "Tovagliette": ("Tovagliett",),
                       "Triangoli": ("Triangoli","Triangolo"),
                       "Tubi": ("Tubo", "Tubi", "Tubolar", "Tubett",),
                       "Vassoi": ("Vassoi",),
                       "Velcri": ("Velcr",),
                       "Verghe": ("Verga","Verghe",),
                       "Viti": ("Viti ","Vite "),
                      }
list_product_group[2]={
                       "Cromature": ("Cromatur",),
                       "Zincature": ("Zincatur",),
                       "Saldature": ("Saldatur",),
                      }

def getProductGroup(sock,dbname,uid,pwd,name,parent=0):
    # Create or get Group
    item_id = sock.execute(dbname, uid, pwd, 'product.category', 'search', [('name', '=', name),('parent_id','=',parent)]) 
    if len(item_id): 
       return item_id[0] # take the first
    else:
       return sock.execute(dbname, uid, pwd,'product.category','create',{'name': name, 'parent_id':parent})  

def ResetAllProductGroup(sock,dbname,uid,pwd):
    category_search_id=getProductGroup(sock,dbname,uid,pwd,list_parent_group[-1]) # The last group
    product_list_searched_ids=sock.execute(dbname, uid, pwd, 'product.product', 'search', [('id','!=','0')])
    product_list_modified_ids=sock.execute(dbname, uid, pwd,'product.product','write', product_list_searched_ids,{'categ_id': category_search_id,}) # write "non classificati"
    

def updateAllProductGroup(sock,dbname,uid,pwd):
    # Read all product in DB and insert correct category group
    for i in range(0,3):
        category_search_id=getProductGroup(sock,dbname,uid,pwd,list_parent_group[i])
        for item_name in list_product_group[i]: # for all product with this parent id
            category_search_id=getProductGroup(sock,dbname,uid,pwd,item_name,list_parent_group[i])
            print "[INFO] Gruppo padre:", list_parent_group[i]
            for item_keyword in list_product_group[i][item_name]:
                print "[INFO]     Gruppo figlio:", item_name            
                print "[INFO]            Keyword:", item_keyword
                
                product_list_searched_ids=sock.execute(dbname, uid, pwd, 'product.product', 'search', [('name', 'ilike', item_keyword)]) 
                product_list_modified_ids=sock.execute(dbname, uid, pwd,'product.product','write',product_list_searched_ids,{'categ_id': category_search_id,})  
    
    return
