# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv, fields
import logging, sys, os        
_logger = logging.getLogger(__name__)

def log_error(self, cr, uid, operation, error, context=None):
    """ Log error in OpenERP log and add in log.activity object the same value
    """    
    self.pool.get('log.activity').log_error(cr, uid, operation, error)
    _logger.error(error) # global variable
    return False

def log_info(self, cr, uid, operation, info, context=None):
    """ Log error in OpenERP log and add in log.activity object the same value
    """    
    self.pool.get('log.activity').log_info(cr, uid, operation, info)
    _logger.info(info) # global variable
    return False
        
# Utility: #####################################################################

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
       
def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()

def getCountryFromCode(sock,dbname,uid,pwd,code):
    if code: 
       find_id = sock.execute(dbname, uid, pwd, 'res.country', 'search', [('code', '=', code),]) 
       if find_id: 
          return find_id[0] 
       else: 
          return False # TODO segnalare la mancanza della sigla
    else:
       return False # no code


def ShortCut(valore=''): 
    # used for code the title (partner or contact), ex.: Sig.ra > SIGRA
    if valore:
       valore = valore.upper()
       valore = valore.replace('.','')
       valore = valore.replace(' ','')
       return valore

def getTaxID(sock,dbname,uid,pwd,description):
    # get ID of tax from description value
    return sock.execute(dbname, uid, pwd, 'account.tax', 'search', [('description', '=', description),])[0]

def getLanguage(sock,dbname,uid,pwd,name):
    # get Language if exist (use english name request 
    return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

# PRODUCT
def getUomCateg(sock,dbname,uid,pwd,categ):
    # Create categ. for UOM
    cat_id = sock.execute(dbname, uid, pwd, 'product.uom.categ', 'search', [('name', '=', categ),]) 
    if len(cat_id): 
       return cat_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom.categ','create',{'name': categ,})  

def getUOM(sock,dbname,uid,pwd,name,data):
    # Create if not exist name: 'name' UOM with data: data{}
    uom_id = sock.execute(dbname, uid, pwd, 'product.uom', 'search', [('name', '=', name),]) 
    if len(uom_id): 
       return uom_id[0] # take the first
    else:
       return sock.execute(dbname,uid,pwd,'product.uom','create',data)  

# PARTNER & CONTACT
def CreateTitle(sock,dbname,uid,pwd,titles,table):
    # Create standard title for partner (procedure batch from tupla, set up from user)
    for title in titles:
        title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
        if not len(title_id):            
           title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                               'domain': table, 
                                                                               'shortcut': ShortCut(title),
                                                                              })  

