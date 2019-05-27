#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
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

class MrpProductionPrevisional(orm.Model):
    """ Model name: MrpProductionPrevisional
    """
    
    _name = 'mrp.production.previsional'
    _description = 'Previsional order'
    _rec_name = 'product_id'
    _order = 'production_date'
    
    _columns = {
        'production_date': fields.date('Date production', required=True),
        'product_id': fields.many2one(
            'product.product', 'Product', required=True),
        'uom_id': fields.related(
            'product_id', 'uom_id', 
            type='many2one', relation='product.uom', string='UM', 
            readonly=True),    
        'qty': fields.float('Q.ty (Kg.)', digits=(16, 3), required=True),
        'bom_id': fields.many2one('mrp.bom', 'BOM', required=True),
        'state': fields.selection([
            ('draft', 'New order'),
            ('used', 'Used for purchase (done)'),
            ], 'State', readonly=True),
        #'purchase_id': fields.many2one('mrp.bom', 'BOM', required=True),
        }
    _defaults = {
        'state': lambda *x: 'draft',
        }        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
