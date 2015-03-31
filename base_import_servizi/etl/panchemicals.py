# -*- encoding: utf-8 -*-
import pdb
def ParseDiscount(discount):
    # get mexal text value, return 
    res={}
    discount=discount.strip()
    discount=discount.replace(",",".")
    discount_list=discount.split('+')
    if len(discount_list): #
       base_discount=100.00  # 100%
       for aliquota in discount_list:
           #print "********************",aliquota
           try: 
              i=float(eval(aliquota))
           except:
              i=0.00
           base_discount-=base_discount * i / 100.00 
       res['value']=100 - base_discount
       res['rates']= '+'.join(discount_list)
    else:
       res['value']=0
       res['rates']=''
    return res

def getCurrency(sock,dbname,uid,pwd,name):
    # get Currency from code, ex. EUR, CHF
    currency_id = sock.execute(dbname, uid, pwd, 'res.currency', 'search', [('name', '=', name),]) 
    if len(currency_id): 
       return currency_id[0] # take the first
    else:
       return #sock.execute(dbname,uid,pwd,'res.currency','create',data)  # TODO create ??

def getPricelistType(sock,dbname,uid,pwd,key,data):
    # Create type pricelist
    pl_id = sock.execute(dbname, uid, pwd, 'product.pricelist.type', 'search', [('key', '=', key),]) 
    if len(pl_id): 
       return pl_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.pricelist.type','create',data)  
 
def CreateAllPricelist(sock, dbname, uid, pwd, name_ids, currency_ids, pl_pricelist=[], pl_version=[]):    
    # create all N pricelist enrty with different currency and type=sale
    ID_pricelist_type=getPricelistType(sock,dbname,uid,pwd,'sale',{'name': 'Sale Pricelist', 'key': 'sale'}) # Create price list 'sale' if not exist
    i=0
    for pricelist in name_ids:   # Create Pricelist (product.pricelist)        
        name="Listino Mexal n. " + pricelist
        pl_id = sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', pricelist,)]) 
        if len(pl_id): 
           pl_pricelist[i]= pl_id[0] 
        else:
           pl_pricelist[i]=sock.execute(dbname,uid,pwd,'product.pricelist','create',{'name':name,
                                                                        'currency_id': getCurrency(sock,dbname,uid,pwd,currency_ids[i]),
                                                                        'type': 'sale',
                                                                        'mexal_id': pricelist, # << extra fields
                                                                        'import': True,        # <<  
                                                                        })  

        # Create base version (product.pricelist.version)
        version="Versione base " + pricelist
        version_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', pricelist,)]) 
        if len(version_id): 
           pl_version[i]= version_id[0] 
        else:
           pl_version[i]=sock.execute(dbname,uid,pwd,'product.pricelist.version','create',{'name':version,
                                                                                           'pricelist_id': pl_pricelist[i],  # TODO verify relation field
                                                                                           'mexal_id': pricelist, # << extra fields
                                                                                           'import': True,        # <<  
                                                                                          })  
         
        i+=1
    return pl_version # return version_id used for items import

def ReadAllPricelist(sock, dbname, uid, pwd,range_list,pricelist_fiam_id=[]):
    for element in range_list:
        pl_id=sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', element,)]) 
        if pl_id:
           pricelist_fiam_id[element]=pl_id[0]
        else:
           pricelist_fiam_id[element]=0
    return       

# Variants per Customer
def GetMexalPLVersion(sock, dbname, uid, pwd, mexal_id): 
    item_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', mexal_id)]) 
    if item_id: 
       return item_id[0] 
    else:
       print "Errore searching Client version price list! *******************" 
       return 0 # Generate an error? *******
def GetMexalPL(sock, dbname, uid, pwd, mexal_id): 
    item_id = sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', mexal_id)]) 
    if item_id: 
       return item_id[0] 
    else:
       print "Errore searching Client version price list! *******************" 
       return 0 # Generate an error? *******

