# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import erppeek
import ConfigParser
import smtplib  
from datetime import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.mime.text import MIMEText
from email import Encoders

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
cfg_file = os.path.expanduser('../openerp.cfg')
now = ('%s' %datetime.now())[:19]

config = ConfigParser.ConfigParser()
config.read([cfg_file])

# ERP Connection:
odoo = {
    'database': config.get('dbaccess', 'dbname'),
    'user': config.get('dbaccess', 'user'),
    'password': config.get('dbaccess', 'pwd'),
    'server': config.get('dbaccess', 'server'),
    'port': config.get('dbaccess', 'port'),
    }

# Mail:
smtp = {
    'to': config.get('smtp', 'to'),
    'text': '''
        <p>Spett.li responsabili produzione PCA,</p>
        <p>Questa &egrave; una mail automatica giornaliera inviata da 
            <b>OpenERP</b> con lo stato produzioni e magazzino contabile.<br/>
            Dove sono presenti valorizzazioni di prezzo va considerata la 
            valuta attualmente impostata in ContipaQ.            
        </p>

        <p>Situazione aggiornata alla data di riferimento: <b>%s</b></p>

        <p>
           <b>Dati di magazzino:</b><br/>
        1. <b>Lotti:</b> Elenco lotti con esistenza e valorizzazione;
            dati che arrivano da ContipaQ. Totali suddivisi per UM.<br/>
        2. <b>Prodotti:</b> Elenco prodotti con esistenza e valorizzazione;
            dati che arrivano da ContipaQ. Totali suddivisi per UM.<br/>
        </p>

        <p>
           <b>Dettagli di produzione:</b><br/>
        3. <b>Carichi produzione:</b> Dettaglio carichi di ogni lavorazione,
              vengono indicati anche i carichi da recuperare (in azzurro).
              La valorizzazione viene calcolata con il totale dei costi
              delle materie prime, degli imballi, dei bancali e del 
              coefficente K di lavorazione per la linea in questione.<br/>
        4. <b>Sarichi produzione:</b> Dettaglio scarichi di ogni lavorazione,
              sono presenti anche i recuperi, gli imballi e i bancali 
              utilizzati nel processo produttivo. La valorizzazione &egrave; 
              datta al prezzo del pedimento, se presente, o al prezzo materia 
              prima.<br/>
        5. <b>Controllo produzione:</b> Verifica scarico e carico con
              segnalazione oltre 10%%. Colori:<br/> 
                 Blu = nessuna pertita<br/>
                 Rosso = prodotto maggiore delle materie prime<br/>
                 Giallo = perdita oltre il 10%%.<br/>
        </p>

        <p>
           <b>Riepilogo di produzione:</b><br/>
        6. <b>Produzioni periodo:</b> Riepilogo dove si estrapola il carico di 
              produzione mensile e il totale produzione di ogni prodotto.<br/> 
              Nelle colonne &egrave; anche possibile avere il dettaglio 
              produzione: prodotto per mese.<br/> 
              Questa stampa viene ricavata dai dati indicato nel foglio 3.<br/>
        7. <b>Scarichi periodo:</b> Riepilogo dove si estrapola lo scarico di 
              materiali mensile e il totale scarico materia prima totale.<br/>
              Nelle colonne &egrave; anche possibile avere il dettaglio 
              scarico: materia prima per mese.<br/>
              Questa stampa viene ricavata dai dati indicato nel foglio 4.<br/>
        </p>

        <p>
            <i>Nota magazzino: Nello stato di magazzino (Lotti e Prodotti) sono 
               evidenziati in rosso le righe con prodotti che non hanno prezzo.
               <br/>
               I lotti senza esistenza sono stati eliminati dalla stampa.
               </i>
        </p>
        <p>
            <i>Nota produzione: Nei fogli di produzione la data indicata viene
               ricavata da quella della produzione, questo &egrave; dovuto
               al fatto che sono state inserite le produzioni a blocchi per
               coprire il periodo in cui non &egrave; stato utilizzato il 
               programma. Da agosto invece si prende la corretta data di 
               carico e scarico indicata.<br/>
               Non escludo una correzione nel database per regolarizzare i dati
               con la collaborazione di Edna.               
               </i>
        </p>
        <b>Micronaet S.r.l.</b>
        ''' % now,
    'subject': 'Dettaglio produzione PCA e stato magazzino: %s' % now,    
    
    'folder': config.get('smtp', 'folder'),
    }

filename = os.path.expanduser(
    os.path.join(smtp['folder'], 'statistiche_produzione.xlsx'))
context = {
    'save_mode': filename,
    }

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (odoo['server'], odoo['port']), 
    db=odoo['database'],
    user=odoo['user'],
    password=odoo['password'],
    )
mailer = odoo.model('ir.mail_server')
model = odoo.model('ir.model.data')

# Setup context for MRP:
odoo.context = context
mrp = odoo.model('mrp.production')

# Launch extract procedure:
mrp.extract_mrp_stats_excel_report()

# -----------------------------------------------------------------------------
# SMTP Sent:
# -----------------------------------------------------------------------------
# Get mailserver option:
mailer_ids = mailer.search([])
if not mailer_ids:
    print '[ERR] No mail server configured in ODOO'
    sys.exit()

odoo_mailer = mailer.browse(mailer_ids)[0]

# Open connection:
print '[INFO] Sending using "%s" connection [%s:%s]' % (
    odoo_mailer.name,
    odoo_mailer.smtp_host,
    odoo_mailer.smtp_port,
    )

if odoo_mailer.smtp_encryption in ('ssl', 'starttls'):
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
else:
    print '[ERR] Connect only SMTP SSL server!'
    sys.exit()

smtp_server.ehlo() #open the connection
smtp_server.starttls()
smtp_server.login(odoo_mailer.smtp_user, odoo_mailer.smtp_pass)


for to in smtp['to'].replace(' ', '').split(','):
    print 'Senting mail to: %s ...' % to
    msg = MIMEMultipart()
    msg['Subject'] = smtp['subject']
    msg['From'] = odoo_mailer.smtp_user
    msg['To'] = smtp['to'] #', '.join(self.EMAIL_TO)
    msg.attach(MIMEText(smtp['text'], 'html'))


    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition', 'attachment; filename="Stato vendite.xlsx"')

    msg.attach(part)

    # Send mail:
    smtp_server.sendmail(odoo_mailer.smtp_user, to, msg.as_string())

smtp_server.quit()
