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
import netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta        
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)


class loan_header(orm.Model):
    ''' Header of Loan element
    '''
    _name = 'loan.header'
    _description = 'Account loan'

    # -------------
    # Button event:
    # -------------
    def generate_plan(self, cr, uid, ids, context=None):
        ''' Generate plan of rates 
        '''
        # Delete previuos rate
        rate_pool = self.pool.get("loan.rate")
        rate_ids = rate_pool.search(cr, uid, [
            ('loan_id', '=', ids[0]),
            #('rate_type', '=', 'normal'),
            ], context=context)
        rate_pool.unlink(cr, uid, rate_ids, context=context)

        loan_proxy = self.browse(cr, uid, ids, context=context)[0]

        # More readeable values:        
        C = loan_proxy.loan_amount
        i = loan_proxy.rate / 100.0
        n = loan_proxy.period
        
        # Calculated value:
        R = C * i / (1.0 - (1.0 + i) ** (-n))
        Res = C # Initial capital (for remain capital)
        
        start_date = datetime.strptime(
            loan_proxy.start_date, DEFAULT_SERVER_DATE_FORMAT)
        if loan_proxy.loan_period == 'month':
            month_x_period = 1
        elif loan_proxy.loan_period == 'bimestral':
            month_x_period = 2
        elif loan_proxy.loan_period == 'trimestral':
            month_x_period = 3
        elif loan_proxy.loan_period == 'quadrimestral':
            month_x_period = 4
        elif loan_proxy.loan_period == 'semestral':
            month_x_period = 6
        elif loan_proxy.loan_period == 'year':
            month_x_period = 12
            
        for period in range(0, n):
            current_date = start_date + relativedelta(
                months=month_x_period * period)
            rate_date = current_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            I = Res * i
            Res -= (R - I)
            rate_pool.create(cr, uid, {
                'name': period + 1,
                'loan_id': loan_proxy.id,
                'rate_date': rate_date,
                'currency_date': rate_date, # Depend on bank
                'rate_amount': R,
                'rate_type': 'normal',
                'capital': R - I, # (Rate - Interest)
                'interest': I,
                'remain': Res,
                'rate': loan_proxy.rate,
                }, context=context)
        return True
        
    # ----------------
    # Workflow method:
    # ----------------
    def wkf_loan_draft(self, cr, uid, ids, context=None):
        ''' State function for draft
        '''
        self.write(cr, uid, ids, {
            'state': 'draft', }, context=context)
        return True

    def wkf_loan_confirmed(self, cr, uid, ids, context=None):
        ''' State function for confirmed
        '''
        self.write(cr, uid, ids, {
            'name': self.pool.get('ir.sequence').get(cr, uid, 'loan.header'),
            'confirmed_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'confirmed',
            }, context=context)
        return True

    def wkf_loan_approved(self, cr, uid, ids, context=None):
        ''' State function for approved
        '''
        self.write(cr, uid, ids, {
            'approve_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'approved', 
            }, context=context)
        return True

    def wkf_loan_close(self, cr, uid, ids, context=None):
        ''' State function for close
        '''
        self.write(cr, uid, ids, {
            'close_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'close', 
            }, context=context)
        return True

    def wkf_loan_cancel(self, cr, uid, ids, context=None):
        ''' State function for cancel
        '''
        self.write(cr, uid, ids, {
            'cancel_date': datetime.now().strftime(
                 DEFAULT_SERVER_DATE_FORMAT),
            'state': 'cancel', 
            }, context=context)
        return True

    # ---------------
    # Field function:
    # ---------------
    def _calculate_total_header(self, cr, uid, ids, fields, args, context=None):
        ''' Calculate for, header view, total of interest and total of C + I
        '''
        res = {}
        for loan in self.browse(cr, uid, ids, context=context):
            res[loan.id] = {}
            
            interest = 0.0
            capital = 0.0
            payed = 0.0
            for rate in loan.rate_ids:
                interest += rate.interest
                capital += rate.capital
                if rate.state == 'payed':
                    payed += rate.rate_amount
                
            res[loan.id]['total_interest'] = interest
            res[loan.id]['total_amount'] = capital + interest
            res[loan.id]['total_payed'] = payed
        return res
    
    _columns = {
        # Loan description:
        'name': fields.char('Ref.', help="Code for reference"), # By workflow
        'description': fields.char('Description', size=128, 
            help="Extra description for loan element"),
        'partner_id': fields.many2one('res.partner', 'Partner', 
            help='Partner that open loan or that is referred to',
            required=True),
        'bank_id': fields.many2one('res.partner.bank', 'Bank', 
            help="Bank reference for this loan, depend on partner", ),
        'guarantor_id': fields.many2one('res.partner', 'Gaurantor',
            help='Partner that is garantor for the loan '
                '(only for statistic purposes'),
        'note': fields.text('Note'),
        
        # Loan descriptiove information:
        'method':fields.selection([
            ('french', 'French'),
            ('italian', 'Italian'),
            ('german', 'German'),
            ('american', 'American'),
            ('variable', 'Variable duration'), ], 'Method', required=True),       
        'loan_type':fields.selection([
            ('early', 'Loan early'),
            ('postponed', 'Load postponed'), ], 'Loan Type', required=True),            
        'loan_period':fields.selection([
            ('month', 'Monthly'),
            ('bimestral', 'Bimestral'),
            ('trimestral', 'Trimestral'),
            ('quadrimestral', 'Quadrimestral'),
            ('semestral', 'Semestral'),
            ('year', 'Year'), ],'Loan Period', required=True),
        'return_type': fields.selection([
            ('cash','By Cash'),
            ('cheque','By Cheque'),
            ('automatic','Automatic Payment'), ],'Payment Type'),
        #'rate_type': fields.selection([
        #    ('flat','Flat'),
        #    ('reducing','Reducing'), ],'Rate Type'),
        'rate_period': fields.selection([
            ('annual', 'Annual'),
            ('match', 'Match with loan period'), ],
            'Rate period',
            help="If rate is referred to annual value or to the "
                "choosen period (in this case is recalculated", ),

        # Loan technical data:
        'loan_amount': fields.float(
            'Capital', 
            digits=(12, 2), 
            required=True),
        'rate': fields.float(
            'Interest rate', 
            digits=(12, 2), 
            help="Rate for calculate interess",
            required=True),
        'period': fields.integer('Periods', required=True),

        # Date elements (used in workflow):
        'start_date': fields.date('Start Date'),
        'request_date': fields.date('Request Date', readonly=True),
        'confirmed_date': fields.date('Confirmed Date', readonly=True),
        'approve_date': fields.date('Approve Date', readonly=True),
        'close_date': fields.date('Close Date', readonly=True),
        'cancel_date': fields.date('Cancel Date', readonly=True),

        'analytic_account': fields.many2one('account.analytic.account',
            type='many2one',
            string="Analytic Account",
            help="Account for analytic entries",
            ),

        # Calculated fields:
        # TODO convert in functions:
        'total_interest': fields.function(
            _calculate_total_header,
            string='Total Interest', 
            method=True, type='float', digits=(12, 2),
            store=False,
            multi='total',
            readonly=True),
        'total_amount': fields.function(
            _calculate_total_header,
            string='Total amount', 
            method=True, type='float', digits=(12, 2),
            store=False,
            multi='total',
            readonly=True),
        'total_payed': fields.function(
            _calculate_total_header,
            string='Total payed', 
            method=True, type='float', digits=(12, 2),
            store=False,
            multi='total',
            readonly=True),
        # end_date function

        # Workflow:
        'state': fields.selection([
            ('draft','Draft'),         # Draft state, to complete
            ('confirmed','Confirmed'), # Confirm information
            ('approved','Approved'),   # Approved from responsible
            ('close','Close'),         # End of life of loan
            ('cancel','Reject'),       # Not approved
            ],'State', readonly=True, select=True),
        }
        
    _defaults = {
        'start_date': lambda *a: datetime.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT),
        'request_date': lambda *a: datetime.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT),
        'loan_type': lambda *x: 'postponed',
        'return_type': lambda *a: 'cash',
        'method': lambda *a: 'french',
        'loan_period': lambda *a: 'month',
        'rate_period': lambda *a: 'match',
        'state': lambda *a: 'draft',
        }

