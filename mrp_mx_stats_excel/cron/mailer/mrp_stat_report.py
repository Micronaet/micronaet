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
    'mode': eval(config.get('smtp', 'mode')),
    'text': {
        'all': '''
            <p>A los Gerentes de producci&oacute;n de PCA,</p> 

            <p>
            Este es un correo diario autom&aacute;tico enviado por <b>OpenERP</b> 
            con el estado del almac&eacute;n de producci&oacute;n y contabilidad.
            <br/>
            Cuando los valores de precios est&aacute;n presentes, debe considerarse
            la moneda establecida actualmente en ContipaQ.
            </p>

            <p>
            Situaci&oacute;n actualizada a la fecha de referencia: <b>%s</b>
            </p>

            <p>
            <b>Datos de inventario</b>:
                (MP = Materia prima, PF = Productos terminados, 
                IT = Producto terminado italiano)
                <br/>

            1. <b>Lotes:</b> Lista de lotes con existencia y valor; 
                datos provenientes de ContipaQ. 
                Totales subdivididos por UM (unidad de medida).
                <br/>

            2. <b>Inventario:</b> Lista de productos con existencia y mejora; 
                datos provenientes de ContipaQ. Totales subdivididos por UM 
                (unidad de medida).
                <br/>
            </p>

            <p>
            <b>Detalles de producci&oacute;n:</b>
            <br/>
            3. <b>Cargas de producci&oacute;n:</b> Se indican los detalles de las 
                cargas de cada procesamiento, y tambi&eacute;n las cargas a 
                recuperar (en azul). El valor se calcula con los costes totales de 
                las materias primas, envases, tarimas y el coeficiente de trabajo K 
                para la l&iacute;nea en cuesti&oacute;n.
                <br/>

            4. <b>Descargas de producci&oacute;n:</b> Detalle de las descargas de 
                cada procesamiento, tambi&eacute;n hay recuperaciones, empaques y 
                tarimas utilizadas en el proceso de producci&oacute;n. El valor se 
                basa en el precio del pedimento, si est&aacute; presente, o en el 
                precio de la materia prima.
                <br/>

            5. <b>Control de producci&oacute;n:</b> Verificaci&oacute;n de 
                descargas y cargas con se&ntilde;alaci&oacute;n superiores al 10%%. 
                    colores:
                    <br/>
                    
                &nbsp;&nbsp;&nbsp;Azul = sin p&eacute;rdida
                <br/>
                
                &nbsp;&nbsp;&nbsp;Rojo = mayor producto que las materias primas!
                <br/>
                
                &nbsp;&nbsp;&nbsp;Amarillo = p&eacute;rdida superior al 10%%.
                <br/>
            </p>

            <p>
            <b>Resumen de producci&oacute;n:</b><br/>
            6. <b>Producci&oacute;n en el periodo:</b> resumen donde se extrapola 
                la carga de producci&oacute;n mensual y la producci&oacute;n total 
                de cada producto.<br/>
                En las columnas es tambi&eacute;n posible tener el detalle de 
                producci&oacute;n: producto por mes.
                <br/>

                Esta impresi&oacute;n se toma desde los datos indicados en la hoja 
                3.<br/>

            7. <b>Descargas en el periodo:</b> Resumen donde se extrapola la 
                descarga mensual de material y la descarga total de la materia 
                prima total.
                </br>
                
                En las columnas tambi&eacute;n es posible descargar el detalle:
                </br>
                
                materia prima por mes.<br/>
                
                Esta impresi&oacute;n se toma desde los datos indicados en la hoja 
                4.
                <br/>
            </p>

            <p>
            <i>
            Nota de existencias: en el almac&eacute;n (lotes y productos) las 
            l&iacute;neas con productos que no tienen precio se resaltan en rojo.
            <br/>
            
            Los lotes sin existencia han sido eliminados de la prensa.
            </i>
            </p>
            
            <b>Micronaet S.r.l.</b><br/>

            <i>
            Nota de producci&oacute;n: en las hojas de producci&oacute;n, la fecha 
            indicada se toma desde la fecha de producci&oacute;n, esto se debe 
            porque las producciones en bloque se insertaron para cubrir el 
            per&iacute;odo en el que no se utiliz&oacute; el programa. A partir de 
            agosto 2019, se toma la fecha correcta de carga y descarga indicada.
            <br/></i>

            <p>
            No excluyo una correcci&oacute;n en el database para regularizar los 
            datos con la colaboraci&oacute;n de Edna.
            <br/>
            </p>
            ''' % now,
            
        'minimal': '''
            <p>A los Gerentes de producci&oacute;n de PCA,</p> 

            <p>
            Este es un correo diario autom&aacute;tico enviado por <b>OpenERP</b> 
            con el estado del almac&eacute;n de producci&oacute;n y contabilidad.
            <br/>
            Cuando los valores de precios est&aacute;n presentes, debe considerarse
            la moneda establecida actualmente en ContipaQ.
            </p>

            <p>
            Situaci&oacute;n actualizada a la fecha de referencia: <b>%s</b>
            </p>

            <p>
            <b>Datos de inventario</b>:
                (MP = Materia prima, PF = Productos terminados, 
                IT = Producto terminado italiano)
                <br/>

            1. <b>Inventario:</b> Lista de productos con existencia y mejora; 
                datos provenientes de ContipaQ. Totales subdivididos por UM 
                (unidad de medida).
                <br/>
            </p>

            <p>
            <b>Detalles de producci&oacute;n:</b>
            <br/>
            2. <b>Control de producci&oacute;n:</b> Verificaci&oacute;n de 
                descargas y cargas con se&ntilde;alaci&oacute;n superiores al 10%%. 
                    colores:
                    <br/>
                    
                &nbsp;&nbsp;&nbsp;Azul = sin p&eacute;rdida
                <br/>
                
                &nbsp;&nbsp;&nbsp;Rojo = mayor producto que las materias primas!
                <br/>
                
                &nbsp;&nbsp;&nbsp;Amarillo = p&eacute;rdida superior al 10%%.
                <br/>
            </p>

            <p>
            <b>Resumen de producci&oacute;n:</b><br/>
            3. <b>Producci&oacute;n en el periodo:</b> resumen donde se extrapola 
                la carga de producci&oacute;n mensual y la producci&oacute;n total 
                de cada producto.<br/>
                En las columnas es tambi&eacute;n posible tener el detalle de 
                producci&oacute;n: producto por mes.
                <br/>

            4. <b>Descargas en el periodo:</b> Resumen donde se extrapola la 
                descarga mensual de material y la descarga total de la materia 
                prima total.
                </br>
                
                En las columnas tambi&eacute;n es posible descargar el detalle:
                </br>
                
                materia prima por mes.<br/>
                <br/>
            </p>

            <p>
            <i>
            Nota de existencias: en el almac&eacute;n (inventario) las 
            l&iacute;neas con productos que no tienen precio se resaltan en rojo.
            <br/>
            
            Los lotes sin existencia han sido eliminados de la prensa.
            </i>
            </p>
            
            <b>Micronaet S.r.l.</b><br/>

            <i>
            Nota de producci&oacute;n: en las hojas de producci&oacute;n, la fecha 
            indicada se toma desde la fecha de producci&oacute;n, esto se debe 
            porque las producciones en bloque se insertaron para cubrir el 
            per&iacute;odo en el que no se utiliz&oacute; el programa. A partir de 
            agosto 2019, se toma la fecha correcta de carga y descarga indicada.
            <br/></i>

            <p>
            No excluyo una correcci&oacute;n en el database para regularizar los 
            datos con la colaboraci&oacute;n de Edna.
            <br/>
            </p>
            ''' % now,
        },
            
    'subject': 'PCA Detalles de produccion / ContipaQ : %s' % now,    
    
    'folder': config.get('smtp', 'folder'),
    }

