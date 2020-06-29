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
import openerp.netsvc
import logging
from openerp import SUPERUSER_ID
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ProductUom(orm.Model):
    """ Model name: ProductUom
    """
    _inherit = 'product.uom'

    _columns = {
        'moltiplicator': fields.integer('Moltiplicator'),
        }

    _defaults = {
       'moltiplicator': lambda *a: 1,
        }


class crm_trip(osv.osv):
    """ CRM Trip object
    """
    _name = 'crm.trip'
    _description = 'CRM Trip'
    _order = 'from_date desc, name'

    # -------------
    # Button event:
    # -------------
    def open_crm_partner_report(self, cr, uid, ids, context=None):
        """ Open report for partner
        """
        return {  # action report
           'type': 'ir.actions.report.xml',
           'report_name': 'crm_trip_info_report',
           # 'datas': datas,
           }

    def reload_country(self, cr, uid, ids, context=None):
        """ Load nation but before delete all elements
        """
        crm_partner_pool = self.pool.get('crm.trip.partner')
        crm_partner_ids = crm_partner_pool.search(cr, uid, [
            ('trip_id', '=', ids[0])], context=context)
        crm_partner_pool.unlink(cr, uid, crm_partner_ids, context=context)
        return self.load_country(cr, uid, ids, context=context)

    def load_country(self, cr, uid, ids, context=None):
        """ Load all customer with selected nation
        """
        crm_partner_pool = self.pool.get('crm.trip.partner')
        partner_pool = self.pool.get('res.partner')

        trip_proxy = self.browse(cr, uid, ids, context=context)[0]
        crm_partner_ids = [item.id for item in trip_proxy.partner_ids]

        partner_ids = partner_pool.search(cr, uid, [
            ('country_id','=', trip_proxy.country_id.id),
            ('customer', '=', True),
            ], context=context)
        partner_proxy = partner_pool.browse(
            cr, uid, partner_ids, context=context)
        i = 0
        for item in partner_proxy:
            i += 1
            if item.id not in crm_partner_ids:
                crm_partner_pool.create(cr, uid, {
                    'sequence': i,
                    'trip_id': ids[0],
                    'partner_id': item.id,
                    }, context=context)
        return True

    # ----------
    # Functions:
    # ----------
    def _get_analysis_year(self, cr, uid, context=None):
        """ Return a list of elements from actual year (as top) to
            year setted up in Company setup for SQL databases exported
        """
        current = datetime.now().year
        company_pool = self.pool.get("res.company")
        # TODO
        company_id = company_pool.search(cr, uid, [], context=context)[0]
        company_proxy = company_pool.browse(
            cr, uid, company_id, context=context)

        # For multicompany create a list from bottom to current year
        if company_proxy.multi_year and company_proxy.bottom_year < current:
            res = [(str(y), str(y)) for y in
                   range(company_proxy.bottom_year, current)]
        else:
            res = []
        res.append((str(current), str(current)))
        return res

    _columns = {
        'partner': fields.boolean(
            'Partner trip',
            help='Partner trip for get status without trip generation'),
        'name': fields.char(
            'Name', required=True, size=40,
            help='Trip short name'),
        'user_id': fields.many2one('res.users', 'Sales man', required=True),
        'from_date': fields.date('From date', required=True),
        'to_date': fields.date('To date'),
        'product_from_date': fields.date(
            'Product buy date',
            help='''Evaluation date for product, filter product last buy date
                after this date (also for sample product)'''),
        'analysis_year': fields.selection(
            _get_analysis_year, "Analysis year",
            help="Choose from what year start analysis (depend on export "
            "mirror in databases selected on SQL DBMS"),
        'note': fields.text('Note', help='Extra information about trip'),
        'country_id': fields.many2one(
            'res.country', 'Country',
            required=False, ondelete='set null'),

        # Report parameters:
        'with_anagraphic': fields.boolean('Print anagraphic'),
        'with_note': fields.boolean('Print note'),
        'with_visit': fields.boolean('Print visit'),
        'with_offer': fields.boolean('Print offer'),
        'with_order': fields.boolean('Print order'),
        'with_movement': fields.boolean('Print movement'),
        'with_product': fields.boolean('Print product'),
        'with_price': fields.boolean('Print price variation'),
        'with_payment': fields.boolean('Print payment'),
        'with_sample': fields.boolean('Print sample'),
        'with_followup': fields.boolean('Print followup'),
        }

    _defaults = {
        'user_id': lambda s, cr, uid, ctx: uid,
        'from_date': lambda *x: datetime.now().strftime(
            DEFAULT_SERVER_DATE_FORMAT),

        # Report parameters:
        'with_anagraphic': lambda *x: True,
        'with_note': lambda *x: True,
        'with_visit': lambda *x: True,
        'with_offer': lambda *x: True,
        'with_order': lambda *x: True,
        'with_movement': lambda *x: False,
        'with_product': lambda *x: True,
        'with_price': lambda *x: True,
        'with_payment': lambda *x: True,
        'with_sample': lambda *x: True,
        'with_followup': lambda *x: True,
        }


