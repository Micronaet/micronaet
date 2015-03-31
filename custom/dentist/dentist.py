# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009  Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2010  Luis Falcon
#    Copyright (C) 2011-2012  Nicola Riolini - Micronaet s.r.l.
#    d$
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

import netsvc
import time
from dateutil.relativedelta import relativedelta
from datetime import datetime
from osv import fields, osv
from tools.translate import _
import decimal_precision as dp

# global parameters:
tooth_list=[('11','11'),('12','12'),('13','13'),('14','14'),('15','15'),('16','16'),('17','17'),('18','18'), # Adult
            ('21','21'),('22','22'),('23','23'),('24','24'),('25','25'),('26','26'),('27','27'),('28','28'),
            ('31','31'),('32','32'),('33','33'),('34','34'),('35','35'),('36','36'),('37','37'),('38','38'),
            ('41','41'),('42','42'),('43','43'),('44','44'),('45','45'),('46','46'),('47','47'),('48','48'),
            ('51','51'),('52','52'),('53','53'),('54','54'),('55','55'), # Baby
            ('61','61'),('62','62'),('63','63'),('64','64'),('65','65'),
            ('71','71'),('72','72'),('73','73'),('74','74'),('75','75'),
            ('81','81'),('82','82'),('83','83'),('84','84'),('85','85'),
            ('*','All'), # All teeth
            ('up','Sup.'),('down','Inf.'), # Up and Down
            ('n','Note'),# Technical note
            ]
# TODO link to notes?
office_list=[("dentistico", "Studio dentistico"), ("cardiologia", "Cardiologia"), ("estetica", "Chirurgia estetica"), ("generale", "Chirurgia generale"), ("dermatologia", "Dermatologia"),
             ("dietologia", "Dietologia"), ("ecografie", "Ecografie"), ("fisiatra", "Fisiatra"), ("ginecologia", "Ginecologia"), 
             ("interna", "Medicina interna"), ("oculistica", "Oculistica"), ("omeopatia", "Omeopatia"), ("oncologia", "Oncologia"), 
             ("ortopedia", "Ortopedia"), ("otorino", "Otorino"), ("proctologia", "Proctologia"), ("pediatria", "Pediatria"), 
             ("reumatologia", "Reumatologia"),("all", "All office")]

'''* STUDIO DENTISTICO
servizi prevenzione ed igiene, tecniche di sbiancamento,
protesi fissa e mobile, odontoiatria infantile ed estetica,
ortodonzia infantile e dell'adulto,
implantologia, parodontologia,
medicina/chirurgia orale e conservativa'''

emergency_list=[('a','Normal'),('b','Urgent'),('c','Medical Emergency'),]            

class res_groups_inherit(osv.osv):
    _name = "res.groups"
    _inherit = "res.groups"

    _columns = {
        'poliambulatory':fields.boolean('Poliambulatori', required=False),
        }
res_groups_inherit()

class dentist_room (osv.osv):
    _name = "dentist.room"
    _columns = {
        'name' : fields.char ('Name', size=128, help="Room description"),
        'code' : fields.char ('Code', size=18),
        'extra_info' : fields.text ('Extra Info'),
        }
dentist_room()

# Class preview:
class dentist_operation(osv.osv):
    ''' List of operation to do on patient (every intervention may be done with
        mote than one appointment
        Every intervention is on one tooth (or All teeth
        TODO Intervention generated from quotations
    '''
    _name = "dentist.operation"
dentist_operation()

class dentist_todo(osv.osv):
    ''' Todo list operation quotation not executed (quotation element that is not
        in dentist.operation
    '''
    _name = "dentist.todo"
    _order = "date,tooth,name"
    
        
    _columns = {    
        'name': fields.char ('Intervent', size=128, help="Short description of internent"),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False, readonly=False),
        'product_id':fields.many2one('product.product', 'Operation', required=False, readonly=False),
        'tooth': fields.selection(tooth_list, 'Tooth', select=True, readonly=False),
        'note': fields.text ('Note'),
        'urgency': fields.selection(emergency_list, 'Urgency Level'),
        'date': fields.date('Date', help="Start date of intervent"),
        'import': fields.boolean('Imported', required=False), # TODO remove when imported!!!
        }
    _defaults = {
                'urgency': lambda *a: 'a',
                }
