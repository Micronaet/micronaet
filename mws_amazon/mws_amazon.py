#!/usr/bin/python
# -*- coding: utf8 -*-

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

from osv import osv, fields
import time
import os

class amazon_order(osv.osv):
    ''' Amazon Orders imported from the system
    '''
    import time, os

    _name = 'amazon.orders'
    _description = 'Amazon Orders'

    _log_file = os.path.expanduser("~/amazon/ocesportati.txt")
    _orders_file = os.path.expanduser("~/amazon/oc.txt")
    
    # Schedule function:
    def import_order_list(self, cr, uid, context = None): # TODO FINIRE ************************************************************
        ''' Scheduled function that get order list, if present new order raise
            events to manage
            
            API for manage Orders:
            Create a Order API request: "ListOrders" for get list (next token?)
            that have the order status from last period
        '''
        import time, datetime
        from mws import mws
        ####################
        # Utility function #
        ####################
        
        def format_text(text, length):
            ''' Return passed text left formatted for max length
                (used for export in csv files left aligned for text elements)
            '''
            # For problems: input win output ubuntu; trim extra spaces
            string=""
            for c in text:
                if ord(c)<128:
                   string += c
                else:  
                   string += "#"
                      
            if string:
                return string[:length] + " "*(length - len(string))
            else: 
                return " "*length   
        
        def format_item_dict(self, cr, uid, item, data, order_id):
            ''' Get item element and data dict, update data dict with correct 
                elements
                return True if data creation works fine                
            '''
            try:
                # Get DB code for product:
                product_proxy = self.pool.get('product.product')
                parameter_proxy = product_proxy._get_parameter_proxy(cr, uid, context=context)
                database_code={}
                
                for database in parameter_proxy.path_ids:
                    database_code[database.name]=database.code
                    
                code = (item['SellerSKU']['value'] or '').replace("_"," ")
                product_ids=product_proxy.search(cr, uid, [('default_code','=',code)])
                if not product_ids:
                    return False # TODO raise roduct SKU not find
                    
                product_browse = product_proxy.browse(cr, uid, product_ids[0], context=context)
                try:
                    db_code = database_code[product_browse.amazon_origin_db]
                except:
                    return False # TODO raise No DB settings     
                 
                # Search product for get DB name:
                data.update({
                        'name': item['Title']['value'] or '',                          # Title
                        'code': code,                                                  # SellerSKU
                        'db_code': db_code,                                            # Supplier database for accounting DDT
                        'is_set': product_browse.amazon_product_set,                   # Product is a set
                        'amazon_asin': item['ASIN']['value'] or '',                    # ASIN
                        'quantity': item['QuantityOrdered']['value'] or '',            # QuantityOrdered
                        'total': item['ItemPrice']['Amount']['value'] or '',           # ItemPrice > Amount                        
                        'currency': item['ItemPrice']['CurrencyCode']['value'] or '',  # ItemPrice > CurrencyCode
                        'amazon_order_item_id': item['OrderItemId']['value'] or '',    # OrderItemId
                        'amazon_order_id': order_id,                                   # (AmazonOrderId)                        
                        
                        'product_id': product_browse.id,                               # Product id (for subelements)
                        })                                      
                        
                return True
            except:
                return False

        def _insert_order(self, cr, uid, Order, amazon_orders_api, parameter_proxy, context=None):
            ''' Get Order dict object and test if exist on OpenERP
                if not exist create header and then request order from Amazon
                for create also item lines
            '''            
            # Order header from list:
            order_oerp_id = False
            if Order['OrderStatus']['value'] == 'Unshipped': # ('Unshipped', 'Shipped') # TODO test value list!! (tolto True or)
                try: 
                    amazon_order_id = Order['AmazonOrderId']['value']                                      # ex. : '402-6350155-9479544                        
                    order_ids = self.search(cr, uid, [('name', '=', amazon_order_id)], context=context)    # search if exist:
                    if order_ids:    # yet exist:
                        #order_oerp_id = order_ids[0] # save the ID for possible lines update
                        order_oerp_id = False   # TODO reset previuos line to create every time sublines
                    else:            # create record:
                        data = {
                                'name': amazon_order_id,
                                'xml': "%s"%(Order,),
                                'parsed': "",
                                #'imported': , # date create record (default)
                                'total': Order['OrderTotal']['Amount']['value'] or "" ,
                                'currency': Order['OrderTotal']['CurrencyCode']['value'] or "" ,
                                'buyer_email': Order['BuyerEmail']['value'] or "" ,
                                'buyer_name': Order['BuyerName']['value'] or "" ,
                                'sales_channel': Order['SalesChannel']['value'] or "" ,
                                'payment_method': Order['PaymentMethod']['value'] or "" ,
                                # Shipping information:
                                'shipping_name': Order['ShippingAddress']['Name']['value'] or "" ,
                                'shipping_phone': Order['ShippingAddress']['Phone']['value'] or "",
                                'shipping_postal': Order['ShippingAddress']['PostalCode']['value'] or "",
                                'shipping_country': Order['ShippingAddress']['CountryCode']['value'] or "",
                                'shipping_region': Order['ShippingAddress']['StateOrRegion']['value'] or "" if 'StateOrRegion' in Order['ShippingAddress'] else "", 
                                'shipping_address': "%s - %s"%(Order['ShippingAddress']['AddressLine1']['value'] if 'AddressLine1' in Order['ShippingAddress'] else "",
                                                               Order['ShippingAddress']['AddressLine2']['value'] if 'AddressLine2' in Order['ShippingAddress'] else ""),
                                'shipping_city': Order['ShippingAddress']['City']['value'] or "",
                                'state': 'draft',
                                # Order['PurchaseDate']['value'] or "",                   # '2012-10-02T05:29:03Z'
                                # Order['ShipmentServiceLevelCategory']['value'] or "",   # 'Standard'
                                # Order['NumberOfItemsUnshipped']['value'] or "",         #  '0'
                                # Order['LastUpdateDate']['value'] or "",                 # '2012-10-04T08:35:32Z'
                                # Order['ShipServiceLevel']['value'] or "",               #'IT Std Domestic'
                                # Order['OrderStatus']['value'] or "",                    # 'Shipped'
                                # Order['MarketplaceId']['value'] or "",                  # 'APJ6JRA9NG5V4'
                                # Order['NumberOfItemsShipped']['value'] or "",           # '1'
                                # Order['ShippedByAmazonTFM']['value'] or "",             # 'false'
                                # Order['FulfillmentChannel']['value'] or "",             # 'MFN'
                               }  
                        order_oerp_id = self.create(cr, uid, data, context=context) # create order

                        ########################################
                        # Log and mail event (every new order) #
                        ########################################
                        log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                             title = "Amazon new order arriverd: %s [Tot.: %s %s]"%(amazon_order_id, Order['OrderTotal']['Amount']['value'] or "", Order['OrderTotal']['CurrencyCode']['value'] or "",), 
                             text = "New order imported in Amazon DB %s and in account program"%(cr.dbname),
                             typology = 'info',
                             email = parameter_proxy.log_to_email or '',     # to recipient
                             context=context)

                except:
                    raise osv.except_osv("error",'Error importing order list')                    
        
            # Order details from order items:
            if order_oerp_id: # only for creation?? TODO actually created only if record is new (elsewhere is possibly to reupdate every time)
                response = amazon_orders_api.list_order_items(amazon_order_id)                
                try: 
                    test = response._response_dict['ListOrderItemsResult']['OrderItems']['OrderItem'][0] # test if it's a list, so loop
                    try:
                        for item in response._response_dict['ListOrderItemsResult']['OrderItems']['OrderItem']:
                            data={}
                            if format_item_dict(self, cr, uid, item, data, order_oerp_id):
                                item_result = self.pool.get('amazon.order.lines').create(cr, uid, data, context=context)
                            else:
                                pass #TODO raise error importing line?
                    except:
                        raise osv.except_osv("error",'Error importing order line')
                            
                except: # if is a dict get the keys
                    try:
                        data = {}
                        if format_item_dict(self, cr, uid, response._response_dict['ListOrderItemsResult']['OrderItems']['OrderItem'], data, order_oerp_id):
                            item_result = self.pool.get('amazon.order.lines').create(cr, uid, data, context=context)
                        else:
                            pass #TODO raise error importing line?
                           
                    except:
                        raise osv.except_osv("error",'Error importing order line')

        #################
        # Main Function #
        #################
        created_after_hours = 1600 # Hours in the past for get order list (according to schedule time)                    # TODO reset to 6 after backup!!!
        parameter_proxy = self.pool.get('product.product')._get_parameter_proxy(cr, uid, context=context)
        if not parameter_proxy:
            raise osv.except_osv("error",'No parameter setted up for Amazon MWS, please setup after publish product')  # TODO Raise error control!
            return
        
        # Run report request: *************************************************
        amazon_orders_api = mws.Orders(parameter_proxy.key, 
                                       parameter_proxy.secret, 
                                       parameter_proxy.seller_number, 
                                       domain = parameter_proxy.market_web_site)
        # Get order list:
        # Parameter marketplaceids, created_after, created_before, lastupdatedafter, lastupdatedbefore, orderstatus=(), fulfillment_channels=(), payment_methods=(), buyer_email=None, seller_orderid=None, max_results='100'
        created_after = (datetime.datetime.now() - datetime.timedelta(hours = created_after_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = amazon_orders_api.list_orders((parameter_proxy.market_place,), created_after=created_after) # market_place = list!

        if "ListOrdersResult" in response._response_dict:
            # Test all orders and see if are inserted (for new raise importation in accounting program)
            try:
               test = response._response_dict['ListOrdersResult']['Orders']['Order']
            except:
               ########################
               # Log no order present #
               ########################
               log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                         title="Import Amazon order: no order present!", 
                         text="No order present during import list operations.",
                         typology='info', 
                         email = parameter_proxy.log_to_email or '',    # to recipient
                         context=context)
               return 

            try: # test if is a list of order or only one?
                test = response._response_dict['ListOrdersResult']['Orders']['Order'][0] # more than one one?
                for Order in response._response_dict['ListOrdersResult']['Orders']['Order']:
                    _insert_order(self, cr, uid, Order, amazon_orders_api, parameter_proxy, context=context)
            except:          
                try: # test if is a list of order or only one?
                     _insert_order(self, cr, uid, response._response_dict['ListOrdersResult']['Orders']['Order'], amazon_orders_api, parameter_proxy, context=context)
                except: # Log error importing
                    log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                                 title = "Amazon: Error importing order from Web", 
                                 text = "Error importing order from web",
                                 typology = 'error',
                                 email = parameter_proxy.log_to_email or '',     # to recipient
                                 context=context)                         
                                    
            # test imported list to update records:
            try:
                #   1) read exchange file with amazon id
                if os.path.exists(self._log_file):
                    f_log=open(self._log_file, "r")
                    order_list = []
        
                    #   2) set state in imported for this record
                    for line in f_log:
                        order_list.append(line.strip())
                    update_ids = self.search(cr, uid, [('name', 'in', order_list)], context=context)    
                    result = self.write(cr, uid, update_ids, {'state': 'imported'}, context=context)                    
                    f_log.close()
                    os.remove(self._log_file)
                    log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                                 title = "Amazon: Mexal order imported", 
                                 text = "Orders imported in mexal, this are Amazon IDs: %s"%(order_list),
                                 typology = 'info',
                                 email = parameter_proxy.log_to_email or '',     # to recipient
                                 context=context)
            except:
                #raise osv.except_osv("error",'Error importing order list')       TODO raise something?               
                pass # no error log file
                
            try:    
                # loop for test the order in draft state to export on accounting program:
                order_draft_ids = self.browse(cr, uid, self.search(cr, uid, [('state', '=', 'draft')], context=context), context=context)
                
                # if exist yet file something go wrong:
                if os.path.exists(self._orders_file):
                    log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                                 title = "Amazon: order file oc.txt yet present", 
                                 text = "Error exporting draft order file in DB %s"%(cr.dbname),
                                 typology = 'error',
                                 email = parameter_proxy.log_to_email or '',     # to recipient
                                 context=context)
                    return  # nothing to do!
                    
                if order_draft_ids: # only if present_
                    f_order = open(self._orders_file, "w") 
                    field = 102   # total of sublines elements)
                    newline=chr(13) + chr(10) 
                    format = "%" + "%ss%s"%(field, newline)
                    exported_list=[]
                    for order in order_draft_ids:
                        # export order (header): 
                        f_order.write(format_text(order.name, field) + newline)
                        f_order.write(format%(order.total))
                        f_order.write(format_text(order.currency, field) + newline)
                        f_order.write(format_text(order.buyer_email, field) + newline)
                        f_order.write(format_text(order.buyer_name, field) + newline)
                        f_order.write(format_text(order.shipping_name, field) + newline)
                        f_order.write(format_text(order.shipping_address, field) + newline)
                        f_order.write(format_text(order.shipping_postal, field) + newline)
                        f_order.write(format_text(order.shipping_country, field) + newline)
                        f_order.write(format_text(order.shipping_region, field) + newline)
                        f_order.write(format_text(order.shipping_city, field) + newline)
                        f_order.write(format_text(order.shipping_phone, field) + newline)

                        # export order (lines):
                        for line in order.line_ids:
                            # test if product is a set (explore subproduct:
                            if line.is_set:  # TODO comunicate set product??
                                # search product subelements: # TODO
                                f_order.write("%15s%3s%60s%10s%9s%3s%2s"%(format_text(line.code, 15), format_text(line.db_code, 3), format_text(line.name, 60), line.quantity, line.total, format_text(line.currency,3), len(line.product_id.amazon_subproduct_ids)))
                                f_order.write(newline)
                                for subproduct in line.product_id.amazon_subproduct_ids:
                                    f_order.write("%15s%3s%60s%10s%9s%3s  "%(format_text(subproduct.product_id.default_code, 15),       # Account code
                                                                             format_text(subproduct.product_id.amazon_origin_db, 3),    # Origin DB of product (set if from amazon DB)
                                                                             format_text(subproduct.product_id.amazon_title, 60) if subproduct.product_id.amazon_title else format_text(subproduct.product_id.name, 60),               # Account name
                                                                             subproduct.quantity * line.quantity,                       # number of set x number of product elements 
                                                                             "",                                                        # no total price
                                                                             "",))                                                      # no currency
                                    f_order.write(newline)
                            else:
                                f_order.write("%15s%3s%60s%10s%9s%3s  "%(format_text(line.code, 15), 
                                                                         format_text(line.db_code, 3), 
                                                                         format_text(line.name, 60), 
                                                                         line.quantity, 
                                                                         line.total, 
                                                                         format_text(line.currency,3))) # + "  " for set not present
                                f_order.write(newline)
                        f_order.write(("*" * field) + newline)

                        exported_list.append(order.id)
                        
                    exported_result=self.write(cr, uid, exported_list, {'state':'exported'}, context=context)    # next trigger will be imported (or read directly the log file)
            except:
                raise osv.except_osv("error",'Error write file for export orders')
        return
    
    _columns = {
                'name': fields.char('Amazon IDName', size=20, required=True, help="Amazon oder code in 3-7-7 number format"),
                'xml': fields.text('XML text'),
                'parsed': fields.text('Parsed text', help="Text for importing in account program"),
                'imported': fields.datetime('Imported date'),
                'total': fields.float('Total', digits=(16, 2)),
                'currency':fields.char('Currency', size=5, required=False, readonly=False),
                'buyer_email': fields.char('Buyer email', size=120, required=False, readonly=False),
                'buyer_name': fields.char('Buyer name', size=120, required=False, readonly=False),
                'sales_channel': fields.char('Sales channel', size=50, required=False, readonly=False),
                'payment_method': fields.char('Payment method', size=30, required=False, readonly=False),
                
                # Shipping information:
                'shipping_name': fields.char('Shipping name', size=60, required=False, readonly=False),
                'shipping_phone': fields.char('Shipping phone', size=30, required=False, readonly=False),
                'shipping_postal': fields.char('Shipping postal code', size=10, required=False, readonly=False),
                'shipping_country': fields.char('Shipping country code', size=5, required=False, readonly=False),
                'shipping_region': fields.char('Shipping region', size=40, required=False, readonly=False),
                'shipping_address': fields.char('Shipping address', size=60, required=False, readonly=False),
                'shipping_city': fields.char('Shipping city', size=40, required=False, readonly=False),

                'state':fields.selection([
                        ('draft','Draft'),
                        ('exported','Exported'),
                        ('imported','Imported'),
                        ('shipped','Shipped'),
                        ('cancel','Cancel'),
                        ('close','Close'),                    
                ],'State', select=True, readonly=False),                
               }
    _defaults = {
        'imported': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state': lambda *a: 'draft',
    }               
