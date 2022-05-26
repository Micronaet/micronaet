# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
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
from openerp.osv import fields, osv, expression
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


class sale_order_line(osv.osv):
    """ Problem with confirmed files # patch
    """
    _name = 'sale.order.line'

    _columns = {
        # Added also here for MX installation
        # Was in partner_product_detail for Italy
        'pallet_weight': fields.integer(
            'Peso pallet',
            help='Caricare per questo prodotto il pallet con questi Kg'),
    }


class sale_order(osv.osv):
    """ Problem with confirmed files # patch
    """
    _name = 'sale.order'
    _inherit = 'sale.order'

    def get_selection(self, cr, uid, context=None):
        """ Get current selection and append field
        """
        if 'state' not in self._columns:
            return []

        confirmed = ('confirmed', 'Confirmed')
        if confirmed not in self._columns['state'].selection:
            self._columns['state'].selection.append(confirmed)

    _columns = {
        'state': fields.selection([
            ('draft', 'Draft Quotation'),
            ('sent', 'Quotation Sent'),
            ('cancel', 'Cancelled'),
            ('confirmed', 'Confirmed'),
            ('waiting_date', 'Waiting Schedule'),
            ('progress', 'Sales Order'),
            ('manual', 'Sale to Invoice'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Done'),
            ], 'State', readonly=True,
        )
    }