dentist_todo()

class dentist_appointment(osv.osv):
    ''' Medical appointment with wf status included
    '''
    _name = "dentist.appointment"

    # WF function:
    def workflow_appointment_confirmed(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'confirmed',
                                  'datetime_confirmed': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'confirmed_user_id': uid,                                  
                                 })
        return True
        
    def workflow_appointment_reminder(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'reminder',
                                  'datetime_reminder': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'reminder_user_id': uid,                                  
                                 })
        return True

    def workflow_appointment_arrived(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'arrived', 
                                  'datetime_arrived': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'arrived_user_id': uid,                                  
                                 })
        return True
        
    def workflow_appointment_enter(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'enter', 
                                  'datetime_enter': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'enter_user_id': uid,                                  
                                 })
        return True
        
    def workflow_appointment_close(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'close', 
                                  'datetime_close': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'close_user_id': uid,                                  
                                 })
        return True
        
    def workflow_appointment_cancel(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancel', 
                                  'datetime_cancel': time.strftime('%Y-%m-%d %H:%M:%S'),
                                  'cancel_user_id': uid,                                  
                                 })
        return True
    _order = "appointment_date desc"


    def _function_get_calendar_description(self, cr, uid, ids, field_name, arg, context=None):
        ''' Get a short description for calendar element
        '''        
        res={}
        for item in self.browse(cr, uid, ids):
            res[item.id]="%s-%s %s"%(item.name,item.patient_id and item.patient_id.last_name, item.patient_id and item.patient_id.first_name)
        return res    
     
    def _function_get_time(self, cr, uid, ids, field_name, arg, context):
        """ Function that return different waiting time:
              wait_time, enter_time, close_time
        """
        #TODO backup
        from datetime import datetime, timedelta
        def slim_time(complete_time):
            if complete_time:
               return complete_time.split(".")[0]
            return False   
        result = {}
        for appointment in self.browse(cr, uid, ids):
            result[appointment.id]={'wait_time':'', 'enter_time':'', 'close_time':'','delay_time':'',}
            if appointment.state in ('arrived', 'enter', 'close', 'close_rescheduled', 'confirmed'):
               appointment_time =appointment.appointment_date and datetime.strptime(appointment.appointment_date, '%Y-%m-%d %H:%M:%S') # to test delay
               if appointment.state!="confirmed":
                  refer_time = datetime.strptime(appointment.datetime_arrived, '%Y-%m-%d %H:%M:%S')
               else:
                  refer_time = False
                     
               now_time =  datetime.now()
               if appointment.state == 'confirmed': # here delay test
                  if (appointment_time) and (appointment_time < now_time): 
                     result[appointment.id]['delay_time']=slim_time("%s"%(now_time - appointment_time,))
               if appointment.state == 'arrived': # only if not entered!
                  result[appointment.id]['wait_time']=slim_time("%s"%(now_time - refer_time,))
               if appointment.state in ('enter', 'close', 'close_time'): # only if not entered!
                  result[appointment.id]['enter_time']=slim_time("%s"%(datetime.strptime(appointment.datetime_enter, '%Y-%m-%d %H:%M:%S') - refer_time,))
               if appointment.state in ('close', 'close_rescheduled'): # only if not entered!
                  result[appointment.id]['close_time']=slim_time("%s"%(datetime.strptime(appointment.datetime_close, '%Y-%m-%d %H:%M:%S') - refer_time,))
        return result

    _columns = {        
        'name': fields.char ('Appointment ID',size=64, required=False),
        'calendar_name': fields.function(_function_get_calendar_description, method=True, type='char', size=50, string='Calendar', store=False),
        'patient_id': fields.many2one ('res.partner', 'Patient', help="Patient Name"),
        'doctor_id': fields.many2one ('res.users','Doctor', domain=[('is_doctor', '=', "1")], help="Doctor Name"),
        'assistant_id': fields.many2one ('res.users','Assistant', domain=[('is_assistant', '=', "1")], help="Assistant name"),
        'alert_by': fields.selection([('no','No advice'),
                                      ('email','E-mail'),
                                      ('sms','SMS'),],'Alert', select=True, readonly=False),
        'appointment_date': fields.datetime ('Date and Time'),
        'duration': fields.float('Durata', digits=(8, 3)),
        'urgency': fields.selection(emergency_list, 'Urgency Level'),
        'comments': fields.text ('Comments'),

        'preparation': fields.selection([
                ('presenza','**>> Presenza <<**'), 
                ('consegna','**>> Consegna <<**'), 
        ],'Preparazione', select=True, readonly=False, help="Indica se e' stata richiesta qualche particolare preparazione all'appuntamento da verificare"),

        'state': fields.selection([
                ('confirmed','Confirmed'), 
                ('reminder','Reminder'), # for rescheduled
                ('arrived','Arrived'),
                ('enter','Enter'),
                ('close','Close'),
                ('cancel','Cancel'),
        ],'State', select=True, readonly=True),
        
        # Time stamp per vedere evasione in WF
        'datetime_confirmed': fields.datetime ('Confirmed time'),
        'confirmed_user_id': fields.many2one('res.users', 'Confirmed from', required=False, readonly=True),
        'delay_time': fields.function(_function_get_time, method=True, type='char', size=30, string='Delay time', store=False, multi=True),

        'datetime_reminder': fields.datetime ('Reminder time'),
        'reminder_user_id': fields.many2one('res.users', 'Reminder from', required=False, readonly=True),

        'datetime_arrived': fields.datetime ('Arrived time'),
        'arrived_user_id': fields.many2one('res.users', 'Signed in from', required=False, readonly=True),
        'wait_time': fields.function(_function_get_time, method=True, type='char', size=30, string='Wait time', store=False, multi=True),

        'datetime_enter': fields.datetime ('Enter time'),
        'enter_user_id': fields.many2one('res.users', 'Carried in from', required=False, readonly=True),
        'enter_time': fields.function(_function_get_time, method=True, type='char', size=30, string='Time to enter', store=False, multi=True),

        'datetime_close': fields.datetime ('Close time'),
        'close_user_id': fields.many2one('res.users', 'Closed from', required=False, readonly=True),
        'close_time': fields.function(_function_get_time, method=True, type='char', size=30, string='Time to close', store=False, multi=True),

        'datetime_cancel': fields.datetime ('Cancel time'),
        'cancel_user_id': fields.many2one('res.users', 'Cancelled from', required=False, readonly=True),
        
        'room_id':fields.many2one('dentist.room', 'Room', required=False),
        'note': fields.text('Note'),
        
        'medical_note_required': fields.boolean('Medical note required'),
        'medical_note_completed': fields.boolean('Medical note completed'),
        'medical_note': fields.text('Medical note'),
        }
        
    _defaults = {
                'confirmed_user_id': lambda obj,cr,uid,context: uid,
                'state': lambda *a: 'confirmed',
                'datetime_confirmed': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
                'urgency': lambda *a: 'a',
                }
