# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
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
import netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
#import time
from dateutil.relativedelta import relativedelta


class dentist_web_wizard(osv.osv_memory):
    ''' Object that manage the request of demo on the web
    '''
    _name = 'dentist.web.wizard'

    def save_contact(self, cr, uid, ids, context=None):
        ''''''
        return True

    _columns = {
        'name': fields.char('Company', size = 100, required=True),
        'email': fields.char('E-mail sender', size = 100, required=True),
        'support_contact': fields.char('Support contact', size = 100),
        'phone': fields.char('Phone number', size = 20),
        'req_desc': fields.text('Request description', required=True),
        'contacted': fields.char('If you would like, you fill in the following fields'),
    }

    _defaults = {
        'contacted': lambda *a: 'Se desiderate essere contattati telefonicamente, compilate i seguenti campi:',
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
