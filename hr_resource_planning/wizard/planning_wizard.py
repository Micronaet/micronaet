# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://axelor.com) All Rights Reserved.
# Copyright (c) 2010-2011 Micronaet  SRL. (http://www.micronaet.it) All Rights Reserved.
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
from datetime import datetime, timedelta

class hr_employee_planner_calendar(osv.osv):
    '''Rappresentazione del calendario delle singole ore in cui vengono rappresentate
       il numero di persone che sono al lavoro.   
    '''
    _name = 'hr.employee.planner.calendar'
    _description = 'Result Planning wizard'

    _columns = {
        'name': fields.char('Name', size=64, required=False, readonly=False),
        'date': fields.datetime('Start date', ), #required=True,),
        'duration': fields.float('Duration', digits=(4, 2)),
        'total': fields.integer('Total'),
        'covered': fields.integer('Covered'),
        'wizard_id': fields.integer('ID Wizard'),
        #'wizard_id': fields.many2one('hr_resource_planning.hr_employee_planner_wizard', 'Wizard ID', readonly=True, ), #required=True),
        }
        
    _defaults = {
        'duration': lambda *x: 1,
    }    
hr_employee_planner_calendar()

class hr_employee_planner_wizard(osv.osv_memory):
    ''' Wizard per scegliere i parametri del calendario da 
        utilizzare per il controllo copertura orario del dipartimento
    '''
    
    _name = 'hr.employee.planner.wizard'
    _description = 'Planning wizard'

    def open_calendar(self, cr, uid, ids, context=None):
       """
       This function load column.
       @param cr: the current row, from the database cursor,
       @param uid: the current users ID for security checks,
       @param ids: List of load column,
       @return: dictionary of query logs clear message window
       """
       
       if context is None:
          context = {}
            
       wizard_obj = self.browse(cr, uid, ids, context=context)[0] # solo uno

       calendar_pool=self.pool.get('hr.employee.planner.calendar')
       
       all_ids=calendar_pool.search(cr, uid, [], context=context) # cancello tutti gli elementi TODO rifinire!       
       calendar_pool.unlink(cr, uid, all_ids, context=context) # cancello tutti gli elementi TODO rifinire!
       
       from_date=datetime.strptime(wizard_obj.from_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")     
       to_date=datetime.strptime(wizard_obj.to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")     
       
       total_workers=3 # da rilevare
       current_date=from_date
       
       first=True
       while current_date <= to_date:
             if first: # all'ingresso inizializzo le variabili di controllo
                first=False
                last_total_workers=total_workers
                last_duration = 0.0
                last_day=datetime.strptime(current_date, "%Y-%m-%d")
             
             # controllo rottura di codice: sia totale lavoratori che giorno (entrambe devono essere vere per continuare)   
             if (last_total_workers == total_workers) and (last_day == datetime.strptime(current_date, "%Y-%m-%d")): # continua l'orario precedente (stesso numero di lavoratori)
                last_duration += 1.0 # continuo ad incrementare
             else: # Scrivo il record per rottura codice
                last_total_workers = total_workers # memorizzo per eventuale rottura di codice lavoratori
                last_day=datetime.strptime(current_date, "%Y-%m-%d") # memorizzo per eventuale rottura di codice per giorno
                record_calendar = {
                                  'date': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                                  'duration': last_duration,
                                  'name': "",
                                  'total': total_workers,
                                  'covered': total_workers - wizard_obj.treshold,
                                  'wizard_id': ids[0] or 0,
                               }
                new_id=calendar_pool.create(cr, uid, record_calendar, context=context)             
                last_duration = 1.0
             current_date = current_date + timedelta(hours = 1)
       if not first: # è entrato nel ciclo almeno una volta (scrivo l'ultimo elemento)
          record_calendar = {
                          'date': current_date.strftime('%Y-%m-%d %H:%M:%S'),
                          'duration': last_duration,
                          'name': "",
                          'total': total_workers,
                          'covered': total_workers - wizard_obj.treshold,
                          'wizard_id': ids[0] or 0,
                          }
          new_id=calendar_pool.create(cr, uid, record_calendar, context=context)             

       #import pdb; pdb.set_trace()     
       data_obj = self.pool.get('ir.model.data')
       form_id = data_obj._get_id(cr, uid, 'hr_resource_planning', 'hr_employee_planner_calendar_form')
       cal_id  = data_obj._get_id(cr, uid, 'hr_resource_planning', 'hr_employee_planner_calendar_calendar')
       tree_id = data_obj._get_id(cr, uid, 'hr_resource_planning', 'hr_employee_planner_calendar_tree')
       if form_id:
          form_id = data_obj.browse(cr, uid, form_id, context=context).res_id
       if cal_id:
          cal_id  = data_obj.browse(cr, uid, cal_id , context=context).res_id
       if tree_id:
          tree_id = data_obj.browse(cr, uid, tree_id, context=context).res_id
                
       value = {
            'view_type': 'form',
            'view_mode': 'calendar, form, tree',
            'res_model': 'hr.employee.planner.calendar',
            'views': [(cal_id, 'calendar'),(form_id, 'form'), (tree_id, 'tree'),],
            #'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            #'context': {'active_ids': [ids],}, #'from_date': search_obj[0].from_date, 'to_date': search_obj[0].to_date, 'department_id': search_obj[0].department_id.id or 0}
            #'domain': "[('wizard_id', '=', %s)]" % ids[0] or 0,            
       }
       return value
       
    _columns = {
        'from_date': fields.datetime('Start date', required=True, help="Start date of verify calendar"),
        'to_date': fields.datetime('End date', required=True, help="End date of verify calendar"),
        'treshold': fields.integer('Minimum treshold'),
        'department_id':fields.many2one('hr.department', 'Department', required=True),
        
        #'type':fields.selection([
        #    ('work','Work'),
        #    ('leave','Leave'),            
        #],'Type', select=True, readonly=False),
        }
        
    _defaults = {
                 'from_date': lambda *x: datetime.now(), #.strftime('%Y-%m-%d %H:%M:%S'),
                 'to_date': lambda *x: datetime.now(), #+ relativedelta(months=+1)).strftime("%Y-%m-%d %H:%M:%S"),
                 'treshold': lambda *x: 1,                  
                 }    
                 
    #'date_to': lambda *a: (datetime.now()+relativedelta(months=1, day=1, days=-1)).strftime('%Y-%m-%d'),             
                 
hr_employee_planner_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
