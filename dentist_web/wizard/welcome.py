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
import netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

class dentist_welcome_wizard(orm.TransientModel):
    """ Welcome wizard for startup message
    """    
    _name = 'dentist.welcome.wizard'
               
    _columns = {
        'message': fields.text('Welcome message'),
        }
        
    _defaults = {
        'message': lambda *x: """
            <p><b>Benvenuti!</b></p>
            <p>Benvenuti!
               Questo programma si occupa della gestione di un Poliambulatorio. Potete navigare all'interno del programma in completa autonomia facendo riferimento al menu qui a sinistra.<br/>
               Tutte le funzioni sono attivate in lettura/scrittura pertanto sarà possibile creare e cancellare records relativi ad appuntamenti, pazienti, preventivi, ecc.<br/>
               In questo menu vengono riepilogate le funzioni principali della gestione: anagrafiche pazienti, appuntamenti visualizzabili graficamente in base a diversi criteri, preventivi e configurazione per la creazione di nuovi ambulatori. Per semplificare abbiamo preferito raggruppare queste funzioni in un unico menu ma il programma consente di gestire naturalmente anche la fatturazione e i pagamenti, le giacenze di magazzino e tutto il ciclo passivo.<br/>
               Non abbiate timore di cancellare dati e di crearne altri visto che il database viene ripristinato al suo stato originale con cadenza giornaliera. <br/>
               Qualora sia necessario un aiuto per orientarsi o per qualsiasi altra informazione, non esitate a contattarci cliccando su "Richiesta informazioni".<br/>
               Buon lavoro
            </p>
            """
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
