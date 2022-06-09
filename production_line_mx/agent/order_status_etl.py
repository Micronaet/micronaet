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
import pdb
import sys
import pyodbc
import erppeek
import ConfigParser
import xlsxwriter
from datetime import datetime, timedelta

filename = 'order_from_contipaq.xlsx'


# -----------------------------------------------------------------------------
# Utility:
# -----------------------------------------------------------------------------
def get_erp(URL, database, user, password):
    """ Connect to log table in ODOO
    """
    return erppeek.Client(
        URL,
        db=database,
        user=user,
        password=password,
        )


def write_xls_mrp_line(WS, row, line, force_format=None):
    """ Write line in excel file
    """
    col = 0
    for record in line:
        if type(record) in (tuple, list) and len(record) == 2:
            item, format_cell = record
        else:
            item = record
            format_cell = force_format

        WS.write(row, col, item, format_cell)
        col += 1
    return True


def write_xls_mrp_line_comment(WS, row, line, gap_column=0):
    """ Write comment cell in excel file
    """
    parameters = {
        'width': 300,
    }
    col = gap_column
    for comment in line:
        if comment:
            WS.write_comment(row, col, comment, parameters)
        col += 1
    return True


# ---------------------------------------------------------------------
# XLS file:
# ---------------------------------------------------------------------
filename = os.path.expanduser(filename)

# Open file and write header
WB = xlsxwriter.Workbook(filename)

# 2 Sheets
WS_customer = WB.add_worksheet('Customer')
WS_supplier = WB.add_worksheet('Supplier')

# ---------------------------------------------------------------------
# Format elements:
# ---------------------------------------------------------------------
num_format = '#,##0'
format_title = WB.add_format({
    'bold': True,
    'font_color': 'black',
    'font_name': 'Arial',
    'font_size': 10,
    'align': 'center',
    'valign': 'vcenter',
    'bg_color': 'gray',
    'border': 1,
    'text_wrap': True,
})
format_header = WB.add_format({
    'bold': True,
    'font_color': 'black',
    'font_name': 'Arial',
    'font_size': 10,
    'align': 'center',
    'valign': 'vcenter',
    'bg_color': '#fcf683',  # Yellow
    'border': 1,
    'text_wrap': True,
})

format_text = WB.add_format({
    'font_name': 'Arial',
    'align': 'left',
    'font_size': 9,
    'border': 1,
})

format_white = WB.add_format({
    'font_name': 'Arial',
    'font_size': 9,
    'align': 'right',
    'bg_color': 'white',
    'border': 1,
    'num_format': num_format,
})
format_yellow = WB.add_format({
    'font_name': 'Arial',
    'font_size': 9,
    'align': 'right',
    'bg_color': '#ffff99',  # 'yellow',
    'border': 1,
    'num_format': num_format,
})
format_red = WB.add_format({
    'font_name': 'Arial',
    'font_size': 9,
    'align': 'right',
    'bg_color': '#ff9999',  # 'red',
    'border': 1,
    'num_format': num_format,
})
format_green = WB.add_format({
    'font_name': 'Arial',
    'font_size': 9,
    'align': 'right',
    'bg_color': '#c1ef94',  # 'green',
    'border': 1,
    'num_format': num_format,
})

