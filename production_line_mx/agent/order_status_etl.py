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


# -----------------------------------------------------------------------------
#                                UTILITY
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
            ad.cfecha BETWEEN '2022-01-01' AND '2022-05-31' AND
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
            CASE WHEN am.CUNIDADESPENDIENTES > 0 THEN 
                am.CUNIDADES - am.CUNIDADESPENDIENTES ELSE am.CUNIDADES END 
                Surtida, 
            am.CUNIDADESPENDIENTES, aum.CABREVIATURA, am.CNETO, 
            CASE CCANCELADO WHEN 0 THEN CASE WHEN (
                am.CUNIDADESPENDIENTES <> am.CUNIDADES AND 
                am.CUNIDADESPENDIENTES > 0) THEN 'Parcial' WHEN 
                am.CUNIDADESPENDIENTES = 0 THEN 'Surtido' WHEN 
                am.CUNIDADESPENDIENTES = am.CUNIDADES THEN 'Sin Surtir' 
                ELSE ' '  
                END ELSE 'Cancelado' END Estado
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
            ad.cfecha BETWEEN '2022-01-01' AND '2022-05-31' AND
            ad.CIDDOCUMENTODE = 17
        ORDER BY CCODIGOCLIENTE, ad.crazonsocial, ad.cfecha;
    ''',
    }

pdb.set_trace()
query_records = {}
for key in query_list:
    query_records[key] = []
    query = query_list[key]
    print('Executing ...:\n%s' % query)
    cr.execute(query)
    for record in cr.fetchall():
        row = tuple(record)
        print(row)
        query_records[key].append(row)

product_pool = erp.model('sale.order')
# product_pool.rpc_import_order_mx(stock)

