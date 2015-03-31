# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
#    Copyright (C) 2011 Micronaet S.r.L. (<http://www.micronaet.it>). All Rights Reserved
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
############################################################################################

from osv import osv, fields
from datetime import datetime, timedelta

#WRITABLE_ONLY_IN_DRAFT = dict(readonly=True, states={'draft': [('readonly', False)]})

class training_lecturer_module(osv.osv):
      '''This object permit to link to the session a base model that that link to a session a particular week.
        The next week are repeated.'''
    
      _name = 'training.lecturer.base'
      _description = 'Docenti base moduli'

      def on_change_lecturer_base(cr, uid, ids, course_id, lecturer_id, context=None): 
          if not context:
             context={}

          try: 
              proxy_course=self.pool.get('training.course').browse(cr, uid, course_id, context=context)
              for lecturer in proxy_course[0].lecturer_ids: # only one course!
                  if lecturer.id==base_lecturer_id:
                     return {value: {},} # exit if there is lecturer for this course       
              proxy_course_lecturer=self.pool.get('training.course')

              actual_lecturer=proxy_course[0].lecturer_ids
              actual_lecturer_list=[]
              for ids in actual_lectuter:
                  actual_lectuter_list.append(ids.id)
              if lecturer_id not in actual_lecturer_list:
                 actual_lecturer_list.append(lecturer_id)

              new_list={'lecturer_ids': [6,0,actual_lecturer.append(lecturer_id)],}
              new_lecturer=proxy_course_lecturer.write(cr, uid, [course_id,], new_list) 
          except:
              pass # do nothing, return normally
          return {value: {'course_id': course_id},}          

      # Funzioni di calcolo campi:
      def _get_statistics(self, cr, uid, ids, field_name, arg, context=None):         
         ''' Calcolo delle statistiche: '''         

         base_proxy= self.browse(cr, uid, ids, context=context)
         
         #import pdb; pdb.set_trace()
         res = {}
         res_vuoto={'daily_hours' : 0.0, 'week_hours': 0.0,}   
         for item in base_proxy: #self.browse(cr, uid, ids, context=context):
             try: 
                 tot_course_h=item.duration
                 if item.session_id.date and item.session_id.date_end:
                     diff=datetime.strptime(item.session_id.date_end[:10], '%Y-%m-%d') - datetime.strptime(item.session_id.date[:10], '%Y-%m-%d') 
                     tot_gg=diff.days
                     tot_gg_eff= int(tot_gg * 6 / 7)
                     if tot_gg_eff >= 6: # se è minore di 6 non ha senso proiettarlo sulla settimana
                        wh=tot_course_h * 6 / tot_gg_eff 
                     else: # metto tutta la durata!
                        wh=tot_course_h
 
                     res[item.id]={
                              'daily_hours' : tot_course_h / tot_gg_eff,
                              'week_hours': wh,  
                              }            
                 else: # set to 0 all statistics
                     res[item.id]=res_vuoto        
             except: # in caso of error return 0.0 values
                 res[item.id]=res_vuoto                               
         return res
     
      #def _get_planned_hours(self, cr, uid, ids, field_name, arg, context=None):         
      #   ''' Calcolo totali ore pianificate '''
      #   
      #   if context is None:
      #      context={}
      #   
      #   planned_ids = self.pool.get('training.seance.plan').search(cr, uid, [('course_base_id', 'in' ,ids)], context=context)   
      #   planned_proxy = self.pool.get('training.seance.plan').browse(cr, uid, planned_ids, context=context)
      #   print "ids", len(ids)
      #   print "planned_ids", len(planned_ids)
      #   res = dict.fromkeys(ids, 0.0)
      #   import pdb; pdb.set_trace()
      #   for lezioni in planned_proxy: 
      #       print lezioni.session_id.id,"-",
      #       res[lezioni.course_base_id.id]+=lezioni.duration
             
      _columns= {
               #'name' : fields.function(_name_compute,
               #                  method=True,
               #                  type="char",
               #                  size=64,
               #                  select=1,
               #                  store=True,
               #                  string='Name',
               #                  help="Modulo dell'edizione"),
               #'name': fields.char('Descrizione settimana tipo', size=32, required=False),
               'name': fields.related('course_id','name', type='char', relation='training.course', string='Modulo edizione'),
               'session_id' : fields.many2one('training.session','Edizione'),
               'course_id': fields.many2one('training.course', 'Modulo', required=True), 
               'base_lecturer_id': fields.many2one('res.partner.job', 'Docente', help="Docente di base che tiene il modulo",),
               'base_lecturer_2_id': fields.many2one('res.partner.job', 'Docente secondario', help="Docente secondario di base che tiene il modulo (compartecipa alle lezioni)",),
               'note': fields.text('Note'),
               #'duration' : fields.float('Duration', help="Ore totali"),
               'duration': fields.related('course_id','duration', type='float', string='Durata'),
               
               # Calculated fields to help planning:             
               #'planned_hours' : fields.function(_get_planned_hours,
               #                       method=True,
               #                       string='Ore pianificate',
               #                       type='float',
               #                       help="Totale ore inserite nel piano settimanale, utilizzato anche in modalità completa.",
               #                       store=False,
               #                       readonly=True),
               'week_hours' : fields.function(_get_statistics,
                                      method=True,
                                      string='Ore medie sett.',
                                      type='float',
                                      multi='statistics',  
                                      help="Valore medio di ore settimanali calcolato = totale giorni effettivi / 6",
                                      readonly=True),
               'daily_hours' : fields.function(_get_statistics,
                                      method=True,
                                      string='Ore medie giorn.',
                                      type='float',
                                      multi='statistics', 
                                      help="Valore medio di ore giornaliere calcolato = totale / giorni effettivi",
                                      readonly=True),
              }             
