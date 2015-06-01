# coding=utf-8
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
import sys
import os
from openerp.osv import osv, fields
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)

class construction_web(osv.osv):
    ''' Construction catalog web
    '''
    _name = 'construction.web'
    _description = 'Construction catalog web'

    _columns = {
        'name': fields.char('Version name', size = 30, required = True, help = 'Catalog version', ),
        'active': fields.boolean('Active', ),
        'web': fields.char('Web FTP file mask', size = 100, required = True, help = 'Es.: http://www.example.com/sw/%Y/TCCBS%q%y.tar' ),
        'category_id': fields.many2one('product.category', 'Root category', required = True, help = 'Default root category for import all sub categories'),
        'note': fields.text('Note', help = 'Extra info catalog importation'),
    }
    _defaults = {
        'active': lambda *x: False,
    }

class construction_catalog(osv.osv):
    ''' Construction catalog imported via web (version)
    '''
    _name = 'construction.catalog'
    _description = 'Construction catalog'

    # ------------
    # Button event
    # ------------    
    def dowload_catalog(self, cr, uid, ids, context = None):
        ''' Download manually the catalog (and import)
        '''
        catalog_proxy = self.browse(cr, uid, ids, context = context)[0] # TODO
        
        self.pool.get('product.product').schedule_import_construction_catalog(
            cr, uid, 
            ftp_file = "http://www.cerbrescia.it/sw/2013/TCCBS413.tar", 
            ftp_name = 'TCCBS413.tar', 
            root_category = catalog_proxy.web_id.category_id.id, 
            context = context,
            )
        return True

    def dowload_uom(self, cr, uid, ids, context = None):
        ''' Download manually the catalog uom for correction after real import
        '''
        if context is None:
            context = {}
            
        context['only_uom'] = True
        self.dowload_catalog(cr, uid, ids, context = context)
        return True
   
    _columns = {
        'name': fields.char('Version name', size = 30, required = True, help = 'Catalog version', ),
        'year': fields.char('Year', size = 4, required = True, help = 'Year of the catalog AAAA format', ),
        'quad': fields.char('Quad', size = 1, required = True, help = 'Quarter of year format N', ),
        'date': fields.date('Date', help = 'Date of download ad installation'),
        'active': fields.boolean('Active', ),
        'file_name': fields.char('File name', size = 100, required = True, ),
        'web_id': fields.many2one('construction.web', 'Web FTP site', ),
        'note': fields.text('Note', help = 'Extra info catalog importation'),
    }
    _defaults = {
        'active': lambda *x: False,
        'date': lambda *x: datetime.now().strftime("%Y-%m-%d"),
    }

class construction_catalog(osv.osv):
    ''' Construction catalog imported via web
    '''
    _name = 'construction.web'
    _inherit = 'construction.web'

    _columns = {
        'catalog_ids': fields.one2many('construction.catalog', 'web_id', "Version",),
    }

class construction_catelog_uom(osv.osv):
    ''' Construction catalog conversion uom
    '''
    _name = 'construction.catalog.uom'
    _description = 'Catalog uom conversion'

    _columns = {
        'name': fields.char('Value in CSV', size = 15, required = True, help = 'UOM indicated in importation files', ),
        'uom_id': fields.many2one('product.uom', 'UOM', required = False, help = 'UOM in OpenERP'), # not required because imported
    }

class product_category(osv.osv):
    ''' Extend product.category
    '''
    _name = 'product.category'
    _inherit = 'product.category'
    
    _columns = {
        'construction_catalog': fields.boolean('Construction category', required=False, help = 'Category imported from catalog'),
        'construction_code': fields.char('Construction code', size = 10, required = False, ),
    }
    _defaults = {
        'construction_catalog': lambda *x: False,
    }

class sale_order(osv.osv):
    ''' Extend sale.order
    '''
    _name = 'sale.order'
    _inherit = 'sale.order'
    
    _columns = {
        'default_category_id': fields.many2one('product.category', 'Focus category', required=False),
    }

class sale_order_line(osv.osv):
    ''' Extend sale.order.line
    '''
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    
    _columns = {
        'filter_category_id': fields.many2one('product.category', 'Filter', required=False),
    }

