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
#cfg_file = os.path.expanduser('../local.cfg')
cfg_file = os.path.expanduser('./openerp.cfg')
now = ('%s' %datetime.now())[:19]

config = ConfigParser.ConfigParser()
config.read([cfg_file])

filename = '/tmp/production_status.xlsx' # From wizard parameter!

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
        <p>Spett.li responsabili acquisto,</p>

        <p>questa &egrave; una mail automatica giornaliera inviata da 
            <b>OpenERP</b> con lo stato materie prime in funzione del
            magazzino attuale e delle produzioni schedulate, data: <b>%s</b>
        </p>

        <p>
        La stampa presenta una finestra di 30 giorni nella quale viene indicato
        lo stato giornaliero del magazzino, nella valorizzazione intervengono: 
        <br/>
        - lo stato attuale da programma di contabilit&agrave;<br/>
        - le uscite di produzione pianificate (segno negativo)<br/>
        - le consegne di materiale da fornitore (segno positivo)<br/>
        </p>

        <p>
        Le materie prime visibili sono solo quelle sotto il livello di 
        riordino. 
        Nella stampa viene indicata la media delle produzione con una finestra
        di 3 mesi antecedenti.
        </p>
        
        <p><i>In giallo vengono indicate le celle dei prodotti sotto il 
            livello minimo di riordino, in rosso le celle negative.</i></p>

        <b>Micronaet S.r.l.</b>


        ''' % now,
    'subject': 'Stato materie prime con produzioni schedulate: %s' % now,    
    'folder': config.get('smtp', 'folder'),
    }

context = {
    'save_mode': True,

    # Wizard setup:
    'datas': {
        'days': 30,
        'row_mode': 'negative',
        'with_medium': True,
        'month_window': 3,
        'with_order_detail': True,
        'fake_ids': [], # TODO << nothing?
        },
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

# Setup context for order:
print context
odoo.context = context
wizard = odoo.model('product.status.wizard')

# Launch extract procedure:
wizard.schedule_send_negative_report_mailer()

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
    smtp_server = smtplib.SMTP_SSL(
        odoo_mailer.smtp_host, odoo_mailer.smtp_port)
else:
    print '[ERR] Connect only SMTP SSL server!'
    sys.exit()
    #server_smtp.start() # TODO Check

smtp_server.login(odoo_mailer.smtp_user, odoo_mailer.smtp_pass)
for to in smtp['to'].replace(' ', '').split(','):
    import pdb; pdb.set_trace()
    msg = MIMEMultipart()
    msg['Subject'] = smtp['subject']
    msg['From'] = odoo_mailer.smtp_user
    msg['To'] = to #smtp['to'] #', '.join(self.EMAIL_TO)
    msg.attach(MIMEText(smtp['text'], 'html'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition', 'attachment; filename="Stato materie prime.xlsx"')
    msg.attach(part)

    # Send mail:
    smtp_server.sendmail(odoo_mailer.smtp_user, to, msg.as_string())#smtp['to'].split(',')

smtp_server.quit()