class loan_rate(orm.Model):
    ''' Rate of Loan element
    '''
    _name = 'loan.rate'
    _description = 'Account loan rate'
    _order = 'loan_id,rate_date,name'

    # ---------
    # Override:
    # ---------
    def name_get(self, cr, uid, ids, context=None): 
        ''' Present foreing ke with loan name . rate name
        '''
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        res = []
        for record in self.browse(cr, uid, ids, context=context):
            name = "%s.%s [%s]" % (
                record.loan_id.name, 
                record.name or "x",
                record.rate_date, )
            res.append((record.id, name))
        return res
        
    # ----------------
    # Workflow method:
    # ----------------
    def wkf_rate_confirmed(self, cr, uid, ids, context=None):
        ''' State function for confirmed
        '''
        self.write(cr, uid, ids, {
            'state': 'confirmed', }, context=context)
        return True

    def wkf_rate_payed(self, cr, uid, ids, context=None):
        ''' State function for confirmed
        '''
        self.write(cr, uid, ids, {
            'state': 'payed', 
            'pay_date': datetime.now().strftime(
                DEFAULT_SERVER_DATE_FORMAT),
            # pay_amount    
            }, context=context)
        return True

    def wkf_rate_cancel(self, cr, uid, ids, context=None):
        ''' State function for confirmed
        '''
        self.write(cr, uid, ids, {
            'state': 'cancel', 
            'cancel_date': datetime.now().strftime(
                DEFAULT_SERVER_DATE_FORMAT),
            }, context=context)
        return True
        
    _columns = {
        # Loan description:
        'name': fields.integer('Ref.', help="Code for reference for rate"),
        
        # Operation date:
        'rate_date': fields.date('Rate Date'),
        'pay_date': fields.date('Pay Date'),        
        'cancel_date': fields.date('Cancel Date'),
        'currency_date': fields.date('Currency Date'),
        
        'rate_amount': fields.float('Amount', digits=(12, 2)),
        'pay_amount': fields.float('Pay amount', digits=(12, 2), 
            help="If import is different from correct rate"),
        
        # Rate import information:
        'capital': fields.float('Capital', digits=(12, 2), readonly=True),
        'interest': fields.float('Interest', digits=(12, 2), readonly=True),
        'remain': fields.float('Remain', digits=(12, 2), readonly=True),
        # Rate?

        'rate_type': fields.selection([
            ('normal', 'Normal'),           # Normal calculated rate
            ('integration', 'Integration'), # Integration rate (for interest)
            ],'Rate type', readonly=True, select=True),
        'rate': fields.float(
            'Rate applied', 
            digits=(12, 2), 
            help="Rate applied (changeable by wizard via header)",
            required=True),

        'loan_id': fields.many2one('loan.header', 'Loan',
            ondelete='cascade'),

        # Related form header:
        'partner_id': fields.related(
            'loan_id',
            'partner_id', 
            type='many2one', 
            relation='res.partner', 
            string='Partner',
            store=True),
        'bank_id': fields.related(
            'loan_id',
            'bank_id', 
            type='many2one', 
            relation='res.partner.bank', 
            string='Bank',
            store=True),
        'guarantor_id': fields.related(
            'loan_id',
            'guarantor_id', 
            type='many2one', 
            relation='res.partner', 
            string='Guarantor',
            store=True),
        'analytic_account': fields.related(
            'loan_id',
            'analytic_account', 
            type='many2one', 
            relation='account.analytic.account', 
            string='Analitic account',
            store=True),
        
        # Workflow:
        'state': fields.selection([
            ('confirmed','Confirmed'), # Confirmed (on create)
            ('payed','Payed'),         # Payed (close rate)
            ('cancel','Cancel'),       # Cancel (for deletion use)
            ],'State', readonly=True, select=True),
        }
        
    _defaults = {
       'rate_type': lambda *x: 'integration',
       'state': lambda *x: 'confirmed',
        }    
    