amazon_order()

class amazon_order_line(osv.osv):
    ''' Amazon order lines imported from the system
    '''
    _name = 'amazon.order.lines'
    _description = 'Amazon order lines'
    
    _columns = {
        'name': fields.char('Name', size=80, required=False, readonly=False, help="Amazon title"),                      # Title
        'code': fields.char('Code', size=15, required=False, readonly=False, help="Internal SKU code"),                 # SellerSKU
        'is_set': fields.boolean('Is set', required=False),                                                             # Product is set
        'db_code': fields.char('DB code', size=3, required=False, readonly=False, help="Accounting programm DB code"),  # Database code
        'amazon_asin': fields.char('Amazon ASIN', size=20, required=False, readonly=False, help="Amazon unique code"),  # ASIN
        'quantity': fields.float('Quantity', digits=(16, 2)),                                                           # QuantityOrdered
        'total': fields.float('Total', digits=(16, 2)),                                                                 # ItemPrice > Amount
        'currency':fields.char('Currency', size=5, required=False, readonly=False),                                     # ItemPrice > CurrencyCode
        'amazon_order_item_id':fields.char('Amazon line ID', size=25, required=False, readonly=False),                  # OrderItemId
        'amazon_order_id':fields.many2one('amazon.orders', 'Amazon order', required=False),                             # (AmazonOrderId)
        'product_id':fields.many2one('product.product', 'Product', required=False),
    }
amazon_order_line()

class amazon_order(osv.osv):
    ''' Extra *2many fields
    '''
    _name = 'amazon.orders'
    _inherit = 'amazon.orders'
    
    _columns = {
        'line_ids':fields.one2many('amazon.order.lines', 'amazon_order_id', 'Lines', required=False),
    }
