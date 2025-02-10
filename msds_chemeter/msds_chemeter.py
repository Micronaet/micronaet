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
import shutil
import pdb
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP, float_compare)
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ResCompany(osv.osv):
    """ Extra fields for res.company object
    """
    _inherit = 'res.company'

    _columns = {
        'msds_chemeter_folder_store': fields.char(
            'MSDS folder store', size=128,
            help="Folder for store imported PDF, default 'store' in addons "
            "root module path"),
        }

    _defaults = {
        'msds_folder_store': lambda *a: False,
        }


class MsdsChemeter(orm.Model):
    """ MSDS Form, all elements are form for product (present in more version)
    """
    _name = 'msds.chemeter'
    _description = 'MSDS Chemeter'
    _order = 'name, alias'

    def _get_file_name(self, cr, uid, product_id, context=None):
        """ Find file name for document stored
            product_id: integer single element
        """
        product_proxy = self.browse(cr, uid, product_id, context=context)
        company = product_proxy.product_id.company_id
        folder = os.path.expanduser(company.msds_chemeter_folder_store)
        res = os.path.join(folder, "%s.pdf" % product_id)
        return res

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    '''
    def open_msds_form(self, cr, uid, ids, context=None):
        """ Return a link element for use agent and open document from file
            system of MSDS form, ex.:
            openerp://msds/id.pdf
        """
        version_pool = self.pool.get('msds.form.version')
        version_ids = version_pool.search(cr, uid, [
            ('msds_id', '=', ids[0])], context=context)
        return version_pool.open_msds_form(
            cr, uid, version_ids, context=context)
    '''

    def download_msds_form(self, cr, uid, ids, context=None):
        """ Download file with PDF
        """
        version_pool = self.pool.get('msds.form.version')
        version_ids = version_pool.search(cr, uid, [
            ('msds_id', '=', ids[0])], context=context)
        return version_pool.download_msds_form(
            cr, uid, version_ids, context=context)

    # -----------------
    # Scheduled action:
    # -----------------
    def import_msds_form(self, cr, uid, context=None):
        """ Scheduled import for MSDS form Chemeter API generator
        """
        sapnaet_pool = self.pool.get('sapnaet')
        company_pool = self.pool.get('res.company')

        # ---------------------------------------------------------------------
        # Get parameters:
        # ---------------------------------------------------------------------
        _logger.info(_('Start import PDF MSDS forms'))
        try:
            # todo better
            company_proxy = company_pool.browse(cr, uid, 1, context=context)
            msds_folder_store = os.path.expanduser(
                company_proxy.msds_folder_store)
            msds_mask = os.path.join(
                msds_folder_store,
                '{}.pdf'
            )
        except:
            log_message = _(
                'Error reading start up path (in / store), check '
                'Company form and correct!')
            _logger.error(log_message)
            return False

        # Launch report with parameter to get
        _logger.info(_('Generate report to get list of MSDS from DDT'))
        sapnaet_ids = sapnaet_pool.search(cr, uid, [], context=context)
        report_data = sapnaet_pool.button_report_msds_delivery_report(
            cr, uid, sapnaet_ids, context=context)

        # Check and update record data:
        _logger.info(_('Update record and creare PDF'))
        pdb.set_trace()
        for key in report_data:
            mixture, alias, language = key
            mixture_ids = self.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '=', alias),
                ('language_id', '=', language.id),
            ], context=context)
            # todo

            if mixture_ids:
                regenerate_pdf = False
                # Update file
                mixture_id = mixture_ids[0]
                # todo raise if more than one?
            else:
                regenerate_pdf = True
                # Create new
                mixture_id = self.create(cr, uid, {

                }, context=context)

            if regenerate_pdf:
                filename = msds_mask.format(mixture_id)
                _logger.info('Generarting {}'.format(filename))
                # todo Generate PDF file

        _logger.info(_('End importation MSDS forms'))
        return True

    _columns = {
        'name': fields.char(
            'Codice Mixture', size=35,
            help="Code for this product"),
        'alias': fields.char(
            'Alias', size=50,
            help='Codice alias indicato nel documento cliente'),
        'language_id': fields.many2one(
            'msds.language', 'Lingua',
            required=True, help='Elenco lingue importate da Chemeter'),
        }

    # -------------
    # Button event:
    # -------------
    '''
    def open_msds_form(self, cr, uid, ids, context=None):
        """ Return a link element for use agent and open document from file
            system of MSDS form, ex.:
            openerp://msds/id.pdf
        """
        return {
            'type': 'ir.actions.act_url',
            'url': 'openerp://msds/%s.pdf' % ids[0],
            'target': 'new',
        }

    def download_msds_form(self, cr, uid, ids, context=None):
        """ Return download file:
        """
        pdf_path = os.path.expanduser('~/ETL/panchemicals/msds/openerp')

        version_proxy = self.browse(cr, uid, ids, context=context)[0]
        msds = version_proxy.msds_id

        attachment_pool = self.pool.get('ir.attachment')
        filename = os.path.join(pdf_path, '%s.PDF' % ids[0])

        name = 'MSDS_%s_%slang_%s_ID_%s' % (
            msds.product_code or '',
            ('alias_%s_' % msds.alias_code) if
            msds.alias_code else '',
            msds.language_id.code or 'XX',
            os.path.basename(filename),
            )
        return attachment_pool.return_file_apache_php(
            cr, uid, filename, name=name, context=context)
    '''


class ProductProduct(orm.Model):
    """ Add extra info in product
    """
    _inherit = 'product.product'

    def _get_msds_chemeter_m2m(
            self, cr, uid, ids, field_names, arg=None, context=None):
        """ Extract Mixture MSDS Chemeter for product
        """
        if context is None:
            context = {}

        chemeter_pool = self.pool.get('msds.chemeter')
        res = {}
        product_id = ids[0]
        product = self.browse(cr, uid, product_id, context=context)
        product_code = product.default_code or ''

        if product.force_mixture:
            mixture = product.force_mixture
        else:
            mixture = '{}_{}'.format(
                product_code[:5],
                product_code[6:],
            )
        if not mixture or not product_code:
            _logger.warning('No Mixture code found')
            return res

        res[product_id] = {
            'msds_chemeter_ids': chemeter_pool.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '=', False),
            ], context=context),
            'msds_chemeter_alias_ids': chemeter_pool.search(cr, uid, [
                ('name', '=', mixture),
                ('alias', '!=', False),
            ], context=context),
        }
        return res

    _columns = {
        # m2m function:
        'msds_chemeter_ids': fields.function(
            _get_msds_chemeter_m2m,
            method=True, type='many2many', multi=True,
            relation='msds.chemeter',
            string='Schede'),
        'msds_chemeter_alias_ids': fields.function(
            _get_msds_chemeter_m2m,
            method=True, type='many2many', multi=True,
            relation='msds.chemeter',
            string='Schede con alias'),
        }