# -----------------------------------------------------------------------------
#                                Parameters
# -----------------------------------------------------------------------------
# Extract config file name from current name
path, name = os.path.split(os.path.abspath(__file__))
fullname = os.path.join(path, 'openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([fullname])

# DSN block:
dsn = config.get('dsn', 'name')
uid = config.get('dsn', 'uid')
pwd = config.get('dsn', 'pwd')

# OpenERP block:
hostname = config.get('openerp', 'server')
port = config.get('openerp', 'port')
database = config.get('openerp', 'database')
user = config.get('openerp', 'user')
password = config.get('openerp', 'password')

URL = 'http://%s:%s' % (hostname, port)

# Access MS SQL Database customer table:
connection = pyodbc.connect('DSN=%s;UID=%s;PWD=%s' % (dsn, uid, pwd))
cr = connection.cursor()

# OPENERP Obj:
erp = get_erp(URL, database, user, password)

records = []

# -----------------------------------------------------------------------------
# Pedimento stock:
# -----------------------------------------------------------------------------
print('Start order detail')
query_list = {
    'customer': '''
        SELECT  
            ad.CIDDOCUMENTO, CCODIGOCLIENTE, ad.CRAZONSOCIAL, ad.CFECHA, 
            ad.CFECHAVENCIMIENTO, ad.CFOLIO, CSERIEDOCUMENTO,  
            act.CNOMBRECONCEPTO, ad.CNETO, ad.CTOTALUNIDADES, ad.CIMPUESTO1, 
            ad.CTOTAL, ad.CIDMONEDA, amo.CPLURAL, amo.CCLAVESAT, 
            am.CIDMOVIMIENTO, am.CNUMEROMOVIMIENTO, am.CIDPRODUCTO, 
            ap.CCODIGOPRODUCTO, ap.CNOMBREPRODUCTO, am.CUNIDADES, am.CPRECIO,  
            CASE 
                WHEN am.CUNIDADESPENDIENTES > 0 THEN 
                    am.CUNIDADES - am.CUNIDADESPENDIENTES 
                ELSE 
                    am.CUNIDADES 
            END Surtida, 
            am.CUNIDADESPENDIENTES, aum.CABREVIATURA, am.CNETO, 
            CASE CCANCELADO 
                WHEN 0 THEN 
                    CASE 
                        WHEN (am.CUNIDADESPENDIENTES <> am.CUNIDADES AND 
                              am.CUNIDADESPENDIENTES > 0) 
                            THEN 'Parcial' 
                        WHEN am.CUNIDADESPENDIENTES = 0 
                            THEN 'Surtido' 
                        WHEN am.CUNIDADESPENDIENTES = am.CUNIDADES 
                            THEN 'Sin Surtir' 
                        ELSE ' ' 
                    END 
                ELSE 'Cancelado' 
            END Estado    
        FROM 
            admDocumentos ad, admClientes ac, admConceptos act, 
            admMovimientos am, admProductos ap, admUnidadesMedidaPeso aum, 
            admMonedas amo      
        WHERE 
            ac.CIDCLIENTEPROVEEDOR = ad.CIDCLIENTEPROVEEDOR AND 
            act.CIDCONCEPTODOCUMENTO = ad.CIDCONCEPTODOCUMENTO AND 
            am.CIDDOCUMENTO = ad.CIDDOCUMENTO AND 
            ap.CIDPRODUCTO = am.CIDPRODUCTO AND 
            aum.CIDUNIDAD = am.CIDUNIDAD AND
            amo.CIDMONEDA = ad.CIDMONEDA AND
            -- ad.cfecha BETWEEN '2022-01-01' AND '2022-05-31' AND
            ad.CIDDOCUMENTODE = 2    
        ORDER BY CCODIGOCLIENTE, ad.crazonsocial, ad.cfecha;
        ''',

    'supplier':  ''' 
        SELECT 
            ad.CIDDOCUMENTO, CCODIGOCLIENTE, ad.CRAZONSOCIAL, ad.CFECHA, 
            ad.CFECHAVENCIMIENTO, ad.CFOLIO, CSERIEDOCUMENTO ,  
            act.CNOMBRECONCEPTO, ad.CNETO, ad.CTOTALUNIDADES, ad.CIMPUESTO1, 
            ad.CTOTAL, ad.CIDMONEDA, amo.CPLURAL, amo.CCLAVESAT,
            am.CIDMOVIMIENTO, am.CNUMEROMOVIMIENTO, am.CIDPRODUCTO, 
            ap.CCODIGOPRODUCTO, ap.CNOMBREPRODUCTO, am.CUNIDADES, am.CPRECIO,  
            CASE 
                WHEN am.CUNIDADESPENDIENTES > 0 THEN 
                    am.CUNIDADES - am.CUNIDADESPENDIENTES 
                ELSE am.CUNIDADES 
                END Surtida, 
            am.CUNIDADESPENDIENTES, aum.CABREVIATURA, am.CNETO, 
            CASE CCANCELADO 
                WHEN 0 THEN CASE WHEN (
                    am.CUNIDADESPENDIENTES <> am.CUNIDADES AND 
                    am.CUNIDADESPENDIENTES > 0) THEN 
                        'Parcial' 
                WHEN am.CUNIDADESPENDIENTES = 0 THEN 
                    'Surtido'
                WHEN am.CUNIDADESPENDIENTES = am.CUNIDADES THEN 
                    'Sin Surtir' 
                ELSE 
                    ' '  
                END 
            ELSE 'Cancelado' 
            END Estado
        FROM 
            admDocumentos ad, admClientes ac, admConceptos act, 
            admMovimientos am, admProductos ap, admUnidadesMedidaPeso aum, 
            admMonedas amo  
        WHERE 
            ac.CIDCLIENTEPROVEEDOR = ad.CIDCLIENTEPROVEEDOR AND 
            act.CIDCONCEPTODOCUMENTO = ad.CIDCONCEPTODOCUMENTO AND 
            am.CIDDOCUMENTO = ad.CIDDOCUMENTO AND 
            ap.CIDPRODUCTO = am.CIDPRODUCTO AND 
            aum.CIDUNIDAD = am.CIDUNIDAD AND 
            amo.CIDMONEDA = ad.CIDMONEDA AND
            -- ad.cfecha BETWEEN '2022-01-01' AND '2022-05-31' AND
            ad.CIDDOCUMENTODE = 17
        ORDER BY CCODIGOCLIENTE, ad.crazonsocial, ad.cfecha;
    ''',
    }

# query_records = {}
header = [
    'ID Ordine',
    'Cod. partner',
    'Cliente',
    'Data',
    'Scadenza',
    'Numero ord.',
    'Serie ord.',
    'Tipo ord.',
    'Imp. ordine',
    'Q. ordine',
    'IVA ordine',
    'Tot. ordine',
    'ID Valuta',
    'Valuta',
    'Sigla',

    'ID Movimento',
    'Seq.',
    'ID Prodotto',
    'Codice',
    'Descrizione',
    'Ordinati',
    'Prezzo unit.',
    'Arrivati',
    'Attesi',
    'UM',
    'Netto riga',
    'Stato riga',
]

for key in query_list:
    if key == 'customer':
        WS = WS_customer
    else:
        WS = WS_supplier

    # Column dimension:
    WS.set_column('A:B', 7)
    WS.set_column('C:C', 30)
    WS.set_column('D:E', 14)
    WS.set_column('H:H', 18)
    WS.set_column('I:G', 8)
    WS.set_column('F:L', 10)
    WS.set_column('M:O', 7)
    WS.set_column('P:P', 10)
    WS.set_column('Q:R', 5)
    WS.set_column('S:S', 10)
    WS.set_column('T:T', 16)
    WS.set_column('U:X', 10)
    WS.set_column('Y:Y', 5)
    WS.set_column('Z:AA', 10)
    WS.set_row(0, 15)

    # Start loop for design table for product and material status:
    # Header:
    row = 0
    write_xls_mrp_line(WS, row, header, format_header)

    query = query_list[key]
    print('Executing ...:\n%s' % query)
    cr.execute(query)
    for record in cr.fetchall():
        if record[26] not in ('Parcial', 'Sin Surtir'):
            continue  # Closed order line
        row += 1
        record = list(record)
        record[3] = str(record[3])
        record[4] = str(record[4])
        write_xls_mrp_line(WS, row, record, format_text)
WB.close()

product_pool = erp.model('sale.order')
# product_pool.rpc_import_order_mx(stock)