amazon_order()

class amazon_warranty(osv.osv):
    ''' Warranty terms (every product can have a different warranty terms)
    '''
    _name = 'amazon.warranty'
    _description = 'Amazon Warranty'
    
    _columns = {
               'name': fields.char('Name', size=40, required=True),
               'warranty': fields.text('Warranty terms', required=True),
               'company_id': fields.many2one('res.company', 'Company', required=True),
                }
amazon_warranty()

class amazon_parameter(osv.osv):
    ''' Add extra fields to product, to manage Amazon publish of product data
        Create all function for generate feed packet for the scheduler
    '''
    _name = 'amazon.parameter'
    _description = 'Amazon access parameter'
    
    _columns = {
               'name': fields.char('Name', size=40, required=True),
               'company_id': fields.many2one('res.company', 'Company', required=False),
               'seller_number': fields.char('Seller Number', size=20, required=True, help="Seller number assigned by Amazon, like: A4M45BERTF3VIV"),
               'market_place':fields.char('Market place', size=20, required=True, help="Market place code assigned by Amazon, like: APJ3JRB2FGD4"),
               'market_web_site': fields.char('Web site market', size=120, required=True, help="Wer service address, every zone has different addres, ex. for EU: 'https://mws-eu.amazonservices.com"),
               'software_account_id': fields.char('SW account', size=20, required=True, help="Software account ID assigned by Amazon, like: 1234-5678-9012", readonly=False),
               'key':fields.char('Key', size=30, required=True, help="Encrypt Key assigned by Amazon, like: AKYAJ4M45BERTFTA3VIV"),
               'secret':fields.char('Secret', size=50, required=True, help="Secret key for encrypt messagesn, like: ivFe6C7aq3UJNhYqg0BH5+6g4+XfkSLJyPgbt2al"),
               'merchant_identification':fields.char('Merchant ID', size=30, required=True, help="Merchant ID assigned by Amazon, like: M_COMPANY_11252334", readonly=False),
               'image_web_root':fields.char('Image web root', size=80, required=True, help="Web site root path where amazon images are published, used for send link for every product image"),
               'feed_deadtime': fields.integer('Feed deadtime', help='Days after a feed with state done is erased from feed list'),
               'ftp_server':fields.char('FTP server', size=40, required=True, help="FTP server name, es. www.example.it", readonly=False),
               'ftp_user':fields.char('FTP user', size=40, required=True, help="FTP user name", readonly=False),
               'ftp_password':fields.char('FTP password', size=40, required=True, help="FTP password", readonly=False),
               'ftp_path':fields.char('FTP path', size=90, required=True, help="FTP path for images (absolute, es.: /home/www/image/amazon)", readonly=False),
               'log_to_email': fields.char('Log to email', size=64, required = False, readonly=False),
               }
                
    _defaults = {
                 'feed_deadtime': lambda *x: 7, # "days"
                 }                
amazon_parameter()

class amazon_parameter_path(osv.osv):
    ''' Path in filesystem where DB images are stored (for publish)
    '''
    _name = 'amazon.parameter.path'
    _description = 'Amazon parameter path'
    
    _columns = {
               'name': fields.char('Database name', size=40, required=True),
               'code': fields.char('Database code', size=3, required=True, help="Database code for accounting program"),
               'image_fs_root':fields.char('Image filesystem root', size=100, required=True, help="File system root path where amazon images are published, used for send link for every product image, ex. '/home/administrator/photo'"),
               'parameter_id':fields.many2one('amazon.parameter', 'Parameter', required=False),
                }
amazon_parameter_path()

class amazon_parameter(osv.osv):
    ''' Add extra *2many fields
    '''
    _name = 'amazon.parameter'
    _inherit = 'amazon.parameter'
    
    _columns = {
               'path_ids':fields.one2many('amazon.parameter.path', 'parameter_id', 'Path', required=False),
                }                
amazon_parameter()

