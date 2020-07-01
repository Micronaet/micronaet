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
        'msds_folder_in': fields.char(
            'MSDS folder in', size=128,
            help="Folder where PDF are exported from EpyPlus (ex.: ~/msds"),
        'msds_folder_store': fields.char(
            'MSDS folder store', size=128,
            help="Folder for store imported PDF, default 'store' in addons "
            "root module path"),
        'msds_log_id': fields.many2one(
            'res.users', 'Log user',
            help="User that receive all logs during importation schedule"),
        }

    _defaults = {
        'msds_folder_in': lambda *a: '~/msds',
        'msds_folder_store': lambda *a: False,
        }


class MsdsFormLanguage(orm.Model):
    """ MSDS language for Form documents
    """
    _name = 'msds.form.language'
    _description = 'MSDS Form language'

    _columns = {
        'name': fields.char('Language', size=64, required=True),
        'code': fields.char('Code', size=4, required=True),
        'note': fields.text('Note'),
        }


class MsdsForm(orm.Model):
    """ MSDS Form, all elements are form for product (present in more version)
    """
    _name = 'msds.form'
    _description = 'MSDS Form'
    _rec_name = 'product_code'
    _order = 'product_code desc'

    # -----------------
    # Utility function:
    # -----------------
    def send_log(
            self, cr, uid, subject='', body='', partner_ids=[], context=None):
        """ Write log in wall
        """
        # TODO Mettere meglio (anche con l'invio della mail)

        # Default part of message:
        message = {
            'subject': subject,
            'body': body,
            'type': 'comment',  # 'comment', 'notification', 'email',
            'subtype': False,   # parent_id, attachments,
            'content_subtype': 'html',
            'partner_ids': partner_ids,
            'email_from': 'openerp@micronaet.it',
            'context': context,
            }
        msg_id = self.pool.get('res.partner').message_post(
            cr, uid, [uid], **message)
        return

    def _get_file_name(self, cr, uid, product_id, context=None):
        """ Find file name for document stored
            product_id: integer single element
        """
        product_proxy = self.browse(cr, uid, product_id, context=context)
        folder = os.path.expanduser(
            product_proxy.product_id.company_id.msds_folder_store)
        res = os.path.join(folder, "%s.pdf" % product_id)
        return res

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
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
        """ Scheduled import for MSDS form
        """
        def log(log_file, message, mode='INFO', newline='\r\n'):
            log_file.write('%s. [%s] %s%s' % (
                datetime.now(),
                mode.upper(),
                message,
                newline,
            ))

        _logger.info(_('Start import PDF MSDS forms'))
        log_message = ''
        log_imported = ''

        # ---------------
        # Get parameters:
        # ---------------
        try:
            company_proxy = self.pool.get('res.company').browse(
                cr, uid, 1, context=context)  # TODO

            msds_folder_in = os.path.expanduser(company_proxy.msds_folder_in)
            msds_folder_store = os.path.expanduser(
                company_proxy.msds_folder_store)
        except:
            log_message = _('Error reading start up path (in / store), check '
                            'Company form and correct!')
            _logger.error(log_message)
            return False

        try:
            msds_log_email = company_proxy.msds_log_id.email
        except:
            _logger.warning(_('No logger mail setup so no mail will be sent!'))

        if not (msds_folder_in and msds_folder_store):
            log_message = _('No path for in or store, see Company form!')
            _logger.error(log_message)
            return False

        # -----------------------
        # Read language for MSDS:
        # -----------------------
        languages = {}
        language_pool = self.pool.get('msds.form.language')
        language_ids = language_pool.search(cr, uid, [], context=context)
        language_proxy = language_pool.browse(
            cr, uid, language_ids, context=context)
        for item in language_proxy:
            languages[item.code] = item.id

        version_pool = self.pool.get('msds.form.version')
        rel_pool = self.pool.get('msds.form.rel')

        # Read IN folder
        log_f = open(os.path.join(msds_folder_in, 'esito.txt'), 'w')
        log(log_f, 'Inizio importazione giornaliera')
        for root, dirs, files in os.walk(msds_folder_in):
            for f in files:
                if f.startswith('DE_S0105'):
                    pdb.set_trace()
                try:
                    filename = f.upper().split(".")

                    # -----------------------
                    # Check if is a PDF file:
                    # -----------------------
                    if filename[-1] != "PDF":
                        log(
                            log_f,
                            '%s Non ha estensione pdf ma: %s' % (
                                f,
                                filename[-1],
                            ),
                            'error',
                        )
                        continue  # Jump

                    # -------------------------------
                    # Read timestamp for modify time:
                    # -------------------------------
                    origin = os.path.join(root, f)  # for copy operation

                    # Read timestamp:
                    timestamp = datetime.fromtimestamp(
                        os.path.getmtime(os.path.join(root, f))).strftime(
                            DEFAULT_SERVER_DATETIME_FORMAT)

                    # Check format of filename
                    filename = filename[0].split("_")
                    format_type = len(filename)
                    if format_type not in (2, 3):
                        error = _('Wrong format: %s') % f
                        log_message += error
                        _logger.error(error)
                        log(
                            log_f,
                            '%s Formato errato, "_" devono essere 1 o 2' % f,
                            'error',
                        )
                        continue

                    # ------------------------
                    # Check if language exist:
                    # ------------------------
                    if filename[0] not in languages:
                        error = _('Language not found: %s') % filename[0]
                        log_message += error
                        _logger.error(error)
                        log(
                            log_f,
                            '%s Lingua non trovata: %s' % (f, filename[0]),
                            'error',
                        )
                        continue

                    language_id = languages.get(filename[0], False)
                    if format_type == 2:  # EN_CODE.PDF
                        product_code = filename[1]
                        alias_code = False
                    elif format_type == 3:  # EN_ALIAS_(CODE).PDF
                        if not filename[2]:
                            log(
                                log_f,
                                '%s Non viene indicato il codice del '
                                'prodotto DARE' % f,
                                'error',
                            )
                            continue
                        if filename[2][:1] != '(' or filename[2][-1:] != ')':
                            log(
                                log_f,
                                '%s Le parentesi non sono posizionate '
                                'correttamente' % f,
                                'error',
                            )
                            continue

                        product_code = filename[2][1: -1]  # remove "(code)"
                        alias_code = filename[1]

                    # ----------
                    # MSDS part:
                    # ----------
                    # Search MSDS:
                    msds_ids = self.search(cr, uid, [
                        ('filename', '=', f),
                        ('language_id', '=', language_id),
                        ], context=context)
                    if msds_ids:
                        msds_id = msds_ids[0]
                        log(
                            log_f,
                            '%s Caricato precedentemente' % f,
                        )
                    else:  # create
                        msds_id = self.create(cr, uid, {
                            'product_code': product_code,
                            'alias_code': alias_code,
                            'filename': f,
                            'language_id': language_id,
                            }, context=context)
                        log(
                            log_f,
                            '%s Nuovo caricamento' % f,
                        )

                    # -------------
                    # Version part:
                    # -------------
                    # Search version:
                    version_ids = version_pool.search(cr, uid, [
                        ('msds_id', '=', msds_id),
                        ('timestamp', '=', timestamp),
                        ], context=context)
                    if version_ids:
                        version_id = version_ids[0]
                    else:
                        version_id = version_pool.create(cr, uid, {
                            'msds_id':  msds_id,
                            'timestamp': timestamp,
                            }, context=context)

                        # Save file in OpenERP:
                        destination = os.path.join(
                            msds_folder_store,
                            "%s.PDF" % version_id)
                        shutil.copyfile(origin, destination)

                    # -------------------
                    # MSDS relation part:
                    # -------------------
                    # Search product (with granulometry)
                    if "#" in product_code:  # Version code
                        if product_code[-1] == "#":  # last char test also no #
                            cr.execute("""
                                SELECT id FROM product_product
                                WHERE default_code = %s 
                                    OR default_code ilike %s;""", (
                                    product_code[:-1],
                                    product_code.replace("#", "_"), ))
                        else:
                            cr.execute("""
                                SELECT id FROM product_product
                                WHERE default_code ilike %s;""", (
                                    product_code.replace("#", "_"), ))
                    else:  # Master version
                        cr.execute("""
                            SELECT id FROM product_product
                            WHERE default_code = %s;
                            """, (product_code, ))

                    records = cr.fetchall()
                    if not records:
                        log(
                            log_f,
                            '%s Non trovato nessun prodotto da abbinare' % f,
                            'error',
                        )
                        continue

                    for record in records:
                        product_id = record[0]
                        rel_ids = rel_pool.search(cr, uid, [
                            ('msds_id', '=', msds_id),
                            ('product_id', '=', product_id),
                            ('alias_id', '=', False),
                            ], context=context)
                        if not rel_ids:  # Create
                            rel_pool.create(cr, uid, {
                                'msds_id': msds_id,
                                'product_id': product_id,
                                'alias_id': False,
                                }, context=context)

                    # Search alias (with granulometry)
                    if alias_code:
                        if " " in alias_code:  # Version code
                            cr.execute("""
                                SELECT id FROM product_product
                                WHERE default_code ilike %s;
                                """, (alias_code.replace("#", "_")))
                        else:  # Master version
                            cr.execute("""
                                SELECT id FROM product_product
                                WHERE default_code = %s;
                                """, (alias_code, ))

                        records = cr.fetchall()
                        if not records:
                            log(
                                log_f,
                                '%s Non trovato nessun alias da abbinare' % f,
                                'error',
                            )
                            continue

                        for record in records:
                            alias_id = record[0]
                            rel_ids = rel_pool.search(cr, uid, [
                                ('msds_id', '=', msds_id),
                                ('product_id', '=', False),
                                ('alias_id', '=', alias_id),
                                ], context=context)
                            if not rel_ids:  # Create
                                rel_pool.create(cr, uid, {
                                    'msds_id': msds_id,
                                    'product_id': False,
                                    'alias_id': alias_id,
                                    }, context=context)
                    log_imported += "%s [%s]<br/>\n" % (f, timestamp)
                    log(
                        log_f,
                        '%s Importato prodotto %s con alias %s' % (
                            f, product_code, alias_code or '/'),
                    )

                except:
                    error = '%s' % (sys.exc_info(), )
                    log_message += error
                    _logger.error(error)
                    continue
                log(log_f, 'Fine caricamento')

        if log_message:
            self.send_log(
                cr, uid, 'Error import MSDS', body=log_message,
                partner_ids=[company_proxy.msds_log_id.partner_id.id],
                context=context)
        if log_imported:
            self.send_log(
                cr, uid, 'Import MSDS', body=log_imported,
                partner_ids=[company_proxy.msds_log_id.partner_id.id],
                context=context)
        if not (log_message and log_imported):
            self.send_log(
                cr, uid, 'Import MSDS', body='No new MSDS',
                partner_ids=[company_proxy.msds_log_id.partner_id.id],
                context=context)

        _logger.info(_('End importation MSDS forms'))
        return True

    _columns = {
        'product_code': fields.char(
            'Product code', size=35,
            help="Code for this product"),
        'alias_code': fields.char(
            'Alias code', size=35,
            help="Code for alias product"),
        'filename': fields.char(
            'Filename', size=35,
            help="Original filename during importation"),
        'language_id': fields.many2one(
            'msds.form.language', 'Language',
            required=True, help="Language for form document"),
        }


