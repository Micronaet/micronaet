#|/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import base64
import tempfile
import logging
import shutil
from openerp.osv import osv, fields
from openerp.tools.translate import _
from datetime import datetime
import pdb

_logger = logging.getLogger(__name__)


class ChemicalAttachment(osv.osv):
    """ Form attachment
    """
    _name = 'chemical.attachment'
    _description = 'Documenti chimici'
    _store_folder = '~/filestore'

    def open_attachment_wizard(self, cr, uid, ids, context=None):
        """ Button from Form
        """
        form_pool = self.pool.get('chemical.analysis')
        attachment_id = ids[0]
        attachment = self.browse(cr, uid, attachment_id, context=context)
        form_id = attachment.form_id.id

        return form_pool.open_attachment_detailed(
            cr, uid, form_id, attachment_id, context=context)

    def open_file(self, cr, uid, ids, context=None):
        """ Fields function for calculate
        """
        attachment = self.browse(cr, uid, ids, context=context)[0]
        origin = attachment.filename
        tmp = tempfile.NamedTemporaryFile()
        extension = origin.split('.')[-1]
        if len(extension) > 6:  # XXX max extension length
            extension = ''
        destination = '%s.%s' % (tmp.name, extension)
        tmp.close()

        # Copy current file in temp destination
        try:
            shutil.copyfile(origin, destination)
        except:
            raise osv.except_osv(
                _('File non trovato'),
                _(u'File non trovato nella gest. documentale!\n%s' % origin),
            )

        name = 'chemical_download.%s' % extension

        # Return link for open temp file:
        return self._get_php_return_page(
            cr, uid, destination, name, context=context)

    def _get_php_return_page(self, cr, uid, fullname, name, context=None):
        """ Generate return object for passed files
        """
        config_pool = self.pool.get('ir.config_parameter')
        key = 'web.base.url.chemical'
        config_ids = config_pool.search(cr, uid, [
            ('key', '=', key)], context=context)
        if not config_ids:
            raise osv.except_osv(
                _('Errore'),
                _('Avvisare amministratore: configurare parametro: %s' % key),
            )
        config_proxy = config_pool.browse(
            cr, uid, config_ids, context=context)[0]
        base_address = config_proxy.value
        _logger.info('URL parameter: %s' % base_address)

        return {
            'type': 'ir.actions.act_url',
            'url': '%s/save_as.php?filename=%s&name=%s' % (
                base_address,
                fullname,
                name
            ),
            # 'target': 'new',
        }

    def _get_filename(self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        root = os.path.expanduser(self._store_folder)
        for attachment in self.browse(cr, uid, ids, context=context):
            attach_id = attachment.id
            res[attach_id] = os.path.join(
                root,
                '%s.%s' % (attachment.id, attachment.extension),
                )
        return res

    _columns = {
        'name': fields.char('Descrizione', size=60),
        'form_id': fields.many2one('chemical.analysis', 'Scheda'),
        'filename': fields.function(
            _get_filename, method=True,
            type='text', string='Nome file',
            ),
        'extension': fields.char('Estensione', size=5),
    }


class ChemicalAnalysis(osv.osv):
    """ Analysis button
    """
    _inherit = 'chemical.analysis'

    def open_attachment_wizard(self, cr, uid, ids, context=None):
        """ Button from Form
        """
        form_id = ids[0]
        return self.open_attachment_detailed(
            cr, uid, form_id, False, context=context)

    def open_attachment_detailed(
            self, cr, uid, form_id, attachment_id, context=None):
        """ Open wizard wit 2 mode:
        """
        attachment_pool = self.pool.get('chemical.attach'.manual.form.wizard'')
        wizard_pool = self.pool.get('chemical.attach.manual.form.wizard')
        model_pool = self.pool.get('ir.model.data')
        view_id = model_pool.get_object_reference(
            cr, uid,
            'chemical_analysis', 'view_chemical_attach_manual_form_form')[1]

        attachment = attachment_pool.browse(
            cr, uid, attachment_id, context=context)
        ctx = context.copy()
        ctx['default_form_id'] = form_id
        ctx['default_attachment_id'] = attachment_id
        ctx['default_extension'] = attachment.extension or 'docx'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Importa allegati'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': False,
            'res_model': 'chemical.attach.manual.form.wizard',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'domain': [],
            'context': ctx,
            'target': 'new',
            'nodestroy': False,
            }

    _columns = {
        'attachment_ids': fields.one2many(
            'chemical.attachment', 'form_id', 'Allegati')
    }


class ChemicalAttachManualFormWizard(osv.osv_memory):
    """ Attach manual form
    """
    _name = 'chemical.attach.manual.form.wizard'
    _description = 'Collega scheda manuale'

    def add_attachment(self, cr, uid, ids, context=None):
        """ Add attachement
        """
        attach_pool = self.pool.get('chemical.attachment')
        wizard = self.browse(cr, uid, ids, context=context)[0]
        form_id = wizard.form_id.id
        attach_id = wizard.attachment_id.id

        if attach_id:
            attach_pool.create(cr, uid, [attach_id], {
                'extension': wizard.extension,  # Update extension
            }, context=context)
        else:
            attach_id = attach_pool.create(cr, uid, {
                'name': wizard.name,
                'form_id': form_id,
                'extension': wizard.extension,
                }, context=context)
        attach_filename = attach_pool.browse(
            cr, uid, attach_id, context=context).filename

        b64_file = base64.decodestring(wizard.file)
        f = open(attach_filename, 'wb')
        f.write(b64_file)
        f.close()
        return True

    _columns = {
        'form_id': fields.many2one('chemical.analysis', 'Form'),
        'attachment_id': fields.many2one(
            'chemical.attachment', 'Allegato'),
        'name': fields.char('Descrizione', size=80),
        'file': fields.binary('File'),
        'extension': fields.selection([
            ('docx', 'Word (docx)'),
            ('doc', 'Word, obsoleto (doc)'),
            ('xlsx', 'Excel (xlsx)'),
            ('xlsx', 'Excel, obsoleto (xls)'),
            ('pdf', 'Acrobat Reader (pdf)'),
            ('txt', 'Blocco note (txt'),
            # ('dat', 'Blocco note (txt'),
        ], 'Estensione', required=True),

    }

    _defaults = {
        'name': lambda *s: 'Scheda di analisi cartacea',
        'extension': lambda *s: 'docx',
    }

