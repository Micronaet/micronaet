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
        # Read customer for get convert dictionary:
        customer_ids = self.search(cr, uid, [
            ('sql_customer_code', '!=', False),
            ('sql_import', '=', True),
            ('type', '=', 'default'),            
            ], context=context)
        customer_db = {}
        for customer in self.browse(cr, uid, customer_ids, 
                context=context):
            customer_db[customer.sql_customer_code] = customer.id
        import pdb; pdb.set_trace()    
            
        # Read customer for get convert dictionary:
        supplier_ids = self.search(cr, uid, [
            ('sql_supplier_code', '!=', False),
            ('sql_import', '=', True),
            ('type', '=', 'default'),            
            ], context=context)
        supplier_db = {}
        for supplier in self.browse(cr, uid, supplier_ids, 
                context=context):
            supplier_db[customer.sql_supplier_code] = supplier.id
        import pdb; pdb.set_trace()    
            
        # Read customer for unlink:
        destination_ids = self.search(cr, uid, [ # TO remove
            ('sql_destination_code', '!=', False),
            ('sql_import', '=', True),
            ('type', '=', 'contact'),
            ], context=context)
        import pdb; pdb.set_trace()    
        for destination in self.browse(cr, uid, destination_ids, 
                context=context):
            # Save changed ID:
            code = destination.sql_destination_code
            data = {}
            if code and code in customer_db:
                data.update({
                    'name': '[RIMUOVERE] %s' % destination.name,
                    #'active': False,
                    'bugfix_id': customer_db[code],
                    })
            else:
                if code and code in supplier_db:
                    data.update({
                        'name': '[RIMUOVERE] %s' % destination.name,
                        #'active': False,
                        'bugfix_id': supplier_db[code],
                        })
            if data:            
                self.write(cr, uid, destination.id, data, context=context)    

        # Update all lines from destination to client or supplier:
        # TODO                
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
