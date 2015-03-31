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

# New: training.subscription.line.vote
class training_subscription_line_vote(osv.osv):
    '''Create object to introduce a system of vote:
       For every subscription line
       in the linked Session
       for every course list (training.lecturer.base)
       the jobs / contacts are represented by them subscription line
       
       So every SL has a vote for a session for a course'''

    _name = 'training.subscription.line.vote'
    _description = 'Subscription Line Votes'

    # Creare la read e write per comporre il nome:
    #def create(self, cr, uid, values, context=None):
    #    if 'category_id' in values:
    #        proxy = self.pool.get('training.course_category')
    #        values['parent_id'] = proxy.browse(cr, uid, values['category_id'], context).analytic_account_id.id
    #    return super(training_course, self).create(cr, uid, values, context)

    #def write(self, cr, uid, ids, values, context=None):
    #    if 'category_id' in values:
    #        proxy = self.pool.get('training.course_category')
    #        values['parent_id'] = proxy.browse(cr, uid, values['category_id'], context).analytic_account_id.id
    #    return super(training_course, self).write(cr, uid, ids, values, context)

    
    _columns= {
              'name' : fields.char('Voto', size=64, required=True),
              'session_date': fields.related('session_id', 'date', readonly=True, type="datetime", string="Session Date"),
              'session_id' : fields.many2one('training.session', 'Session', required=True),
              'base_course_id' : fields.many2one('training.lecturer.base', 'Modulo', select=1, required=True, help='Moduli base'),
              'subscription_line_id' : fields.many2one('training.subscription.line', 'Linea iscrizione',
                                       #ondelete='cascade',
                                       #select=1, help='Linea iscrizione contatto'
                                       ),
              'job_id' : fields.related('subscription_line_id', 'job_id', type='many2one', relation='res.partner.job', string='Lavoro contatto'), 
              'contact_id' : fields.related('subscription_line_id', 'contact_id', type='many2one', relation='res.partner.contact', string='Contatto', select=1, readonly=True, store=True), 
              'vote': fields.char('Voto', size=40),
              'opinion': fields.text('Giudizio'),
              'note': fields.text('Annotazioni'),                             
              }

    _order= 'name'

training_subscription_line_vote()

# res.partner.job:
class training_job_add_fields(osv.osv):
    '''Add some job fields:
           1. Link a job with subscription.line list'''

    _name = 'res.partner.job'
    _inherit = 'res.partner.job' 
    
    _columns= {
              'subscription_line_ids' : fields.one2many('training.subscription.line', 'job_id', 'Iscrizioni', required=False),
              }             

training_job_add_fields()

# res.partner.contact
class training_contact_add_fields(osv.osv):
    '''Add some job fields:
           1. Link a job with subscription.line list'''

    _name = 'res.partner.contact'
    _inherit = 'res.partner.contact' 
    
    _columns= {
              'subscription_line_ids': fields.one2many('training.subscription.line', 'contact_id', 'Elenco iscrizioni', required=False),
              'vote_ids': fields.one2many('training.subscription.line.vote', 'contact_id', 'Elenco Giudizi', required=False), 
               }

training_contact_add_fields()

# res.partner
class training_contact_add_fields(osv.osv):
    '''Add some job fields:
           1. Link a job with subscription.line list'''

    _name = 'res.partner'
    _inherit = 'res.partner' 
    
    _columns= {
              'subscription_line_ids' : fields.one2many('training.subscription.line', 'partner_id', 'Elenco iscrizioni', required=False),
              }             

training_contact_add_fields()

# training.subscription.line (per la gestione PIP)
class training_subscription_line_add_fields(osv.osv):
    '''Add some fields to subscription line:
           1. PIP number
           2. Costo orario
           3. Annualità
           4. Stato PIP'''

    _name = 'training.subscription.line'
    _inherit = 'training.subscription.line' 
    
    def _get_pres_ads_hours(self, cr, uid, ids, field_name, arg, context=None):
        ''' Calcola l'elenco delle ore di presenza per questa subscription line 
            nell'oggetto training.participation
            viene consierata la spunta di presenza per sommare la 
           duration - numberhours (ovvero l'assenza)
           IN FUNZIONE DEL CAMPO RITORNA ORE PRESENZA O ORE ASSENZA'''

        if context is None:
           context={}
        
        res={}
        sl_browse=self.browse(cr, uid, ids, context=context)
        for sl in sl_browse:
            tot_hours=0.0
            if sl.participation_ids: 
               part_ids=[]
               for id_item in sl.participation_ids:
                   part_ids.append(id_item.id)  
               particip_browse=self.pool.get('training.participation').browse(cr, uid, part_ids, context=context)
               for present in particip_browse:
                   if field_name=='present_hours':
                      if (present.present) and (present.seance_state in ('opened','done','closed')): # TODO verifica gli stati da utilizzare
                         tot_hours += present.duration or 0.0
                         tot_hours -= present.numberhours or 0.0
                   else: # field name= absence_hours
                      if (not present.present) and (present.seance_state in ('opened','done','closed')): 
                         tot_hours += present.duration or 0.0                         
        
            res[sl.id]=tot_hours
        return res
          
    _columns= {
              'pip_number' : fields.char('Numero PIP', size=10, required=False, readonly=False),
              'hourly_cost' : fields.float('Costo orario', digits=(16, 2)),
              'annuality' : fields.char('Annualità', size=1, required=False, readonly=False),
              'pip_state_id' : fields.many2one('res.partner.contact.pip', 'Stato PIP', required=False),
              'present_hours': fields.function(_get_pres_ads_hours, method=True, type='float', string='Ore presenza', readonly=True),
              'absence_hours': fields.function(_get_pres_ads_hours, method=True, type='float', string='Ore assenza', readonly=True),
              }             

