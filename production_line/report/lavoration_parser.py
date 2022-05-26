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
import openerp.netsvc as netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse


_logger = logging.getLogger(__name__)

# Global parameters:
parameters = False

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'load_parameter': self.load_parameter,
            'get_parameter': self.get_parameter,
            'get_analysis_info': self.get_analysis_info,
            'translate_static': self.translate_static,
        })

    def translate_static(self, term, lang):
        """ Translate static text for module
        """
        languages = {
            # 'en_US': {
            #    },
            'es_AR': {
                u'ORDINE DI PRODUZIONE': u'ORDER DE FABRICACIÓN',
                u'Ordine di lavorazione': u'Orden de Fabricación',
                u'ORDINE DI LAVORAZIONE': u'ORDER DE FABRICACIÓN',
                u'FOGLIO PRODUZIONE': u'HOJA DE PRODUCCIÓN',
                u'FOGLIO CONFEZIONAMENTO': u'HOLA DE ALMACEN',
                u'N. Partita': u'N. Partida',
                u'Prodotto': u'Producto',
                u'Impianto': u'Planta',
                u'Data': u'Fecha',
                u'Lavorazioni': u'Fecha',
                u'Cod. Dogan.': u'Cod. Dog.',
                u'Componenti': u'Componente',
                # 'KG': u'KG',
                # 'LT': u'LT',
                # 'SAC': u'SAC',
                u'Lotto': u'Lote',
                u'Variazioni': u'Modificación',
                u'Totale': u'Total',
                u'Quantità da produrre': u'Ciclos totales',
                u'Quantità prodotta': u'Cantidad Producida',
                u'Q.tà a magazzino Kg.': u'Cantidad en Almacen Kg.',
                u'Totale Kg.': u'Total Kg.',
                u'Griglia': u'Malla',
                u'Martelli': u'Martillos',
                u'Imballo': u'Tipo de envase',
                u'Analisi': u'Analisis',
                u'Operatori': u'Operador',
                u'Macchine': u'Ciclos producidos',
                u'Velocità': u'Velocidad',
                u'Note lavorazione': u'Notas',
                u'Tempo miscelaz.': u'Tiempo',
                u'Anomalie riscontrate': u'Anomalias de maquinaria',
                u'Temperatura': u'Temperatura',
                u'Note': u'Notas',
                u'Aspirazione': u'Aspiración',
                u'N. bancale': 'N. Tarima',
                u'Peso bancale': 'Peso',
                u'Campione n.': 'N. Muestra',
                u'Q.C.P.': 'Notas',
                u'Verifica bonifica': 'Verifica bonifica',
                u'Silos stoccaggio': 'Silos stoccaggio',
                u'Ora inizio': 'Ora inizio',
                u'Ora fine': 'Ora fine',
                },
            }
        if lang == 'it_IT' or lang not in languages:
            return term

        return languages[lang].get(term, term)

    def load_parameter(self, product_id, workcenter_id):
        """ Load browse object for get parameters
        """
        global parameters, parameter_loaded
        parameters = False  # reset previous value

        workcenter_pool = self.pool.get('mrp.workcenter')
        history_pool = self.pool.get('mrp.workcenter.history')
        if product_id and workcenter_id:
            # test if workcenter is a child:
            workcenter_proxy = workcenter_pool.browse(
                self.cr, self.uid, workcenter_id)
            if workcenter_proxy.parent_workcenter_id:
                workcenter_id = workcenter_proxy.parent_workcenter_id.id

            # Setup browse object
            history_ids = history_pool.search(self.cr, self.uid, [
                ('product_id', '=', product_id),
                ('workcenter_id', '=', workcenter_id)
            ])
            if history_ids:
                parameters = history_pool.browse(
                    self.cr, self.uid, history_ids)[0]
            else:
                _logger.error('Paramter Line - Product not found!')
        return

    def get_parameter(self, name):
        """ Return parameters browse obj
        """
        global parameters
        try:
            return parameters.__getattr__(name)
        except:
            return ""
        return parameters

    def get_analysis_info(self, production_id):
        """ Return specific information for customers that have this order line
        """
        production_browse = self.pool.get("mrp.production").browse(self.cr, self.uid, production_id)
        note = {}

        for line in production_browse.order_lines_ids:
            if line.partner_id and line.partner_id.analysis_required and line.partner_id.name not in note:
                note[line.partner_id.name] = line.partner_id.analysis_note if line.partner_id.analysis_note else "Analysis mandatory"

        res = ""
        for key in note:
            res += "[%s] %s\n" % (key, note[key])
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