dentist_appointment()

class sale_order_line_field(osv.osv):
    """
    Add extra field order line  
    """
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    _columns = {
        'tooth' : fields.selection(tooth_list, 'Tooth', select=True, readonly=False),
        'discarded': fields.boolean('Discarded', required=False),
        # TODO put tooth_ids for more than one operations                            
    }
sale_order_line_field()

class inherit_sale_order(osv.osv):
    """
    Add extra field sale.order
    """
    _name = 'sale.order'
    _inherit = 'sale.order'
    
    import datetime

    def onchange_partner_id(self, cr, uid, ids, partner_id):        # Override on_change partner in sale.order (add privacy check)
        res_id = super(inherit_sale_order, self).onchange_partner_id(cr, uid, ids, partner_id)

        if partner_id:
           partner_pool=self.pool.get("res.partner").browse(cr, uid, partner_id)
           res_id['value']['print_privacy_policy']=not partner_pool.privacy_signed
        return res_id
    
    def button_discard(self, cr, uid, ids, context=None):    
        ''' Delete selected lines but before save the operations in client form as "dentist.todo"
        '''
        import datetime

        order_line_pool = self.pool.get('sale.order.line')
        order_line_ids = order_line_pool.search(cr, uid, [('order_id','=',ids),('discarded', '=', True),], context=context)
        for operations in order_line_pool.browse(cr, uid, order_line_ids): # copy operation in todo:                         
            data_todo= {
                'name': operations.name,
                'partner_id': operations.order_partner_id.id,
                'product_id': operations.product_id.id,
                'tooth': operations.tooth,
                'note': 'Da preventivo n.: %s'%(operations.order_id.name,),
                #'urgency': 
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'import': False,
                }
            import_todo=self.pool.get("dentist.todo").create(cr, uid, data_todo)
            
        # delete lines after stored as todo operations
        delete_result = order_line_pool.unlink(cr, uid, order_line_ids, context=context)        
        return True

    def action_wait(self, cr, uid, ids, *args):
        ''' Override WF state function of sale.order WF:
            Add extra action when get in this state for migrate order lines in
            operation, deleting discarded lines (stored in todo operation)
        '''
        import datetime
        
        # delete discard lines putting in todo operations:
        self.button_discard(cr, uid, ids)
        
        # Search remain lines 
        line_pool=self.pool.get("sale.order.line")
        line_ids=line_pool.search(cr, uid, [('order_id', '=', ids)]) # TODO right?
        
        # create operations for partner
        for operations in line_pool.browse(cr, uid, line_ids):
            data_operation= {
                'name': operations.name,
                'order_id': operations.order_id.id,
                'partner_id': operations.order_partner_id.id,
                'product_id': operations.product_id.id,
                'tooth': operations.tooth,
                'note': 'Da preventivo n.: %s'%(operations.order_id.name,), #TODO eliminare con il link già si sa
                #'urgency': 
                #'state'
                'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                'date_end': datetime.datetime.now().strftime("%Y-%m-%d"),
                'import': False,
                }
                
            import_todo=self.pool.get("dentist.operation").create(cr, uid, data_operation)
            
        # leave focus on overrided function    
        return super(inherit_sale_order, self).action_wait(cr, uid, ids, *args)
    _columns = {
              'print_privacy_policy':fields.boolean('Print privacy', required=False),  
              'print_conditions':fields.boolean('Print conditions', required=False),  
              'print_discount':fields.boolean('Print detail discount', required=False),  
              'print_subtotal_price':fields.boolean('Print subtotal price', required=False),  
    }    