class loan_header_rate(orm.Model):
    ''' Header of Loan rate element
        Changing of rate in loan header elements 
        (loaded from wizard)
    '''
    _name = 'loan.header.rate'
    _description = 'Loan change rates'
    _rec_name = 'rate'
    _order = 'rate_id'
    
    _columns = {
        'rate': fields.float('Rate', digits=(12, 2)),
        'rate_id': fields.many2one('loan.rate', 'From rate #', 
            ondelete='cascade'),
        'rate_period': fields.selection([
            ('annual', 'Annual'),
            ('match', 'Match with loan period'), ],
            'Rate period',
            help="If rate is referred to annual value or to the "
                "choosen period (in this case is recalculated", ),
        'loan_id': fields.many2one('loan.header', 'Loan', 
            ondelete='cascade'),        
        'note': fields.text('Note'),
        }
        
    _sql_constraints = [(
        'load_header_rate_change_unique', 
        'unique(loan_id,rate_id)', 
        'Change rate already setted for this period',
        )]
    
class loan_header(orm.Model):
    ''' Rate of Loan element
    '''
    _name = 'loan.header'
    _inherit = 'loan.header'    
    
    _columns = {
        'rate_ids': fields.one2many('loan.rate', 'loan_id', 'Plan rate',),
        'rate_change_ids': fields.one2many('loan.header.rate', 'loan_id', 
            'Change of rate', ),
        }

class res_partner_loan(orm.Model):
    ''' Add extra relation to partner obj
    '''
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    _columns = {
        'loan_ids': fields.one2many('loan.header', 'partner_id', 'Loan'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
