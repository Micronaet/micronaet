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

class hr_employee_planner(osv.osv):
    _name = 'hr.employee.planner'
    _description = 'Planning of employee'    
    _rec_name = 'resource_id'

    def _get_plan_element(self, cr, uid, ids, fields, values, context=None):
        res = {}
        import pdb; pdb.set_trace()
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.employee_id.name
        return res

    _columns = {
        #'name': fields.char('Name', size=64, required=False, readonly=False),
        #  fields.function(_get_plan_element, method=True, type='char', size=32, string='Plan element', store=True),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True, ondelete='cascade'),
        'date': fields.datetime('Start date', required=True, help="Begin of the job session"),
        'duration': fields.float('Duration', help="Duration of job session"),
         
        'parent_id': fields.related('department_id', 'parent_id', relation='resource.resource', type='many2one', string='Manager', store=True),
        'department_id': fields.related('employee_id', 'department_id', relation='hr.department', type='many2one', string='Department', store=True),
        'resource_id': fields.related('employee_id','resource_id', type='many2one', relation='resource.resource', string='User'),        
        
        'from_timesheet':fields.boolean('From timesheet', required=False, help="If checked record comes from time machine"),        
        'date_real': fields.datetime('Start date (real)', help="Begin of the job session (real time)"),
        'duration_real': fields.float('Duration (real)', help="Duration of job session (real time)"), 

        'type':fields.selection([
            ('work','Work'),
            ('leave','Leave'),            
        ],'Type', select=True, readonly=False),
        #'date_deadline': lambda *a :  (datetime.now() + relativedelta(months=+1)).strftime("%Y-%m-%d %H:%M:%S")        
        }
    _defaults = {
                     'type': lambda *x: 'work',
                     'from_timesheet': lambda *x: False,
    }
hr_employee_planner()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