class product_product_extra_fields(osv.osv):
    ''' Extra fields for ETL in product.product
    ''' 
    _inherit = 'product.product'

    # Utility function: ########################################################
    def get_uom(self, cr, uid, name, context=None):
        uom_id = self.pool.get('product.uom').search(cr, uid, [('name', '=', name),],context=context) 
        if uom_id: 
            return uom_id[0] # take the first
        else:
            return False   

    def force_uom(self, cr, uid, item_id, uom_id, context=None):
        ''' Force update of UOM for passed product
            item_id: single record id (to update)
            uom_id: new value
        '''
        try:
            return cr.execute("""update product_template set uos_id=%s, uom_id=%s, uom_po_id=%s where id=%s""", (
                uom_id, uom_id, uom_id, item_id))
        except:
            return False
        
    # Scheduled action: ########################################################
    def schedule_etl_product_import(self, cr, uid, context=None):
        ''' ETL operations for import product in OpenERP (parameter setted up in
            scheduled action for file name
        '''
        import logging, sys
        _logger = logging.getLogger('base_panchem')

        _logger.info("base_panchem: Start base sync product from AR_ANAGRAFICHE!")
        counter = {'tot':0, 'upd':0, 'err':0, 'err_upd':0, 'new':0}

        um = {}
        force_update_uom = {} #tuple list of ID and uom_id
        um['KG'] = self.get_uom(cr, uid, 'kg', context=context)
        um['T'] = self.get_uom(cr, uid, 't', context=context)
        um['N'] = self.get_uom(cr, uid, 'Unit(s)', context=context)

        cursor = self.pool.get('micronaet.accounting').get_product(
            cr, uid, context=context)
        if not cursor:
            _logger.error("Unable to connect no importation of product!")

        error_list = []
        supply_method_dbp = {}  # save product father > supply method
        father_dbp_ids = {}     # save product father > [product_id]

        for line in cursor:
            try:
                counter['tot'] += 1  
                # Retrive data:
                description = ("%s%s" % (
                    line['CDS_ART'].strip(),
                    line['CDS_AGGIUN_ART'].strip())
                ).title().replace(r"/", r"-")
                ref = line['CKY_ART'].strip()
                cost = line['NMP_UCA'] or line['NMP_COSTD'] or 0.0
                uom = line['CSG_UNIMIS_PRI'].strip()
                if line['IFL_ART_DBP'].strip().upper() == "S":
                    supply_method = 'produce'
                else: 
                    supply_method = 'buy'

                if uom in ['NR', 'N.']:
                    uom_id = um.get('N', False)  # Unit(s)
                elif uom in ["KG", "KN"]:
                    uom_id = um.get('KG', False) # UM inserita errata KN
                elif uom in ["TN", "T", "T."]:
                    uom_id = um.get('T', False)  # Tons
                else: 
                    uom_id = um.get('N', False)  # default
                
                # Prepare record
                data = {
                    'name': description, 
                    'name_template': description, 
                    'mexal_id': ref,      # Memorizzato ma non utilizzato
                    'default_code': ref, 
                    'imported': True,
                    'sale_ok':True,
                    'type': 'consu',      # TODO parametrize: product consu service <<<<<<<<<<
                    'standard_price': cost,
                    'list_price': 0.0,     
                    'description_sale': description, # preserve original name (not code + name)
                    'description': description,
                    'uos_id': uom_id,
                    'uom_id': uom_id,  
                    'uom_po_id': uom_id,

                    'statistic_category': "%s%s" % (
                        line['CKY_CAT_STAT_ART'] or '', 
                        "%02d" % int(
                            line['NKY_CAT_STAT_ART'] or '0') if line['CKY_CAT_STAT_ART'] else '',)
                      
                    #'procure_method': 'make_to_order', 'purchase_ok': True, 
                    #'categ_id': category_id, 'chemical_category_id': chemical_category_id,
                    #'need_analysis': True, 'partner_ref': sale_name,
                    #'mexal_c': ref,  # TODO utilizzato ref per la sincronizzazione! 
                }

                if supply_method == 'produce' and len(ref) in (5,6):
                    supply_method_dbp[ref] = supply_method
                    data['supply_method'] = supply_method

                # -------------------------------------------------------------
                #                           PRODUCT CREATION
                # -------------------------------------------------------------
                item = self.search(cr, uid, [
                    ('default_code', '=', ref)], context=context)
                if item: # update
                    try:
                        modify_id = self.write(cr, uid, item, data, context=context)
                        product_id=item[0]
                        _logger.info('Update Product ref: %s' % (ref, ))
                        counter['upd'] += 1  
                    except: # usually change of UOM, try to force:
                        # try to force UOM: 
                        force_update_uom[item[0]] = uom_id
                        counter['err_upd'] += 1  
                        error_list.append(ref)
                        _logger.error("Error modify product: %s [%s]" % (
                            ref, sys.exc_info(), ))
                else:           
                    try:
                        data['supply_method'] = supply_method # produce, buy (setup only during creation)
                        product_id=self.create(cr, uid, data, context=context)
                        _logger.info('Create Product ref: %s' % (ref,))
                        counter['new'] += 1  
                    except:
                        counter['err'] += 1  
                        error_list.append(ref)
                        _logger.error("Error create product %s [%s]" % (
                            ref, sys.exc_info(),))

                if len(ref) > 6: # Is a child product?
                    father=ref[:6].strip()
                    if father in father_dbp_ids:
                        father_dbp_ids[father].append(product_id) # create list for child
                    else:
                        father_dbp_ids[father] = [product_id] # create list for child
               
            except: # Master error for line!
                _logger.info('Error importing line: %s [%s]' % (
                    line, sys.exc_info()))
               
        # TODO force update of lines UOM:
        
        # ---------------------------------------------------------------------
        #                           Force UOM for product
        # ---------------------------------------------------------------------
        for item in force_update_uom:
            try:
                self.force_uom(cr, uid, item, force_update_uom[item], context=context)
            except:
                _logger.error(_("Error updating UOM for product!"))
                
        ##force_update_uom
        #_logger.warning("To update UOM: %s" % (force_update_uom, ))

        # ---------------------
        # Update supply method:
        # ---------------------
        # TODO Ottimizzare per non continuare ad aggiornare
        for element in father_dbp_ids:
            supply_method = supply_method_dbp.get(element, False)
            if supply_method:
                self.write(cr, uid, father_dbp_ids[element], {'supply_method': supply_method})
               
        # UPDATE ORDER LEVEL ON PRODUCTS:              
        _logger.info("Start sync level from AB_UBICAZIONI!")

        cursor = self.pool.get('micronaet.accounting').get_product_level(cr, uid, store=1, context=context)
        if not cursor:
            _logger.error("Unable to connect no order level informations!")

        error_list=[]        
        for line in cursor:
            try:
                item = self.search(cr, uid, [
                    ('default_code', '=', line['CKY_ART'])], context=context)
                if item: # update
                    try:
                        modify_id = self.write(cr, uid, item, {
                            'minimum_qty': line['NQT_SCORTA_MIN'] or 0.0, 
                            'maximum_qty': line['NQT_SCORTA_MAX'] or 0.0, 
                        }, context=context)
                        _logger.info('Update order level for product: %s' % (
                            line['CKY_ART'],))
                    except:
                        error_list.append(line['CKY_ART'])
                        _logger.error("Error modify order level product: %s [%s]" % (
                            line['CKY_ART'], sys.exc_info(),))
            except: # Master error for line!
               # KO log:
               _logger.info('Error importing line: %s [%s]' % (
                   line, sys.exc_info()))
               continue
                              
        _logger.info('End order level importation!')
        if error_list: _logger.info('Code import errors: [%s]'%(error_list))     # TODO Log in a dashboard    
        return True
        
    _columns = {
        'imported': fields.boolean('Imported', required=False),
        'mexal_id' : fields.char('Product mexal ID', size=20, required=False, readonly=False),                 
    }
    _defaults = {
        'imported': lambda *a: False,
    }                               