class crm_trip_partner(osv.osv):
    """ CRM Trip partner visited object
    """
    _name = 'crm.trip.partner'
    _description = 'CRM Trip partner'
    _order = 'sequence, date desc'
    _rec_name = 'partner_id'

    _columns = {
        'sequence': fields.integer('Sequence'),
        'partner_id': fields.many2one('res.partner', 'Customer', required=True,
            domain=[('customer', '=', True)]),
        'date': fields.date('Date'),
        'abstract': fields.text(
            'Abstract', help='Topic argument for the visit'),
        'note': fields.text('Note', help='Extra information about trip'),
        'trip_id': fields.many2one('crm.trip', 'Visit'),
        # TODO needed?
        'partner': fields.related(
            'trip_id', 'partner', type='boolean', string='Partner trip'),
        }

    _default = {
        'sequence': lambda *x: 0,
        }


class crm_trip(osv.osv):
    """ CRM Trip object
    """
    _inherit = 'crm.trip'

    _columns = {
        'partner_ids': fields.one2many(
            'crm.trip.partner', 'trip_id', 'Customers'),
        }


class res_partner(osv.osv):
    """ Extra relation in partner
    """
    _inherit = 'res.partner'

    def create_open_analysis_document(self, cr, uid, ids, context=None):
        """ Create a fake visit for partner statistic analysis
        """
        partner_proxy = self.browse(cr, uid, ids, context=context)[0]
        crm_trip_id = partner_proxy.crm_trip_id.id

        if not crm_trip_id: # else update evaluation period?
            # ----------------------
            # Generate (first time):
            # ----------------------
            current_year = datetime.now().year
            # Header
            crm_trip_id = self.pool.get('crm.trip').create(cr, uid, {
                'partner': True,
                'name': partner_proxy.name,
                'analysis_year': '%s' % (current_year -1),
                'product_from_date': datetime.now().strftime(
                    '%d-01-01' % (current_year - 1)),
                'user_id': SUPERUSER_ID,
                'from_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'to_date': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
                'note': _('Automatic generation from partner, used for setup'),
                }, context=context)

            # Lines
            self.pool.get('crm.trip.partner').create(cr, uid, {
                'sequence': 1,
                'partner_id': ids[0],
                'trip_id': crm_trip_id,
                }, context=context)

            # Update partner for future ref
            self.write(cr, uid, ids, {
                'crm_trip_id': crm_trip_id}, context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Analysis parameters'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': crm_trip_id,
            'res_model': 'crm.trip',
            # 'view_id': view_id, # False
            'views': [(False, 'form')],
            'domain': [('id', '=', crm_trip_id)],
            'context': context,
            'target': 'current', # 'new'
            'nodestroy': False,
            }

    _columns = {
        'trip_ids': fields.one2many(
            'crm.trip.partner', 'partner_id', 'Visit', domain=[
                ('partner', '=', False)]),
        'crm_trip_id': fields.many2one(
            'crm.trip', 'Analysis parameters'),
        }
