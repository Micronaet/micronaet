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
    _inherit = 'sale.order.line'

    def dummy_button(self, cr, uid, ids, context=None):
        """ Return button
        """
        return True

    def open_sale_line_note(self, cr, uid, ids, context=None):
        """ Open note view
        """
        model_pool = self.pool.get('ir.model.data')
        view_id = model_pool.get_object_reference(
            cr, uid, 'production_line', 'view_sale_order_line_note_form')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Note di riga ordine'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'res_model': 'sale.order.line',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'domain': [],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }

    _columns = {
        # Added also here for MX installation
        # Was in partner_product_detail for Italy
        'pallet_weight': fields.integer(
            'Peso pallet',
            help='Caricare per questo prodotto il pallet con questi Kg'
            ),

        'note_packaging': fields.char(
            'Note packaging', size=100,
            help='Note per il personale che preparerà la consegna nel '
                 'magazzino',
            ),
        'note_mrp': fields.char(
            'Note produzione', size=100,
            help='Note per il personale che prepara la produzione',
            ),
        'note_laboratory': fields.char(
            'Note laboratorio', size=100,
            help='Note per il personale del laboratorio',
            ),
        'note_delivery': fields.char(
            'Note consegna', size=100,
            help='Note per il personale che effettua fisicamente la consegna',
            ),
        'note_internal': fields.char(
            'Note interne', size=100,
            help='Note interne amministrative che rimangono collegate alla'
                 'riga della offerta'
            ),

        'note_pr': fields.char(
            'Note Offerta', size=100,
            help='Note scritte sulla offerta'
            ),
        'note_oc': fields.char(
            'Note Ordine', size=100,
            help='Note scritte sull\'ordine di vendita'
            ),
        'note_ddt': fields.char(
            'Note DDT', size=100,
            help='Note scritte sul documento di trasporto'
            ),
        'note_all_document': fields.char(
            'Note documenti', size=100,
            help='Note scritte sul tutti i documenti (offerta, ordine, DDT)'
        ),
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