training_lecturer_module()

class training_seance_plan(osv.osv):
    '''
    Class for create a calendar linked to one Training Session 
          (every training session might have only one calendar)
          for each session in this week calendar are represented all
          training course scheda for replicate a seance creation for all
          session from/to period. 
    '''

    _name = 'training.seance.plan'
    _description = 'Piano base lezioni'

    def _duration_approx(self, duration):
        '''Approssimazione dell'errore del web nel calcolo durata'''
        import fpformat    
        return fpformat.fix(duration + 0.04, 1) or 0.0 # TODO vedere se si puo' fare meglio l'approssimazione...
        
    def lecturer_busy_for_period(self, cr, uid, ids, vals, context = None):
        '''Procedura che riceve i due insegnanti interessati, la data e la
           durata delle attual lezione
           Il controllo viene fatto per verificare che non ci siano sovapposizioni
           con altre lezioni presenti lo stesso giorno e la stessa durata
           Il valore di ritorno è vuoto nel caso non ci siano errori, in caso contrario
           c'e' il testo contenente l'errore
        '''
        if context is None:
           context={}
        
        #import pdb; pdb.set_trace()   
        pg_sql=''' SELECT id
                   FROM training_seance_plan 
                   WHERE (base_lecturer_id = %s OR base_lecturer_2_id = %s)
                         AND   
                         (('%s'::TIMESTAMP , '%d Minutes'::INTERVAL) 
                         OVERLAPS 
                         (date , '1 Minutes'::INTERVAL * duration * 60))'''
                         
        if ids: # sono in write
           #import pdb; pdb.set_trace()
           read_ids=self.read(cr, uid, ids, ['id', 'date', 'duration', 'base_lecturer_id', 'base_lecturer_2_id',], context=context) # TODO CHECK solo uno
           # Controllo i dati necessari per controllarlo come per "create"
           if 'duration' not in vals: # else dovrebbe essere già approssimata nella creazione
              vals['duration'] = read_ids['duration'] or 0.0
           if ('base_lecturer_id' not in vals) or (not vals['base_lecturer_id']):
              vals['base_lecturer_id'] = read_ids['base_lecturer_id'] and read_ids['base_lecturer_id'][0] or 0 
           if ('base_lecturer_2_id' not in vals) or (not vals['base_lecturer_2_id']):
              vals['base_lecturer_2_id'] = read_ids['base_lecturer_2_id'] and read_ids['base_lecturer_2_id'][0] or 0 
           if 'date' not in vals: # Necessaria (non viene passata se cambio ad es. solo la durata)
              vals['date'] = read_ids['date']
           pg_sql = pg_sql + " AND (id!=%d)" % (ids,)
        else: # Create
           vals['duration'] = self._duration_approx(vals.get('duration', 0.0))
        # Tolgo il false eventuale perchè la SQL darebbe errore (comune a tutti e 2 create e write)
        if not vals.get('base_lecturer_id', 0):
           vals['base_lecturer_id'] = 0
        if not vals.get('base_lecturer_2_id', 0):
           vals['base_lecturer_2_id'] = 0           

        cr.execute(pg_sql % (vals.get('base_lecturer_id', 0),  vals.get('base_lecturer_id', 0), vals.get('date',''), 60 * float(vals.get('duration',0.0)))) # TODO: serve il float?
        
        busy_ids=[]
        for seance_busy in cr.fetchall():
            busy_ids.append(seance_busy[0])
        
        if vals.get('base_lecturer_2_id',''): # se esiste il secondo insegnante:
           cr.execute(pg_sql % (vals.get('base_lecturer_2_id', 0),  vals.get('base_lecturer_2_id',''), vals.get('date',''), 60 * float(vals.get('duration',0.0))))
           for seance_busy in cr.fetchall():
               if seance_busy[0] not in busy_ids:
                  busy_ids.append(seance_busy[0])        

        res=""
        for item in self.browse(cr, uid, busy_ids, context=context):
            res+="\n|%s (%s)| {%s, %s} [data: %s, dur.: %s];" % (item.course_id.name,
                                                                 item.session_id.name,
                                                                 item.base_lecturer_id.contact_lastname,
                                                                 item.base_lecturer_2_id.contact_lastname or "/",
                                                                 item.date,
                                                                 item.duration,)
        return res 
        
    def create(self, cr, uid, vals, context=None):
        '''Controllo le interferenze per l'insegnante primario e per il secondario
        '''
        if context is None:
           context={}

        busy_list=self.lecturer_busy_for_period(cr, uid, 0, vals, context=context) 
        if busy_list:
           raise osv.except_osv('Attenzione', 'Interferenza con appuntamenti: \n%s' % (busy_list,))
        else:   
           return super(training_seance_plan, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        '''Controllo le interferenze per l'insegnante primario e per il 
           secondario.
           l'ids dovrebbero essere uno (TODO controllare!)
        '''
        if context is None:
           context={}

        busy_list=self.lecturer_busy_for_period(cr, uid, ids[0], vals, context=context) 
        if busy_list:
           raise osv.except_osv('Attenzione', 'Interferenza con appuntamenti: \n%s' % (busy_list,))
        else:   
           return super(training_seance_plan, self).write(cr, uid, ids, vals, context=context)

    def on_change_course_base_id(self, cr, uid, ids, course_base_id, session_id):
        ''' Al cambio del modulo cambia il docente che è stato impostato per tenerlo
            per la data sessione
            TODO gestione migliore della durata!!!!
        '''

        if course_base_id and session_id:  
           proxy_cb=self.pool.get('training.lecturer.base').browse(cr, uid, course_base_id)
           course_id=proxy_cb.course_id.id
           lecturer_id=proxy_cb.base_lecturer_id.id
           lecturer_2_id=proxy_cb.base_lecturer_2_id.id
           return {'value': {'course_id': course_id, 'base_lecturer_id': lecturer_id, 'base_lecturer_2_id': lecturer_2_id, 'session_id': session_id,}} 
        return {'value': {'course_id': False, 'base_lecturer_id': False, 'base_lecturer_2_id': False, 'session_id': session_id,}}  

    # NON USATA:
    def on_change_course_id(self, cr, uid, ids, course_id, session_id):
        ''' Al cambio del modulo cambia il docente che è stato impostato per tenerlo
            per la data sessione
            TODO gestione migliore della durata!!!!
        '''
        if course_id and session_id:  
           cr.execute('select base_lecturer_id from training_lecturer_base where course_id = %d and session_id=%d' % (course_id, session_id,))
           res=cr.fetchall()
           try: 
             if res[0][0]:
                return {'value': {'base_lecturer_id': res[0][0],'session_id': session_id,}} 
           except: 
                return {'value': {'base_lecturer_id': False, 'session_id': session_id,}}  
        return {'value': {'base_lecturer_id': False, 'session_id': session_id,}}  
        
    _columns = {
        'session_id' : fields.many2one('training.session','Edizione', select="1"), # Obj: Session (Course)
        'course_id' : fields.many2one('training.course','Modulo', select="1"),   # Obj: Course  (Subject)
        'date' : fields.datetime('Data inizio', required=True, help="Data, ora inizio lezione"),
        'date_end' : fields.datetime('Data fine', help="Data ora fine lezione"),
        'duration' : fields.float('Duration', help="The duration of the seance"), # required=True, digits=(4,1),
        'base_lecturer_id': fields.many2one('res.partner.job', 'Docente abbinato', select="1", help="Docente base che tiene il modulo",),
        'base_lecturer_2_id': fields.many2one('res.partner.job', 'Docente secondario abbinato', select="1", help="Docente base secondario che compartecipa al modulo",),
        'course_base_id': fields.many2one('training.lecturer.base', 'Modulo base', select="1"),
        }

    _order = "date asc"
training_seance_plan()

class training_session_add_base_fields(osv.osv):
      ''' Add link to training.lecturer.base'''
      _name = 'training.session'
      _inherit= 'training.session'

          
      def action_create_group(self, cr, uid, ids, context=None):
          ''' 
             Creazione del gruppo per le lezioni create in manuale (normalmente lo fa comunque quella
             procedura durante l'automazione)
          '''
          #import pdb; pdb.set_trace()
          session=self.browse(cr, uid, ids[0], context=context)      
          if session:           
              group_proxy = self.pool.get('training.group') 
              group_ids = group_proxy.search(cr, uid, [('session_id', '=', session.id)]) 
              if not group_ids:
                  group_id = group_proxy.create(cr, uid, {'name' : 'Classe: %s' % (session.name,), 'session_id': session.id }, context=context)
 
          return True

      def action_load_modules(self, cr, uid, ids, context=None):
          ''' Azione bottone per impostare l'insegnante unico per tutti i moduli dell'elenco presente
              (verrà forzato il ricaricamento dell'elenco moduli)
              TODO: Inserire gli insegnanti cosi' creati nel corso dell'offerta (per fare vedere chi ha insegnato 
                    la materia (non bloccante)'''
          if not context:
             context={}        
          
          try: 
             lecturer_course_pool=self.pool.get('training.lecturer.base') 
             session_browse=self.browse(cr, uid, ids, context=context)[0]
             session_courses_browse=session_browse.lecturer_base_ids
             session_courses=[]
             for course in session_courses_browse:
                 session_courses.append(course.course_id.id) #  lista corsi dell'edizione
      
             offer_courses_browse=session_browse.offer_id.course_ids # Leggo la lista corsi presente nell'offerta
             offer_courses=[]             
             name_course={}
             
             for course in offer_courses_browse:
                 if course.course_id.id not in session_courses:
                    new_course_data = {'session_id': session_browse.id, 'course_id': course.course_id.id,}
                    if len(course.course_id.lecturer_ids)==1: # un solo insegnante nel modulo
                       new_course_data['base_lecturer_id']= course.course_id.lecturer_ids[0].id
                    new_course=lecturer_course_pool.create(cr, uid, new_course_data)                      
             if ('unique_lecturer_id' in context.keys()) and context.get('unique_lecturer_id',False): # update unique lecturer field if it's present in context
                cr.execute('update training_lecturer_base set base_lecturer_id=%s where session_id=%s', (context.get('unique_lecturer_id', False), session_browse.id)) # Prima era 0
          except:
             raise osv.except_osv('Attenzione:', 'Errore caricando i corsi!')
             return False
          return True    

      # Carico l'elenco completo per sicurezza
      _columns={
                'lecturer_base_ids': fields.one2many('training.lecturer.base', 'session_id', 'Docenti base', required=False),
                'seance_plan_ids': fields.one2many('training.seance.plan', 'session_id', 'Piano lezioni base', required=False),
                'unique_lecturer_id': fields.many2one('res.partner.job', 'Docente unico', help="Docente base che tiene tutti i moduli",),
                # sezione relativa all'importazione FET
                'imported_plan': fields.boolean('Lezioni importate', required=False, help="Il piano lezioni viene importato, il calendario settimanale perciò conterrà tale importazione!"),
                'fet_class':fields.char('Classe FET', size=10, required=False, readonly=False),
                }
training_session_add_base_fields()      

class training_catalog_add_fields(osv.osv):
      '''
      Extra fields for FET importation
      '''
      _name = 'training.catalog'
      _inherit = 'training.catalog'

      
      def action_catalog_import_seance_plan(self, cr, uid, ids, context=None):
          '''
          Procedura che effettua l'importazione dei file FET copiati nella cartella di riferimento
          cercando in tutte le edizioni le classi che sono abbinate con l'apposito campo
          Viene verificato preventivamente la presenza degli insegnanti e delle materie
          Verificato l'abbinamento corretto senza omonimie o ricerche multiple
          Nota: normalmente per importare tutte le lezioni dell'anno scolastico
          servirà fare importazioni plurime che comporteranno un aggiornamento della
          data attuale di import nelle lezioni                    
          '''
          import csv
          from datetime import datetime, timedelta
          
          if context is None:
             context={}
             
          def utf8_convert(valore):  
              # File come from Win P so in cp1252 format, not UTF-8, so convert!
              valore=valore.decode('cp1252')
              valore=valore.encode('utf-8')
              return valore #.strip() # returned without extra spaces # TODO dava errore perche' c'era uno spazio, toglierlo pero' da tutti e due
              
          def get_addons_path():
              '''Import addons module, read the path!'''
              import addons, os
              return os.path.dirname(addons.__file__) + "/training_seance_plan/csv/" 

          def return_view(self, cr, uid, name, res_id):
              '''Function that return dict action for next step of the wizard'''
              return {
                      'view_type': 'form',
                      'view_mode': 'form,tree',
                      'res_model': name, # object linked to the view
                      #'views': [(view_id, 'form')],
                      'view_id': False,
                      'type': 'ir.actions.act_window',
                      #'target': 'new',
                      'res_id': 0 #res_id,  # ID selected
                      }

          # Proxy utilizzati:
          catalog_browse=self.browse(cr, uid, ids, context=context)[0] # one only
          session_pool=self.pool.get('training.session') # edizioni
          seance_plan_pool=self.pool.get('training.seance.plan') # calendario settimanale
          # Controlli pre importazione:
          # - Controllo l'esistenza del prefisso obbligatorio al nome file csv
          if not catalog_browse.fet_prefix: 
             raise osv.except_osv('Attenzione:',"Prefisso dei file CSV esportati da FET mancante" )
             
          # File students.csv ##################################################   
          # - Carico l'elenco delle classi e verifico che siano tutte presenti nel catalogo:
          lista_classi = []
          lista_classi_test = []
          classi_2_session_id = {} # corrispondenza classe - ID sessione
          file_csv = get_addons_path() + catalog_browse.fet_prefix + "_students.csv"
          try:
             input_csv = open(file_csv,'rb')
          except:
             raise osv.except_osv("Attenzione:","Errore nell'apertura del file " + input_csv)   
          lines = csv.reader(input_csv, delimiter=',')
          counter=-1 # salto la riga intestazione iniziale (1 sola)
          for line in lines:
              counter+=1 
              if counter:
                 csv_id=0 # Anno >> classe??
                 classe = utf8_convert(line[csv_id]) #.lower() 
                 csv_id+=1 # numero studenti
                 csv_id+=1 # classe
                 if classe:
                    if classe not in lista_classi:
                       lista_classi.append(classe)
                       lista_classi_test.append(classe)
                    else: # la classe è già presente
                       raise osv.except_osv("Attenzione:","Trovata tra le edizioni la classe doppia:" + classe)
          input_csv.close()

          for edizione in catalog_browse.session_ids: # è uno solo!
              if (edizione.imported_plan) and (edizione.fet_class in lista_classi_test):
                 lista_classi_test.remove(edizione.fet_class)
                 if edizione.fet_class not in classi_2_session_id:
                    if not (edizione.date and edizione.date_end):
                       raise osv.except_osv("Attenzione:","Controllare che esiste la data inizio e la data fine:\n" + edizione.name)    
                    classi_2_session_id[edizione.fet_class]=edizione.id
                    
          if lista_classi_test: # non devono esserci classi residue
             raise osv.except_osv("Attenzione:","Nelle edizioni mancano queste classi FET:\n" + "\n".join(lista_classi,))
          # TODO segnalare le mancanze di classi nelle edizioni rispetto a FET          

          if not classi_2_session_id.values(): # sono 0 tutti gli id delle sessioni
             raise osv.except_osv("Attenzione:","Nessuna edizione da importare!")
          
          # File subjects.csv ##################################################   
          # - Importazione materie:
          lista_materie=[]
          
          file_csv = get_addons_path() + catalog_browse.fet_prefix + "_subjects.csv"
          try:
             input_csv = open(file_csv,'rb')
          except:
             raise osv.except_osv("Attenzione:","Errore nell'apertura del file " + input_csv)   
          lines = csv.reader(input_csv, delimiter=',')
          counter=-1 # salto la riga intestazione iniziale (1 sola)
          for line in lines:
              counter+=1 
              if counter:
                 materia = utf8_convert(line[0]).lower()
                 if (materia) and (materia not in lista_materie): # non dovrebbe essere doppia
                    lista_materie.append(materia)
          input_csv.close()
          
          # File teachers.csv ##################################################   
          # - Importazione insegnanti
          lista_insegnanti=[]
          
          file_csv = get_addons_path() + catalog_browse.fet_prefix + "_teachers.csv"
          #import pdb; pdb.set_trace()
          try:
             input_csv = open(file_csv,'rb')
          except:
             raise osv.except_osv("Attenzione:","Errore nell'apertura del file " + input_csv)   
          lines = csv.reader(input_csv, delimiter=',')
          counter=-1 # salto la riga intestazione iniziale (1 sola)
          for line in lines:
              counter+=1 
              if counter:
                 insegnante = utf8_convert(line[0]).lower() 
                 if (insegnante) and (insegnante not in lista_insegnanti): # non dovrebbe essere doppia 
                    lista_insegnanti.append(insegnante)
          input_csv.close()
          
          # - Controllo nelle edizioni gli insegnanti base impostati con le materie:
          #   TODO controllare che non siano state già create le lezioni!!
          lista_materie_ko=[]; lista_insegnanti_ko=[]
          get_ids_edizione_da_classe={}
          for edizione in session_pool.browse(cr, uid, classi_2_session_id.values(), context):
              # [ID, Data Inizio, Data Fine, Dict materie, Dict insegnanti]
              get_ids_edizione_da_classe[edizione.fet_class]=[edizione.id,       # 0. id   # non serve
                                                              edizione.date,     # 1. data inizio
                                                              edizione.date_end, # 2. data fine
                                                              {},                # 3. materie
                                                              {}]                # 4. insegnanti (anche il secondario)
              for base in edizione.lecturer_base_ids:
                  ''' ci sono problemi a rilevare il contrario: ovvero se il corso di FET
                      è anche presente in Openerp, il motivo è perchè le materie 
                      è un elenco di tutti i corsi non solo di questo
                  '''                  
                  
                  corso = base.course_id.name.lower()                  
                  if corso in lista_materie: # TODO correggere il warning!!!
                     get_ids_edizione_da_classe[edizione.fet_class][3][corso]=[base.course_id.id, base.id] # Aggiunto i due ID
                  else: # warning, materia presente non in FET
                     lista_materie_ko.append(corso)                     
                     
                  if base.base_lecturer_id: # esiste l'insegnante
                     # Insegnante base:
                     insegnante= base.base_lecturer_id.contact_lastname.lower()   
                     if insegnante in lista_insegnanti:
                        get_ids_edizione_da_classe[edizione.fet_class][4][insegnante]=base.base_lecturer_id.id                    
                     else: # warning, insegnante presente non in FET
                        lista_insegnanti_ko.append(insegnante)
                     # Insegnange secondario (se presente):   
                     if base.base_lecturer_2_id:
                        insegnante= base.base_lecturer_2_id.contact_lastname.lower()   
                        if insegnante in lista_insegnanti:
                           get_ids_edizione_da_classe[edizione.fet_class][4][insegnante]=base.base_lecturer_2_id.id                    
                        else: # warning, insegnante presente non in FET
                           lista_insegnanti_ko.append(insegnante)
                        
          # Warning!
          '''if lista_insegnanti_ko or lista_materie_ko:
             raise osv.except_osv("Attenzione:",
                                  "Non trovati gli abbinamenti insegnante o materia:\n\n" +
                                  "Materie:\n" + "\n".join(lista_materie_ko) +
                                  "\n\nInsegnanti:\n" + "\n".join(lista_insegnanti_ko))'''

          # File timetable.csv #################################################   
          # - Carico l'elenco delle lezioni e le importo nel calendario tipo:
          tot_col = 0
          file_csv = get_addons_path() + catalog_browse.fet_prefix + "_timetable.csv"
          try:
             input_csv = open(file_csv,'rb')
          except:
             raise osv.except_osv("Attenzione:","Errore nell'apertura del file " + input_csv)   
          lines = csv.reader(input_csv, delimiter=',')
          
          # Ciclo per creare l'inserimento della prima settimana per tutte le classi
          elenco_lezioni = {} 
          elenco_lezioni_durata = {}
          counter=-1 # ho l'intestazione (utile per rilevare anche il tot_col)
          giorni_x_esteso={'do':7, 'lu':1, 'ma':2, 'me':3, 'gi':4, 've':5, 'sa':6}
          for line in lines:
              counter+=1
              if not counter: 
                 tot_col=len(line) # Memorizzo l'elenco colonne per controllo            
              else: # data lines                 
                 if len(line) != tot_col: 
                    if len(line) != 0: # altrimenti salto la riga se è 0
                       raise osv.except_osv("Attenzione:", 
                             "File: %s_timetable.csv riga %s > colonne errate (%s ora %s)" 
                             % (catalog_browse.fet_prefix, counter, tot_col, len(line)))                        
                 else: 
                    csv_id=0
                    ref = utf8_convert(line[csv_id]) #﻿Activity Id (doppio per le ore spezzate)
                    csv_id+=1
                    day = utf8_convert(line[csv_id]) #Day
                    csv_id+=1
                    hour_start = utf8_convert(line[csv_id]) #Hour
                    csv_id+=1
                    class_id = utf8_convert(line[csv_id]) #.upper() #Students Sets (2 A)
                    csv_id+=1
                    subject = utf8_convert(line[csv_id]).lower() #Subject
                    csv_id+=1
                    job_id_name = utf8_convert(line[csv_id]).lower() #Teachers
                    csv_id+=1
                    activity_tag = utf8_convert(line[csv_id]) #Activity Tags
                    csv_id+=1
                    room = utf8_convert(line[csv_id]) #Room
                    # computed fields:
                    if not (day>=1 and day<=7):
                       if day[:2].lower() in giorni_x_esteso: # trasformo da nome a numero
                          day=giorni_x_esteso[day[:2].lower()]
                    job_id_name=job_id_name.split("+") # divido la lista dove trovo il "+"
                    if len(job_id_name)>2:
                       raise osv.except_osv("Error", "Trovato lezioni in FET con piu' di 2 insegnanti!")
                       
                    # TODO contollare se arriva come numero intero se funziona la verifica (serve per i calcoli poi)      
                    if ref in elenco_lezioni_durata: # la lezione è già stata caricata
                       elenco_lezioni_durata[ref]+=1 # TODO e' sempre uno?
                    else:   
                        elenco_lezioni_durata[ref]=1    
                        # Carico la struttura divisa per id giorno:
                        if day<1 or day>7: # se non ho trovato il numero o il giorno è scritto male:
                           raise osv.except_osv("Error", "I giorni in FET devono essere compresi tra 1 e 7")
                           
                        if class_id not in elenco_lezioni:
                           elenco_lezioni[class_id]={} # preparo la lista per i giorni
                        if day not in elenco_lezioni[class_id]:
                           elenco_lezioni[class_id][day]=[] # preparo la lista per le lezioni
                        elenco_lezioni[class_id][day].append([subject, job_id_name, hour_start, ref]) # ref for get tot hour
                       
          input_csv.close()
          
          holiday_pool = self.pool.get('training.holiday.period')
          last_id=0
          last_ref=0
          last_dur=0
          for sessione_item in elenco_lezioni.keys(): # per tutte le classi interessate
              session_id=classi_2_session_id[sessione_item]
              
              # elimino tutte le eventuali lezioni presenti:
              seance_plan_ids=seance_plan_pool.search(cr, uid, [('session_id','=', session_id)]) # tutte le lezioni sett. della sessione
              seance_plan_unlink=seance_plan_pool.unlink(cr, uid, seance_plan_ids) # elimino le selezionate
              
              session_date_start = datetime.strptime(get_ids_edizione_da_classe[sessione_item][1], "%Y-%m-%d 00:00:00") 
              session_date_end = datetime.strptime(get_ids_edizione_da_classe[sessione_item][2], "%Y-%m-%d 00:00:00")
              
              for week_day in range(1,8): # giorni della settimana da 1 a 7
                  week_number=0             
                  # calcolo da data attuale
                  actual_date=session_date_start + timedelta(days = week_number * 7 + week_day - 1) 
                  actual_date_string=actual_date.strftime('%Y-%m-%d 00:00:00')

                  while actual_date <= session_date_end: # controllo che non sfori la fine
                      if not holiday_pool.is_in_period(cr, actual_date_string[:10]): # per i non festivi:
                          if week_day in elenco_lezioni[sessione_item]: # salvo eventuali giorni non presenti
                             for lezione_del_giorno in elenco_lezioni[sessione_item][week_day]: # inserisco tutte le lezioni                            
                                 # uso get_ids_edizione_da_classe per reperire gli id che mi servono:
                                 # Controlli pre inserimento (bloccanti!):
                                 if lezione_del_giorno[0] not in get_ids_edizione_da_classe[sessione_item][3]: # Corso
                                    raise osv.except_osv("Error", "Corso non trovato nei corsi base %s: %s" %(sessione_item, lezione_del_giorno[0],))
                                 else:
                                    course_id = get_ids_edizione_da_classe[sessione_item][3][lezione_del_giorno[0]][1]

                                 if lezione_del_giorno[1][0] not in get_ids_edizione_da_classe[sessione_item][4]: # Insegnante
                                    raise osv.except_osv("Error", "Insegnante non trovato nei corsi base %s: %s" %(sessione_item, lezione_del_giorno[1][0],))
                                 else:
                                    base_lecturer_id = get_ids_edizione_da_classe[sessione_item][4][lezione_del_giorno[1][0]]
                                    
                                 if len(lezione_del_giorno[1])==2:
                                    if lezione_del_giorno[1][1] not in get_ids_edizione_da_classe[sessione_item][4]: # Insegnante
                                       raise osv.except_osv("Error", "Insegnante secondario non trovato nei corsi base %s: %s" %(session_item, lezione_del_giorno[1][1],))
                                    else:
                                       base_lecturer_2_id = get_ids_edizione_da_classe[sessione_item][4][lezione_del_giorno[1][1]]
                                 else:      
                                    base_lecturer_2_id = False
                                 seance_plan_data = {'course_base_id': course_id, # base_lecturer_id
                                              'session_id': session_id,
                                              'course_id': get_ids_edizione_da_classe[sessione_item][3][lezione_del_giorno[0]][0], 
                                              'base_lecturer_id': base_lecturer_id, 
                                              'base_lecturer_2_id': base_lecturer_2_id,
                                              #date_end
                                              'date': actual_date_string[:11] + lezione_del_giorno[2].replace('.',':') + ":00",
                                              'duration': elenco_lezioni_durata[lezione_del_giorno[3]] or 0, # da modificare in caso si incrementi
                                              }
                                 seance_plan_pool.create(cr, uid, seance_plan_data, context) 
                                 
                      week_number+=1
                      actual_date=session_date_start + timedelta(days = week_number * 7 + week_day - 1)
                      actual_date_string=actual_date.strftime('%Y-%m-%d 00:00:00')                
          return True 

      _columns={
               'fet_prefix': fields.char('Prefisso file', size=32, required=False, readonly=False, help="Prefisso standard che viene apposto ai file esportati da FET"),
                }
      
training_catalog_add_fields()
class training_subscription_add_base_fields(osv.osv):
      ''' 
         Add link to training.subscription 
      '''
      
      _name = 'training.subscription'
      _inherit= 'training.subscription'

      def on_change_search_contact(self, cr, uid, ids, search_contact_id, context=None):
          if not context:
             context={}        
          
          # Ricerco il partner abbinato a questo job:
          try: 
              res={}
              if search_contact_id:
                 job_proxy=self.pool.get('res.partner.job').browse(cr, uid, search_contact_id, context=context)             
                 partner_id=job_proxy.address_id.partner_id.id
                 if partner_id: # Lancio la procedura originale dell on change partner passandogli quello rilevato
                    subscription_proxy=self.pool.get('training.subscription')
                    res=subscription_proxy.on_change_partner(cr, uid, [], partner_id)
                    res['value']['partner_id']=partner_id 
              return res              
          except:
              raise osv.except_osv(('Attenzione:'),
                    ('Errore cercando il partner abbinato!'))
             
      _columns={
               'search_contact_id': fields.many2one('res.partner.job', 'Ricerca contatto', help="Permette di ricercare il contatto direttamente",),
                }

training_subscription_add_base_fields()

class training_seance_add_base_fields(osv.osv):
      ''' 
      Add link to training.seance and some funct
      '''
      
      _name = 'training.seance'
      _inherit= 'training.seance'

      def _compute_date_end(self, cr, uid, ids, name, args, context=None): 
          """
          @param cr: the current row, from the database cursor,
          @param uid: the current user’s ID for security checks,
          @param ids: List of Openday’s IDs
          @return: date_end = date + duration
          @param context: A standard dictionary for contextual values
          """
          from datetime import datetime 
          from datetime import timedelta

          res = {} 
          for seance in self.browse(cr, uid, ids, context=context): 
              date_from=datetime.strptime(seance.date, "%Y-%m-%d %H:%M:%S")
              date_to=date_from + timedelta(hours=round(seance.duration,0))
              res[seance.id]=date_to.strftime('%Y-%m-%d %H:%M:%S')
          return res
     
      _columns={
              'base_lecturer_id': fields.many2one('res.partner.job', 'Docente principale', help="Docente base che tiene il modulo",), # sostituito per stakeholder?
              'base_lecturer_2_id': fields.many2one('res.partner.job', 'Docente secondario', help="Docente base secondario che partecipa al modulo",), 
              'session_id' : fields.many2one('training.session','Edizione collegata'),   # TODO andrebbe eliminato!!!
              'date_end': fields.function(_compute_date_end, method=True, type='datetime', string='Fine lezione', store=False),               
              }
               
training_seance_add_base_fields()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