class amazon_feed(osv.osv):
    ''' Every comunication with Amazon create a amazon.feed
        The sceduler launch feed according to schedule time 
        When feed are in done state are eliminate after dead time periode setted
        on parameter
    '''
    _name = 'amazon.feed'
    _description = 'Amazon feed'
    
    # Button action:
    def button_reschedule_feed(self, cr, uid, ids, context=None):    
        ''' Restart feed in draft state leave actual scheduling time
        '''
        self.write(cr, uid, ids, {'state': 'draft'})
        return True
    
    
    # Action raised from the scheduler to test feed:
    # Action for wizard button (or automated scheduled action):
    def schedule_inventory_report(self, cr, uid, context = None):    
        ''' Send a report request for get inventory FLAT files 
        '''
        import logging    
            
        _logger = logging.getLogger('mws_amazon')        
        _logger.info('Amazon: Request inventory status')

        self.pool.get('product.product').create_report(cr, uid, "InventoryRequest", context = context)          # TODO ERRORE
        return True
    
    # TODO Amazon extra (daily) schedule for delete unused element and so on...        
    # Amazon normal scheduled operation (every 5/10 minutes)
    def schedule_product_feed(self, cr, uid, context=None):    
        ''' See in the list if there's some feed to launched
            The schedule works for product feed (4 type)
            and works also for Report (get flat inventory)
        '''
        # TODO divide procedure??
        from mws import mws
        import logging, time
        
        # TODO Parametrize:
        max_count = "30" # max count of feed list request (for evaluate done state)
        
        _logger = logging.getLogger('mws_amazon')        
        _logger.info('Scheduled MWS Amazon publish product')
                
        # Read MWS access parameter: *******************************************
        parameter_proxy = self.pool.get('product.product')._get_parameter_proxy(cr, uid, context=context)
        if not parameter_proxy:
            raise osv.except_osv("error",'No parameter setted up for Amazon MWS, please setup after publish product')  # TODO Raise error control!

        ########################################################################
        ######################### PROCESS REPORT FEED LIST #####################
        ########################################################################
        _logger.info('Amazon: start get report:')

        # Check server status: *************************************************
        try:
            amazon_report_api = mws.Reports(parameter_proxy.key, 
                                            parameter_proxy.secret, 
                                            parameter_proxy.seller_number, 
                                            domain=parameter_proxy.market_web_site)
        except:
            try:
                log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                          title="Amazon connection error", 
                          text="Error connecting API for report",
                          typology='error', 
                          email = parameter_proxy.log_to_email or '',    # to recipient
                          context=context)
            except:
                pass # no error             
            raise osv.except_osv("error", 'Error start connection with Amazon (Report)!')
                                                                
        status = amazon_report_api.get_service_status()
        if status._response_dict["GetServiceStatusResult"]['Status']['value'] != "GREEN":
            raise osv.except_osv("error", 'Amazon not working (status not GREEN)!')

        # Search all operation (schedule time passed and draft): ***************
        feed_ids = self.search(cr, uid, [('state', '=', 'draft'),('api','=','report'),('scheduled_datetime', '<=', time.strftime('%Y-%m-%d %H:%M:%S'))], context=context)        
        is_report=False
        for feed in self.browse(cr, uid, feed_ids, context=context):
            report_request_id = feed.feed_code  # to test what element see the status:
            response = amazon_report_api.get_report_request_list(requestids=(report_request_id,)) #, types=(), processingstatuses=(), max_count=None, fromdate=None, todate=None):
            try:  # Try to test if is done and get flat file:
                if response._response_dict['GetReportRequestListResult']['ReportRequestInfo']['ReportProcessingStatus']['value'] == "_DONE_":     
                    # TODO Test request list may introduce nexttoken for all values, better test open feed adding loop after 20 minutes!!!
                    generated_report_id = response._response_dict['GetReportRequestListResult']['ReportRequestInfo']['GeneratedReportId']['value']
                    response_file = amazon_report_api.get_report(generated_report_id)
                    flat_file=response_file.parsed
                    product_pool = self.pool.get('product.product')
                    i=0
                    header = True
                    is_report = True
                    delete_sku = [] # list with sku to delete (items that are in Amazon market but not published on OpenERP)
                    for line in flat_file.split("\r\n"):
                        i+=1
                        if header:
                            header = False
                        else: # jump header    
                            line_item=line.split("\t")
                            sku = line_item[0].replace("_"," ")
                            product_ids = product_pool.search(cr, uid, [('default_code','=',sku)], context=context)
                            if product_ids:
                                product_browse = product_pool.browse(cr, uid, product_ids[0], context=context)
                                if not product_browse.amazon_published:
                                    delete_sku.append(sku)
                                update = product_pool.write(cr, uid, product_ids, {'amazon_amazon_inventory': int(line_item[3]) or 0,
                                                                                   'amazon_amazon_price': float(line_item[2]) or 0,
                                                                                   'amazon_asin_code': line_item[1] or '',                                                                                   
                                                                                  }, context=context)

                    ##################
                    # Log Delete SKU #
                    ##################
                    #log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                    #          title = "TODO Delete SKU!", 
                    #          text = "%s"%(delete_sku,),
                    #          typology='info', 
                    #          email = parameter_proxy.log_to_email or '',    # to recipient
                    #          context=context)
                                       
                    ###############################
                    # Log Amazon Inventory import #
                    ###############################
                    log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                              title="Import Amazon inventory!", 
                              text=flat_file,
                              typology='info', 
                              email = parameter_proxy.log_to_email or '',    # to recipient
                              context=context)

                    if delete_sku: # TODO Test for delete product not present 
                        # IMPORTANT *****************************************************************                        
                        pass # create feed to delete elements
                    # TODO Test total product for limit 400 

                    # Import inventory values:
                    self.write(cr, uid, feed.id, {'state': 'done',
                                                  'send_datetime': time.strftime('%Y-%m-%d %H:%M:%S'),                                              
                                                  }, context=context)
                else:
                    pass # leave in sheduled list
            except:
                raise osv.except_osv("error", 'Error reading Report Feed!')
        _logger.info('Amazon: End get report [# record update: %s ]'%(i) if is_report else 'Amazon: End get report (no record found!)')

        ########################################################################
        ###################### PROCESS PRODUCT FEED LIST #######################
        ########################################################################

        # Check server status: *************************************************
        amazon_product_api = mws.Products(parameter_proxy.key, 
                                          parameter_proxy.secret, 
                                          parameter_proxy.seller_number, 
                                          domain=parameter_proxy.market_web_site)
            
        status = amazon_product_api.get_service_status()
        if status._response_dict["GetServiceStatusResult"]['Status']['value'] != "GREEN":
            raise osv.except_osv("error", 'Amazon not working (status not GREEN)!')
        try:    
            amazon_feed_api = mws.Feeds(parameter_proxy.key, parameter_proxy.secret, parameter_proxy.seller_number, domain=parameter_proxy.market_web_site)
        except:
            try: # Log and mail errors activating API
                log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid,
                          title="Amazon connection error", 
                          text="Error connecting API for feed",
                          typology='error', 
                          email = parameter_proxy.log_to_email or '',    # to recipient
                          context=context)
            except:
                pass # no error             
            raise osv.except_osv("error", 'Error start connection with Amazon (Feed)!')
                 
        # Search all operation (schedule time passed and draft): ***************
        feed_ids = self.search(cr, uid, [('state', '=', 'draft'),('api','=','product'),('scheduled_datetime', '<=', time.strftime('%Y-%m-%d %H:%M:%S'))], context=context)        

        # SUBMEET FEEDS: *******************************************************
        i=0
        for feed in self.browse(cr, uid, feed_ids, context=context):
            i+=1
            now = time.strftime('%Y-%m-%d %H:%M:%S')
            try: # Send feed:
                response = amazon_feed_api.submit_feed(feed.feed_xml, feed.feed_type, marketplaceids=(parameter_proxy.market_place,), content_type="text/xml", purge='false')
            except:
                try: # Log and mail errors activating API
                    log_create=self.pool.get('logmail.log').create_logmail_event(cr, uid, 
                              title="Amazon launch feed error", 
                              text="Error connecting API for report: %s"%(response._response_dict),
                              typology='error', 
                              email = parameter_proxy.log_to_email or '',    # to recipient
                              context=context)
                except:
                    pass # no error             
                raise osv.except_osv("error", 'Error start connection with Amazon (Feed)!')

            try: # Parse response feed submitted:
                feed_code = response._response_dict['SubmitFeedResult']['FeedSubmissionInfo']['FeedSubmissionId']['value']
                self.write(cr, uid, feed.id, {'feed_code': feed_code,
                                              'state': 'submitted',
                                              'send_datetime': now,
                                              }, context=context)
            except:
                raise osv.except_osv("error", 'Error write feed ID on amazon.feed') # [%s]!'%(now))

        _logger.info('%s Feed submitted to the system'%(i))

        # Get list of feed operations: *****************************************
        _logger.info('Get list of feed submitted to test esit')
        response_list = amazon_feed_api.get_feed_submission_list(max_count=max_count)   # TODO parametrize according to open feed submitted
        submitted_ids=self.search(cr, uid, [('state', '=', 'submitted')], context=context)
        submitted={}
        for f in self.browse(cr, uid, submitted_ids, context=context):
            submitted[f.feed_code]= f.id

        # Search in the list submitted feed ************************************
        for feed_response_item in response_list._response_dict['GetFeedSubmissionListResult']['FeedSubmissionInfo']:
            feed_id = feed_response_item.FeedSubmissionId
            # Get result when they become "DONE" *******************************
            if feed_id in submitted and feed_response_item.FeedProcessingStatus == '_DONE_':
                #print "Feed type %s - Status %s  [ID: %s]"%(feed_sub['FeedType']['value'], feed_sub['FeedProcessingStatus']['value'], feed_sub['FeedSubmissionId']['value'])
                feed_state = amazon_feed_api.get_feed_submission_result(feed_id)
                is_error = False
                error_message=""
                # TODO test if there's error messages
                # test if there's some result list (so errors), instead there's a "StatusCode" field with "Complete"
                if 'Result' in feed_state._response_dict['Message']['ProcessingReport']: 
                    for message in feed_state._response_dict['Message']['ProcessingReport']['Result']: # More messages for every error!
                        if type(message) != type("") and message.ResultCode in ('Warning', 'Error'):
                           is_error = True
                           error_message += message.ResultDescription + "\n"
                       
                if is_error: # test error:
                   feed_state_data = {'error_text': error_message,
                                      'state': 'error',
                                      'response_text': feed_state._response_dict,
                                     }
                else:                                 
                   feed_state_data = {'state': 'done',
                                      'response_text': feed_state._response_dict,
                                     }
                   
                self.write(cr, uid, submitted[feed_id], feed_state_data, context=context)

        _logger.info('End scheduled MWS Amazon publish product')        
        return

    _columns = {
                'name': fields.char('Description', size=50, required=True),
                'description': fields.text('Long description', required=False, help="Long description of the feed"),
                'parameter_id': fields.many2one('amazon.parameter', 'Amazon Market', required=False),
                'create_datetime': fields.datetime('Create time', required=False), 
                'scheduled_datetime': fields.datetime('Scheduled time', required=False, help="Send feed passed this time"), 
                'send_datetime': fields.datetime('Send time', required=False, help="Launched time, compiled by the sistem scheduler"), 
                'feed_code': fields.char('Feed code', size=50, required=False, help="ID assigned by Amazon when feed is submitted to the system"),
                'feed_xml': fields.text('XML file', required=False),   # TODO parse for not ascii character!
                'error_text': fields.text('Error', required=False, help='Error text when feed not accepted from the system'),
                'response_text': fields.text('Response XML', required=False, help='For debug purposes'),
                'api': fields.selection([('product', 'Product'),
                                         ('report', 'Report'),
                                         ('ftp', 'FTP operation (Image)')], 'API type', select = True, readonly = False),
                'feed_type': fields.selection([# Product API Feed:
                                               ('_POST_PRODUCT_DATA_', 'Product data'), 
                                               ('_POST_PRODUCT_RELATIONSHIP_DATA_', 'Relationship feed'),         
                                               ('_POST_ITEM_DATA_', 'Single product feed'), 
                                               ('_POST_PRODUCT_OVERRIDES_DATA_', 'Shipping Override Feed'),
                                               ('_POST_PRODUCT_IMAGE_DATA_', 'Product Images Feed'), 
                                               ('_POST_PRODUCT_PRICING_DATA_', 'Pricing Feed'),
                                               ('_POST_INVENTORY_AVAILABILITY_DATA_', 'Inventory Feed'), 
                                               ('_POST_ORDER_ACKNOWLEDGEMENT_DATA_', 'Order Acknowledgement Feed'),
                                               ('_POST_ORDER_FULFILLMENT_DATA_', 'Order Fulfillment Feed'), 
                                               ('_POST_FULFILLMENT_ORDER_REQUEST_DATA_', 'FBA Shipment Injection Fulfillment Feed'),
                                               ('_POST_FULFILLMENT_ORDER_CANCELLATION_', 'FBA Shipment Injection'), 
                                               ('_REQUEST_DATA_', 'Cancellation Feed'),  
                                               ('_POST_PAYMENT_ADJUSTMENT_DATA_', 'Order Adjustment Feed'), 
                                               ('_POST_INVOICE_CONFIRMATION_DATA_', 'Invoice Confirmation Feed'),
                                               ('_POST_FLAT_FILE_LISTINGS_DATA_', 'Flat File Listings Feed'),
                                               ('_POST_FLAT_FILE_ORDER_ACKNOWLEDGEMENT_DATA_', 'Flat File Order Acknowledgement Feed'),
                                               ('_POST_FLAT_FILE_FULFILLMENT_DATA_', 'Flat File Order Fulfillment Feed'),
                                               ('_POST_FLAT_FILE_FULFILLMENT_ORDER_REQUEST_DATA_', 'Flat File FBA Shipment Injection Fulfillment Feed'),
                                               ('_POST_FLAT_FILE_FULFILLMENT_ORDER_CANCELLATION_', 'Flat File FBA Shipment Injection Cancellation Feed'),
                                               ('_REQUEST_DATA_', 'Request data feed'),
                                               ('_POST_FLAT_FILE_FBA_CREATE_INBOUND_SHIPMENT_', 'FBA Flat File Create Inbound Shipment Feed'),
                                               ('_POST_FLAT_FILE_FBA_UPDATE_INBOUND_SHIPMENT_', 'FBA Flat File Update Inbound  Shipment Feed'),
                                               ('_POST_FLAT_FILE_PAYMENT_ADJUSTMENT_DATA_', 'Flat File Order Adjustment  Feed'),
                                               ('_POST_FLAT_FILE_INVOICE_CONFIRMATION_DATA_', 'Flat File Invoice Confirmation Feed'),
                                               ('_POST_FLAT_FILE_INVLOADER_DATA_', 'Flat File Inventory Loader Feed'),
                                               ('_POST_FLAT_FILE_CONVERGENCE_LISTINGS_DATA_', 'Flat File Music Loader File'),
                                               ('_POST_FLAT_FILE_BOOKLOADER_DATA_', 'Flat File Book Loader File'),
                                               ('_POST_FLAT_FILE_LISTINGS_DATA_', 'Flat File Video Loader File'),
                                               ('_POST_FLAT_FILE_PRICEANDQUANTITYONLY_', 'Flat File Price and Quantity'),
                                               ('_UPDATE_DATA_', 'Update File'), 
                                               ('_POST_FLAT_FILE_SHOPZILLA_DATA_', 'Product Ads Flat File Feed'),
                                               ('_POST_UIEE_BOOKLOADER_DATA_', 'UIEE Inventory File Exchange Environment'),
                                               
                                               # Report API feed:
                                               ('_GET_FLAT_FILE_OPEN_LISTINGS_DATA_', 'Get inventory report'),
                                               
                                               # FTP operation:
                                               ('_FTP_', 'FTP Image')
                                               ], 'Feed type', select = True, readonly = False),
                'state': fields.selection([('draft','Draft'),
                                           ('submitted', 'Submitted'),
                                           ('done', 'Done'),
                                           ('error', 'Error')], 'State', select = True, readonly = False),     
    }
    _defaults = {
                'state': lambda *x: 'draft',
                'create_datetime': lambda *x: time.strftime('%Y-%m-%d %H:%M:%S'),
                'scheduled_datetime': lambda *x: time.strftime('%Y-%m-%d %H:%M:%S'),
                'api': lambda *x: 'product',
                }