class res_partner_extra_fields(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    # Scheduled action: ########################################################
    def schedule_etl_partner_import(self, cr, uid, path, file_name, file_name_supplier, context=None):
        ''' ETL operations for import partner in OpenERP (parameter setted up in
            scheduled action for file name
        '''
        import logging, os, csv, sys
        
        def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()
            
        def get_country_id_from_code(code):
            ''' Get country ID from code
            '''
            if not code:
                return False
            country_pool = self.pool.get("res.country")
            country_ids = country_pool.search(cr, uid, [
                ('code', '=', code)], context=context)
            if country_ids:
                return country_ids[0]
            else:
                False              
            
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}
        comment = "" # for step of import, usefull for log error
        mexal_types={'c': file_name, 's': file_name_supplier }
        mexal_destination = False
        
        try:
            for mexal_type in mexal_types:
                try:
                    file_name = os.path.expanduser(os.path.join(path, mexal_types.get(mexal_type)))
                    lines = csv.reader(open(file_name,'rb'), delimiter = ";")
                except:
                    log_error(self, cr, uid, "schedule_etl_partner_import", 'Error reading file: %s %s'%(path, mexal_types.get(mexal_type)), context=context)
                    continue # jump importation file                    

                tot_colonne=0
                for line in lines:
                    if counter['tot'] < 0:  # jump n lines of header 
                       counter['tot'] += 1
                    else: 
                       if not tot_colonne:
                           tot_colonne=len(line)
                           _logger.info('Start sync of partners type: %s [cols=%s, file=%s]'%(mexal_type, tot_colonne, file_name))
                       try:                          
                           if len(line): # jump empty lines
                               if tot_colonne == len(line): # tot # of colums must be equal to # of column in first line
                                   counter['tot'] += 1 
                                   csv_id=0
                                   ref = Prepare(line[csv_id])
                                   csv_id+=1
                                   name = Prepare(line[csv_id]).title()
                                   csv_id+=1
                                   first_name = Prepare(line[csv_id]).title() or ''
                                   csv_id+=1
                                   street = Prepare(line[csv_id]).title() or ''
                                   csv_id+=1
                                   zipcode = Prepare(line[csv_id])
                                   csv_id+=1
                                   city = Prepare(line[csv_id]).title() or ''
                                   csv_id+=1
                                   prov = Prepare(line[csv_id]).upper() or ''
                                   csv_id+=1
                                   phone = Prepare(line[csv_id])
                                   csv_id+=1
                                   fax = Prepare(line[csv_id])
                                   csv_id+=1
                                   email = Prepare(line[csv_id]).lower() or ''
                                   csv_id+=1
                                   fiscal_code = Prepare(Prepare(line[csv_id])).upper() or ''  # Verify field
                                   csv_id+=1
                                   vat = Prepare(line[csv_id]).upper()        # IT* format   (checked ??)
                                   csv_id+=1
                                   type_CEI = Prepare(line[csv_id]).lower()   #  C | E | I 
                                   csv_id+=1
                                   #website = Prepare(line[12]).lower()       # not present!!!!
                                   code = Prepare(line[csv_id]).upper()       # Verify "IT" 
                                   csv_id+=1
                                   private = Prepare(line[csv_id]).upper()=="S"  # S | N (True if S)
                                   csv_id+=1
                                   parent=Prepare(line[csv_id]) # ID parent partner of this destination
                                   csv_id+=1
                                   ref_agente=Prepare(line[csv_id]) or '' # ID agente
                                   csv_id+=1
                                   name_agente=Prepare(line[csv_id]).title() or ''
                                   csv_id+=1
                                   csv_id+=1
                                   discount=Prepare(line[csv_id])       # Discount, string to parse
                                   csv_id+=1
                                   esention_code= 0 #Prepare(line[csv_id])    # Codice esenzione IVA (se presente allora è esente)
                                   csv_id+=1
                                   #country_international_code = code #Prepare(line[csv_id]).upper()    # Codice Nazione
                                   csv_id+=1
                                   # ID Categoria
                                   csv_id+=1
                                   category = Prepare(line[csv_id])              # categoria statistica cliente
                                   #category_id=get_statistic_category(sock, dbname, uid, pwd, category)                    

                                   country_id = get_country_id_from_code(code)
                                   
                                   if mexal_destination:  # TODO with ^ XOR
                                      if not parent: # Destination have parent field                       if verbose: print "[INFO]", "JUMPED (not a destination)",ref,name
                                         continue # jump if is destination and record is c or s
                                   else: # c or s 
                                      if parent: 
                                         continue # jump if is c or s but parent is present
                     
                                   if type_CEI in ('c','e','i','v','r',):
                                      if type_CEI in ('v','r',):
                                          type_CEI='e' # Vaticano and RSM are extra CEE
                                          
                                   if type_CEI == "i":
                                       lang = "it_IT" #getLanguage(sock,dbname,uid,pwd,"Italian / Italiano")   
                                       property_account_position = 1
                                   else:
                                       lang = "en_US" #getLanguage(sock,dbname,uid,pwd,"English")
                                       if type_CEI == "c":
                                           property_account_position = 3
                                       elif type_CEI == "e":
                                           property_account_position = 2
                                       else:
                                           property_account_position = False
                                       
                                   # Calculated fields:    
                                   if first_name: name+=" " + first_name
                                   if prov: city+=" ("+ prov + ")"
                                   type_address='default'  # TODO decide if invoice or defaulf (even for update...)

                                   if not mexal_destination: # create partner only with c or s
                                       data={'name': name,
                                             'active': True,
                                             'property_account_position': property_account_position,  # TODO parametrizzare
                                             'phone': phone,
                                             'email': email, 
                                             'street': street,
                                             #'street2': street,
                                             'zip': zipcode,
                                             'city': city,
                                             'country_id': country_id,
                                             'is_company': True,
                                             'employee': False,
                                             'parent_id': False,
                                             'website': '',
                                             'lang': lang,
                                             'vat': vat,
                                             #'vat_subject': not private,
                                             'type_cei': type_CEI,
                                             #'category_id': [(6,0,[category_id])], # m2m
                                             #'comment': comment, # TODO create list of "province" / "regioni"
                                             'mexal_' + mexal_type : ref,
                                             #'discount_value': discount_parsed['value'],
                                             #'discount_rates': discount_parsed['rates'],                             
                                             'imported': True,
                                             
                                             # Compatibility with SQL importat
                                             'sql_import': True,
                                            }
                                            
                                       if mexal_type=='c': # and not destination!
                                          data['ref']=ref
                                          data['customer']=True
                                          #data['property_account_position']= fiscal_position
                                          
                                          # extra part for compatibility with SQL import
                                          data['sql_customer_code'] = ref
                                          
                                       if mexal_type=='s':
                                          data['supplier']=True

                                          # extra part for compatibility with SQL import
                                          data['sql_supplier_code'] = ref

                                       #data_address['type']=type_address  # default
                                   else:  # destination
                                       pass
                                       #data_address['mexal_' + mexal_type]= ref      # ID in address
                                       #data_address['type']= type_address_destination # delivery
                                       #data_address['mexal']= ref      # Codice mexal nell'address

                                   #data['statistic_category_id']= category_id
                                      
                                   # PARTNER CREATION ***************
                                   if not mexal_destination:  # partner creation only for c or s
                                       error="Searching partner with ref"
                                       item = self.search(cr, uid, [('mexal_' + mexal_type, '=', ref)]) # search if there is an import
                                       if not item: 
                                          if vat:
                                             item = self.search(cr, uid, [('vat', '=', vat),('mexal_' + mexal_type, '=', False)]) # link if there's vat but not account code
                                             
                                          if not item and mexal_type=="s":
                                             data['customer']=False # If pass from here is: supplier and not customer

                                       if item: # update
                                          counter['upd'] += 1  
                                          try:
                                              partner_id=item[0] 
                                              item_mod = self.write(cr, uid, partner_id, data, context=context) 

                                              # OK log:
                                              _logger.info('Update Partner ref: %s'%(ref,))
                                          except:
                                              try: # Riprovo a scrivere rimuovendo la vat
                                                  data['vat']=False
                                                  item_mod = self.write(cr, uid, partner_id, data, context=context)
                                              except: 
                                                  _logger.error('Error update partner ref: %s [%s]'%(ref,sys.exc_info()))  
                                                  counter['err_upd']+=1  
                                       else: # new
                                          counter['new'] += 1  
                                          try:
                                              partner_id = self.create(cr, uid, data)
                                              # OK log:
                                              _logger.info('Create Partner ref: %s'%(ref,))
                                          except:
                                              try: # Riprovo a scrivere rimuovendo la vat
                                                  data['vat']=False
                                                  partner_id = self.create(cr, uid, data)
                                              except: 
                                                  _logger.error('Error create partner ref: %s [%s]'%(ref,sys.exc_info()))  
                                                  counter['err']+= 1  
                                   else: # destination
                                       partner_id = self.search(cr, uid, [('mexal_' + mexal_type, '=', parent),])
                                       if partner_id: 
                                          partner_id=partner_id[0] # only the first
                                   
                                   if not partner_id:  
                                      _logger.error('Error no partner ID ref: %s [%s]'%(ref,sys.exc_info()))  
                                      continue # next record                           
                               else: 
                                   counter['err']+=1

                       except:
                           # KO log:
                           _logger.error('Error importing line: %s [%s]'%(line,sys.exc_info()))
                           continue
                                    
                _logger.info('End sync of partner type: %s \nCounter:%s'%(mexal_type, counter))
                
        except:
            _logger.error('Error scheduler operation during: %s [%s]'%(comment,sys.exc_info()))                    

        log_info(self, cr, uid, "schedule_etl_partner_import", "End scheduled action [Import partner: customer and supplier]", context=context)
                        
        return    
    
    _columns = {
               'imported': fields.boolean('Imported', required=False),
               'mexal_c': fields.char('Code Customer', size=9, required=False),
               'mexal_s': fields.char('Code Supplier', size=9, required=False),
               'mexal_d': fields.char('Code Destination', size=9, required=False),
               'type_cei': fields.selection([
                   ('i', 'Italy'),
                   ('c', 'CEE'),
                   ('e', 'Extra CEE'),               
               ], 'CEI'),
    }
    _defaults = {
        'imported': lambda *a: False,
    }

