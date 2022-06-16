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


class SafetySymbol(orm.Model):
    """ Model name: SafetySymbol
    """

    _name = 'safety.symbol'
    _description = 'Safety symbol'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'image': fields.binary('Image', filters=None),
        'note': fields.text('Note'),
        }


class SafetySymbolTemplate(orm.Model):
    """ Model name: Safety Symbol Template
    """

    _name = 'safety.symbol.template'
    _description = 'Safety symbol template'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'symbol_ids': fields.many2many(
            'safety.symbol', 'template_safety_rel',
            'template_id', 'symbol_id',
            'Symbol'),
        'note': fields.text('Note'),
        }


class SafetyH(orm.Model):
    """ Model name: Safety H
    """

    _name = 'safety.H'
    _description = 'Safety H'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Nome H', size=64, required=True),
        'note': fields.text('Descrizione'),
        }


class SafetyP(orm.Model):
    """ Model name: Safety P
    """

    _name = 'safety.P'
    _description = 'Safety P'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Nome P', size=64, required=True),
        'note': fields.text('Descrizione'),
        }


class SafetyDPI(orm.Model):
    """ Model name: Safety DPI
    """

    _name = 'safety.DPI'
    _description = 'Safety DPI'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('Nome DPI', size=64, required=True),
        'note': fields.text('Descrizione'),
        }


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """

    _inherit = 'product.product'

    _columns = {
        'security_template_id': fields.many2one(
            'safety.symbol.template', 'Modello sicurezza'),

        'H_ids': fields.many2many(
            'safety.H', 'product_H_rel',
            'template_id', 'H_id',
            'H'),
        'P_ids': fields.many2many(
            'safety.P', 'product_P_rel',
            'template_id', 'P_id',
            'P'),
        'DPI_ids': fields.many2many(
            'safety.DPI', 'product_DPI_rel',
            'template_id', 'DPI_id',
            'DPI'),
        }
