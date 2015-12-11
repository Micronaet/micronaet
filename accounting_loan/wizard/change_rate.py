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
from openerp.osv import osv, fields
import shutil
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class loan_change_rate_wizard(osv.osv_memory):
    ''' Change rate wizard:
        Insert a new rate and recalculate rate from # selected
    '''
    _name = 'loan.change.rate.wizard'
    _description = 'Change rate'

    # -------------
    # Button event: 
    # -------------
    def action_change_button(self, cr, uid, ids, context=None):
        ''' Change button
        '''
        wizard_proxy = self.browse(cr, uid, ids, context=context)[0]
        change_rate_pool = self.pool.get("loan.header.rate")
        rate_pool = self.pool.get("loan.rate")
        
        # TODO Verificare che non ci siano altri cambi dopo questo periodo
        # TODO Verificare che non ci siano periodi pagati dopo questa data
        
        # Read wizard value:
        rate = wizard_proxy.rate
        rate_id = wizard_proxy.rate_id.id
        loan_id = context.get("loan_id", False)
        rate_period = wizard_proxy.rate_period
        rate_name = wizard_proxy.rate_id.name
        
        # Insert record:
        change_rate_pool.create(cr, uid, {
            'rate': rate,
            'rate_id': rate_id,
            'loan_id': loan_id,
            'rate_period': rate_period, # match or annual
            }, context=context)
        
                    
        # Update rate capital and interest:
        rate_ids = rate_pool.search(cr, uid, [
            ('loan_id', '=', loan_id),    # This loan header
            ('name', '>=', rate_name),   # >= start rate period
            ('rate_type', '=', 'normal'), # Only rate (no corrections)
            ], context=context)
            
        if not rate_ids:
            raise osv.except_osv(_("Error!"), _("No rate to modify"))
            return True

        rate_proxy = rate_pool.browse(cr, uid, rate_ids[0], context=context) # first
        
        # TODO controllare i calcolo!!!!!!!
        # Set start value to current rate:
        C = rate_proxy.remain # residual
        n = len(rate_ids) - 1.0
        i = rate / 100.0
        
        # Calculated value:
        R = C * i / (1.0 - (1.0 + i) ** (-n))
        Res = C # Initial capital (for remain capital)
        
        for item_id in rate_ids:
            if item_id == rate_ids[0]: 
                continue # jump first element (was last)
            
            I = Res * i
            Res -= (R - I)
            rate_pool.write(cr, uid, item_id, {
                'rate_amount': R,
                'capital': R - I, # (Rate - Interest)
                'interest': I,
                'remain': Res,
                'rate': rate,
                }, context=context)
        return True
        
    _columns = {
        'rate': fields.float('Rate', digits=(12, 2), required=True),
        'rate_id': fields.many2one('loan.rate', 'Last rate #', 
            required=True,
            help='Last rate before change (this rate use old interest rate)'),
        'rate_period': fields.selection([
            ('annual', 'Annual'),
            ('match', 'Match with loan period'), ],
            'Rate period',
            required=True,
            help="If rate is referred to annual value or to the "
                "choosen period (in this case is recalculated", ),
        
        }
    _defaults = {
        'rate_period': lambda *x: 'match',
        }
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