class account_payment_term_extra_fields(osv.osv):
    ''' Extra fields for ETL in account.payment.term
    ''' 
    _name='account.payment.term'
    _inherit = 'account.payment.term'

    # Scheduled action: ########################################################
    def schedule_etl_payment_import(self, cr, uid, context=None):
        ''' ETL operations for import payment in OpenERP:
            1. Create account.payment.term with list
            2. Create payment default for res.partner
        '''
        import logging, os, csv, sys
        _logger = logging.getLogger('base_panchem')

        _logger.info('Start sync of payment [CP_PAGAMENTI]')
        payments = {}
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        cursor=self.pool.get('micronaet.accounting').get_payment(cr, uid, context=context)
        if not cursor:
            _logger.error("Unable to connect no importation of payments!")            
            
        # Import account.payment.term ##########################################
        try:
            for line in cursor:
                    counter['tot']+=1 
                    ref = line['NKY_PAG']                   # code
                    name = line['CDS_PAG'].strip().title()  # payment description
                    data={'name': name.replace(r"/",r"-"), 'active': True,}
                            
                    # PAYMENT CREATION ***************
                    item = self.search(cr, uid, [('name', '=', name)], context=context)
                    if not item: # update
                        counter['new'] += 1  
                        try:
                           payment_id = self.create(cr, uid, data, context=context) 
                        except:
                            _logger.info("[ERROR] Create payment [%s]"%(sys.exc_info(),))
                    else:
                        payment_id = item[0]        

                    payments[ref]=payment_id
            _logger.info('End importation payment, counter: %s'%(counter))
        except:
            _logger.error('Error import payment [%s]'%(sys.exc_info(),))
                              
        # TODO Convert in SQL:                              
        # Set default payment to res.partner ###################################
        _logger.info('Start sync of payment for partners [PC_CONDIZIONI_COMM]')
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}
        if not payments: _logger.error("No payment elements collected!")            

        cursor=self.pool.get('micronaet.accounting').get_payment_partner(cr, uid, context=context)
        if not cursor:
            _logger.error("Unable to connect no importation of payments for partners!")            
        try:
            for line in cursor:
                counter['tot']+=1
                ref = line["CKY_CNT"]                         # code
                payment = line["NKY_PAG"]     # payment description
                payment_id = payments.get(payment,False)
                if payment_id:
                   data = {'property_payment_term': payment_id,}

                   # PAYMENT CREATION ***************
                   # TODO also for supplier!!!!!
                   item = self.pool.get('res.partner').search(cr, uid, ['|',('mexal_s', '=', ref),('mexal_c', '=', ref)], context=context)
                   if item:    
                      try:
                          modify_id = self.pool.get('res.partner').write(cr, uid, item, data, context=context)
                          counter['upd']+=1
                      except:
                          _logger.info("[ERROR] Modify partner payment %s [Info: %s]"%(ref, sys.exc_info(),))
                   else:
                       counter['err']+=1
                       _logger.info("[ERROR] Partner not found %s [Info: %s]"%(ref, sys.exc_info(),))

                # verbose:
                if not (counter['tot'] % 100):
                    _logger.info('%s Record of partner payment read!'%(counter['tot']))
            _logger.info('End importation partner payment, counter: %s'%(counter))
        except:
            _logger.error('Error import partner payment [%s]'%(sys.exc_info(),))
        return                           
account_payment_term_extra_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