amazon_feed()

class amazon_product_category(osv.osv):
    ''' Category for Amazon, also called BrowseNode
    '''
    _name = 'amazon.product.category'
    _description = 'Amazon Category'
    
    _columns = {
        'name':fields.char('Category', size=80, required=True, readonly=False),
        'code':fields.char('Amazon code', size=15, required=True, readonly=False),
        'active': fields.boolean('Active', required=False),
        'parent_id':fields.many2one('amazon.product.category', 'Label', required=False),        
    }
    _defaults = {
        'active': lambda *a: True,
        'parent_id': lambda *a: False,
    }
amazon_product_category()    

class amazon_subproduct(osv.osv):
    ''' Amazon subproduct (for manage set)
    '''
    _name = 'amazon.subproduct'
    _description = 'Amazon subproduct'
    _rec_name = "product_id"
    _order = "product_id"
    
    # override fields:
    def unlink(self, cr, uid, ids, context=None):
        """
        Delete subproduct raise a write operation in product element (empty)
        this is for raise update event
    
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be removed from table
        @param context: context arguments, like lang, time zone
        
        @return: True on success, False otherwise
        """
        
        subproduct = self.browse(cr, uid, ids, context=context)[0]
        if subproduct.parent_id and subproduct.parent_id.amazon_product_set:
            res = super(amazon_subproduct, self).unlink(cr, uid, ids, context)
            self.pool.get('product.product').write(cr, uid, [subproduct.parent_id.id], {'amazon_product_set':True,}, context=context) # force update if is a set
        else:
            res = super(amazon_subproduct, self).unlink(cr, uid, ids, context)
        return res
        
    # function fields:
    def _possibly_sef_function(self, cr, uid, ids, field_name, arg, context=None):
        ''' Compute max set availability // quantity
        '''
        res={}
        for subproduct in self.browse(cr, uid, ids, context=context):
            res[subproduct.id] = 0
            if subproduct.product_id.amazon_inventory and subproduct.quantity:
                res[subproduct.id] = subproduct.product_id.amazon_inventory / subproduct.quantity
        return res

    _columns = {
        'product_id':fields.many2one('product.product', 'Subproduct', required=True),
        'quantity': fields.integer('Quantity', required=True),
        'parent_id':fields.many2one('product.product', 'Subproduct', required=True),       
         
        # related fields:
        'max_set': fields.function(_possibly_sef_function, method=True, type='integer', string='Max set', store=False),
        'amazon_inventory': fields.related('product_id','amazon_inventory', type = 'integer', string = 'Company inventory'),
        'amazon_amazon_inventory': fields.related('product_id','amazon_amazon_inventory', type = 'integer', string = 'Amazon inventory'),
    }
    
    _defaults = {
        'quantity': lambda *a: 1.0,
    }
amazon_subproduct()    

