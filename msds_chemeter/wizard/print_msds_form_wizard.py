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
import pdb
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class MsdsPrintFormWizard(orm.TransientModel):
    """ Wizard for print MSDS from Chemeter
    """
    _name = 'msds.print.form.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_print(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        chemeter_pool = self.pool.get('msds.chemeter')
        if context is None: 
            context = {}        
        
        wizard = self.browse(cr, uid, ids, context=context)[0]
        mixture = wizard.mixture
        alias = wizard.alias
        language = wizard.language_id

        # Try to search in MDSD
        chemeter_ids = chemeter_pool.search(cr, uid, [
            ('name', '=', mixture),
            ('alias', '=', alias),
            ('language_id', '=', language.id),
        ], context=context)

        if chemeter_ids:
            chemeter_id = chemeter_ids[0]
        else:
            chemeter_id = chemeter_pool.create(cr, uid, {
                'manual': True,
                'name': mixture,
                'alias': alias,
                'language_id': language.id,
            }, context=context)
        chemeter_pool.download_msds_form(
            cr, uid, [chemeter_id], context=context)
        return chemeter_pool.download_msds_form(
            cr, uid, [chemeter_id], context=context)


    _columns = {
        'mixture': fields.char(
            'Codice Mixture', size=35,
            help='Codice Mixture, es: S0007_1 (granulometria di solito '
                 'indicata come _ per dire che il carattere scritto '
                 'non è importante'),
        'alias': fields.char(
            'Alias', size=20,
            help='Codice alias indicato nel documento cliente'),
        'language_id': fields.many2one(
            'msds.language', 'Lingua',
            required=True, help='Elenco lingue importate da Chemeter'),
    }
