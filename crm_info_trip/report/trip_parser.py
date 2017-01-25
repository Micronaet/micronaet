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
import openerp.netsvc
import logging
from openerp.osv import osv, orm, fields
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse

_logger = logging.getLogger(__name__)


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_partner_offer': self.get_partner_offer,   # browse list
            'get_data': self.get_data,                     # return data dict
            'load_mysql_partner': self.load_mysql_partner,
            'format_date': self.format_date,
            
            # get/set method:
            'get_value': self.get_value,
            'set_value': self.set_value,            
            
            'get_total_invoiced': self.get_total_invoiced,
            
            # Price variation:
            'load_price_variation': self.load_price_variation,
            'get_price_variation': self.get_price_variation,          
        })

        # Parameters:
        self.values = {}         # dictionary for get/set manage
        self.products = {}       # for price variations
        self.products_last = {}  # last date of delivery        
        self.dictionary = {      # Query cursor dictionary
            'invoice': {'data': None},         # Browse object
            'invoice_header': {'data': None},
            'total': {'data': None}
            }
        self.causal = {}         # Causal movement list    
        self.total_invoiced = {} # Total invoiced per year
            
        today = datetime.now()
        self.status = {        
            'green': today.strftime(
                DEFAULT_SERVER_DATE_FORMAT), # 6 month
            'yellow': (today - timedelta(days=180)).strftime(
                DEFAULT_SERVER_DATE_FORMAT), # 1 year
            'red': (today - timedelta(days=365)).strftime(
                DEFAULT_SERVER_DATE_FORMAT), # 1 year + 6 month
            }

    def get_total_invoiced(self, ):
        ''' Return total_invoiced
        '''
        return self.total_invoiced

    def format_date(self, value):
        ''' Format date
        '''
        if value:
            return "%02d/%02d/%s" % (value.day, value.month, value.year)
        
    # Method for get/set functions
    def get_value(self, name, default=''):
        ''' Get name variable in self.values dictionary
        '''        
        if name not in self.values:
            self.values[name] = default
        return self.values.get(name, default)

    def set_value(self, name, value, return_value=False):
        ''' Set value for variable name
        '''
        self.values[name] = value
        if return_value:
            return value
        return 

    def get_data(self, dict_type='invoice'):
        ''' Return dict with all data collected during load_invoice_partner
            dict_type: key of dict with data ('total', 'invoice')
        '''
        return self.dictionary.get(dict_type, {})
    
    def load_mysql_partner(self, partner_code, ref_year=False, 
        dict_type='invoice'):
        ''' Search total in MySQL database all BC for this partner
            partner_code: Account ref code (not odoo or ID)
            ref_year: Date from whom start SQL analysis (multi DB)
            dict_type: sql category (search perform, default invoice)
        '''        
        if not partner_code:
            return False
        
        query = self.pool.get('micronaet.accounting')
        current_year = datetime.now().year

        # Load movement description 
        #for record in query.get_transportation(cr, uid, year=current_year, context=context):
        #    self.causal[record[CKY_]]

        years = []
        if ref_year:
            from_year = int(ref_year)
            if current_year > from_year:
                # Generate list of year (for DB search)
                years.extend(range(from_year, current_year))
        years.append(current_year) # Last year (order crescent for year)
        years.sort(reverse=True) # reverse year list

        # Parametric code depend on dict_type:
        if dict_type == 'invoice': 
            # -----------------------------------------------------------------
            #                   Accounting movement list
            # -----------------------------------------------------------------
            mysql_data = [] # dict of fetch all years
            for year in years:
                mysql_cursor = query.get_mm_header_line( #get_mm_line(
                    self.cr, self.uid, 
                    where_document=("BC", "BS"), # TODO no FT only BC in this DB
                    where_partner=partner_code,
                    originator=True,
                    year=year,
                    order_by="DTT_DOC desc",
                    )
                mysql_data.append(mysql_cursor.fetchall())
                
        elif dict_type == 'invoice_header': 
            # -----------------------------------------------------------------
            #                            Price change
            # -----------------------------------------------------------------
            mysql_data = [] # dict of fetch all years
            for year in years:
                mysql_cursor = query.get_mm_header_line(
                    self.cr, self.uid, 
                    where_document= ("BC", "BS"), 
                    where_partner=partner_code,
                    originator=True,
                    year=year,
                    order_by="DTT_DOC desc",
                    )
                mysql_data.append(mysql_cursor.fetchall())
                
        elif dict_type == 'total':
            # -----------------------------------------------------------------
            #                    Totals (delivery and amount)
            # -----------------------------------------------------------------            
            mysql_data = {} # this is a dict not list
            
            for year in years:
                self.total_invoiced[year] = 0.0
                mysql_cursor = query.get_mm_situation(
                    self.cr, self.uid, 
                    document="BC", 
                    partner_code=partner_code,
                    originator=True,
                    year=year)

                # Generate dictionary for report directly:
                for record in mysql_cursor.fetchall():
                    if record['CKY_ART'] not in mysql_data:
                        # Create default element:
                        mysql_data[record['CKY_ART']] = [
                            record['CDS_VARIAB_ART'], # description
                            {}, # delivery per year
                            ]
                    # Add totals for this year        
                    mysql_data[record['CKY_ART']][1][year] = (
                        record['CONSEGNE'],
                        record['TOTALE'],
                        record['IMPONIBILE'],
                        )
                    self.total_invoiced[year] += record['TOTALE']
                    # TODO also imponibile
                    
        else:
            return False
        
        # Save list of cursor for report purpose:
        self.dictionary[dict_type]['data'] = mysql_data
        return True

    def load_price_variation(self, partner_code, ref_year):
        ''' Create a product database with price variations
            partner_code: for filter
            ref_year: for evaluation period
        '''
        last = {}               # CKY_ART: last price
        self.products = {}      # CKY_ART: [list of (date, price)]
        self.products_last = {} # CKY_ART: date

        if self.load_mysql_partner(partner_code, ref_year, 'invoice_header'):
            for year in self.get_data('invoice_header')['data']:
                for invoice in year:
                    price = round(invoice['NPZ_UNIT'] / (
                        1.0 / invoice['NCF_CONV'] if invoice['NCF_CONV'] else 1.0
                        ), 4)
                    date = self.format_date(invoice['DTT_DOC_ORI'])
                    #date_doc = self.format_date(invoice['DTT_DOC'])
                    #total = price * invoice['']
                    
                    if invoice['CKY_ART'] not in self.products:
                        self.products[invoice['CKY_ART']] = []
                    if invoice['CKY_ART'] not in self.products_last:
                        self.products_last[invoice['CKY_ART']] = date # first
                        
                    if invoice['CKY_ART'] not in last or last[invoice['CKY_ART']] != price:
                        last[invoice['CKY_ART']] = price
                        self.products[invoice['CKY_ART']].append((
                            date, price, 
                            #date_doc # real data document
                            ))
        return

    def get_price_variation(self, product_code, mode='price'):
        ''' Return list of product variation (loaded before with 
            load_price_variation)
            Used in list of changing price for product
            product_code: product code to evaluate
            mode: 
             - price: return list of price variations
             - date: return last sold date
             - yellow: return last sold evaluation state (red, green, yellow)
        '''
        if mode == 'price':
            return self.products.get(product_code, [])
        elif mode == 'date':
            return self.products_last.get(product_code, "#ERR Date?")    
        elif mode == 'state':        
            date = self.get_price_variation(product_code, mode='date')
            if not date: 
                return False
                
            date = datetime.strptime(date, "%d/%m/%Y").strftime(
                DEFAULT_SERVER_DATE_FORMAT)
                
            if date < self.status['red']:
                return 'red'                
            elif date < self.status['yellow']:
                return 'yellow'
            else: # default
                return 'green'

    def get_partner_offer(self, partner_id, is_order=True):
        ''' Return browse object of open offers
        '''
        offer_pool = self.pool.get('sale.order')
        domain = [('partner_id', '=', partner_id)]
        
        # TODO andrà riveduta in base alla gestione che faremo delle offerte
        domain.append(('accounting_order', '=', is_order)) # else if offer
            
        offer_ids = offer_pool.search(self.cr, self.uid, domain)
        offer_proxy = offer_pool.browse(self.cr, self.uid, offer_ids)        
        return offer_proxy