class product_product_amazon(osv.osv):
    ''' Add extra information for Manage Amazon information and sign product for
        publication on Web Service
        Add also creation of Feed task that schedule evaluate for publication
        on task trigger
    '''
    _name = 'product.product'
    _inherit = 'product.product'
    
    ########################
    # Parameter for Amazon #
    ########################
    
    # Feed type: 
    _feed_type_list = ('Product', 'ProductImage', 'Inventory', 'Price') 
    # UM: 
    _um_volume = ("cubic-cm", "cubic-ft", "cubic-in", "cubic-m", "cubic-yd", "cup", "fluid-oz", "gallon", "liter", "milliliter", "ounce", "pint", "quart", "liters", "deciliters", "centiliters", "milliliters", "microliters", "nanoliters", "picoliters")
    _um_weight = ("GR", "KG", "OZ", "LB", "MG")
    _um_length = ("MM", "CM", "M", "IN", "FT", "inches", "feet", "meters", "decimeters", "centimeters", "millimeters", "micrometers", "nanometers", "picometers")
    _um_area = ("square-in", "square-ft", "square-cm", "square-m")

    # Scheduled action:
    def publish_inventory_scheduled(self, cr, uid, context = None): 
        ''' Scheduled function that every day push on the web product inventory
            for: description, price, image, inventory 
        '''
        return self.pool.get('product.product').create_all_product_feed(cr, 
                                                                        uid, 
                                                                        False, # force all images
                                                                        False, # force selected images
                                                                        context = context)
    
    # Utility function:
    def get_sku(self, code):
        ''' Create sku correctly (with particularity: space=_)
        '''
        return code.replace(" ", "_") if code else ""
        
    def get_file_name(self, code):
        ''' Create image name (with particularity: space=_)
        '''
        return "%s.jpg"%(self.get_sku(code),) if code else ""
        
    def _ftp_images(self, cr, uid, ids, context = None):
        ''' Publish images on external web site for Amazon import
            Search all ids elements and test if file exist for publish
            according of dbname folder (the image arrives from 2 different DB)
        '''
        import ftplib, os, logging
        from ftplib import FTP
            
        parameters = self._get_parameter_proxy(cr, uid, context=context)  
        error = ""
            
        ftp = FTP(parameters.ftp_server)
        ftp.login(parameters.ftp_user, parameters.ftp_password)
        ftp.cwd(parameters.ftp_path)

        origin_folder={}  # Every DB has his origin folder
        for db in parameters.path_ids:
            origin_folder[db.name] = db.image_fs_root
        
        for product in self.browse(cr, uid, ids, context=context):
            if product.default_code:                
                file_name = self.get_file_name(product.default_code)
                image_org = os.path.join(origin_folder[product.amazon_origin_db], file_name)
                image_dest = file_name #os.path.join(origin_folder[parameters.ftp_path], file_name)
                is_error=False
                try: 
                    f = open(image_org, "rb")
                except:  # and image not exist
                    is_error=True
                    error += "Error: %s\n"%(image_org)

                try:
                    if not is_error:
                        ftp.storbinary('STOR ' + image_dest, f)
                    # for remove forced publish image
                    self.write(cr, uid, product.id, {'amazon_image_publish': False}, context=context)                    
                except:
                    error += "Error FTP file: %s\n"%(file_name)
                    
                if not is_error:
                    f.close()
            else:
                error += "Error code not present: %s\n"%(product.name)
                        
        return error
    
    def _get_parameter_proxy(self, cr, uid, context = None):
        ''' Return browse object for actual Company, used for reach every parameter
            setted up for Amazon market
        '''        
        company_ids=self.pool.get('res.company').search(cr, uid, [], context=context) # TODO search the first (only one!)
        if company_ids:
           parameter_ids=self.pool.get('amazon.parameter').search(cr, uid, [('company_id','=',company_ids[0])], context=context)
           if parameter_ids:
              parameter_proxy=self.pool.get('amazon.parameter').browse(cr, uid, parameter_ids[0], context=context)
              if parameter_proxy:
                 return parameter_proxy
        return False   

    # Amazon function for publish product:
    def _get_amazon_envelope(self, parameter_proxy, feed_type, messages):
        ''' Get 2 parameter and messages text, necessary for fill in Amazon 
            envelope for a generi product Feed
        '''        
        if messages=="":   # if no record don't create Feed record
            return ""
        else:    
            return """<?xml version="1.0" encoding="UTF-8"?>\n<AmazonEnvelope xsi:noNamespaceSchemaLocation="amzn-envelope.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                         <Header>\n<DocumentVersion>1.01</DocumentVersion>\n<MerchantIdentifier>%s</MerchantIdentifier>\n</Header>
                         <MessageType>%s</MessageType>\n%s
                         </AmazonEnvelope>"""%(parameter_proxy.merchant_identification, feed_type, messages)

    def _create_feed_message(self, cr, uid, ids, parameter_proxy, feed_type, context=None):
        ''' Create single message XML text for all product passed to include
            in Amazon product envelope
            feed_type is for the 4 type of message: product, image, inventary, price
        '''            
        company_id = 1 # TODO change
        result=""
        message_list=""
        i=0      
        warranty_ids = self.pool.get("amazon.warranty").search(cr, uid, [('company_id', '=', company_id)], context=context)
        if feed_type=="Product":
            # Get warranty terms:
            warranty_item = self.pool.get("amazon.warranty").search(cr, uid, [('company_id', '=', company_id)], context=context)
            if warranty_item:
                warranty = self.pool.get('amazon.warranty').browse(cr, uid, warranty_item[0], context=context).warranty
                warranty_xml = "<LegalDisclaimer>%s</LegalDisclaimer>"%(warranty.replace("\n", "&lt;br /&gt;") if warranty else "Nessuna garanzia produttore")
            else:
                warranty_xml = ""    
                
            for product in self.browse(cr, uid, ids, context=context):  # TODO actually always: Home / Outdoor Living
                i += 1
                
                # fields computed before:
                sku = self.get_sku(product.default_code)                

                description = (product.amazon_description or product.name or "Empty description").replace("\n", "&lt;br /&gt;")

                bullet_count = 0; bullet_xml = ""
                if product.amazon_material or product.amazon_color:
                    bullet_count += 1
                    bullet_xml += "<BulletPoint>%s %s</BulletPoint>"%("Colore: %s"%(product.amazon_color) if product.amazon_color else "", "Materiale: %s"%(product.amazon_material) if product.amazon_material else "", )                    
                if product.amazon_function:
                    for item_bullet in product.amazon_function.split("\n"):
                        if item_bullet.strip():
                            bullet_count += 1
                            if bullet_count <= 5:
                                bullet_xml += "<BulletPoint>%s</BulletPoint>"%(item_bullet.strip()[:50],)
                                
                # TODO correggere!!! mettere 5 righe da 50 caratteri
                key_count = 0; keywords_xml = ""
                if product.amazon_keywords:                    
                    for keyword_line in product.amazon_keywords.replace(","," ").replace("  "," ").split("\n"):
                        if keyword_line.strip(): # only exist keywords
                            key_count += 1                        
                            if key_count <= 5: # 5 line of keywords
                                keywords_xml += "<SearchTerms>%s</SearchTerms>"%(keyword_line.strip()[:50])

                message_list += "%s) SKU:%s\n"%(i, sku)
                result +="""<Message>
                            \t<MessageID>%s</MessageID>
                            \t<OperationType>Update</OperationType>
                            \t<Product>                            
                            \t\t<SKU>%s</SKU>%s%s%s
                            \t\t<NumberOfItems>%s</NumberOfItems>
                            \t\t<DescriptionData>
                            \t\t\t<Title>%s</Title>%s%s
                            \t\t\t<Description>%s</Description>%s%s%s
                            \t\t\t<Manufacturer>%s</Manufacturer>%s%s%s%s%s%s%s
                            \t\t</DescriptionData>
                            \t\t<ProductData>
                            \t\t\t<Home>
                            \t\t\t\t<ProductType>
                            \t\t\t\t\t<OutdoorLiving>%s%s</OutdoorLiving>
                            \t\t\t\t</ProductType>
                            \t\t\t\t<Parentage>child</Parentage>%s
                            \t\t\t</Home>
                            \t\t</ProductData>
                            \t</Product>
                            </Message>"""%(i,                                               # Message ID
                                           sku,                                             # SKU
                                           "\n<StandardProductID>\n<Type>EAN</Type>\n<Value>%s</Value>\n</StandardProductID>"%(product.ean13) if product.ean13 else "",    # EAN
                                           "<LaunchDate>%sT00:00:00Z</LaunchDate>"%(product.amazon_sale_start) if product.amazon_sale_start else "",
                                           "<ReleaseDate>%sT00:00:00Z</ReleaseDate>"%(product.amazon_sale_end) if product.amazon_sale_end else "",
                                           product.amazon_q_x_pack or 1,                    # Number of items     (TODO NumberOfItems difference ItemPackageQuantity )??
                                           product.amazon_title or product.name,            # Title
                                           "\n<Brand>%s</Brand>"%(product.amazon_brand) if product.amazon_brand else "",                      # Brand 
                                           "", #"\n<BulletPoint>%s</BulletPoint>"%(product.amazon_function) if product.amazon_function else "",    # Bullet point (function) 
                                           description,      # Description
                                           bullet_xml,           # Bulletpoint
                                           "<ItemDimensions><Length unitOfMeasure='%s'>%s</Length><Width unitOfMeasure='%s'>%s</Width><Height unitOfMeasure='%s'>%s</Height><Weight unitOfMeasure='%s'>%s</Weight></ItemDimensions>"%(
                                                                                                                                                  product.amazon_dimension_um.upper() if product.amazon_dimension_um else "CM",   # TODO: Manage better!
                                                                                                                                                  product.amazon_length, 
                                                                                                                                                  product.amazon_dimension_um.upper() if product.amazon_dimension_um else "CM",
                                                                                                                                                  product.amazon_width,
                                                                                                                                                  product.amazon_dimension_um.upper() if product.amazon_dimension_um else "CM",
                                                                                                                                                  product.amazon_height,
                                                                                                                                                  product.amazon_weight_um.upper() if product.amazon_dimension_um else "KG",
                                                                                                                                                  product.amazon_weight,
                                                                                                                                                  ),            # unitOfMeasure
                                           "", #TODO tolto e messo in fondo: warranty_xml,                                                                      # LegalDisclaimer
                                           product.amazon_manufacturer or "Re Desiderio",                                                                       # Manufacturer
                                           keywords_xml,                                                                                                        # Search Keywords
                                           "\n<SubjectContent>%s</SubjectContent>"%(product.amazon_function[0:50]) if product.amazon_function else "",          # Subject Content (function)       TODO non necessario
                                           "\n<IsGiftMessageAvailable>true</IsGiftMessageAvailable>" if product.amazon_is_gift else "",                         # Gift
                                           "\n<IsGiftWrapAvailable>true</IsGiftWrapAvailable>" if product.amazon_is_wrap else "",                               # Wrap
                                           "\n<IsDiscontinuedByManufacturer>true</IsDiscontinuedByManufacturer>" if product.amazon_is_discontinued else "",     # Discontinued                                           
                                           "\n<RecommendedBrowseNode>%s</RecommendedBrowseNode>"%product.amazon_category1_id.code if product.amazon_category1_id else "",     # BrowseNode 1
                                           "\n<RecommendedBrowseNode>%s</RecommendedBrowseNode>"%product.amazon_category2_id.code if product.amazon_category2_id else "",     # BrowseNode 2
                                           "<Material>%s</Material>"%(product.amazon_material) if product.amazon_material else "",                              # Material (Fabrics)               TODO non necessario
                                           "<VariationData><Color>%s</Color></VariationData>"%(product.amazon_color) if product.amazon_color else "",           # VariationData  > color           TODO non necessario
                                           "<SellerWarrantyDescription>%s</SellerWarrantyDescription>"%(warranty_xml) if False else "",                         # TODO cambiare frase poi attivare e provare 1500
                                           )  
        elif feed_type=="ProductImage":
            for product in self. browse(cr, uid, ids, context=context):  # TODO actually tutto  Home / Outdoor Living
                sku=self.get_sku(product.default_code)
                i += 1
                message_list += "%s) SKU:%s\n"%(i, sku)
                if product.default_code: # only for existant product  (if not present there's error associating product):
                    # TODO remove!!! only for test: part that delete image feed!!
                    #result +="""<Message>
                    #                <MessageID>%s</MessageID>
                    #                <OperationType>Delete</OperationType>
                    #                <ProductImage>\n<SKU>%s</SKU>\n<ImageType>Main</ImageType>\n<ImageLocation>%s</ImageLocation>\n</ProductImage>
                    #            </Message>"""%(i,                             # Message ID
                    #                           sku, #product.default_code,    # SKU
                    #                           "%s/%s"%(parameter_proxy.image_web_root, self.get_file_name(product.default_code)),
                    #                          )
                    i += 1
                    result +="""<Message>
                                    <MessageID>%s</MessageID>
                                    <OperationType>Update</OperationType>
                                    <ProductImage>\n<SKU>%s</SKU>\n<ImageType>Main</ImageType>\n<ImageLocation>%s</ImageLocation>\n</ProductImage>
                                </Message>"""%(i,                             # Message ID
                                               sku, #product.default_code,    # SKU
                                               "%s/%s"%(parameter_proxy.image_web_root, self.get_file_name(product.default_code)),
                                              )                   
        elif feed_type=="Inventory":
            for product in self. browse(cr, uid, ids, context=context):  # TODO actually tutto  Home / Outdoor Living
                    sku=self.get_sku(product.default_code)
                    i += 1
                    message_list += "%s) SKU:%s\n"%(i, sku)
                    result += """<Message><MessageID>%s</MessageID><OperationType>Update</OperationType>
                                <Inventory><SKU>%s</SKU><Quantity>%s</Quantity>
                                <FulfillmentLatency>%s</FulfillmentLatency></Inventory>
                                </Message>"""%(i,                             # Message ID
                                               sku,                           # SKU
                                               product.amazon_inventory,      # Company availability (decremented for security quantity)
                                               product.amazon_manage_days or 2,    # Time in days for manage orders
                                               )                           

        elif feed_type=="Price": 
            for product in self. browse(cr, uid, ids, context=context):  # TODO actually tutto  Home / Outdoor Living
                sku=self.get_sku(product.default_code)
                i += 1
                message_list += "%s) SKU:%s\n"%(i, sku)
                result += """<Message><MessageID>%s</MessageID>
                             <Price><SKU>%s</SKU>
                                <StandardPrice currency="EUR">%s</StandardPrice>%s</Price>
                             </Message>"""%(i,                       # Message ID
                                            sku,    # SKU
                                            "%2.2f"%(product.amazon_price),
                                            "", 
                                            #"""<Sale><StartDate>%s</StartDate><EndDate>%s</EndDate><SalePrice currency="EUR">%s</SalePrice></Sale>"""
                                            #%("2012-08-31T00:00:00Z", "2012-12-31T00:00:00Z", "100") if product.amazon_discount_price else "",   # TODO put rabat price
                                            )                           
        return result, message_list

    def create_report(self, cr, uid, feed_type, context = None): # TODO FINIRE ************************************************************
        ''' API for manage Reporting:
            FeedType:
            1) InventoryRequest = do a inventory flat file request for all product
            2) GetReport
        '''
        import time, datetime
        from mws import mws

        late_block = 300 # 5 minutes for generate report (default)

        if feed_type == "InventoryRequest":                  # Inventory
           report_type= "_GET_FLAT_FILE_OPEN_LISTINGS_DATA_"   
        else:                                                 
           raise osv.except_osv("error",'Incorrect report type request')  
           return
            
        parameter_proxy = self.pool.get('product.product')._get_parameter_proxy(cr, uid, context=context)
        if not parameter_proxy:
            raise osv.except_osv("error",'No parameter setted up for Amazon MWS, please setup after publish product')  # TODO Raise error control!
            return
        
        # Run report request: *************************************************
        amazon_report_api = mws.Reports(parameter_proxy.key, 
                                        parameter_proxy.secret, 
                                        parameter_proxy.seller_number, 
                                        domain = parameter_proxy.market_web_site)
        
        response = amazon_report_api.request_report(report_type) # start_date=None, end_date=None, marketplaceids=)
        try: # find code on response and create packed for report get
            report_request_id = response._response_dict['RequestReportResult']['ReportRequestInfo']['ReportRequestId']['value']
            time_home_product = (datetime.datetime.now() + datetime.timedelta(seconds = late_block)).strftime('%Y-%m-%d %H:%M:%S')
            feed_data = {'parameter_id': parameter_proxy.id,
                         'feed_xml': '',
                         'send_datetime': False,
                         'feed_code': report_request_id, # ReportRequestId (from response)
                         'error_text': False,
                         'description': "",
                         'api': 'report',
                         'name': 'Get inventory status',
                         'feed_type': report_type,
                         'scheduled_datetime': time_home_product,                         
                        }
            self.pool.get('amazon.feed').create(cr, uid, feed_data)
        except:
            raise osv.except_osv("error",'Error creating feed or analyzing response value') 
        # Schedule report read:
        return 

    def create_feed(self,cr, uid, ids, feed_type, lot_id, context = None):
        ''' Create Feed for product operation
            feed_type specify the 4 type of feed:
            Product, ProductImage, Inventory, Price 
            The lot_id is use for manage time scheduling for feeds
        '''
        import time, datetime
        late_time_feed = 300 # (seconds) that shift secondary feed time after the home product feed (that need to be created first
        late_block = 900     # (seconds) for shift block (lot) elements  15 minutes
        
        # Function utility for this method:
        def ascii_normalize(feed_xml):
            ''' Test every character for normalization
            '''
            tmp=""            
            for char in feed_xml:
                try:
                    if ord(char)<=128:
                       tmp += char
                except:                
                    pass # TODO error?
            return tmp    

        if feed_type not in self._feed_type_list:
           # TODO Error
           return 

        parameter_proxy = self._get_parameter_proxy(cr, uid, context=context)  
        (xml_text, description_text) = self._create_feed_message(cr, uid, ids, parameter_proxy, feed_type, context=context)
        feed_xml = self._get_amazon_envelope(parameter_proxy, 
                                             feed_type,
                                             xml_text,)
        if not feed_xml: # No record!
            return 
        feed_xml = ascii_normalize(feed_xml)
        feed_data = {'parameter_id': parameter_proxy.id,
                     #'create_datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
                     'feed_xml': feed_xml, 
                     'send_datetime': False,
                     'feed_code': False,
                     'error_text': False,
                     'description': description_text,
                     'api': 'product',
                    }

        # Different information according to feed type:
        time_home_product = (datetime.datetime.now() + datetime.timedelta(seconds = lot_id * late_block)).strftime('%Y-%m-%d %H:%M:%S')
        time_secondary_product = (datetime.datetime.now() + datetime.timedelta(seconds = lot_id * late_block + late_time_feed)).strftime('%Y-%m-%d %H:%M:%S')
        if feed_type=='Product':
           feed_data.update({
                             'name': 'Create/Update product (home) for %s items'%(len(ids)),
                             'feed_type': '_POST_PRODUCT_DATA_',
                             'scheduled_datetime': time_home_product,
                             })
        elif feed_type=='ProductImage':
            feed_data.update({
                              'name': 'Update image for %s items'%(len(ids)),
                              'feed_type': '_POST_PRODUCT_IMAGE_DATA_',
                              'scheduled_datetime': time_secondary_product,
                             })           
        elif feed_type=='Inventory': # TODO cambiare        
            feed_data.update({
                              'name': 'Update inventary for %s items'%(len(ids)),
                              'feed_type': '_POST_INVENTORY_AVAILABILITY_DATA_',
                              'scheduled_datetime': time_secondary_product,
                             })           
        elif feed_type=='Price':   # TODO Cambiare
            feed_data.update({
                              'name': 'Update price for %s items'%(len(ids)),
                              'feed_type': '_POST_PRODUCT_PRICING_DATA_',
                              'scheduled_datetime': time_secondary_product,
                             })
                             
        self.pool.get('amazon.feed').create(cr, uid, feed_data)
        return


    def create_all_product_feed(self,cr, uid, force_image, force_selected_image, context = None):
        ''' Batch block creation of product (first or forced by wizard)
        '''
        import logging        
        # Parameters:
        block=50
        
        _logger = logging.getLogger('mws_amazon')        
        product_ids=self.search(cr, uid, [('amazon_published','=',True)], context=context)
        
        #########################
        # CREATE IMAGE FTP FEED #
        #########################
        
        # TODO  publish check on each image:        
        if force_image or force_selected_image:
            if force_selected_image:
               _logger.info('Amazon: Force image publish on FTP')
               image_ids=self.search(cr, uid, [('amazon_published','=',True),('amazon_image_publish','=',True)], context=context)
               name='FTP publish selected images: %s'
            else:   
               _logger.info('Force image publish on FTP Amazon')
               image_ids = product_ids
               name='FTP publish all images: %s'
               
            error = self._ftp_images(cr, uid, image_ids, context = context)
            feed_img_data = {'name': name%(len(image_ids)),
                             'parameter_id': False,
                             'feed_xml': "No XML", 
                             'feed_type': "_FTP_",
                             'feed_code': "ImageFTP",
                             'error_text': False,
                             'api': 'ftp',
                            }
            if error:
                feed_img_data['error_text']=error
                feed_img_data['state']='error'
            else:    
                feed_img_data['state']='done'
            # Create e 'closed' feed for log operations    
            self.pool.get('amazon.feed').create(cr, uid, feed_img_data, context=context)
            
        ##################################
        # CREATE PRODUCT 4 FEED IN BLOCK #
        ##################################

        # Split packed in block of 20 records
        for i in range(0, (len(product_ids) // block) + (1 if len(product_ids) % block else 0)):        
            from_product = i * block
            to_product = (i + 1) * block
            lot_ids = product_ids[from_product:to_product]
            _logger.info('Amazon: Generate publish product update feed [%s:%s] - tot: %s'%(from_product, to_product, len(lot_ids)))            
            
            # Schedule Feed for product:
            self.create_feed(cr, uid, lot_ids, "Product", i, context = context)
            # Schedule Feed for product image:
            self.create_feed(cr, uid, lot_ids, "ProductImage", i, context = context)
            # Schedule Feed for product price:
            self.create_feed(cr, uid, lot_ids, "Inventory", i, context = context)
            # Schedule Feed for product avaliability
            self.create_feed(cr, uid, lot_ids, "Price", i, context = context)
        return True

    # on change function:
    def replace_char(self, value):
        ''' Transform chars non ascii (called from on_change functions)
        '''        
        replace={"à":"a'","è":"e'","é":"e'","ì":"i'","ò":"o'","ù":"u'",}
        
        if value:
            for key in replace:
                value.replace(key, replace[key])
        return value
        
    def on_change_long(self, cr, uid, ids, amazon_description, context=None):
        ''' Transform chars non ascii 
        '''
        # TODO controllare non funziona        
        return {'value': {'amazon_description': self.replace_char(amazon_description)}}

    # overrided function:
    def write(self, cr, uid, ids, vals, context=None):
        """ 
        When update record calculate values for inventory of company and
        amazon inventory update
            
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids to be update
        @param vals: dict of new values to be set
        @param context: context arguments, like lang, time zone
        
        @return: True on success, False otherwise
        """
     
        #TODO: process before updating resource
        res = super(product_product_amazon, self).write(cr, uid, ids, vals, context=context)
            
        product_proxy = self.browse(cr, uid, ids, context=context)[0]
        if product_proxy.amazon_product_set and 'amazon_amazon_inventory' in vals: # update amazon esistence
            vals={'amazon_amazon_set_inventory': product_proxy.amazon_amazon_inventory,}
            res = super(product_product_amazon, self).write(cr, uid, ids, vals, context=context)                       
        elif product_proxy.amazon_product_set:  # update inventory for company
            #('amazon_subproduct_ids' in vals or 'amazon_set_inventory' in vals or 'amazon_set_inventory_security_level' in vals): #amazon_amazon_set_inventory
            vals={'amazon_inventory': product_proxy.amazon_set_inventory,}
            res = super(product_product_amazon, self).write(cr, uid, ids, vals, context=context)                       
        return res
    
    # function fields:
    def _function_compute_set_company_inventory(self, cr, uid, ids, field_name, arg, context=None):
        ''' Compunte value depend on single inventory product and decremented with security level
        '''
        res={}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = 0    
            quantities = []
            for subproduct in product.amazon_subproduct_ids:
                if subproduct.max_set:  
                   quantities.append(int(subproduct.max_set))
            if quantities: 
                inventory = min(quantities) - product.amazon_set_inventory_security_level
                if inventory > 0:
                    res[product.id] = inventory
        return res
    
    def _is_amazon_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Test if exist amazon image file
        '''
        import os
        
        res={}
        if ids:
            root_path={}   # contains DB name linked to path         
            
            parameter = self._get_parameter_proxy(cr, uid, context=context)
            for path in parameter.path_ids:
                root_path[path.name]=path.image_fs_root
        
            for product in self.browse(cr, uid, ids, context=context):                
                if product.amazon_origin_db in root_path:
                    res[product.id] = os.path.exists(os.path.join(root_path[product.amazon_origin_db], self.get_file_name(product.default_code)))
                else:
                    res[product.id] = "" # TODO error
        return res

    def _get_amazon_image(self, cr, uid, ids, field_name, arg, context=None):
        ''' Read image from file (according to default folder for every DB 
            that own the linked to image)
        '''
        import base64, urllib, os

        res={}
        if ids:
            root_path={}   # contains DB name linked to path         
            
            parameter = self._get_parameter_proxy(cr, uid, context=context)
            for path in parameter.path_ids:
                root_path[path.name]=path.image_fs_root
        
            for product in self.browse(cr, uid, ids, context=context):
                if product.amazon_origin_db in root_path:
                    file_name = os.path.join(root_path[product.amazon_origin_db], self.get_file_name(product.default_code))                
                    exist=False
                    try: # Original image:
                        (filename, header) = urllib.urlretrieve(file_name)
                        f = open(filename , 'rb')
                        img = base64.encodestring(f.read())
                        f.close()
                        exist=True
                    except:
                        img = False
                    res[product.id] = img    
                    #res[product.id] = {}                
                    #res[product.id]['amazon_image'] = img
                    #res[product.id]['amazon_is_image'] = exist
                else:
                    img = False    
        return res
        
    _columns = {
               # Produt set:
               'amazon_product_set':fields.boolean('Amazon product set', required=False),
               'amazon_subproduct_ids':fields.one2many('amazon.subproduct', 'parent_id', 'Subproduct', required=False),
               'amazon_set_inventory_security_level': fields.integer('Set security level', help="Every set availability is calculated with max set formed with subproduct existence, the value on amazon is decremented with this security level"),
               'amazon_set_inventory': fields.function(_function_compute_set_company_inventory, method=True, type='integer', string='Company inventory', store=False),
               'amazon_amazon_set_inventory': fields.integer('Amazon inventory', help="Amazon inventory value"),
               
               'graph_total': fields.integer('Total'),
               # Amazon anagraphic extra fields:              
               'amazon_asin_code': fields.char('Amazon ASIN', size=25, required=False, help="ASIN / ISBN, Amazon unique key code number"),
               'amazon_title': fields.char('Amazon title', size=100, required=False, translate=True, help="Title of product in amazon"),
               'amazon_category1_id':fields.many2one('amazon.product.category', 'Amazon category 1', required=False, help="Also called Browse Node in Amazon"),
               'amazon_category2_id':fields.many2one('amazon.product.category', 'Amazon category 2', required=False, help="Also called Browse Node in Amazon"),
               'amazon_warranty': fields.boolean('Show Warranty', required=False, help="Show warranty terms on Amazon"),
               'amazon_published': fields.boolean('Published on Amazon', required=False, help="Product is visible on Amazon"),
               'amazon_image_publish': fields.boolean('Force image publish', required=False, help="Force FTP of image for publishing on Amazon (feed after)"),
               'amazon_origin_db': fields.char('Amazon Origin DB', size=80, required=False, help="Database origin of this product"),
               'amazon_description': fields.text('Amazon description', required=False, translate=True, help="Description of product in amazon"),
               'amazon_brand': fields.char('Amazon brand', size=80, required=False, translate=True, help="Brand of the product in amazon"),
               'amazon_designer': fields.char('Amazon designer', size=80, required=False, translate=True, help="Designer of product in amazon"),            # not used!
               'amazon_manufacturer': fields.char('Amazon manufacturer', size=80, required=False, translate=True, help="Manufacturer of product in amazon"),
               'amazon_is_gift': fields.boolean('Product if gift', required=False, help="Product is consider gift on Amazon"),
               'amazon_is_wrap': fields.boolean('Product if wrap', required=False, help="Product is wrap available on Amazon"),                             # not used!
               'amazon_is_discontinued': fields.boolean('Product discontinued', required=False, help="Product is discontinued by manufacturer on Amazon"),  # not used!
               
               'amazon_min_level': fields.integer('Re-order level', help="Quantity considered as minimum level of availability, used for highlight product or produce action"),
               'amazon_inventory': fields.integer('Company inventory', help="Availability on company (inventory quantity in the company store)"),
               'amazon_amazon_inventory': fields.integer('Amazon inventory', help="Availability on Amazon (inventory quantity in Amazon store)"),
               #'amazon_security_level' NOT present here!

               # Amazon anagrafic fields (coming from migration):
               'amazon_q_x_pack': fields.integer('Q. x pack', help="Quantity per pack"),
               'amazon_sale_start': fields.date('Amazon sale start date'),
               'amazon_sale_end': fields.date('Amazon sale end date'),
               'amazon_country_id':fields.many2one('res.country', 'Amazon origin (country)'),
               'amazon_out':fields.boolean('Amazon out of production', required=False),
               'amazon_function':fields.text('Principal function', required=False),
               'amazon_keywords':fields.text('Keywords', required=False),
               'amazon_manage_days': fields.integer('Amazon Manage days', help="Important for manage order, usually 2 days, after are added automatically the days for delvery, not managed, depend on carrier"),
               # Caracteristic:
               'amazon_color':fields.char('Color', size=50, required=False, readonly=False),                               
               'amazon_material':fields.char('Material', size=50, required=False, readonly=False),                               
               # Price:
               'amazon_price': fields.float('Amazon price', digits=(16, 2)),
               'amazon_amazon_price': fields.float('Amazon price (published)', digits=(16, 2), help="Amazon published price"),
               'amazon_discount_price': fields.float('Amazon discount price', digits=(16, 2)),
               'amazon_discount_start': fields.date('Start discount price'),
               'amazon_discount_end': fields.date('End discount price'),
               # Dimension:
               'amazon_length': fields.float('Amazon Length', digits=(16, 2)),
               'amazon_width': fields.float('Amazon Width', digits=(16, 2)),
               'amazon_height': fields.float('Amazon Height', digits=(16, 2)),
               'amazon_dimension_um':fields.char('Dimension UM', size=20, required=False, readonly=False),                
               # Volume
               'amazon_volume': fields.float('Amazon Volume', digits=(16, 2)),
               'amazon_volume_um':fields.char('Volume UM', size=20, required=False, readonly=False),                
               # Weight
               'amazon_weight': fields.float('Amazon Weight', digits=(16, 2)),
               'amazon_weight_um':fields.char('Weight UM', size=20, required=False, readonly=False),                
               'amazon_image': fields.function(_get_amazon_image, type="binary", string="Preview", method=True, store=False), #multi="Load image", 
               'amazon_is_image':fields.function(_is_amazon_image, type="boolean", string="Image find", method=True, store=False),               
               }
               
    _defaults = {
                'amazon_inventory': lambda *a: 0,
                'amazon_amazon_inventory': lambda *a: 0,
                'amazon_origin_db': lambda self, cr, uid, c: cr.dbname,
                'graph_total': lambda *a: 1,
                'amazon_manage_days': lambda *a: 4,
                'amazon_warranty': lambda *a: True,                
                }
product_product_amazon()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
