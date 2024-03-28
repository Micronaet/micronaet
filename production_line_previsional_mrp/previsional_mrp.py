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

    def wkf_used_2_draft(self, cr, uid, ids, context=None):
        """ WK Button restore
        """
        return self.write(cr, uid, ids, {
            'state': 'draft',
            }, context=context)

    def wkf_draft_2_used(self, cr, uid, ids, context=None):
        """ WK Button done
        """
        return self.write(cr, uid, ids, {
            'state': 'used',
            }, context=context)

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
        # 'purchase_id': fields.many2one('mrp.bom', 'BOM', required=True),
        }

    _defaults = {
        'state': lambda *x: 'draft',
        }


class ProductStatusWizard(osv.osv_memory):
    """ Parameter for product status per day
    """
    _inherit = 'product.status.wizard'

    def schedule_send_negative_report_mailer(self, cr, uid, context=None):
        """ Action from external mailer:
        """
        return self.schedule_send_negative_report(cr, uid, context=context)

    # -------------------------------------------------------------------------
    # Override schedule action:
    # -------------------------------------------------------------------------
    def schedule_send_negative_report(
            self, cr, uid, wizard=None, context=None):
        """ Send mail to group user for negative elements
        """
        also_previsional = False  # XXX need here?
        if context is None:
            context = {}

        # ---------------------------------------------------------------------
        # Add previsional order:
        # ---------------------------------------------------------------------
        if also_previsional:
            previsional_pool = self.pool.get('mrp.production.previsional')
            previsional_ids = previsional_pool.search(cr, uid, [
                ('state', '=', 'draft'),
                ], context=context)
            fake_ids = previsional_pool.browse(
                cr, uid, previsional_ids, context=context)
        else:
            fake_ids = []

        # Default if not parameter
        if 'datas' not in context:
            context['datas'] = {
                'days': 30,
                'row_mode': 'negative',
                'with_medium': True,
                'month_window': 3,
                'with_order_detail': True,
                'fake_ids': fake_ids,
                'rop_page': True,
                }

        if wizard is not None:
            context['datas'].update(wizard)

        self.export_excel(cr, uid, False, context=context)

        # ---------------------------------------------------------------------
        # Update previsional order
        # ---------------------------------------------------------------------
        # todo correct here?
        if also_previsional:
            _logger.warning('Update previsional order as done!')
            previsional_pool.write(cr, uid, previsional_ids, {
                'state': 'used',
                }, context=context)
        return True

    # -------------------------------------------------------------------------
    # Default function:
    # -------------------------------------------------------------------------
    def _get_default_previsional_ids(self, cr, uid, context=None):
        """ Get previsonal list
        """
        previsional_pool = self.pool.get('mrp.production.previsional')
        return [(6, 0, previsional_pool.search(cr, uid, [
            ('state', '=', 'draft'),
            ], context=context), )]

    _columns = {
        # Override ex wizard sub object:
        'fake_ids': fields.many2many(
            'mrp.production.previsional', 'previsional_wiz_rel',
            'wiz_id', 'prev_id',
            'Previsional order'),
        }

    _defaults = {
        'fake_ids': lambda s, cr, uid, ctx:
            s._get_default_previsional_ids(cr, uid, ctx),
        }