inherit_sale_order()

class product_category_add_fields(osv.osv):
    """
    add extra fields in category of products
    """
    
    _name = 'product.category'
    _inherit = 'product.category'
    _columns = {
        'code':fields.char('code', size=12, required=False, readonly=False),
    }
product_category_add_fields()

class dentist_annotation(osv.osv):
    _name = "dentist.annotation"
    _order = "date desc,name"

    '''def _user_ids_list(self, cr, uid, ids, name, arg, context = None):
        res={}
        for item in self.browse(cr, uid, ids, context=context):
            import pdb; pdb.set_trace()
            if item.group_id and item.group_id.users:
               res[item.id]=[user.id for user in item.group_id.users]
        return res'''
    
    _columns = {
        'name' : fields.char ('Annotation', size=128, help="Annotation"),
        'note' : fields.text ('Note'),
        
        'date' : fields.date('Date', help="Date of creations partner record"),
        'date_from' : fields.date('Date form', help="Ex. for medicaments or farmacology"),
        'date_to' : fields.date('Date to', help="Ex. for medicaments or farmacology"),
        
        'type':fields.selection([
            ('danger','Danger'),            
            ('controindications','Controindications'),            
            ('farmacology','Farmacology'),
            ('info','Information'),
        ],'Type', select=True, readonly=False),
        'group_id':fields.many2one('res.groups', 'Group', required=False, readonly=False, domain=[('poliambulatory','=',True)]),         
        'user_id':fields.many2one('res.users', 'User', required=False, readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False, readonly=False),
        #'superpartes':fields.boolean('Extra group', help="This note is important also for other office"),

        'import': fields.integer('ID importazione'), # TODO to remove (used for importation sincro)
        
        'office':fields.selection(office_list,'Office', select=True, readonly=False, help="Used for filter annotation basing on office"),
        #'user_ids': fields.function(_user_ids_list, method=True, type='one2many', model="res.users", string='Users',),
        }
        
    _defaults = {
            'date': lambda *a: time.strftime('%Y-%m-%d'),
            'date_from': lambda *a: time.strftime('%Y-%m-%d'),
            'user_id': lambda obj,cr,uid,context: uid,
    }    
