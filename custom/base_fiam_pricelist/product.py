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

from osv import osv, fields
from datetime import datetime
import decimal_precision as dp
import tools  # for parameters
import base64, urllib

class product_custom_duty(osv.osv):
    '''Anagrafic to calculate product custom duty depending of his category
       (using % of tax per supplier cost)
    '''
    _name = 'product.custom.duty'
    _description = 'Product custom duty'
    
    _columns = {
        'name':fields.char('Custom duty', size=100, required=True, readonly=False),
        'code':fields.char('Code', size=24, required=False, readonly=False),
        'tax_ids':fields.one2many('product.custom.duty.tax', 'duty_id', '% Tax', required=False),
        #'tax': fields.float('% Tax', digits=(16, 2)),
    }
product_custom_duty()

class product_custom_duty_tax(osv.osv):
    '''Cost for country to import in Italy
    '''
    _name = 'product.custom.duty.tax'
    _description = 'Product custom duty tax'
    _rec_name = 'tax'
    
    _columns = {
        'tax': fields.float('% Tax', digits=(8, 3)),
        'country_id':fields.many2one('res.country', 'Country', required=True),
        'duty_id':fields.many2one('product.custom.duty', 'Duty code', required=False),
    }
    
    _defaults = {
        'tax': lambda *a: 0.0,
    }
product_custom_duty_tax()    

class create_base_image_folder(osv.osv):    
    _name = 'base.image.folder'
        
    _columns = {
               'name':fields.char('Description', size=64, required=True,),
               'addons':fields.boolean('Addons root path', required=False),
               'root_path': fields.char('Foder extra path', size=128,required=False, help="Path extra default root folder, ex.: http://server/openerp"),
               'folder_path': fields.char('Foder extra path', size=128, required=True, help="Path extra default root folder, ex.: thumb/400/color"),
               'extension_image': fields.char('Extension', size=15, required=True, readonly=False, help="without dot, for ex.: jpg"),
               'default':fields.boolean('Default', required=False),
               'width': fields.integer('Witdh in px.'),
               'height': fields.integer('Height in px.'),
               'empty_image': fields.char('Empty image', size=64, required=True, help="Complete name + ext. of empty image, ex.: 0.png"),
               }
               
    _defaults = {
                'default': lambda *x: False,
                }          
                 
create_base_image_folder()

class base_product_exchange(osv.osv):
    '''Exchange USD to EUR
    '''    
    _name='base.product.exchange'
        
    def get_last_exchange(self, cr, uid, ids):
        '''Search last date exchange and return value
        '''
        try:
            exchange_ids = self.search(cr, uid, [], order="date DESC")
            exchange_read = self.read(cr, uid, exchange_ids[0], ['exchange',]) 
            if exchange_read:
               return round(exchange_read['exchange'],2) or 0.0
            else:   
               return 0.0
        except:       
            return 0.0       
        
    _columns = {
               'name': fields.char('Description', size=40, required=True, readonly=False),
               'exchange': fields.float('Exchange', digits=(16, 2)),               
               'date': fields.date('Date of quotation'),               
                }
                
    _defaults = {
                'exchange': lambda *x: 0.0,
                'date': lambda *a: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }                            
base_product_exchange()

class base_container_type(osv.osv):
    '''Type of Container: type of container used for standard total cost
       used for divide for tot article to part cost on unit
    '''
    
    _name='base.container.type'
        
    _columns = {
               'name': fields.char('Container', size=40, required=True, readonly=False),
               'cost': fields.float('Loan cost (EUR)', digits=(16, 2)),               
               'date': fields.date('Date of quotation'),               
                }
                
    _defaults = {
                'cost': lambda *x: 0.0,
                'date': lambda *a: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }                            
base_container_type()