training_subscription_line_add_fields()

# training.participation
class training_participation_add_fields(osv.osv):
    '''Add some job fields:
           1. Stato della lezione (per il calcolo delle presenze) '''

    _name = 'training.participation'
    _inherit = 'training.participation' 
    
    _columns= {
              'seance_state' : fields.related('seance_id', 
                                              'state', 
                                              string='Stato lezione', 
                                              type='selection', 
                                              selection=[('opened', 'Opened'),
                                                         ('confirmed', 'Confirmed'),
                                                         ('inprogress', 'In Progress'),
                                                         ('closed', 'Closed'),
                                                         ('cancelled', 'Cancelled'),
                                                         ('done', 'Done')],
                                              readonly=True),
              }             
training_participation_add_fields()

# training.session
class training_session_add_fields(osv.osv):
    '''Add some job fields:
           1. Totale ore fatte
           2. Totale partecipanti*
           3. Ore totale partecipanti
           4. Ore di assenza partecipanti
           5. Valore ore * costo orario partecipante 

           1. Voti o2m della Session'''

    _name = 'training.session'
    _inherit = 'training.session' 
    
    def _get_summary_all(self, cr, uid, ids, fieldnames, args, context=None):
        '''Return a list of fields with statistic values'''

        if context is None:
           context={}

        res = {}
        for session_id in ids: #self.browse(cr, uid, ids, context=context): # per ogni sessione
            res[session_id] = {'tot_hours_presence' : 0.0, 'tot_hours_absence' : 0.0, 'tot_hours_x_cost_contact' : 0.0, }
            # get all training.participation with session_id=actual_id
            partec_browse=self.pool.get('training.participation').browse(cr, uid, self.pool.get('training.participation').search(cr, uid, [('session_id','=',session_id)]), context=context)
              
            for partecipation in partec_browse:
                if (partecipation.present) and (partecipation.seance_state in ('opened','done','closed')): # TODO verifica gli stati da utilizzare
                   res[session_id]['tot_hours_presence'] += partecipation.duration or 0.0
                   res[session_id]['tot_hours_x_cost_contact'] += (partecipation.subscription_line_id.hourly_cost or 0.0) * (partecipation.duration or 0.0) # Unico caso di somma costi
                   res[session_id]['tot_hours_presence'] -= partecipation.numberhours or 0.0
                elif (not partecipation.present) and (partecipation.seance_state in ('opened','done','closed')): # not present, seance closed
                   res[session_id]['tot_hours_absence'] += partecipation.duration or 0.0
                else:
                   # TODO decide what TODO
                   pass # for now do nothing!
        return res

    def action_load_contact_x_modules(self, cr, uid, ids, context=None):
        ''' Caricamento dell'elenco delle iscrizioni allo stato attuale (senza cancellazione)
            esploso su tutte le materie dei corsi base indicati in questa Edizione
        '''
        if context is None:
           context={}        
        
        try: 
           # Leggo SL e Moduli della Edizione
           #import pdb; pdb.set_trace()
           ids_sl=self.pool.get('training.subscription.line').search(cr, uid, [('session_id','=',ids[0])]) # assert: only 1 ids!
           ids_modules=self.pool.get('training.lecturer.base').search(cr, uid, [('session_id','=',ids[0])]) # assert: only 1 ids!
           vote_pool=self.pool.get('training.subscription.line.vote')
           ids_actual_votes=vote_pool.search(cr, uid, [('session_id','=',ids[0])]) # assert: only 1 ids!
           ids_actual_votes_read=vote_pool.read(cr, uid, ids_actual_votes, ['base_course_id','subscription_line_id',]) 
           presenti=[]

           for elemento in ids_actual_votes_read:
               presenti.append((elemento['subscription_line_id'][0], elemento['base_course_id'][0],))

           for student in ids_sl:
               for module in ids_modules:
                   if (student, module) not in presenti:
                      vote_pool.create(cr, uid, {'name': "mod: %d - stu: %d" % (module, student),
                                                'session_id': ids[0],
                                                'base_course_id': module,
                                                'subscription_line_id': student,
                                                })        
              
        except:
           raise osv.except_osv(('Attenzione:'),
                               ('Errore caricando contatti x corso!'))
           return False
        return True    

    _columns= {
               'vote_ids' : fields.one2many('training.subscription.line.vote', 'session_id', 'Votazioni', readonly=False),
               #'tot_hours_lesson' : fields.function(_get_summary_all,  # Eliminare (non serve come dato)
               #                     method=True,
               #                     string='Totale ore di lezione fatte',
               #                     type='float',
               #                     multi='summary',
               #                     help="Numero massimo di ore fatte,ricavato dal totale lezioni chiuse.",
               #                     readonly=True),              
               'tot_hours_presence' : fields.function(_get_summary_all,
                                    method=True,
                                    string='Totale ore di presenza partecipanti',
                                    type='float',
                                    multi='summary',
                                    help="Numero totale di ore fatte da tutti i partecipanti: somma(ore presenza part, per ogni lezione)",
                                    readonly=True),              
               'tot_hours_absence' : fields.function(_get_summary_all,
                                    method=True,
                                    string='Totale ore di assenza partecipanti',
                                    type='float',
                                    multi='summary',
                                    help="Numero totale di ore assenza di tutti i partecipanti: somma(ore assenza part, per ogni lezione)",
                                    readonly=True),              
               'tot_hours_x_cost_contact': fields.function(_get_summary_all,  
                                    method=True,
                                    string='Valorizzazione edizione',
                                    type='float',
                                    multi='summary',
                                    help="(Totale ore frequentate) x (tariffa oraria partecipante)",
                                    readonly=True),              
               
              }             
training_session_add_fields()