dentist_annotation()

class res_users_extra(osv.osv):
    ''' Add extra field for administration to openerp users'''
    _name="res.users"
    _inherit="res.users"
    
    _columns = {
                #'is_patient' : fields.boolean('Patient', help="Check if the partner is a patient"),
                'is_doctor' : fields.boolean('Doctor', help="Check if the partner is a doctor"),
                'is_assistant' : fields.boolean('Assistant', help="Check if the partner is an assistant"),    
               }
res_users_extra()
               
class partner_patient_extra_fields(osv.osv):
    ''' Extra fields for manage partners in Dentist Studio'''
    _name = "res.partner"
    _inherit = "res.partner"
    _order = "name"
    #TODO Inserire le procedure di write e create per mettere in name first e last
    
    def write(self, cr, user, ids, vals, context=None):
        """
        Update redord(s) comes in {ids}, with new value comes as {vals}
        return True on success, False otherwise
    
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be update
        @param vals: dict of new values to be set
        @param context: context arguments, like lang, time zone
        
        @return: True on success, False otherwise
        """
    
        # TODO Error if there is a batch update, like all first_name="John"
        for item in self.browse(cr, user, ids, context=context):
           if ('last_name' in vals) and ('first_name' in vals): # first and last are present:
              vals['name']="%s %s"%(vals['last_name'] or "",vals['first_name'] or "",)
           else: #one is not present
              if ('last_name' in vals):
                 vals['name']=vals['last_name'] + " "
              else:   
                 vals['name']=(item.last_name or "") + " "
              if ('first_name' in vals):
                 vals['name']+=vals['first_name'] 
              else:   
                 vals['name']+=item.first_name or ""
                     
        res = super(partner_patient_extra_fields, self).write(cr, user, ids, vals, context)
        return res
    
    def create(self, cr, user, vals, context={}):
        """
        Create a new record for a model ModelName
        @param cr: cursor to database
        @param user: id of current user
        @param vals: provides a data for new record
        @param context: context arguments, like lang, time zone
        
        @return: returns a id of new record
        """
        vals['name']=""
        if 'last_name' in vals:
           vals['name']=(vals['last_name'] or "") + " " 
        if 'first_name' in vals:
           vals['name']+=(vals['first_name'] or "")
           
        res_id = super(partner_patient_extra_fields, self).create(cr, user, vals, context)
        return res_id
    
    '''def _patient_age(self, cr, uid, ids, name, arg, context={}):
        def compute_age_from_dates (patient_dob,patient_deceased,patient_dod):
            now=datetime.now()
            if (patient_dob):
                dob=datetime.strptime(patient_dob,'%Y-%m-%d')
                if patient_deceased :
                    dod=datetime.strptime(patient_dod,'%Y-%m-%d %H:%M:%S')
                    delta=relativedelta (dod, dob)
                    deceased=" (deceased)"
                else:
                    delta=relativedelta (now, dob)
                    deceased=''
                years_months_days = str(delta.years) +"y "+ str(delta.months) +"m "+ str(delta.days)+"d" + deceased
            else:
                years_months_days = "No DoB !"

            return years_months_days
        result={}
            for patient_data in self.browse(cr, uid, ids, context=context):
                result[patient_data.id] = compute_age_from_dates (patient_data.dob,patient_data.deceased,patient_data.dod)
            return result'''
    
    _columns = {
        # override:
        'name': fields.char('Name', size=128, required=False, select=True),

        # added fields:
        'date_creation' : fields.date('Partner since',help="Date of creations partner record"),
        'alias' : fields.char('alias', size=64),
        'last_name' : fields.char('Last name', size=64),
        'first_name' : fields.char('First name', size=64),
        'fiscal_id_code' : fields.char('Fiscal code', size=16),
        'profession' : fields.char('Professione', size=64),

        #'is_person' : fields.boolean('Person', help="Check if the partner is a person."),
        #'is_patient' : fields.boolean('Patient', help="Check if the partner is a patient"),
        #'is_doctor' : fields.boolean('Doctor', help="Check if the partner is a doctor"),
        #'is_assistant' : fields.boolean('Assistant', help="Check if the partner is an assistant"),
        #'is_institution' : fields.boolean ('Institution', help="Check if the partner is a Medical Center"),

        #'lastname' : fields.char('Last Name', size=128, help="Last Name"),
        
        # Patient data:
        'photo' : fields.binary ('Picture'),
        'dob' : fields.date ('Date of Birth'),
        'lob' : fields.char('Place of birth', size=80),
        'pob' : fields.char('Province of birth', size=4),
        #'age' : fields.function(_patient_age, method=True, type='char', size=32, string='Patient Age',help="It shows the age of the patient in years(y), months(m) and days(d).\nIf the patient has died, the age shown is the age at time of death, the age corresponding to the date on the death certificate. It will show also \"deceased\" on the field"),
        'deceased' : fields.boolean ('Deceased',help="Mark if the patient has died"),

        'sex' : fields.selection([('m','Male'),
                                  ('f','Female'),
                                 ], 'Sex', select=True),
        'marital_status' : fields.selection([('s','Single'),
                                             ('m','Married'),
                                             ('w','Widowed'),
                                             ('d','Divorced'),
                                             ('x','Separated'),
                                             ], 'Marital Status'),
        'blood_type' : fields.selection([('A','A'),
                                         ('B','B'),
                                         ('AB','AB'),
                                         ('O','O'),
                                         ], 'Blood Type'),
        'rh' : fields.selection([('+','+'),
                                 ('-','-'),
                                 ], 'Rh'),

        #'user_id':fields.related('name','user_id',type='many2one',relation='res.partner',string='Doctor',help="Physician that logs in the local Medical system (HIS), on the health center. It doesn't necesarily has do be the same as the Primary Care doctor"),
        #'ethnic_group' : fields.many2one ('medical.ethnicity','Ethnic group'),
        #'vaccinations': fields.one2many ('medical.vaccination','name',"Vaccinations"),
        #'medications' : fields.one2many('medical.patient.medication','name','Medications'),
        #'prescriptions': fields.one2many ('medical.prescription.order','name',"Prescriptions"),
        #'diseases' : fields.one2many ('medical.patient.disease', 'name', 'Diseases'),
        
        #'critical_info' : fields.text ('Important disease, allergy or procedures information',help="Write any important information on the patient's disease, surgeries, allergies, ..."),
        #'evaluation_ids' : fields.one2many ('medical.patient.evaluation','name','Evaluation'),
        #'admissions_ids' : fields.one2many ('medical.patient.admission','name','Admission / Discharge'),
        
        'general_info' : fields.text ('General Information',help="General information about the patient"),
        'send_from' : fields.char('Send from', size=64),
        #'cod' : fields.many2one ('medical.pathology', 'Cause of Death'),
        'annotations_ids':fields.one2many('dentist.annotation', 'partner_id', 'Annotations', required=False),
        'operation_ids':fields.one2many('dentist.operation', 'partner_id', 'Operations', required=False),
        'todo_ids':fields.one2many('dentist.todo', 'partner_id', 'Operations todo', required=False),
        # Malattie:
        'disease_allergie' : fields.boolean ('Allergie'),
        'disease_pressure' : fields.boolean ('Presure'),
        'disease_cardio' : fields.boolean ('Cardio'),
        'disease_emo' : fields.boolean ('Emo'),
        'disease_ricamb' : fields.boolean ('Ricamb'),
        'disease_nerve' : fields.boolean ('Nerve'),
        'disease_pregnant' : fields.boolean ('Pregnant'), # TODO date term?
        'disease_infectious' : fields.boolean ('Infectious'),
    }

    _defaults = {
           'date_creation': lambda *a: time.strftime('%Y-%m-%d'),
    }

