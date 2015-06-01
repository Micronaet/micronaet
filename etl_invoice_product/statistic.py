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
import csv
import sys
import openerp.netsvc
import logging
from openerp.osv import osv, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


_logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
#                                     Utility
# -----------------------------------------------------------------------------
def etl_date(valore):
    ''' Format date in format used in etl file
    '''
    if valore:
       return valore
    else:
       return time.strftime("%d/%m/%Y")

def etl_float(valore):
    ''' Convert ETL value in float number
    '''
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",", "."))
    else:
       return 0.0   # for empty values
       
def etl_value(valore):  
    ''' Problem during importo from Windows system
    '''
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

class product_product(osv.osv):
    ''' Extra info for product
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    
    _columns = {
        'statistic_hide': fields.boolean('Hide in statistic', required=False),
        'invoice_level': fields.selection([
            ('cold', 'Cold'),
            ('normal', 'Normal'),
            ('hot', 'Hot'),
        ], 'Invoice level', select=True, readonly=True),
    }
    
    _defaults = {
        'statistic_hide': False,
        'invoice_level': 'normal',
    }

class etl_statistic_product(osv.osv):
    ''' Extra fields for ETL in product.product
    ''' 
    _name = 'etl.statistic.product'
    _description = 'ETL statistic product'
    _rec_name = 'product_id'
    _order = 'season,month'

    # -------------------------------------------------------------------------
    #                               Scheduled action
    # -------------------------------------------------------------------------
    def schedule_etl_statistic_product_import(self, cr, uid, path, file_name, context=None):
        """ ETL operations for import partner in OpenERP (parameter setted up in
            scheduled action for file name
        """
        product_pool = self.pool.get('product.product')
        statistic_total = {}
        try:
            f = os.path.expanduser(os.path.join(path, file_name))
            lines = csv.reader(open(f, 'rb'), delimiter = ";")
        except:
            _logger.error("Error reading file: %s %s" % (path, file_name))
            return False

        # Delete all records:
        delete_ids = self.search(cr, uid, [], context=context)
        self.unlink(cr, uid, delete_ids)
        
        _logger.info('Start sync of statistic product')
        tot_colonne = 0
        i = 0 # -1 for header lne
        for line in lines:
            i += 1
            if i <= 0:
               continue
            if i % 100 == 0:
                _logger.info("%s record imported" % (i, ))

            if not tot_colonne:
                tot_colonne = len(line)
            try:                          
                if len(line) and tot_colonne == len(line):
                    ref = etl_value(line[0])
                    try:
                        month = int(etl_value(line[1]))
                        year = int(etl_value(line[2]))
                    except:
                        _logger.error('Error reading month / year %s' % (line))
                    quantity = etl_float(line[3])
                    document = etl_value(line[4]).upper()
                    total = etl_float(line[5])

                    if ref not in statistic_total:
                        statistic_total[ref] = 0.0
                    statistic_total[ref] = quantity

                    if month >= 9:
                        season = "%d-%d" % (year, year + 1)
                    else:    
                        season = "%d-%d" % (year -1, year)
                    
                    month = "%d-%02d" % (year, month)
                    
                    product_ids = product_pool.search(cr, uid, [('default_code', '=', ref)], context=context)                    
                    if not product_ids:                           
                        #_logger.error('Line [%s] Product code not found: %s (jumped)' % (i, ref))
                        product_pool.create(cr, uid, {
                            'default_code': ref,
                            'name': ref,
                        }, context=context)
                    data = {
                        'product_id': product_ids[0],
                        'season': season, 
                        'month': month, 
                        'quantity': quantity, 
                        'total': total, 
                        'document': document,                           
                    }
                    self.create(cr, uid, data, context=context)
            except:
                _logger.error('Error importing line: %s %s [%s]' % (
                    i, data, sys.exc_info()))
                continue
        _logger.info("End importation, line [%s]" % (i, ))
                        
        return True
        
    _columns = {
        'product_id': fields.many2one('product.product', 'Product', required=False),
        'season': fields.char('Season', size=10, required=False, readonly=False, help="Format year_1 - year_2, ex.: 2014-2015 (sept 2014 - august 2015)"),
        'month': fields.char('Month', size=10, required=False, readonly=False, help="Format year-month, ex.: 2014-01"),
        'quantity': fields.float('Quantity', digits=(16, 2)),
        'total': fields.float('Total', digits=(16, 2)),
        'document': fields.selection([
            ('FT', 'Invoice'),
            ('OC', 'Order'),            
        ], 'Document', select=True, readonly=False),        
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
