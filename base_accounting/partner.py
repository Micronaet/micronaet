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
        title_id = sock.execute(
            dbname, uid, pwd, 'res.partner.title', 'search', [
                ('name', '=', title)])
        if not len(title_id):
           title_id = sock.execute(
               dbname, uid, pwd, 'res.partner.title', 'create', {
                   'name': title,
                   'domain': table,
                   'shortcut': ShortCut(title),
                   })


class product_product_extra_fields(osv.osv):
    """ Extra fields for ETL in product.product
    """
    _name='product.product'
    _inherit = 'product.product'

    # Utility function: #######################################################
    def get_uom(self, cr, uid, name, context=None):
        uom_id = self.pool.get('product.uom').search(cr, uid, [('name', '=', name),],context=context)
        if uom_id:
            return uom_id[0] # take the first
        else:
            return False

    # Scheduled action: #######################################################
    def schedule_etl_product_import(self, cr, uid, path, file_name, verbose=False, context=None):
        """ ETL operations for import product in OpenERP (parameter setted up in
            scheduled action for file name
        """
        import logging, os, csv, sys
        _logger = logging.getLogger('base_accounting')

        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        um={}
        um['KG'] = self.get_uom(cr, uid, 'kg', context=context)
        um['T'] = self.get_uom(cr, uid, 't', context=context)
        um['N'] = self.get_uom(cr, uid, 'Unit(s)', context=context)

        try:
            file_name = os.path.expanduser(os.path.join(path, file_name))
            lines = csv.reader(open(file_name,'rb'), delimiter = ";")

            tot_colonne=0
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header
                   counter['tot'] += 1
                else:
                   if not tot_colonne:
                       tot_colonne=len(line)
                       _logger.info('Start sync of product [cols=%s, file=%s]'%(tot_colonne, file_name))

                   if len(line): # jump empty lines
                       if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                           _logger.error('Colums not the same')
                           continue

                       counter['tot']+=1
                       csv_id=0
                       ref = Prepare(line[csv_id])                      # codice
                       csv_id+=1
                       name = Prepare(line[csv_id]).title()             # descrizione prodotto
                       name=name.replace(r"/",r"-")
                       csv_id+=1
                       #name_eng1 = Prepare(line[csv_id]).title()
                       #csv_id+=1
                       #name_eng2 = Prepare(line[csv_id]).title()
                       #csv_id+=1
                       uom = Prepare(line[csv_id]).upper()              # UOM
                       csv_id+=1
                       taxes_id = Prepare(line[csv_id])                 # IVA
                       csv_id+=1
                       # descrizione aggiuntiva
                       csv_id+=1
                       # numero 3 decimali??
                       csv_id+=1
                       cost_std = PrepareFloat(line[csv_id])
                       csv_id+=1
                       cost_ult = 0.0 #PrepareFloat(line[csv_id])
                       csv_id+=1
                       #has_bom = "S" == Prepare(line[csv_id]).upper()
                       csv_id+=1

                       csv_id+=1

                       csv_id+=1

                       csv_id+=1

                       csv_id+=1

                       csv_id+=1
                       contropartita = Prepare(line[csv_id]).upper()              # Contropartita

                       # Calculated field:
                       contropartita=contropartita.strip()
                       if contropartita not in ("",
                                                "RICAVI DA PRESTAZIONI DI SERVIZIO",
                                                "MERCI C/VENDITE",
                                                "TRASPORTI ADDEBITATI A CLIENTI",
                                                "AFFITTI ATTIVI",
                                                "TRASPORTI SU VENDITE",
                                                "NS. LAVORAZIONI PER TERZI",
                                                "RIMBORSO SPESE BOLLI",
                                                "COMPARTECIPAZIONE SPESE RECUPERI",
                                                "MERCI C/VENDITE             (C.AUTO)"):
                          contropartita=contropartita.replace("VENDITA","")
                          contropartita=contropartita.title()
                          contropartita=contropartita.strip()
                          #chemical_category_id=get_chemical_category(sock, dbname, uid, pwd, contropartita)
                       else:
                          #chemical_category_id=False
                          pass

                       sale_name = name
                       category_id= False

                       if uom in ['NR', 'N.', ]: # Unit(s)
                          uom_id = um.get('N',False)
                       elif uom in ["KG", "KN",]:  # UM inserita errata KN
                           #uom_id = um.get('KG',False)
                           uom_id = um.get('T',False) # uso T in OpenERP al posto di Kg.
                       elif uom in ["TN", "T", "T."]:
                           uom_id = um.get('T',False)
                       else:
                           uom_id = um.get('N',False) # default


                       data={'name': sale_name,
                             'name_template': sale_name,
                             #'partner_ref': sale_name,
                             'mexal_id': ref,    # Memorizzato ma non utilizzato
                             'default_code': ref,
                             #'mexal_c': ref,  # TODO utilizzato ref per la sincronizzazione!
                             'imported': True,
                             'sale_ok':True,
                             #'purchase_ok': True,
                             'default_code': ref,
                             'type': 'consu',          # TODO parametrize: product consu service <<<<<<<<<<
                             #'supply_method': 'produce', # TODO parametrize: produce buy
                             'standard_price': cost_ult or cost_std or 0, #cost_std or 0,
                             'list_price': 0.0,
                             #'procure_method': 'make_to_order',
                             'description_sale': sale_name, # preserve original name (not code + name)
                             'description': sale_name,
                             #'categ_id': category_id,
                             #'chemical_category_id': chemical_category_id,
                             #'need_analysis': True,
                             'uos_id': uom_id,
                             'uom_id': uom_id,
                             'uom_po_id': uom_id,
                             }

                       # PRODUCT CREATION ***************
                       item = self.search(cr, uid, [('default_code', '=', ref)], context=context)
                       if item: # update
                          try:
                              modify_id = self.write(cr, uid, item, data, context=context)
                              product_id=item[0]
                              if verbose: _logger.info("%s. Product updated [%s]"%(counter['tot'],ref))
                          except:
                              _logger.error("%s. Error modify product [%s]"%(counter['tot'],sys.exc_info()[0],))

                       else:
                           counter['new'] += 1
                           try:
                              product_id=self.create(cr, uid, data, context=context)
                              if verbose: _logger.info("%s. Product created [%s]"%(counter['tot'],ref))
                           except:
                               _logger.info("%s. Error create product [%s]"%(counter['tot'],sys.exc_info()[0],))
            _logger.info('End importation! Counter: %s'%(counter))
        except:
            _logger.error('Error import product [%s]'%(sys.exc_info()[0],))
        return

    _columns = {
               'imported': fields.boolean('Imported', required=False),
               'mexal_id' : fields.char('Product mexal ID', size=20, required=False, readonly=False),
    }
    _defaults = {
        'imported': lambda *a: False,
    }
