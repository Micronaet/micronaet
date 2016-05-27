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

class MrpProductStatus(orm.Model):
    """ Model name:  MrpProductStatus(
    """    
    _name = 'mrp.product.status'
    _description = 'MRP product status'
    _rec_name = 'product_id'
    _order = 'product_id'
    
    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product', required=True), 
            
        # Stock status columns:
        'day_0': fields.float('Day 0', digits=(16, 3)),
        'day_1': fields.float('Day 1', digits=(16, 3)),
        'day_2': fields.float('Day 2', digits=(16, 3)),
        'day_3': fields.float('Day 3', digits=(16, 3)),
        'day_4': fields.float('Day 4', digits=(16, 3)),
        'day_5': fields.float('Day 5', digits=(16, 3)),
        'day_6': fields.float('Day 6', digits=(16, 3)),
        'day_7': fields.float('Day 7', digits=(16, 3)),
        
        # Manage line state:
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