def GetPricelist(sock, dbname, uid, pwd, customer_id, mexal_pl_id, pl_default_id, pl_ids={}): # 2 returned values in dict
    '''Create price list for customer, Create a price list version (set up main price list with max priority)
       Create base version (product.pricelist.version)
       Note: 1 PL for 1 imported customer, 2 PV version for 1 imported customer!
    '''
    
    item_currency_id=sock.execute(dbname,uid,pwd,'product.pricelist','read',pl_default_id,[]) # get currency from default PL base
    #print item_currency_id,pl_ids, pl_default_id, customer_id, "**************************************"
    
    if item_currency_id:
       #print item_currency_id['currency_id'][0] 
       currency_id=item_currency_id['currency_id'][0] 
    else:
       currency_id=0
       
    if not currency_id:
       currency_id=getCurrency(sock,dbname,uid,pwd,"EUR") # TODO parametrize default currency if there isn't a PL!

    # Create Pricelist base per client:   
    name="Listino base cliente: [%s] " %(customer_id)
    pl_id = sock.execute(dbname, uid, pwd, 'product.pricelist', 'search', [('mexal_id', '=', customer_id)]) 
    if pl_id: 
       pl_ids['pricelist']= pl_id[0]  # <<<<<<<<<<<<<<<
    else:
       pl_ids['pricelist']=sock.execute(dbname,uid,pwd,'product.pricelist','create',{'name':name,
                                                                      'currency_id': currency_id, # getCurrency(sock,dbname,uid,pwd,currency),
                                                                      'type': 'sale',  # Sale already exist, created from first base importation of PL
                                                                      'mexal_id': customer_id, # << extra fields
                                                                      'import': True,        # <<  
                                                                      })  

    # Create Pricelist verion base per client:
    version="Versione cliente: [%s]"  % (customer_id)
    version_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', customer_id)])
    if version_id:
       pl_ids['version']= version_id[0] 
    else:
       pl_ids['version']=sock.execute(dbname,uid,pwd,'product.pricelist.version','create',{'name':version,
                                                                                           'pricelist_id': pl_ids['pricelist'],  # TODO verify relation field
                                                                                           'mexal_id': customer_id, # << extra fields
                                                                                           'import': True,        # <<  
                                                                                           })
    # Create item: price list based on (if there is not particularity is the base version PL):
    #pdb.set_trace()  
    # Controllo se il cliente esiste già per prelevare il listino di Mexal base:
    item_based_data={#'price_round': 0.0, 
                    #'price_discount': 0.0, 
                    'base_pricelist_id': GetMexalPL(sock, dbname, uid, pwd, mexal_pl_id), #mexal_pl_id), # Dovrebbe puntare al listino base, es.4
                    'sequence': 10, 
                    #'price_max_margin': 0.0, 
                    #'company_id': False, 
                    #'product_tmpl_id': False, 
                    #'product_id': False, 
                    'base': -1,  # Price list
                    'price_version_id': GetMexalPLVersion(sock, dbname, uid, pwd, customer_id),  # mandatory  ******************* metter quello di base
                    'min_quantity': 1, 
                    #'price_surcharge': 0.0, 
                    #'price_min_margin': 0.0, 
                    #'categ_id': False, 
                    'name': "Listino di riferimento n. %d" % (mexal_pl_id),
                    'mexal_id': customer_id, # << extra fields
                    }
    item_based_id = sock.execute(dbname, uid, pwd, 'product.pricelist.item', 'search', [('mexal_id', '=', customer_id,)]) 
    if len(item_based_id): # update
       upd_item_based=sock.execute(dbname,uid,pwd,'product.pricelist.item','write',item_based_id[0],item_based_data)
    else:
       pl_ids['version']=sock.execute(dbname,uid,pwd,'product.pricelist.item','create',item_based_data)
    return

def GetVersionPricelist(sock, dbname, uid, pwd, customer_id): 
    version_id = sock.execute(dbname, uid, pwd, 'product.pricelist.version', 'search', [('mexal_id', '=', customer_id,)]) 
    if len(version_id): 
       return version_id[0] 
    else:
       print "Errore searching Client version price list! *******************" 
       return 0 # Generate an error? *******

def GetProductID(sock, dbname, uid, pwd, ref): 
    item = sock.execute(dbname, uid, pwd, 'product.product', 'search', [('mexal_id', '=', ref)])
    if item: 
       return item[0]
    else:
       print "Errore searching Client particularity product from code! ******************"
       return 0 # ERROR!

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
