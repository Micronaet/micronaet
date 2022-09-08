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
import pdb
import sys
import openerp.netsvc as netsvc
import logging
from openerp import tools
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from utility import no_establishment_group


_logger = logging.getLogger(__name__)


class BomProductAlernative(osv.osv):
    """ Alternative groups for BOM
    """
    _name = 'bom.product.alternative'

    def get_alternative_groups(self, cr, uid, ids, product_id, context=None):
        """ Extract product alternatives for a product
        """
        res = False
        if not product_id:
            return res
        query = """
            SELECT DISTINCT product_id
            FROM bom_product_alternative_group_rel
            WHERE group_id in (
                SELECT group_id
                FROM bom_product_alternative_group_rel
                WHERE product_id = %s);
            """
        cr.execute(query, [product_id])
        res = [r[0] for r in cr.fetchall]
        return res

    _columns = {
        'name': fields.char('Nome raggruppamento', size=35, required=True),
        'group_ids': fields.many2many(
            'product.product', 'bom_product_alternative_group_rel',
            'group_id', 'product_id',
            'Prodotti'),
    }