class product_product(osv.osv):
    ''' Extend product.product
    '''
    _name = 'product.product'
    _inherit = 'product.product'

    _columns = {
        'construction_catalog': fields.boolean('Construction catalog', required=False, help = 'Product imported and sync in web production catalog'),
        'percentual': fields.float('Percentual %', digits=(16, 3), help = 'Percentual value depend on other elements (only for rember)'),
        'categ_parent_id':fields.many2one('product.category', 'Parent category', required = False),
    }

    _defaults = {
        'construction_catalog': lambda *a: False,        
    }

    # Scheduled action: ########################################################
    def schedule_import_construction_catalog(self, cr, uid, default_path = None, ftp_file = False, ftp_name = False, root_category = False, context=None):
        ''' Import product from web catalog
        '''
        import csv
        cambio = 1936.27
        
        _logger.info('Check on web if there\'s a catalog and start import!')

        # --------------------------
        # Create default path for DB
        # --------------------------
        if default_path is None:
            default_path = ("~", "openerp_catalog", cr.dbname, )
        try:
            root_path = os.path.expanduser(os.path.join(*default_path))
            os.mkdir(root_path)
        except:
            pass

        # ------------------
        # Download database:
        # ------------------
        today = datetime.now()   # also start time
        if not ftp_file:
            ftp_file = "http://www.cerbrescia.it/sw/%s/TCCBS%s%y.tar" % (today.strftime("%Y"), 1 + today.month // 4 , today.strftime("%y")) # 2013  1 13
            ftp_name = "TCCBS%s%y.tar" % (1 + today.month // 4 , today.strftime("%y")) # 2013  1 13
        
        if not os.path.isfile(os.path.join(root_path, ftp_name)): # only if not present (for now) TODO
            os.system ('cd %s;wget %s' % (root_path, ftp_file))
        today_end = datetime.now()   # also start time
        #if False: # test duration > 30 sec.# TODO or dimension of file

        # ---------------------
        # Extract data from DB:
        # ---------------------
        os.system ('cd %s;mdb-export -d "|" %s ELENCO > elenco.csv' % (root_path, ftp_name, ))
        os.system ('cd %s;mdb-export -d "|" %s Sommario > sommario.csv' % (root_path, ftp_name, ))
        ##os.system ('cd %s;mdb-export %s -d "|" "Sommario Ufficiale" > sommario_ufficiale.csv' % (root_path, ftp_name, ))

        # ----------------
        # Import category:
        # ----------------
        separator = "|"
        i = -1                    # no 1st line
        category_converter = {}   # For category
        category_pool = self.pool.get('product.category')
        elenco_csv = open(os.path.join(root_path, "sommario.csv"), "r")
        for line in elenco_csv:
            try:
                i += 1
                if i == 0: # jump firs line                
                    continue
                line_csv = line.replace("\"", "").split(separator)
                
                code1= line_csv[0].split(".")       # Ordine scelta,
                code2 = line_csv[1]                 # ELENCO,
                description1 = line_csv[2].title()  # Codice,            
                description2 = line_csv[3].title()  # 00000100000100001 Codice2,
                code_extended = line_csv[4]         # 00010000100001

                code_a = code1[0]
                code_b = code1[1]
                
                data = {
                    'name': "%s) %s" % (code_a, description1),
                    'parent_id': root_category,
                    'construction_catalog': True,
                    'construction_code': code_a,                
                }
                
                item_ids = category_pool.search(cr, uid, [
                    ('construction_catalog', '=', True), ('construction_code', '=', code_a)], context = context)
                    
                if item_ids:    # update
                    item_id = item_ids[0]
                    category_pool.write(cr, uid, item_id, data, context = context)
                    _logger.info("%s. %s Category updated!" % (i, code_a))
                else:           # create
                    item_id = category_pool.create(cr, uid, data, context = context)
                    _logger.info("%s. %s Category insert!" % (i, code_a))
                category_converter[code_a] = item_id    

                code_a_b = "%s.%s" % (code_a, code_b)
                data = {
                    'name': "%s) %s" % (code_a_b, description2),
                    'parent_id': item_id,
                    'construction_catalog': True,
                    'construction_code': code_a_b,
                }
                item_ids = category_pool.search(cr, uid, [
                    ('construction_catalog', '=', True), ('construction_code', '=', code_a_b)], context = context)
                    
                if item_ids:        # update
                    item_id = item_ids[0]
                    category_pool.write(cr, uid, item_id, data, context = context)
                    _logger.info("%s. %s Category updated!" % (i, code_a_b))
                else:               # crate
                    item_id = category_pool.create(cr, uid, data, context = context)
                    _logger.info("%s. %s Category insert!" % (i, code_a_b))
                category_converter[code_a_b] = item_id    
            except:
                _logger.info("%s. Error: %s!" % (i, sys.exc_info()))
                continue # jump line

        # -----------------
        # Read UOM from DB:
        # -----------------
        uom_pool = self.pool.get('construction.catalog.uom')
        uom_converter = {}
        uom_ids = uom_pool.search(cr, uid, [], context = context)
        for uom in uom_pool.browse(cr, uid, uom_ids, context = context):
            uom_converter[uom.name] = uom.uom_id.id # also False elements
                
        # ---------------        
        # Import product:
        # ---------------
        i = -1 # no 1st line
        product_pool = self.pool.get('product.product')
        elenco_csv = csv.reader(
            open(os.path.join(root_path, "elenco.csv"), "r"), delimiter = separator)
        error = ""
        column = 0
        lenght_name = 40
        for line_csv in elenco_csv:
            try:
                error = "reading file..."
                i += 1
                #line_csv = line.replace("\"", "").replace("\n", " ").replace("\r", " ").split(separator)

                if i == 0: # jump firs line                
                    column = len(line_csv)
                    continue
                    
                error = "test line columns..."                    
                if column != len(line_csv):
                    _logger.error("%s. Error [%s]: %s! [col correct %s, actual column]" % (i, error, "line too short", column, len(line_csv)))

                error = "parse csv elements..."
                #sequence = line_csv[0]         # Ordine scelta,
                #version = line_csv[1]          # ELENCO,
                default_code = line_csv[2]     # Codice,            
                #default_code_0 = line_csv[3]   # 00000100000100001 Codice2,
                try:
                    price = float(line_csv[4]) / cambio # Prezzo,
                except:
                    price = 0.0    
                try:
                    percentual = float(line_csv[5])  # Percentuale,
                except:
                    percentual = 0.0
                    
                error = "parse csv elements continue..."
                uom = line_csv[6]              # UMis,
                name = line_csv[7].strip()     # Descrizione,
                choose = line_csv[8]           # Scelta,
                total2 = line_csv[9]           # Totale2,
                rid = line_csv[10]             # CodRid,
                cap = line_csv[11]             # CodCap,
                #fig1 = line_csv[12]            # FIGURA,
                #fig2 = line_csv[13]            # FIGURA1,
                #spar = line_csv[14]            # SPAR,
                #sparcod = line_csv[15]         # SPARCOD,
                #cost = line_csv[15]            # Costo,
                cost = 0.0
                #cry = line_csv[16]             # Cry

                error = "parse extra csv elements..."
                code_a = default_code.split(".")[0]
                code_a_b = ".".join(default_code.split(".")[0:2])

                error = "create record product..."
                data = {
                    'active': True,
                    'name': name[:lenght_name], # "" if len(name) <= lenght_name else "..."),  #'Cap. %s' % (default_code), #".join(name.split(",")[0:2]),
                    'description_sale': name,
                    'default_code': default_code,
                    'percentual': percentual,
                    'construction_catalog': True,
                    'list_price': price,
                    'standard_price': cost,
                    'categ_parent_id': category_converter.get(code_a, False),
                    'categ_id': category_converter.get(code_a_b, False),
                }

                # Problema con il cambio UOM
                if uom in uom_converter:       # Link uom elements
                    if uom_converter[uom]:
                        data['uom_id'] = uom_converter[uom]
                        data['uom_po_id'] = uom_converter[uom]
                        data['uos_id'] = uom_converter[uom]
                else:                          # Create for next time the elements
                    uom_pool.create(
                        cr, uid, {'name': uom, 'uom_id': False,}, context = context)        
                    uom_converter[uom] = False # for not create double
                
                if context.get('only_uom', False): # Jump product importazione (for adjus UOM before)
                    continue 

                error = "search product record..."
                item_ids = product_pool.search(cr, uid, [
                    ('construction_catalog', '=', True), ('default_code', '=', default_code)], context = context)
                    
                error = "create / update product record..."
                if item_ids:    # update product 
                    product_pool.write(cr, uid, item_ids[0], data, context = context)
                    _logger.info("Line %s. Product updated!" % (i,))
                else:           # create product
                    item_id = product_pool.create(cr, uid, data, context = context)
                    _logger.info("Line %s. Product insert!" % (i,))
            except:
                _logger.error("%s. Error [%s]: %s!" % (i, error, sys.exc_info()))
                continue # jump line
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