partner_patient_extra_fields()

#Add the partner relationship field to the contacts.
class res_partner_patient_extra(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    
    def _function_browse_web(self, cr, uid, ids, field_name=None, arg=False, context=None):

        def get_ip_address(ifname):
            ''' Get IP address of interface passed
            '''
            import socket
            import fcntl
            import struct
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', ifname[:15])
            )[20:24])

        res={}
        try:
           server_ip=get_ip_address('eth0') or "192.168.0.102" # TODO default value
        except:   
           server_ip="192.168.0.102"
           
        for item in ids:
           res[item]="http://%s/d.php?id=%s"%(server_ip,item)
           
        return res   
    
    _columns = {
        'relationship': fields.text('Relationship', help="Elenco delle relazioni con altri pazienti"),
        'privacy_signed':fields.boolean('Privacy firmata', required=False),
        'browse_web': fields.function(_function_browse_web, method=True, type='char', size=100, string='Link ortofoto', store=False),
    }
res_partner_patient_extra()

class dentist_appointment (osv.osv):
    ''' Medical appointment with wf status included
    '''
    _name = "dentist.appointment"
    _inherit = "dentist.appointment"

    _columns = {
               'operation_ids':fields.many2many('dentist.operation', 'appointment_operation_relation', 'appointment_id', 'operation_id', 'Operations', required=False),  # TODO many2many!!!!
               }
