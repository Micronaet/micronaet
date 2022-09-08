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


# Objects:
class BomProductAlernative(osv.osv):
    """ Alternative groups for BOM
    """
    _name = 'bom.product.alternative'

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
            context with parameter: from_model, from_id
        """
        # Pool used:
        alternative_pool = self.pool.get('bom.product.alternative')
        model_pool = self.pool.get('ir.model.data')

        view_id = model_pool.get_object_reference(
            cr, uid,
            'production_line', 'view_bom_product_alternative_list_tree')[1]

        this_line = self.browse(cr, uid, ids, context=context)[0]
        old_product_id = this_line.product_id.id  # For alternative
        product_ids = alternative_pool.get_alternative_groups(
            cr, uid, ids, old_product_id, context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti alternativi'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'res_model': 'product.product',
            'view_id': view_id,
            'views': [(view_id, 'tree')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }


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
        res = [r[0] for r in cr.fetchall()]
        return res

    _columns = {
        'name': fields.char('Nome raggruppamento', size=35, required=True),
        'group_ids': fields.many2many(
            'product.product', 'bom_product_alternative_group_rel',
            'group_id', 'product_id',
            'Prodotti'),
    }


class MrpBom(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'product.product'

    def select_alternative_product_button(self, cr, uid, ids, context=None):
        """ Update previous DB with new product
        """
        if context is None:
            context = {}
        from_id = context.get('from_id')
        from_model = context.get('from_model')
        if not from_id or not from_model:
            raise Exception('Non trovato origine per aggiornare')

        from_pool = self.pool.get(from_model)
        from_pool.write(cr, uid, [from_id], {
            'product_id': ids[0]}, context=context)
        return


class MrpBom(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'mrp.bom'

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        pdb.set_trace()
        if context is None:
            context = {}
        alternative_pool = self.pool.get('bom.product.alternative')
        ctx = context.copy()
        ctx.update({
            'from_id': ids[0],
            'from_model': 'mrp.bom',
        })
        return alternative_pool.choose_material_alternative(
            cr, uid, ids, context=ctx)


class MrpProductionMaterial(osv.osv):
    """ Alternative groups for BOM
    """
    _inherit = 'mrp.production.material'

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        if context is None:
            context = {}
        alternative_pool = self.pool.get('bom.product.alternative')
        ctx = context.copy()
        ctx.update({
            'from_id': ids[0],
            'from_model': 'mrp.production.material',
        })
        return alternative_pool.choose_material_alternative(
            cr, uid, ids, context=ctx)

