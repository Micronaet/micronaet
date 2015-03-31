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

company_id = 1 # TODO parametrize

class amazon_publish_wizard(osv.osv_memory):   
    ''' Force publication of all product signed as amazon_published
    '''    
    _name='amazon.publish.wizard'
    _description='Amazon publish wizard'

    # Wizard button function:    
    def publish_on_amazon(self, cr, uid, ids, context = None):
        ''' Event button:
            publish on Amazon using API of MWS Amazon market
        '''
        import logging

        _logger = logging.getLogger('mws_amazon')
        _logger.info('Start publish on Amazon:')
        # TODO publish procedure (publish all product and after image, price, esistence etc.)
        
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]        
        # Create / publish product and generate link with SKU-Amazon ID
        self.pool.get('product.product').create_all_product_feed(cr, uid, wiz_proxy.force_image, wiz_proxy.force_selected_image, context = context)
        # Image
        # Esistence
        # Price
        
        return {'type' : 'ir.actions.act_window_close'} 

    _columns = {
                'market_id': fields.many2one('amazon.parameter', 'Market', required=True, readonly=False),
                'force_image': fields.boolean('Force image', required=False, help="Force publishing of product image via FTP of all Amazon articles"),
                'force_selected_image': fields.boolean('Force selected image', required=False, help="Force publishing of selected product image via FTP of all Amazon articles"),
    }    
    _defaults = {
        'market_id': lambda *a: company_id, # TODO change and parametrize!
        'force_image': lambda *a: False,
        'force_selected_image': lambda *a: False,
    }
amazon_publish_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
