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
cfg_file = os.path.expanduser('./openerp.cfg')
now = ('%s' % datetime.now())[:19]
now_text = now.replace('/', '_').replace('-', '_').replace(':', '_')

config = ConfigParser.ConfigParser()
config.read([cfg_file])

filename = '/tmp/stock_status_commpleted.xlsx'

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

        <p>questa &egrave; una mail automatica inviata da 
            <b>OpenERP</b> con lo stato materie prime, come da magazzino,
            in data: <b>%s</b>
        </p>
        <p>
        I 3 colori indicano lo stato le prodotto:<br/>
        - Bianco: presente<br/>
        - Giallo: sotto il livello di scorta minimo<br/>
        - Rosso: non presente o negativo<br/>        
        </p>

        <p><i>Le colonne: obsoleto, escludi, leadtime e gg. approvv. si possono
        usare anche per impostare in Excel per poi reimportarle in OpenERP!
        </i></p>

        <b>Micronaet S.r.l.</b>
        ''' % now,
    'subject': 'PAN Stato magazzino: %s' % now,
    'folder': config.get('smtp', 'folder'),
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
wizard = odoo.model('product.product.extract.xls.wizard')

# Launch extract procedure:
wizard.action_done_filename(filename)

# -----------------------------------------------------------------------------
# SMTP Sent:
# -----------------------------------------------------------------------------
# Get mailserver option:
mailer_ids = mailer.search([])
if not mailer_ids:
    print('[ERR] No mail server configured in ODOO')
    sys.exit()

odoo_mailer = mailer.browse(mailer_ids)[0]

# Open connection:
print('[INFO] Sending using "%s" connection [%s:%s]' % (
    odoo_mailer.name,
    odoo_mailer.smtp_host,
    odoo_mailer.smtp_port,
))

if odoo_mailer.smtp_encryption in ('ssl', 'starttls'):
    smtp_server = smtplib.SMTP_SSL(
        odoo_mailer.smtp_host, odoo_mailer.smtp_port)
else:
    print('[ERR] Connect only SMTP SSL server!')
    sys.exit()
    # server_smtp.start() # TODO Check

smtp_server.login(odoo_mailer.smtp_user, odoo_mailer.smtp_pass)
for to in smtp['to'].replace(' ', '').split(','):
    print('Senting mail to: %s ...' % to)
    msg = MIMEMultipart()
    msg['Subject'] = smtp['subject']
    msg['From'] = odoo_mailer.smtp_user
    msg['To'] = to  # smtp['to'] #', '.join(self.EMAIL_TO)
    msg.attach(MIMEText(smtp['text'], 'html'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(open(filename, 'rb').read())
    Encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        'attachment; filename="PAN Stato_magazzino_%s.xlsx"' % now_text)
    msg.attach(part)

    # Send mail:
    smtp_server.sendmail(odoo_mailer.smtp_user, to, msg.as_string())

smtp_server.quit()
