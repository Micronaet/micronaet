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

# Anagrafiche C.F.P.:
class res_partner_schoolsheet(osv.osv):
    _name = 'res.partner.schoolsheet'
    _description = 'Titoli di studio'
    
    _columns = {
        'name': fields.char('Titolo di studio', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False),        
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_schoolsheet()

class res_partner_profposition(osv.osv):
    _name = 'res.partner.profposition'
    _description = 'Posizione professionale'

    _columns = {
        'name': fields.char('Posizione professionale', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_profposition()

class res_partner_contract(osv.osv):
    _name = 'res.partner.contract'
    _description = 'Descrizione contratto'

    _columns = {
        'name': fields.char('Descrizione contratto', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_contract()

class res_partner_prioritycat(osv.osv):
    _name = 'res.partner.prioritycat'
    _description = 'Categoria prioritaria'

    _columns = {
        'name': fields.char('Categoria prioritaria', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_prioritycat()

class res_partner_profstatus(osv.osv):
    _name = 'res.partner.profstatus'
    _description = 'Condizione professionale'

    _columns = {
        'name': fields.char('Condizione professionale', size=128, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_profstatus()

class res_partner_currentprof(osv.osv):
    _name = 'res.partner.currentprof'
    _description = 'Attuale professione'

    _columns = {
        'name': fields.char('Attuale professione', size=150, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_partner_currentprof()

# Anagrafiche: Ufficio doti:
class res_contact_pip_state(osv.osv):
    _name = 'res.partner.contact.pip'
    _description = 'Stato PIP'

    _columns = {
        'name': fields.char('Stato PIP', size=80, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_contact_pip_state()

class res_contact_ccnl(osv.osv):
    _name = 'res.partner.contact.ccnl'
    _description = 'CCNL'

    _columns = {
        'name': fields.char('CCNL', size=80, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_contact_ccnl()

class res_contact_formation(osv.osv):
    _name = 'res.partner.contact.formation'
    _description = 'Tipo di formazione'

    _columns = {
        'name': fields.char('Tipo di formazione', size=80, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_contact_formation()

class res_contact_profile(osv.osv):
    _name = 'res.partner.contact.profile'
    _description = 'Profilo / Mansione'

    _columns = {
        'name': fields.char('Tipo di profilo', size=80, required=True, readonly=False),
        'note': fields.text('Note', required=False), 
    }
    _order='name'
    _sql_constraints = [('uniq_name','unique(name)','Il nome deve essere unico!'),]
res_contact_profile()

class res_partner_contact_add_fields(osv.osv):
    # Integration object: res.partner.contact
    _name = 'res.partner.contact'
    _inherit = 'res.partner.contact'

    def on_change_fiscal_code_contact(self, cr, uid, ids, fiscal_id_code, context=None):
        # TODO procedura on change per CF tutor
        if not context:
           context={}

        res={}      
        if fiscal_id_code:
           fc=fiscal_id_code.upper()
    
           # Verifico la correttezza prima del doppione (proc. partner):
           if not self.pool.get('res.partner').verifica_codice_fiscale(fc): 
              res['warning']= {
                              'title': "Fallito controllo codice fiscale",
                              'message': "Verifica carattere di controllo errata!"
                              }
              res['value']= {'fiscal_id_code': fc,} # ritorna comunque il valore in maiuscolo

           # Controllo i doppioni:
           proxy_contact=self.pool.get('res.partner.contact')
           search_ids=proxy_contact.search(cr, uid, [('fiscal_id_code','=',fc),('id', 'not in', ids)]) # there's only one!
           if search_ids:
              res['warning']= {
                              'title': "Controllo codice fiscale",
                              'message': "Attenzione è già presente il codice fiscale, verificare l'elenco col bottone a destra!"
                              }
              res['value']= {'fiscal_id_code': fc,}
        return res

    def check_fiscalcode_contact(self, cr, uid, ids, context=None): # Constrains for fiscal code contact
        if not context:
           context={}    
        for contact in self.browse(cr, uid, ids, context=context):            
            if not contact.fiscal_id_code:
                return True # if empty no check!
            return self.pool.get('res.partner').verifica_codice_fiscale(contact.fiscal_id_code)  # return test of control char

    # TODO Vedere se unificare le procedure di controllo
    def check_fiscalcode_tutor(self, cr, uid, ids, context=None): # Constrains for fiscal code tutor
        if not context:
           context={}    
        for contact in self.browse(cr, uid, ids, context=context):            
            if not contact.tutor_fiscal_id_code:
                return True # if empty no check!
            return self.pool.get('res.partner').verifica_codice_fiscale(contact.tutor_fiscal_id_code)  # return test of control char

    _columns = {
        # Super partes:
        'domain': fields.char('Sigla azienda', size=4, required=False),
        'import' : fields.char('ID Importazione', size=16,required=False), # for localize trance of import
        'prev_id': fields.integer('Import linked ID'),
        'telephone': fields.char('Phone', size=64, help="Numero di telefono del contatto"),
        'telefax': fields.char('Fax', size=64, help="Numero di fax del contatto"),
        # School:
        'fiscal_id_code' : fields.char('Codice Fiscale', size=16, required=False),
        # C.F.P.:   
        'disadvantage':fields.boolean('Allievo svantaggiato', required=False),
        'matricola':fields.char('Matricola', size=16,required=False), # for delete matricule ex-module
        'gender':fields.selection([
            ('male','Maschio'),
            ('female','Femmina'),            
        ],'Sesso', select=True, required=False),
        'title_school_id':fields.many2one('res.partner.schoolsheet', 'Titolo di studio', required=False),   
        'title_profpos_id':fields.many2one('res.partner.profposition', 'Posizione professionale', required=False),   
        'title_contract_id':fields.many2one('res.partner.contract', 'Descrizione contratto', required=False),   
        'title_prioritycat_id':fields.many2one('res.partner.prioritycat', 'Categorie prioritarie', required=False),   
        'title_profstatus_id':fields.many2one('res.partner.profstatus', 'Condizione professionale', required=False),
        'title_currentprof_id':fields.many2one('res.partner.currentprof', 'Attuale professione', required=False),
        'study_broken': fields.char('Studi interrotti', size=64, required=False, readonly=False),
        'study_broken_year': fields.char('Anno interruzione', size=4, required=False, readonly=False),     
        'privacy':fields.boolean('Consenso al trattamento', required=False),
        'hourly':fields.float('Retribuzione oraria', digits=(8,2), required=False),     
        'office_id':fields.many2one('base.laser.office', 'Uff. di apparten. principale', required=False, select=1),        
        # Ufficio doti:
        'formation_id':fields.many2one('res.partner.contact.formation', 'Tipo di formazione', required=False),
        'profile_id':fields.many2one('res.partner.contact.profile', 'Mansione / Profilo apprendista', required=False),
        'annuality': fields.integer('Annualità'),
        'title_pip_state_id':fields.many2one('res.partner.contact.pip', 'Stato PIP', required=False),
              #TODO : import time required to get currect date
        'date': fields.date('Data'),
        'pip_state':fields.char('N. PIP', size=16, required=False, readonly=False),
        'trainee_residence':fields.char('Residenza apprendista', size=64, required=False, readonly=False),
        'trainee_location':fields.char('Sede operativa apprendista', size=64, required=False, readonly=False),
        'title_ccnl_id':fields.many2one('res.partner.contact.ccnl', 'CCNL', required=False),
              #TODO : import time required to get currect date
        'recruitment_date': fields.date('Data assunzione'),
        'cost': fields.float('Costo', digits=(8, 2)),
        'tutor':fields.char('Tutor', size=64, required=False, readonly=False),
        'tutor_fiscal_id_code' : fields.char('Codice fiscale tutor aziendale', size=16, required=False),
        'course_tutor':fields.boolean('Corso tutor aziendale', required=False),
        'internal_ref':fields.char('Referente aziendale', size=64, required=False, readonly=False),
        }
    _constraints = [(check_fiscalcode_contact, "Il codice fiscale contatto non sembra corretto!", ['fiscal_id_code']),
                    (check_fiscalcode_tutor, "Il codice fiscale tutor non sembra corretto!", ['tutor_fiscal_id_code']),
                   ]

res_partner_contact_add_fields()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