class base_fiam_pricelist_product_packaging(osv.osv):
    '''Add extra fields for 
    '''
    _name='product.packaging'
    _inherit ='product.packaging'

    # fields function         
    def _function_get_volume(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pack in self.browse(cr, uid, ids, context=context):
            res[pack.id] = (pack.length or 0 * pack.width or 0 * pack.height or 0) / 1000000 # TODO approx
        return res
 
    def _function_get_transport(self, cr, uid, ids, name, args, context=None):
        res = {}
        for pack in self.browse(cr, uid, ids, context=context):
            try:
               res[pack.id] = round((pack.container_id and pack.container_id.cost or 0) / (pack.q_x_container or 0),2)
            except: # division by zero!
               res[pack.id]=0.00
        return res
        
           
    _columns = {
               #'package_volume': fields.function(_function_get_volume, method=True, type='float', string='Transport cost unit', store=False),
               'container_id':fields.many2one('base.container.type', 'Container type', required=False, ondelete="set null"),
               'q_x_container': fields.integer('Q. per container'),  
               'transport_cost': fields.function(_function_get_transport, method=True, type='float', string='Transport cost unit (EUR)', store=False),

               'dimension_text': fields.text('Dimensione (testuale)'), # eliminare solo per importazione
               'error_dimension_pack': fields.boolean('Errore dimens. pack'), # eliminare solo per importazione
              
               'pack_volume': fields.float('Pack volume (manual)', digits=(16, 3)),
               'pack_volume_manual': fields.boolean('Manual volume'),
                }
                
    _defaults = {
                'q_x_container': lambda *x: 0,
                }            
base_fiam_pricelist_product_packaging()

class base_fiam_product_history_cost(osv.osv):
    _name = 'product.product.history.cost'
    
    _columns = {
               'name':fields.char('Name of history', size=40, required=True, readonly=False, help="Normalmente calcolato dal wizard di storicizzazione: Anno 2010"),
               'fob_cost': fields.float('FOB history cost USD', digits=(16, 2)),                
               'fob_pricelist': fields.float('Pricelist EUR', digits=(16, 2)),                
               'date': fields.date('Date of storicization'),
               'product_id':fields.many2one('product.product', 'Product ref.', required=True),               
               }
               
    _order = 'date DESC'
    
base_fiam_product_history_cost()

class base_fiam_pricelist_partnerinfo(osv.osv):
    _name = 'pricelist.partnerinfo'
    _inherit = _name

    def on_change_price_usd(self, cr, uid, ids, price_usd, context=None):
       '''Get USD price and translate in EUR value taken the last exchange value
       '''
       
       res = {'value':{'price': 0.0}}
       exchange = self.pool.get("base.product.exchange").get_last_exchange(cr, uid, ids) 
       if exchange:
          res['value']['price']=round((price_usd / exchange), 2)
       
       return res
    
    _columns = {
               'price_usd': fields.float('Unit Price USD', required=True, digits_compute=dp.get_precision('Purchase Price'),)
               }
base_fiam_pricelist_partnerinfo()

class base_fiam_pricelist_product(osv.osv):
    _name = 'product.product'
    _inherit = 'product.product'

    # Fields function:
    def _get_fob_cost_default_selected(self, product):
        ''' In the product search default value for supplier setted up as default
            (return the first)
        '''
        if not product.seller_ids: 
            return 0.0
        for pricelist in product.seller_ids[0].pricelist_ids:
            if pricelist.is_active:                
                return pricelist.price or 0.0
        return product.seller_ids[0].pricelist_ids[0].price if product.seller_ids[0].pricelist_ids else 0.0
    
    def _get_fob_cost_default(self, cr, uid, ids, args, field_list, context=None):
        ''' Return default cost for first supplier
        '''        
        product_proxy=self.browse(cr, uid, ids, context=context)
        res = {}
        for item in product_proxy:
            res[item.id] = {}
            exchange = self.pool.get("base.product.exchange").get_last_exchange(cr, uid, ids)
            price_eur = self._get_fob_cost_default_selected(item) # item.seller_ids and item.seller_ids[0].pricelist_ids and item.seller_ids[0].pricelist_ids[0].price or 0.0
            if exchange:
               res[item.id]['fob_cost_supplier'] = price_eur * exchange
            else:
               res[item.id]['fob_cost_supplier']=0.0
            res[item.id]['fob_cost_supplier_eur'] = price_eur
        return res

    def _get_full_calculation(self, cr, uid, ids, args, field_list, context=None):
        ''' Return all calculation for eur conversion and pricelist
        '''
        if context is None:
           context = {}
        res = {}
  
        product_proxy=self.browse(cr, uid, ids, context=context)
        for item in product_proxy:
            res[item.id] = {}
            exchange = self.pool.get("base.product.exchange").get_last_exchange(cr, uid, ids)             
            
            calc_transport = item.transport_packaging or 0.0
            calc_cost = item.fob_cost_supplier or 0.0
            
            if exchange:
               res[item.id]['dazi_eur'] = item.dazi / exchange
               res[item.id]['fob_cost_total'] = round(calc_cost + item.dazi + (calc_transport * exchange), 2) 
               res[item.id]['fob_cost_total_eur'] = res[item.id]['fob_cost_total'] / exchange
               res[item.id]['transport_packaging_usd'] = calc_transport * exchange
               res[item.id]['fob_pricelist_compute'] = round((100 + item.margin) * res[item.id]['fob_cost_total'] / 100, 2)
               res[item.id]['fob_pricelist_compute_eur'] = res[item.id]['fob_pricelist_compute'] / exchange
            else:
               res[item.id]['dazi_eur'] = 0.0
        return res

    def _get_transport_cost_default(self, cr, uid, ids, args, field_list, context=None):
        ''' Return default cost first package
        '''        
        package_proxy=self.browse(cr, uid, ids, context=context)
        res = {}
        for item in package_proxy:   
            res[item.id] = item.packaging and item.packaging[0].transport_cost or 0.0
        return res
       
    # Button function:       
    def button_dummy(self, cr, uid, ids, context=None):
        return True
 
    def copy_price_calculated(self, cr, uid, ids, data, context = None):
        ''' Button function for copy calculated price in fields price
            TODO unificare con _get_fob_cost_default
        '''      
        if context is None:
           context = {}  

        res = {}
        product_proxy=self.browse(cr, uid, ids, context=context)
        exchange = self.pool.get("base.product.exchange").get_last_exchange(cr, uid, ids) or 0.0  # change EUR price only
        for item in product_proxy: # write EUR e USD price
            if context.get('start_from_cost',0): # exist start_cost context (start from seller pricelist cost:
               res['fob_cost_eur']=item.seller_ids and item.seller_ids[0].pricelist_ids and item.seller_ids[0].pricelist_ids[0].price or 0.0
               res['fob_cost']=item.seller_ids and item.seller_ids[0].pricelist_ids and item.seller_ids[0].pricelist_ids[0].price_usd or 0.0
            
            self.write(cr, uid, ids, res)
                 
        return True

    def get_image(self, cr, uid, id):
        ''' Get folder (actually 200 px) and extension from folder obj.
            Calculated dinamically image from module image folder + extra path + ext.
            Return image
        '''
        img = ''        
        folder_proxy = self.pool.get('base.image.folder')
        folder_ids = folder_proxy.search(cr, uid, [('width', '=', 200)])
        #import pdb; pdb.set_trace()     
        if folder_ids:
           folder_browse = folder_proxy.browse(cr, uid, folder_ids)[0]
           extension = "." + folder_browse.extension_image
           empty_image= folder_browse.empty_image
           if folder_browse.addons:
              image_path = tools.config['addons_path'] + '/base_fiam_pricelist/images/photo/' + folder_browse.folder_path + "/"
           else:
              image_path = folder_browse.root_path + '/' + folder_browse.folder_path + "/"
              
        else: # no folder image
           return img # empty!
           
        product_browse=self.browse(cr, uid, id)
        if product_browse.code:
            # codice originale
            try:
                (filename, header) = urllib.urlretrieve(image_path + product_browse.code + extension)
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            # codice padre:
            
            # immagine vuota:
            if not img:       
                try:
                    (filename, header) = urllib.urlretrieve(image_path + empty_image)
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''                
        return img
    
    def _get_image(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for item in ids:
            res[item] = self.get_image(cr, uid, item)
        return res                
        
    _columns = {
                'preview':fields.function(_get_image, type="binary", method=True),
                'in_pricelist': fields.boolean('In Pricelist', required=False),
                
        
                'height': fields.float('Height', help='The max height of the product'),
                'width': fields.float('Width', help='The max width of the product'),
                'length': fields.float('Length', help='The max length of the product'),
                
                'error_import': fields.boolean('Import error'), # eliminare solo per importazione
                'dimension_text': fields.text('Dimensione (testuale)'), # eliminare solo per importazione
                'error_dimension': fields.boolean('Errore dimens.'), # eliminare solo per importazione
                
                
                'colour': fields.text('colour'),
                'fabric': fields.text('Fabric - Glass'),
                'type_of_material': fields.text('Type of material or fabric'),
                
                #'weight_tare': fields.float('Tare weight', help="Tare weight in Kg."),  
                'description_web': fields.text('Web Description',translate=True),               
                
                # Cost calculation:
                'fob_cost_supplier': fields.function(_get_fob_cost_default, method=True, type='float', string='Cost from supplier', store=False, multi="supplier_cost"),
                'fob_cost_supplier_eur': fields.function(_get_fob_cost_default, method=True, type='float', string='Cost from supplier (EUR)', store=False, multi="supplier_cost"),
                'transport_packaging': fields.function(_get_transport_cost_default, method=True, type='float', string='Cost from packaging (EUR)', store=False),
                
                # Campi di input:
                'duty_id':fields.many2one('product.custom.duty', 'Custom duty', required=False),
                'dazi': fields.float('Dazi (USD)', digits=(16, 2)),                
                'margin': fields.float('% margin (calc)', digits=(5, 2)),                
                'fixed_margin': fields.float('% margin (fixed)', digits=(5, 2)),                
                
                # Campi calcolati:
                'dazi_eur': fields.function(_get_full_calculation, method=True, type='float', string='Dazi (EUR)', digits=(16, 2), store=False, multi="total_cost"), 
                'transport_packaging_usd': fields.function(_get_full_calculation, method=True, type='float', string='Cost from packaging (USD)', store=False, multi="total_cost"),
                'fob_cost_total': fields.function(_get_full_calculation, method=True, type='float', string='FOB cost total (USD)', digits=(16, 2), store=False, multi="total_cost", help='FOB cost + transport + dazi'), 
                'fob_cost_total_eur': fields.function(_get_full_calculation, method=True, type='float', string='FOB cost total (EUR)', digits=(16, 2), store=False, multi="total_cost"), 
                'fob_pricelist_compute_eur': fields.function(_get_full_calculation, method=True, type='float', string='Pricelist compute (EUR)', digits=(16, 2), store=False, multi="total_cost"), 
                'fob_pricelist_compute': fields.function(_get_full_calculation, method=True, type='float', string='Pricelist compute (UDS)', digits=(16, 2), store=False, multi="total_cost"), 
                'manual_pricelist':fields.boolean('Manual pricelist', required=False, help='If manual pricelist user set up price and program compute margin, else margin is set up and price list is compute'),
                
                'fob_pricelist': fields.float('Pricelist (EUR)', digits=(16, 2)),                

                'history_cost_ids':fields.one2many('product.product.history.cost', 'product_id', 'History cost', required=False),
                }
                
    _defaults = {
                'manual_pricelist': lambda *x: False,
                'in_pricelist': lambda *x: False,
                }                      
base_fiam_pricelist_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
