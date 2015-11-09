# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class sql_move_line(osv.osv):
    ''' Add a back door for return if problems (
    '''
    _inherit = 'sql.move.line'
    
    def force_unification_partner(self, cr, uid, ids, context=None):
        ''' Force unification for partner double
            Re assign all movement line
        '''
        # Save original log partner in movement:        
        cr.execute( # Update only once:
            ''' UPDATE sql_move_line
                SET bugfix_old_id = partner_id 
                WHERE bugfix_old_id is null;
            ''')        
        return True        
        
    _columns = {
        'bugfix_old_id': fields.many2one('res.partner', 'Bugfix old ID'),
        }

class res_partner(osv.osv):
    ''' Add partner ref 
        Bugfix = record to delete (ref to original partner)
    '''
    _inherit = 'res.partner'
    
    _columns = {
        'bugfix_id': fields.many2one('res.partner', 'Bugfix ID'),        
        }
    
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
