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


# Wizard:
class BomProductAlernativeWizard(osv.osv_memory):
    """ Alternative groups for BOM Wizard
    """
    _name = 'bom.product.alternative.wizard'

    _columns = {
        'name': fields.char('Nome', size=20)
        }


class BomProductAlernativeLineWizard(osv.osv_memory):
    """ Alternative groups for BOM Wizard
    """
    _name = 'bom.product.alternative.line.wizard'

    def select_alternative_product_button(self, cr, uid, ids, context=None):
        """ Select this product
        """
        if context is None:
            context = {}
        bom_id = context.get('this_bom_id')
        bom_obj = context.get('this_bom_obj')  # comes from various part

        # todo Update caller record:

        return True

    _columns = {
        'wizard_id': fields.many2one(
            'bom.product.alternative.wizard', 'Wizard'),
        'product_id': fields.many2one('product.product', 'Prodotto'),
    }


class BomProductAlernativeWizardInherit(osv.osv_memory):
    """ Alternative groups for BOM Wizard
    """
    _inherit = 'bom.product.alternative.wizard'

    _columns = {
        'product_ids': fields.many2one(
            'bom.product.alternative.line.wizard', 'wizard_id', 'Prodotti'),
        }


# Objects:
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
    _inherit = 'mrp.bom'

    def choose_material_alternative(self, cr, uid, ids, context=None):
        """ Open alternatives materials
        """
        if context is None:
            context = {}

        # Pool used:
        alternative_pool = self.pool.get('bom.product.alternative')
        wizard_pool = self.pool.get('bom.product.alternative.wizard')
        wizard_line_pool = self.pool.get('bom.product.alternative.line.wizard')
        model_pool = self.pool.get('ir.model.data')

        view_id = model_pool.get_object_reference(
            cr, uid,
            'production_line', 'view_bom_product_alternative_wizard_form')[1]

        this_line = self.browse(cr, uid, ids, context=context)[0]
        old_product_id = this_line.product_id.id  # For alternative

        # Prepare data:
        pdb.set_trace()
        wizard_id = wizard_pool.create(cr, uid, {
            'name': datetime.now(),
        }, context=context)
        for product_id in alternative_pool.get_alternative_groups(
                cr, uid, ids, old_product_id, context=context):
            wizard_line_pool.create(cr, uid, {
                'wizard_id': wizard_id,
                'product_id': product_id,
            }, context=context)
        ctx = context.copy()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti alternativi'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wizard_id,
            'res_model': 'mrp.product.alternative.wizard',
            'view_id': view_id,  # False
            'views': [(view_id, 'tree')],
            'domain': [],
            'context': ctx,
            'target': 'new',
            'nodestroy': False,
            }

