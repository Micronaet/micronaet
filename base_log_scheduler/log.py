# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

from openerp.osv import osv, fields
from datetime import datetime

class log_activity(osv.osv):
    ''' Log activity recorded on scheduled operations
    '''
    _name="log.activity"
    _description="Log Activity"

    def log_info(self, cr, uid, name, note, context=None):
        ''' Log an info for activity name
        '''
        return self.create(cr, uid, {'name': name,
                                     'note': note,
                                     'type': 'info',}, context=context)
                                     
    def log_warning(self, cr, uid, name, note, context=None):
        ''' Log an warning for activity name
        '''
        return self.create(cr, uid, {'name': name,
                                     'note': note,
                                     'type': 'warning',}, context=context)
                                     
    def log_error(self, cr, uid, name, note, context=None):
        ''' Log an error for activity name
        '''
        return self.create(cr, uid, {'name': name,
                                     'note': note,
                                     'type': 'error',}, context=context)
        
        
    _columns = {
        'name': fields.char("Name", size=64, help="Identiy the schedule operation with a name", required=True),
        'date': fields.datetime("Date"),
        'note': fields.text("Note", help="Extended log of operation"),
        'type': fields.selection([('info','Information'),('warning','Warning'),('error','Error')], "Type", select=True, readonly="False"),
    }

    _defaults = {
         'date': lambda *x: datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    }          
log_activity()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
