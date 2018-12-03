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

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'
    
    def update_uom(self, cr, uid, db, contex=None):
        ''' Update product
            [(product_id, uom_id)]
        ''' 
        # Template ID database:
        template_db = {}       
        product_ids = self.search(cr, uid, [], context=None)
        for product in self.browse(
                cr, uid, product_ids, context=context):
            template_db[product.id] = product.product_tmpl_id.id
                    
        # Update UOM in template:
        not_updated = []
        for record in db:
            product_id, uom_id = record
            template_id = template_db.get(product_id, False)
            if not template_id:
                not_updated.append(product_id)
            query = '''
                UPDATE template_product 
                SET uom_id = %s, uos_id = %s, uom_po_id = %s 
                WHERE id = %s
                ''' 
            cr.execute(query, (uom_id, uom_id, uom_id, template_id))
        return not_updated
        
    _columns = {
        #'contipaq_import': fields.boolean('Contipaq import'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