product_product_extra_fields()


class res_partner_extra_fields(osv.osv):
    _name='res.partner'
    _inherit ='res.partner'

    # Scheduled action: ########################################################
    def schedule_etl_partner_import(self, cr, uid, path, file_name, file_name_supplier, verbose=False, context=None):
        """ ETL operations for import partner in OpenERP (parameter setted up in
            scheduled action for file name
        """
        import logging, os, csv, sys
        _logger = logging.getLogger('base_accounting')

        def Prepare(valore):
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()

        #partner_proxy=self.pool.get("res.partner")
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        mexal_types={'c': file_name, 's': file_name_supplier }
        mexal_destination = False

        try:
            for mexal_type in mexal_types:
                file_name = os.path.expanduser(os.path.join(path, mexal_types.get(mexal_type)))
                lines = csv.reader(open(file_name,'rb'), delimiter = ";")

                tot_colonne=0
                for line in lines:
                    if counter['tot'] < 0:  # jump n lines of header
                       counter['tot'] += 1
                    else:
                       if not tot_colonne:
                           tot_colonne=len(line)
                           _logger.info('Start sync of partners type: %s [cols=%s, file=%s]'%(mexal_type, tot_colonne, file_name))

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
                               country_international_code=code #Prepare(line[csv_id]).upper()    # Codice Nazione
                               csv_id+=1
                               # ID Categoria
                               csv_id+=1
                               category = Prepare(line[csv_id])              # categoria statistica cliente
                               #category_id=get_statistic_category(sock, dbname, uid, pwd, category)

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
                                         'is_company': True,
                                         'employee': False,
                                         'parent_id': False,
                                         'website': '',
                                         'lang': lang,
                                         'vat': vat,
                                         #'vat_subject': not private,
                                         #'type_cei': type_CEI,
                                         #'category_id': [(6,0,[category_id])], # m2m
                                         #'comment': comment, # TODO create list of "province" / "regioni"
                                         'mexal_' + mexal_type : ref,
                                         #'discount_value': discount_parsed['value'],
                                         #'discount_rates': discount_parsed['rates'],
                                         'imported': True,
                                        }

                                   if mexal_type=='c': # and not destination!
                                      data['ref']=ref
                                      data['customer']=True
                                      #data['property_account_position']= fiscal_position
                                   if mexal_type=='s':
                                      data['supplier']=True

                                   #data_address['type']=type_address  # default
                               else:  # destination
                                   pass
                                   #data_address['mexal_' + mexal_type]= ref      # ID in address
                                   #data_address['type']= type_address_destination # delivery
                                   #data_address['mexal']= ref      # Codice mexal nell'address

                               #data['statistic_category_id']= category_id

                               # PARTNER CREATION ***************
                               if not mexal_destination:  # partner creation only for c or s
                                   item = self.search(cr, uid, [('mexal_' + mexal_type, '=', ref)]) # search if there is an import
                                   if not item:
                                      if vat:
                                         item = self.search(cr, uid, [('vat', '=', vat)]) # search if there is a partner with same vat (c or f)

                                      if not item and mexal_type=="s":
                                         data['customer']=False # If pass from here is: supplier and not customer

                                   if item: # update
                                      counter['upd'] += 1
                                      try:
                                          item_mod = self.write(cr, uid, item, data, context=context)
                                          partner_id=item[0] # save ID (remove?)
                                          if verbose: _logger.info('%s. Partner updated [%s]'%(counter['tot'],ref))
                                      except:
                                          try: # Riprovo a scrivere rimuovendo la vat
                                              del data['vat']
                                              item_mod = self.write(cr, uid, item, data, context=context)
                                              partner_id=item[0] # save ID (remove?)
                                              if verbose: _logger.info('%s. Partner updated [%s]'%(counter['tot'],ref))
                                          except:
                                              _logger.error('%s. Error update partner ref: %s'%(counter['tot'],ref))
                                              counter['err_upd']+=1
                                   else: # new
                                      counter['new'] += 1
                                      try:
                                          partner_id = self.create(cr, uid, data)
                                          if verbose: _logger.info('%s. Partner created [%s]'%(counter['tot'],ref))
                                      except:
                                          try: # Riprovo a scrivere rimuovendo la vat
                                              del data['vat']
                                              partner_id = self.create(cr, uid, data)
                                              if verbose: _logger.warning('%s. Partner created (no vat) [%s]'%(counter['tot'],ref))
                                          except:
                                              _logger.error('%s. Error create partner ref: %s'%(counter['tot'],ref))
                                              counter['err']+= 1
                               else: # destination
                                   partner_id = self.search(cr, uid, [('mexal_' + mexal_type, '=', parent),])
                                   if partner_id:
                                      partner_id=partner_id[0] # only the first

                               if not partner_id:
                                  _logger.error('%s. Error no partner ID ref: %s'%(counter['tot'],ref))
                                  continue # next record
                           else:
                               counter['err']+=1
                _logger.info('End sync of partner type: %s \nCounter:%s'%(mexal_type, counter))
        except:
            _logger.error('Generic error in scheduler operation!')

        return

    _columns = {
               'imported': fields.boolean('Imported', required=False),
               'mexal_c': fields.char('Code Customer', size=9, required=False),
               'mexal_s': fields.char('Code Supplier', size=9, required=False),
               'mexal_d': fields.char('Code Destination', size=9, required=False),
    }
    _defaults = {
        'imported': lambda *a: False,
    }
