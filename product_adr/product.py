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
import openerp.netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class product_product_duty(osv.osv):
    ''' Extra fields for ETL in product.product
    ''' 
    _name = 'product.product.duty'
    _description = 'Product for duty'
    
    _columns = {
        'name': fields.char('Duty code', required=True, 
            help="Coded used for duty import / export"),
        'note': fields.text('Duty specific'),
    }
    
class product_product_adr(osv.osv):
    ''' Extra fields for ETL in product.product
    ''' 
    _name = 'product.product'
    _inherit = 'product.product'
    
    _columns = {
        'adr':fields.boolean('ADR', required=False, 
            help="Product that need ADR for transport"),
        'duty_id': fields.many2one('product.product.duty', 'Duty'),
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
