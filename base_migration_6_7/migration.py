# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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

from openerp.osv import osv, fields

class migration_mapping(osv.osv):
    ''' Migration mapping table for ID
    ''' 
    _name = 'migration.mapping'
    _description = 'Migration mapping table'

    _columns = {
               'name': fields.char('Database name', size=40, required=True, readonly=False, help="Object name v. 6.0 (and v. 7.0)"),
               'old_id': fields.integer('V.6 ID', required=True, readonly=False, help="ID element V. 6.0"),
               'new_id': fields.integer('V.7 ID', required=True, readonly=False, help="ID element V. 7.0"),
               }
migration_mapping()
            
class migration_server(osv.osv):
    ''' Migration server configuration
    ''' 
    _name = 'migration.server'
    _description = 'Migration Server'

    def get_parameters(self, cr, uid, context=None):
        ''' Read the only record and return browse obj
            return browse object for read XML-RPC parameter or PG parameters
        '''
        item_ids = self.search(cr, uid, [], context=context)
        if item_ids:
            return self.browse(cr, uid, item_ids, context=context)[0]
        return False

    def get_pg_cursor(self, cr, uid, context=None):
        ''' Connect to PG and return cursor
        '''
        import psycopg2
        
        parameters = self.get_parameters(cr, uid, context=context)
        try:
            connection = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'"%(parameters.dbname, parameters.username, parameters.server, parameters.password ))
        except:
            return False
        return connection.cursor()   # cur.execute("""SELECT datname from pg_database""")         rows = cur.fetchall()

    def get_xmlrpc(self, cr, uid, context=None):
        ''' Get xmlrpx object for read data from V.6
        '''
        import logging, sys, xmlrpclib
        _logger = logging.getLogger('base_migration_6_7')

        parameters = self.get_parameters(cr, uid, context=context)
        error=(False, False, False)
        if not parameters:
            return error

        # XMLRPC connection for autentication (UID) and proxy 
        try: 
            sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/common'%(parameters.server, parameters.port), allow_none = True)
            uid = sock.login(parameters.dbname, parameters.username , parameters.password)
            if not uid: return error
            sock = xmlrpclib.ServerProxy('http://%s:%s/xmlrpc/object'%(parameters.server, parameters.port), allow_none = True)
            return sock, uid, parameters
        except:
            return error
        
    _columns = {
               'name': fields.char('Database name', size=40, required=True, readonly=False, help="Database name for version 6.0"),
               'server': fields.char('Server V.6', size=40, required=True, readonly=False, help="Server name or IP address (or hostname for PG) OpenERP version 6.0"),
               'dbname': fields.char('DB name V.6', size=40, required=True, readonly=False, help="DB name of version 6.0"),
               'port': fields.integer('XML-RPC port', required=True, readonly=False, help="Server port for version 6.0 (for PG use 5432, for XML-RPC use 8069"),
               'username': fields.char('User name V.6', size=40, required=True, readonly=False, help="User name for database version 6.0"),
               'password': fields.char('Password V.6', size=40, required=True, readonly=False, help="Password for database version 6.0"),
    }
    
    _defaults = {
        'port': lambda *a: 5432,
        'username': lambda *a: 'admin',
    }
migration_server()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