class MsdsFormVersion(orm.Model):
    """ Version for MSDS form
    """
    _name = 'msds.form.version'
    _description = 'MSDS Form version'
    _rec_name = 'msds_id'
    _order = 'timestamp desc'

    # -------------
    # Button event:
    # -------------
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

    _columns = {
        'msds_id': fields.many2one('msds.form', 'MSDS', ondelete='cascade'),
        'timestamp': fields.datetime('Datetime',
            help="Time stamp for file version"),
        }


class MsdsForm(orm.Model):
    """ Inherit for relations
    """
    _inherit = 'msds.form'

    _columns = {
        'version_ids': fields.one2many(
            'msds.form.version', 'msds_id',
            'Version'),
        }


class MsdsFormRel(orm.Model):
    """ Relation from product and MSDS form
    """
    _name = 'msds.form.rel'
    _description = 'MSDS Form rel'
    _rec_name = 'product_id'
    _order = 'product_id'

    # -------------------------------------------------------------------------
    # Button event:
    # -------------------------------------------------------------------------
    def open_msds_form(self, cr, uid, ids, context=None):
        """ Open MSDS last revision form
        """
        form_pool = self.pool.get('msds.form')

        rel_proxy = self.browse(cr, uid, ids, context=context)[0]
        return form_pool.open_msds_form(
            cr, uid, [rel_proxy.msds_id.id], context=context)

    def download_msds_form(self, cr, uid, ids, context=None):
        """ Open MSDS last revision form
        """
        form_pool = self.pool.get('msds.form')

        rel_proxy = self.browse(cr, uid, ids, context=context)[0]
        return form_pool.download_msds_form(
            cr, uid, [rel_proxy.msds_id.id], context=context)

    _columns = {
        'msds_id': fields.many2one(
            'msds.form', 'MSDS',
            ondelete='cascade'),
        'product_id': fields.many2one(
            'product.product', 'Product',
            ondelete='cascade'),
        'alias_id': fields.many2one(
            'product.product', 'Alias product',
            ondelete='cascade', help="Alias product"),
        'language_id': fields.related(
            'msds_id', 'language_id',
            type='many2one', relation='msds.form.language',
            string='Language', store=False),
        'product_code': fields.related(
            'msds_id', 'product_code',
            type='char', size=35, string='Product code', store=False),
        'alias_code': fields.related(
            'msds_id', 'alias_code',
            type='char', size=35, string='Alias code', store=False),
        }


class ProductProduct(orm.Model):
    """ Add extra info in product
    """
    _inherit = 'product.product'

    _columns = {
        'msds_ids': fields.one2many('msds.form.rel', 'product_id', 'MDSD'),
        'msds_alias_ids': fields.one2many(
            'msds.form.rel', 'alias_id', 'Alias MDSD'),
        }
