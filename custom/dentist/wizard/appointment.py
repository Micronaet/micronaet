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

from osv import fields, osv
from tools.translate import _

class dentist_appointment_wizard(osv.osv_memory):
    """ OpenERP osv memory wizard : dentist_appointment_wizard
    """    
    _name = 'dentist.appointment.wizard'
    _rec_name='next_date'
    
    def create_next_appointment(self, cr, uid, ids, context=None):
        #import pdb; pdb.set_trace()
        if context is None:
           context={}
           
        if "appointment_id" in context:
           appointment_id=context.get('appointment_id', False)
           
        wizard_browse=self.browse(cr, uid, ids, context=context)[0]
        appointment_pool=self.pool.get("dentist.appointment")
        appointment_browse=appointment_pool.browse(cr, uid, appointment_id, context=context)
        if appointment_browse:
           new_appointment={
                           'patient_id': appointment_browse.patient_id.id, 
                           'appointment_date': wizard_browse.next_date,
                           'duration': appointment_browse.duration, 
                           'note': appointment_browse.note, 
                           'user_id': uid, 
                           #'operation_ids': [6,0,[x.id for x in appointment_browse.operation_ids]],
                           'name': appointment_browse.name, 
                           'urgency': appointment_browse.urgency, 
                           'doctor_id': False, 
                           }
           next_app_id = appointment_pool.create(cr, uid, new_appointment, context=context)
           
        return {
                'name': _('Nuovo appuntamento'),
                'view_type': 'form',
                'view_mode': 'form,tree,calendar',
                'res_model': 'dentist.appointment',
                'res_id': next_app_id,
                #'view_id': False,
                #'views': [(form_id, 'form'), (tree_id, 'tree')],
                #'context': "{'type': 'out_invoice'}",
                'type': 'ir.actions.act_window',
               }
    _columns = {
        'next_date': fields.datetime('Date', required=True),
    }
dentist_appointment_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