now = now.replace('/', '_').replace('-', '_').replace(':', '_')

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


# Setup context for MRP:
odoo.context = context
mrp = odoo.model('mrp.production')

# Extract 2 files
import pdb; pdb.set_trace()
for mode in smtp['mode']:
    if not smtp['mode'][mode]:
        print('No recipients for mode: %s' % mode)
        continue

    filename = u'PCA OpenERP Contipaq %s.%s.xlsx' % (now, mode)
    fullname = os.path.expanduser(
        os.path.join(smtp['folder'], filename))
    context = {
        'save_mode': fullname,
        }

    # Launch extract procedure for this mode:
    mrp.extract_mrp_stats_excel_report(mode)

    for to in smtp[mode]:
        to = to.replace(' ', '')
        print 'Senting mail %s to: %s ...' % (mode, to)
        msg = MIMEMultipart()
        msg['Subject'] = smtp['subject']
        msg['From'] = odoo_mailer.smtp_user
        msg['To'] = smtp[mode] # See all delivery!
        msg.attach(MIMEText(smtp['text'][mode], 'html'))


        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(fullname, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition', 'attachment; filename="%s"' % filename)

        msg.attach(part)

        # Send mail:
        smtp_server.sendmail(odoo_mailer.smtp_user, to, msg.as_string())

smtp_server.quit()
