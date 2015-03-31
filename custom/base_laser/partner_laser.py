# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://axelor.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields

class res_partner_sector(osv.osv):
    _name = 'res.partner.sector'
    _description = "Settore di attivita'"

    _columns = {
        'name': fields.char("Settore attivita'", size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False),        
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_sector()

class res_partner_dimension(osv.osv):
    _name = 'res.partner.dimension'
    _description = 'Dimensione azienda'
    
    _columns = {
        'name': fields.char('Dimensione azienda', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False),        
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_dimension()


class res_partner_add_fields(osv.osv):
    # Add fields on object: res.partner
    _name = 'res.partner'
    _inherit = 'res.partner'

    def verifica_codice_fiscale(self, cf):  # Metodo che verrà utilizzato anche da contatti!
        """Controlla l'ultimo carattere se corrisponde al calcolo di controllo"""

        LETTERE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        REGOLECONTROLLO = {
        'A':(0,1),   'B':(1,0),   'C':(2,5),   'D':(3,7),   'E':(4,9),
        'F':(5,13),  'G':(6,15),  'H':(7,17),  'I':(8,19),  'J':(9,21),
        'K':(10,2),  'L':(11,4),  'M':(12,18), 'N':(13,20), 'O':(14,11),
        'P':(15,3),  'Q':(16,6),  'R':(17,8),  'S':(18,12), 'T':(19,14),
        'U':(20,16), 'V':(21,10), 'W':(22,22), 'X':(23,25), 'Y':(24,24),
        'Z':(25,23),
        '0':(0,1),   '1':(1,0),   '2':(2,5),   '3':(3,7),   '4':(4,9),
        '5':(5,13),  '6':(6,15),  '7':(7,17),  '8':(8,19),  '9':(9,21)
        }
        # Verifica lunghezza stringa:
        if len(cf)!=16:
           return False

        # TODO: Verifica corrispondenza lettere / numeri nel codice:
        sommone = 0
        cf=cf.upper()
        for i, car in enumerate(cf[:15]): # first 15 char
            j = 1 - i % 2
            sommone += REGOLECONTROLLO[car][j]
        resto = sommone % 26               
        return cf[15:16]==LETTERE[resto]  # return test of last char
    
    def check_fiscalcode(self, cr, uid, ids, context=None): # Constrains for fiscal code
        if not context:
           context={}    

        for partner in self.browse(cr, uid, ids, context=context):            
            if not partner.fiscal_id_code:
                return True # if empty no check!
            return self.verifica_codice_fiscale(partner.fiscal_id_code)  # return test of control char

    def on_change_fiscal_code_partner(self, cr, uid, ids, fiscal_id_code, type_of_control, context=None):
        # TO DO unificare con una funzione il controllo sia per partner che per contatto   
        if context is None:
           context={}

        res={}      
        if type_of_control not in ('vat', 'fiscal_id_code'):
           res['warning']= {
                           'title': "Controllo numeri identificativi:",
                           'message': "Attenzione è stato richiesto un indentificativo diverso da 'vat' o 'cf'!"
                           } 
           return res 
        
        if fiscal_id_code: # Se esiste (TODO vedere controllo VAT)
           fc=fiscal_id_code.upper() # lo rendo maiuscolo
           if not self.verifica_codice_fiscale(fc): # Verifico la correttezza prima del doppione
              res['warning']= {
                              'title': "Fallito controllo codice fiscale",
                              'message': "Verifica carattere di controllo errata!"
                              }
              res['value']= {'fiscal_id_code': fc,} # ritorna comunque il valore in maiuscolo
              
           # Verifico potenziali doppioni:
           proxy_contact=self.pool.get('res.partner')
           search_ids=proxy_contact.search(cr, uid, [(type_of_control,'=',fc),('id', 'not in', ids)]) # there's only one!
           if search_ids: 
              res['warning']= {
                              'title': "Controllo codice fiscale/partita iva",
                              'message': "Attenzione è già presente il valore digitato, verificare l'elenco col bottone a destra!"
                              }
              res['value']= {'fiscal_id_code': fc,} # ritorno il valore in maiuscolo
        return res

    def action_create_lecturer(self, cr, uid, ids, context=None):
        if context is None:
           context={}

        if "type_of_partner_contact" not in context.keys():
           return False  

        function=context['type_of_partner_contact'] # .capitalize()
        if function not in ("docente", "studente"):    
           return False  

        partner=self.browse(cr, uid, ids, context=context)[0]
        address_default=None
        address_invoice=None        
        if partner:
           try:  # safe eval (error if empty office_id)
              if not partner.name: #(not partner.office_id) or
                 raise osv.except_osv(('Attenzione:'), ('Manca il nome partner da riportare al contatto!'))
                 return False  
           except:
              raise osv.except_osv(('Attenzione:'), ('Errore creando il contatto!'))
              return False
           for address in partner.address: # search in all address
               if address.type=='default':
                  address_default=address
               elif address.type=='invoice':
                  address_invoice=address
               for job in address.job_ids: # search in all job
                   if job.function==function:
                      raise osv.except_osv(('Attenzione:'), ('Esiste già un docente abbinato a questo partner!'))
                      return False
                   if job.contact_id.name==partner.name: # Test if there is the father
                      raise osv.except_osv(('Attenzione:'), ('Esiste già un nome contatto uguale al partner!'))
                      return False

           # Create a contact with partner data (if we arrive here there isn't a contact with same name or function docente)
           address_select=address_default or address_invoice or False
           if not address_select:  
              raise osv.except_osv(('Attenzione:'), ('Creare prima un indirizzo (default o fatturazione)!'))
              return False
           contacts=self.pool.get('res.partner.contact')
        
           try:
              contact_data={'name': partner.name,
                            'email': address_select.email,     
                           }  
              if partner.office_id:
                 contact_data['office_id']=partner.office_id.id
              contact_id=contacts.create(cr, uid, contact_data)
           except:
              raise osv.except_osv(('Attenzione:'), ('Errore creando il contatto!'))
              return False
           # Create job linked to new contact
           job_data={'contact_id': contact_id,
                     'function': function,
                     'address_id': address_select.id,
                     'phone': address_select.phone,
                     'fax': address_select.fax,
                     'email': address_select.email,     
                     }
           created_job_id=self.pool.get('res.partner.job').create(cr, uid, job_data)
           return True
           #return {'value': {}, 'warning': {"title": "Creazione contatto", "message": "Docente creato!",},}
        else:
           return {'value': {}, 'warning':  {"title": "Creazione contatto", "message":"Prego verificare di avere ufficio di appartenenza e il nome partner!",},}
    
    #def _get_office_uid(self, cr, uid, ids, field_name, arg, context=None):
    #    '''Compute office_id for search depending on logged user'''

    #    if context is None:
    #       context={}
    #    #import pdb; pdb.set_trace()
    #    utente_browse=self.pool.get('res.users').browse(cr, uid, uid, context=context)
    #    partner_browse=self.pool.get('res.partner').browse(cr, uid, ids, context=context)

    #    res={}
    #    for partner in partner_browse:
    #        if utente_browse.office_id.id == partner.office_id.id:
    #           res[partner.id]=True
    #        else:
    #           res[partner.id]=False
    #    return res

    _columns = {
        # Super partes:  
        'import' : fields.char('ID Importazione', size=16, required=False),
        'domain' : fields.char('Sigla Azienda', size=4, required=False), 
        'prev_id': fields.integer('Import linked ID'),
        # School:
        'fiscal_id_code' : fields.char('Codice Fiscale', size=16, required=False),
        'vatnumber': fields.char('Partita IVA', size=16, required=False),
        'cciaanumber': fields.char('Numero iscrizione CCIAA', size=16, required=False),
        # C.F.P.:
        'title_sector_id':fields.many2one('res.partner.sector', "Settore di attivita'", required=False),  
        'title_dimension_id':fields.many2one('res.partner.dimension','Dimensione azienda', required=False),
        'office_id':fields.many2one('base.laser.office', 'Uff. di apparten. principale', required=False),
        # Ufficio doti e apprendistato:
        'number_employee': fields.integer('Numero dipendenti'),
        'pmi_company': fields.boolean('Azienda PMI', required=False),
        #'office_uid_id': fields.function(_get_office_uid, method=True, type='boolean', string="Solo proprio ufficio", store=True),        
        }
    _constraints = [(check_fiscalcode, "Il codice fiscale non sembra corretto!", ['fiscal_id_code'])]

res_partner_add_fields()
