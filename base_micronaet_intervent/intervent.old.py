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
import sys

# Utility: #####################################################################
def PrepareDate(valore):
    import time
    valore=valore.strip()
    if valore and len(valore)==8: 
       return "%s-%s-%s"%(valore[:4],valore[4:6],valore[6:8])
    else:
       return time.strftime("%Y-%m-%d")

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

class hr_analyitic_timesheet_extra_fields(osv.osv):
    _name='hr.analytic.timesheet'
    _inherit ='hr.analytic.timesheet'

    # Scheduled action: ########################################################
    def schedule_etl_intervent_import(self, cr, uid, path, csv_file, context=None):
        ''' ETL operations for import intervent (temporary)
        '''
        import logging, os, csv
        _logger = logging.getLogger('base_micronaet_intervent')
                
        def Prepare(valore):  
            # For problems: input win output ubuntu; trim extra spaces
            #valore=valore.decode('ISO-8859-1')
            valore=valore.decode('cp1252')
            valore=valore.encode('utf-8')
            return valore.strip()

        def get_user_id(self, cr, uid, login, context=context):
            ''' Search login name return id
            '''
            if not login:
                return False
             
            item_ids=self.pool.get('res.users').search(cr,uid,[('login','=',login)])
            if item_ids:
                return item_ids[0]
            return False

        def get_cause_id(self, cr, uid, cause, context=context):
            ''' Search cuse name return id
            '''
            if not cause:
                return False
             
            item_ids=self.pool.get('hr_timesheet_invoice.factor').search(cr,uid,[('name','=',cause)], context=context)
            if item_ids:
                return item_ids[0]
            return False

        def get_partner_account_id(self, cr, uid, partner_id, context=context):
            if not partner_id:
                return (False,False)
                
            item_ids=self.pool.get('res.partner').search(cr,uid,[('mexal_c','=',partner_id)], context=context)
            if item_ids:
                partner_proxy=self.pool.get('res.partner').browse(cr, uid, item_ids[0], context=context)
                return (partner_proxy.id, partner_proxy.default_contract_id.id if partner_proxy.default_contract_id else False)
            return (False,False)

        def get_account_id(self, cr, uid, account_id, context=context):
            return 

        # Setup iniziale:
        user_ids={'631.00006': 'laura',
                  '631.00002': 'riolini',
                  '631.00001': 'mazzoletti',}
                         
        cause_ids ={ "1": "Pay", # vendita
                     #"2": "", # reso riparato
                     #"3": "", # c/visione
                     #"4": "", # c/lavorazione
                     #"5": "", # acquisto
                     #"6": "", # c/sostituzione
                     #"7": "", # acconto
                     #"8": "", # reso non riparato
                     #"9": "", # c/riparazione
                     #"10": "", # per accredito
                     "11": "Pay", # int. pagamento
                     "12": "Job work", # int. commessa
                     "13": "Warranty", # int. garanzia
                     "14": "Gratis", # int. gratuito
                     "15": "Job work", # int. contratto
                     #"16": "", # svendita
                     #"17": "", # reso fornitore
                     #"18": "", # eliminazione merce
                     #"19": "", # c/prestito
                     #"20": "", # reso non conforme
                     #"21": "", # reso c/visione
                     "25": "Gratis", # Intervento non a pagamento
                     "26": "Free analysis", # Analisi preventivo
                     #"27": "", # err. fatturazione
                   }                 
        #partner_proxy=self.pool.get("res.partner")
        counter = {'tot':0,'upd':0, 'err':0, 'err_upd':0, 'new':0}
        comment = "" # for step of import, usefull for log error        
        
        cause_pay=get_cause_id(self, cr, uid, "Pay", context=context) 
        cause_gratis=get_cause_id(self, cr, uid, "Gratis", context=context) 
        file_name = os.path.expanduser(os.path.join(path, csv_file))
        lines = csv.reader(open(file_name,'rb'), delimiter = ";")
        tot_colonne=0
        for line in lines: # TODO line with one element!
            if not tot_colonne:
                tot_colonne=len(line)
                _logger.info('Start sync of intervent [cols=%s, file=%s]'%(tot_colonne, file_name))
               
            counter['tot'] += 1 
            if not len(line): # jump empty lines                    
                _logger.info('Jumped empty line [%s]!'%(counter['tot']))
                continue
            
            if tot_colonne != len(line): # 1 colum or sama tot cols   len(line)==1 or
                if len(line)==1: 
                    intervention += "%s,%s"%(" " if not intervention else "", Prepare(line[0]) or "")
                _logger.info('Jumped line different cols [%s]!'%(counter['tot']))
                counter['err'] += 1
                continue
            
            # TODO write previous intervent here!
            
            intervention="" # reset intervent for new report
                
            csv_id=0
            ref = Prepare(line[csv_id]) or ""
            csv_id+=1
            date = PrepareDate(line[csv_id])
            csv_id+=1
            tech_ref = Prepare(line[csv_id])
            csv_id+=1
            customer_ref = Prepare(line[csv_id])
            csv_id+=1
            customer_description = Prepare(line[csv_id])
            csv_id+=1
            from_1 = Prepare(line[csv_id])
            csv_id+=1
            to_1 = Prepare(line[csv_id])
            csv_id+=1
            from_2 = Prepare(line[csv_id])
            csv_id+=1
            to_2 = Prepare(line[csv_id])
            csv_id+=1
            trip_hour = (PrepareFloat(line[csv_id]) or 0.0) / 60
            csv_id+=1
            total_invoice = PrepareFloat(line[csv_id]) or 0.0
            csv_id+=1
            cause = Prepare(line[csv_id]).strip() # anagrafic list
            csv_id+=1
            product_ref = Prepare(line[csv_id]) # IIT IIO IIP
            csv_id+=1
            hour_cost = PrepareFloat(line[csv_id]) or 0.0 # empty = free

            if not ref:
                _logger.error('Reference not present! Line: %s'%(counter['err'],))
                continue

            # Calculated fields:    
            ref = "BC2/%s"%(ref)
            
            if from_1 or from_2 or to_1 or to_2:
                total_intervent = 1 # TODO
            else:
                total_intervent = total_invoice
                
            break_require = from_1 and from_2 and to_1 and to_2
            break_hour = 0.0         # TODO
               
            user_id = get_user_id(self, cr, uid, user_ids.get(tech_ref,False), context=context) 
            if not user_id:
                _logger.error('User not found: %s ! [Line: %s]'%(tech_ref,line,))
                continue                    
            
            (partner_id, account_id) = get_partner_account_id(self, cr, uid, customer_ref, context=context)
            if not partner_id:
                _logger.error('Partner not found: %s) %s ! [Line: %s]'%(customer_ref, customer_description, line,))
                continue

            if not account_id:
                _logger.error('Account not found, partner: %s) %s ! [Line: %s]'%(customer_ref, customer_description, line,))
                account_id=1 # TODO !!!!!!!
                #continue # TODO replace with assistant
                           
            cause_id = get_cause_id(self, cr, uid, cause_ids.get(cause,False), context=context) 
            if not cause_id:
                _logger.error('Cause not found: %s ! [Line: %s]'%(cause,counter['tot'],))
                cause_id = cause_pay if hour_cost else cause_gratis
                           
            data = {
                    'name': "Intervento %s"%(ref,),
                    'account_id': account_id,
                    'partner_id': partner_id,
                    'user_id': user_id, 
                    
                    'mode': 'customer' if trip_hour else 'company', #TODO
                    'ref': ref,
                    
                    'date_start': "%s %s"%(date, from_1 or "08:00:00"),
                    'intervent_duration': 1.0,
                    'manual_total': total_invoice != total_intervent,
                    'intervent_total': total_intervent,
                    'manual_total_internal': False,
                    'unit_amount': total_intervent,

                    'google_from': 'company', # company, home, previous
                    'google_to': 'company',   # company, home, next
                    'trip_require': trip_hour > 0.0,
                    'trip_hour': trip_hour,
                    'break_require': break_require,
                    'break_hour': break_hour,
                    'intervention_request': "Richiesta generica", 
                    'intervention': "",
                    'internal_note': "",
                    'amount': 20.0 * total_intervent,  # TODO
                    'to_invoice': cause_id, # TODO
                    
                    'product_uom_id': 5, # TODO
                    'journal_id': 2,     # TODO
                    'product_id': 1,     # TODO
                    'general_account_id': 88, # TODO 
                    'state': 'close',
            }   
            # INTERVENT CREATION ***************
            item = self.search(cr, uid, [('ref', '=', ref)]) 
            if item: # update
                counter['upd'] += 1  
                item_mod = self.write(cr, uid, item, data, context=context) 
                intervent_id=item[0] 
                _logger.info('Update Intervent ref: %s'%(ref,))
            else: # new
               counter['new'] += 1  
               import pdb; pdb.set_trace()
               intervent_id = self.create(cr, uid, data)
               _logger.info('Create Intervent ref: %s'%(ref,))
                            
        _logger.info('End sync of intervent: %s - Counter:%s'%(mexal_type, counter))
            
        return    
hr_analyitic_timesheet_extra_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
