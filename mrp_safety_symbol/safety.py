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
        'code': fields.char('Codice', size=10),
        'name': fields.char('Name', size=64, required=True),
        'image': fields.binary('Image', filters=None),
        'note': fields.text('Note'),
        'mode': fields.selection([
            ('equipment', 'Attrezzatura'),
            ('danger', 'Pericolosità')
        ], 'Modalità', required=True)
        }

    _defaults = {
        'mode': lambda *x: 'equipment',
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

    _name = 'safety.h'
    _description = 'Safety H'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char(
            'H: Particolarità prodotto', size=64, required=True),
        'note': fields.text('Descrizione particolarità prodotto'),
        }


class SafetyP(orm.Model):
    """ Model name: Safety P
    """

    _name = 'safety.p'
    _description = 'Safety P'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('P: Comportamento', size=64, required=True),
        'note': fields.text('Descrizione comportamento da tenere'),
        }


class SafetyDPI(orm.Model):
    """ Model name: Safety DPI
    """

    _name = 'safety.dpi'
    _description = 'Safety DPI'
    _rec_name = 'name'
    _order = 'name'

    _columns = {
        'name': fields.char('DPI: Dotazione', size=64, required=True),
        'note': fields.text('Descrizione dotazione personale'),
        }


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """

    _inherit = 'product.product'


    _columns = {
        'security_off': fields.boolean(
            'Non pericoloso',
            help='Indica che la materia prima non è da considerarsi '
                 'pericolosa quindi nella scheda di produzione non '
                 'viene indicata nella tabella riepilogativa'),
        'security_template_id': fields.many2one(
            'safety.symbol.template', 'Modello di sicurezza'),

        # Mandatory for equipmeny:
        'protection_eye_id': fields.many2one(
            'safety.symbol', 'Protezione occhi',
            domain="[('mode', '=', 'equipment')]"),
        'protection_skin_id': fields.many2one(
            'safety.symbol', 'Protezione pelle',
            domain="[('mode', '=', 'equipment')]"),
        'protection_hand_id': fields.many2one(
            'safety.symbol', 'Protezione mani',
            domain="[('mode', '=', 'equipment')]"),
        'protection_air_id': fields.many2one(
            'safety.symbol', 'Protezione respiratoria',
            domain="[('mode', '=', 'equipment')]"),
        'protection_body_id': fields.many2one(
            'safety.symbol', 'Protezione tuta',
            domain="[('mode', '=', 'equipment')]"),
        'protection_foot_id': fields.many2one(
           'safety.symbol', 'Protezione scarpe',
           domain="[('mode', '=', 'equipment')]"),

        'protection_eye_text': fields.text('Protezione occhi'),
        'protection_skin_text': fields.text('Protezione pelle'),
        'protection_hand_text': fields.text('Protezione mani'),
        'protection_air_text': fields.text('Protezione respiratoria'),
        'protection_body_text': fields.text('Protezione tuta'),
        'protection_foot_text': fields.text('Protezione scarpe'),

        'symbol_ids': fields.many2many(
           'safety.symbol', 'safety_symbol_danger_rel',
           'product_id', 'simbol_id',
           'Pittogrammi'),

        'term_h_ids': fields.many2many(
           'safety.h', 'safety_h_rel',
           'product_id', 'term_h_id',
           'Termini H'),
        'term_p_ids': fields.many2many(
            'safety.p', 'safety_p_rel',
            'product_id', 'term_p_id',
            'Termini P'),
        'term_dpi_ids': fields.many2many(
            'safety.dpi', 'safety_dpi_rel',
            'product_id', 'term_dpi_id',
            'Termini DPI'),
    }
