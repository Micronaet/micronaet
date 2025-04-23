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
import pdb
import sys
import logging
import openerp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class ProductProduct(orm.Model):
    """ Model name: Product
    """

    _inherit = 'product.product'

    def name_get(self, cr, uid, ids, context=None):
        """ Return a list of tupples contains id, name.
            result format : {[(id, name), (id, name), ...]}

            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of ids for which name should be read
            @param context: context arguments, like lang, time zone

            @return: returns a list of tupples contains id, name
        """
        if context is None:
            context = {}
        if not context.get('mrp_mode'):
            return super(ProductProduct, self).name_get(cr, uid, ids, context=context)

        if not ids:
            return []

        if isinstance(ids, (long, int)):
            ids = [ids]
        res = []
        records = self.browse(cr, uid, ids, context=context)
        for record in sorted(records, key=lambda x: (x.mrp_obsolete, x.default_code)):
            res.append((
                record.id,
                u'{obsolete}[{code}] {name}'.format(
                    code=record.default_code or '?',
                    name=record.name,
                    obsolete='{OLD} ' if record.mrp_obsolete else '',
                )))
        return res

    _columns = {
        'mrp_obsolete': fields.boolean('Obsolete (MRP)'),
    }