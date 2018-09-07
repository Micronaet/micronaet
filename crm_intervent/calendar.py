# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare,
    )
from openerp.osv.fields datetime as datetime_field


_logger = logging.getLogger(__name__)


class crm_meeting_relation_fields(osv.osv):
    """ CRM meeting extra field for send relation about appointment
    """
    _name = 'crm.meeting'    
    _inherit = 'crm.meeting'
    
    '''def formatLang(self, cr, uid, value, date=False, datetime=False, 
            context=None):
        """ Convert datetime with TZ
        """
        if context is None:
            context = {
                'lang': 'it_IT',
                }

        DEFAULT_SERVER_TIME_FORMAT = 'HH:MM:SS'
        if not value:
            return ''

        if datetime:
            value = value.split('.')[0]
            date_format = '%s %s' % (
                DEFAULT_SERVER_DATETIME_FORMAT,
                DEFAULT_SERVER_TIME_FORMAT,
                )
            parse_format = DEFAULT_SERVER_DATETIME_FORMAT
            # Convert datetime values to the expected client/context timezone
            date = datetime_field.context_timestamp(
                cr, uid, timestamp=date, context=context)#self.localcontext)
        else:    
            date_format = DEFAULT_SERVER_DATE_FORMAT
            parse_format = DEFAULT_SERVER_DATE_FORMAT
            date = datetime(*value.timetuple()[:6])
        return date.strftime(date_format.encode('utf-8'))'''

    # Workflow trigger action ##################################################
    def meeting_draft(self, cr, uid, ids):
        ''' Activity when a new crm.meeting is created
        '''
        self.write(cr, uid, ids, { 'state': 'draft',})
        return True

    def meeting_confirmed(self, cr, uid, ids):
        ''' Activity when a meeting is confirmed without relation at the end
        '''
        self.write(cr, uid, ids, { 'state': 'confirmed' })
        return True

    def meeting_confirmed_relation(self, cr, uid, ids):
        ''' Activity when a crm.meeting is confirmed and relation in necessary
        '''
        self.write(cr, uid, ids, { 'state': 'relation', 
                                   'relation_needed': True, })
        return True

    def meeting_close(self, cr, uid, ids):
        ''' Activity when meeting is close
        '''
        self.write(cr, uid, ids, { 'state': 'close'})
        return True

    # Button action ############################################################
    def action_relation_send(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'crm_intervent', 'email_crm_interven_relation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict(context)
        ctx.update({
            'default_model': 'crm.meeting',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    _columns = {
        'relation_manager_id':fields.many2one('res.partner', 'Relation manager', domain=[('is_company','=',False)], required=False),
        'relation_partner_id':fields.many2one('res.partner', 'Relation partner', domain=[('is_company','=',True)], required=False),
        'relation_needed':fields.boolean('Need relation', required=False),
        'relation_department': fields.char('Department', size=64, required=False, readonly=False),
        'relation_ref': fields.char('Referent', size=64, required=False, readonly=False),
        'relation_supervisor': fields.char('Supervisor', size=64, required=False, readonly=False),
        'relation_supervisor_position': fields.char('Superv. position', size=64, required=False, readonly=False),
        'relation_goal': fields.text('Goal', help="Goal during evaluation period"),
        'relation_result': fields.text('Result', help="Result and responsability (employee part)"),
        'relation_evaluation': fields.text('Evaluation', help="Supervisor evaluation"),
        'relation_strength': fields.text('Strength', help="Strength point and powerfull area"),
        'relation_plan': fields.text('Svil. plan',),
        'relation_goal_future': fields.text('Goal for next period',),
        
        'state':fields.selection([
                ('draft','Draft'),
                ('confirmed','Confirmed'),
                ('relation','Confirmed with rel.'),
                ('close','Close'),            
        ],'State', select=True, readonly=True),
    }
    
    _defaults = {
        'state': lambda *a: 'draft',
        'relation_needed': lambda *a: False,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