dentist_appointment()

class dentist_operation(osv.osv):
    ''' List of operation to do on patient (every intervention may be done with
        mote than one appointment
        Every intervention is on one tooth (or All teeth
        TODO Intervention generated from quotations
    '''
    _name = "dentist.operation"
    _inherit = "dentist.operation"
    _order = "date,tooth,name"

    def wkf_operation_draft(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'draft',
                                 })
        return True
    def wkf_operation_done(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'done',
                                 })
        return True
    def wkf_operation_irrilevant(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'irrilevant',
                                 })
        return True
    def wkf_operation_cancel(self, cr, uid, ids):
        self.write(cr, uid, ids, {'state': 'cancel',
                                 })
        return True

    def xml_rpc_operation_complete(self, cr, uid, context=None):
        """ Function called from XML-RPC to trigger operation in right state
            TODO remove after importation
        """
        wf_service = netsvc.LocalService("workflow")

        # Trigger to done imported operation:
        operation_ids=self.search(cr, uid, [('state','=','draft'),('import','=',True)])
        for operation_id in operation_ids:
            wf_service.trg_validate(uid, 'dentist.operation', operation_id, 'operation_done', cr)

        # Trigger to irrilevant Note operation:
        note_operation_ids=self.search(cr, uid, [('state','=','done'),('import','=',True),('tooth','=','n')])
        for note_operation_id in note_operation_ids:
            wf_service.trg_validate(uid, 'dentist.operation', note_operation_id, 'operation_irrilevant', cr)
        return True
        
    _columns = {    
        'name': fields.char ('Extra info', size=128, help="Short description of internent"),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False, readonly=False),
        'product_id':fields.many2one('product.product', 'Operation', required=False, readonly=False),
        'order_id':fields.many2one('sale.order', 'Order', required=False, readonly=False),
        'tooth': fields.selection(tooth_list, 'Tooth', select=True, readonly=False),
        'note': fields.text ('Note'),
        'urgency': fields.selection(emergency_list, 'Urgency Level'),
        # TODO Link to quotation (use sale.order or new object???)
        'date': fields.date('Date', help="Start date of intervent"),
        'date_end': fields.date('Date end', help="End date for intervent"),
        #'date_from' : fields.date('Date form', help="Ex. for medicaments or farmacology"),
        #'date_to' : fields.date('Date to', help="Ex. for medicaments or farmacology"),
        'state': fields.selection([
                ('draft','To do'), 
                ('done','Done'), 
                ('irrilevant','Irrilevant'),
                ('cancel','Cancel'),
        ],'State', select=True, readonly=True), # TODO (managed with button but not WF! TODO reset readonly
        'appointment_ids': fields.many2many('dentist.appointment', 'appointment_operation_relation', 'operation_id', 'appointment_id', 'Appointment', required=False),
        'import': fields.boolean('Imported', required=False), # TODO remove when imported!!!
        }
    _defaults = {
                'state': lambda *a: 'draft',
                'urgency': lambda *a: 'a',
                }        
dentist_operation()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
