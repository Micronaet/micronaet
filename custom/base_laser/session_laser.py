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

class training_session_baselecturer(osv.osv):
    '''This object permit to link to the session a base model that that link to a session a particular week.
       The next week are repeated.'''
    
    _name = 'training.session.baselecturer'
    
    _columns= {
              'name': fields.char('Descrizione settimana tipo', size=32, required=False),
              #'session_id' : fields.many2one('training.session', 'Edizione', select=1, required=True),
              #'course_id': fields.many2one('training.course', 'Modulo', required=True),  
              'base_lecturer_id': fields.many2one('res.partner.job', 'Docente', help="Docente che tiene il corso",),
              }             
training_session_baselecturer()
    
class training_session_baseweek(osv.osv):
    '''This object permit to link to the session a base model week calendar for plan the seances. After confirmed
       the create seance function replicate all indicated seance for all planned session.
       This object permit also to manage a view with total planned hours (for a best plan)'''
    
    _name='training.session.baseweek'
    
    _columns={
             'name': fields.char('Descrizione lezione tipo', size=32, required=False),
             #'session_id' : fields.many2one('training.session', 'Edizione origine'), #, ondelete='cascade'),
             'date' : fields.datetime('Date', required=True, select=1, help="Data settimanale della lezione"),
             'duration' : fields.float('Duration', select=1, help="Durata della lezione"),
             #'course_id' : fields.many2one('training.course', 'Modulo', select=1),
             }
training_session_baseweek()

