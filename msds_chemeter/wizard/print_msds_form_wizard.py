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


class ProductProduct(orm.Model):
    """ Button to open wizard
    """
    _inherit = 'product.product'

    def open_print_msds_wizard(self, cr, uid, ids, context=None):
        """ Open Wizard button
        """
        wizard_pool = self.pool.get('msds.print.form.wizard')

        if context is None:
            context = {}
        # Clear context here:
        context = {'lang': context.get('lang')}

        ctx = context.copy()
        ctx['origin'] = {
            'model': 'product.product',
            'id': ids[0],
        }
        return wizard_pool.open_wizard_from(cr, uid, False, context=ctx)


class SaleOrderLine(orm.Model):
    """ Button to open wizard
    """
    _inherit = 'sale.order.line'

    def open_print_msds_wizard(self, cr, uid, ids, context=None):
        """ Open Wizard button
        """
        wizard_pool = self.pool.get('msds.print.form.wizard')

        if context is None:
            context = {}
        # Clear context here:
        context = {'lang': context.get('lang')}

        ctx = context.copy()
        ctx['origin'] = {
            'model': 'sale.order.line',
            'id': ids[0],
        }
        return wizard_pool.open_wizard_from(cr, uid, False, context=ctx)


class MrpAnalysisSample(orm.Model):
    """ Button to open wizard
    """
    _inherit = 'mrp.analysis.sample'

    def open_print_msds_wizard(self, cr, uid, ids, context=None):
        """ Open Wizard button
        """
        record = self.browse(cr, uid, ids[0], context=context)

        # Call other actions:
        if record.sale_line_id:
            return self.pool.get('sale.order.line').open_print_msds_wizard(
                cr, uid, [record.sale_line_id.id], context=context)
        else:
            return self.pool.get('product.product').open_print_msds_wizard(
                cr, uid, [record.product_id.id], context=context)


class MsdsPrintFormWizard(orm.TransientModel):
    """ Wizard for print MSDS from Chemeter
    """
    _name = 'msds.print.form.wizard'

    def open_wizard_from(self, cr, uid, ids, context=None):
        """ Open wizard with passing reference of origin dict:
            'model': sale.order.line product.product res.partner.pricelist.product
            'id': item ID
        """
        if context is None:
            context = {}

        origin = context.get('origin', {})
        _logger.info('Wizard with origin: {}'.format(origin))

        model = origin.get('model')
        item_id = origin.get('id')

        this_pool = self.pool.get(model)
        record = this_pool.browse(cr, uid, item_id, context=context)

        # ---------------------------------------------------------------------
        # Product mode:
        # ---------------------------------------------------------------------
        ctx = context.copy()
        if model == 'product.product':
            product = record
        else:
            product = record.product_id  # both sale line and pricelist
            # -----------------------------------------------------------------
            # Sale line mode:
            # -----------------------------------------------------------------
            if model == 'sale.order.line':
                partner = record.order_id.partner_id
                ctx['default_alias'] = record.name

            # -----------------------------------------------------------------
            # Partner pricelist:
            # -----------------------------------------------------------------
            else:
                partner = record.partner_id
                ctx['default_alias'] = record.alias_name or ''

            ctx['default_language_id'] = partner.msds_language_id.id or False

        # Extract Mixture:
        product_code = product.default_code or ''
        ctx['default_mixture'] = product.force_mixture or '{}_{}'.format(
            product_code[:5],
            product_code[6:],
            )

        _logger.info('Wizard context: {}'.format(ctx))

        view_id = self.pool.get('ir.model.data').get_object_reference(
            cr, uid,
            'msds_chemeter', 'msds_print_form_wizard_view')[1]
        return {
            'name': 'Wizard stampa MSDS',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'msds.print.form.wizard',
            'views': [(view_id, 'form')],
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new',
        }

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
        ctx = context.copy()
        ctx['wizard_mode'] = True
        return chemeter_pool.download_msds_form(
            cr, uid, [chemeter_id], context=ctx)
        #return chemeter_pool.download_msds_form(
        #    cr, uid, [chemeter_id], context=context)


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