res_partner_extra_fields()

class account_payment_term_extra_fields(osv.osv):
    """ Extra fields for ETL in account.payment.term
    """
    _name='account.payment.term'
    _inherit = 'account.payment.term'

    # Scheduled action: ########################################################
    def schedule_etl_payment_import(self, cr, uid, path, file_name, partner_file_name, verbose=False, context=None):
        """ ETL operations for import payment in OpenERP:
            1. Create account.payment.term with list
            2. Create payment default for res.partner

            Parameter:
            1. Path
            2. CSV file for payment list
            3. CSV file for client (extra importation after res.partner)
        """
        import logging, os, csv, sys
        _logger = logging.getLogger('base_accounting')

        payments = {}
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        # Import account.payment.term ##########################################
        try:
            file_name = os.path.expanduser(os.path.join(path, file_name))
            lines = csv.reader(open(file_name,'rb'), delimiter = ";")

            tot_colonne=0
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header
                   counter['tot'] += 1
                else:
                   if not tot_colonne:
                       tot_colonne=len(line)
                       _logger.info('Start sync of payment [cols=%s, file=%s]'%(tot_colonne, file_name))

                   if len(line): # jump empty lines
                       if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                           _logger.error('Colums not the same')
                           continue

                       counter['tot']+=1
                       csv_id=0
                       ref = Prepare(line[csv_id])                      # code
                       csv_id+=1
                       name = Prepare(line[csv_id])                     # payment description
                       name=name.replace(r"/",r"-")

                       data={'name': name,
                             'active': True,
                             }

                       # PAYMENT CREATION ***************
                       item = self.search(cr, uid, [('name', '=', name)], context=context)
                       if item: # update
                          try:
                              modify_id = self.write(cr, uid, item, data, context=context)
                              payment_id=item[0]
                              if verbose: _logger.info("%s. Payment updated [%s]"%(counter['tot'],sys.exc_info()[0],))
                          except:
                              _logger.error("%s. Error modify payment [%s]"%(counter['tot'],sys.exc_info()[0],))

                       else:
                           counter['new'] += 1
                           try:
                              payment_id=self.create(cr, uid, data, context=context)
                              if verbose: _logger.info("%s. Payment created [%s]"%(counter['tot'],sys.exc_info()[0],))
                           except:
                               _logger.error("%s. Error create payment [%s]"%(counter['tot'],sys.exc_info()[0],))
                       payments[name]=payment_id


            _logger.info('End importation payment, counter: %s'%(counter))
        except:
             _logger.error('Error import payment [%s]'%(sys.exc_info()[0],))

        # Set default payment to res.partner ###################################
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}

        try:
            file_name = os.path.expanduser(os.path.join(path, partner_file_name))
            lines = csv.reader(open(file_name,'rb'), delimiter = ";")

            tot_colonne=0
            for line in lines:
                if counter['tot'] < 0:  # jump n lines of header
                   counter['tot'] += 1
                else:
                   if not tot_colonne:
                       tot_colonne=len(line)
                       _logger.info('Start sync of payment to res.partner [cols=%s, file=%s]'%(tot_colonne, file_name))

                   if len(line): # jump empty lines
                       if tot_colonne != len(line): # tot # of colums must be equal to # of column in first line
                           _logger.error('Colums not the same')
                           continue

                       counter['tot']+=1
                       ref = Prepare(line[0])           # code
                       payment = Prepare(line[25])      # payment description
                       payment_id = payments.get(payment.replace(r"/",r"-"),False)

                       if payment_id:
                           data = {'property_payment_term': payment_id,}

                           # PAYMENT CREATION ***************
                           item = self.pool.get('res.partner').search(cr, uid, [('mexal_c', '=', ref)], context=context)
                           if item: # update
                              try:
                                  modify_id = self.pool.get('res.partner').write(cr, uid, item, data, context=context)
                                  partner_id=item[0]
                                  _logger.info("%s. Partner-payment updated [%s]"%(counter['tot'],sys.exc_info()[0],))
                              except:
                                  _logger.error("%s. Error modify partner payment [%s]"%(counter['tot'],sys.exc_info()[0],))
                           else:    # jump
                               counter['new'] += 1
                               _logger.error("%s. Error partner not found %s [%s]"%(counter['tot'],ref, sys.exc_info()[0],))

            _logger.info('End importation partner payment, counter: %s'%(counter))
        except:
            _logger.error('Error import partner payment [%s]'%(sys.exc_info()[0],))



        return
account_payment_term_extra_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
