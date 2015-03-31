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

class product_quotation_folder(osv.osv):    
    _name = 'product.quotation.folder'
        
    _columns = {
               'name':fields.char('Description', size=64, required=True,),
               'addons':fields.boolean('Addons root path', required=False, help="Start from addons path, extra path is append to addons folder, instead of extra is complete path"),
               'root_path': fields.char('Folder extra path', size=128,required=False, help="Path extra default root folder, ex.: http://server/openerp"),
               'folder_path': fields.char('Folder extra path', size=128, required=True, help="Path extra default root folder, ex.: thumb/400/color, or complete path: /home/admin/photo"),
               'extension_image': fields.char('Extension', size=15, required=True, readonly=False, help="without dot, for ex.: jpg"),
               'default':fields.boolean('Default', required=False),
               'width': fields.integer('Witdh in px.'),
               'height': fields.integer('Height in px.'),
               'empty_image': fields.char('Empty image', size=64, required=True, help="Complete name + ext. of empty image, ex.: 0.png"),
               }
               
    _defaults = {
                'default': lambda *x: False,
                }          
product_quotation_folder()

class inherit_product_product(osv.osv):
    _name = 'product.product'
    _inherit = 'product.product'

    def get_image(self, cr, uid, item):
        ''' Get folder (actually 200 px) and extension from folder obj.
            Calculated dinamically image from module image folder + extra path + ext.
            Return image
        '''
        import os
        img = ''        
        folder_proxy = self.pool.get('product.quotation.folder')
        folder_ids = folder_proxy.search(cr, uid, [('width', '=', 200)])

        if folder_ids:
           folder_browse = folder_proxy.browse(cr, uid, folder_ids)[0]
           extension = "." + folder_browse.extension_image
           empty_image= folder_browse.empty_image
           if folder_browse.addons:
              image_path = tools.config['addons_path'] + '/quotation_photo_fiam/images/' + folder_browse.folder_path + "/"
           else:
              image_path = os.path.expanduser((folder_browse.folder_path + "/")%(cr.dbname) 
                                              if len(folder_browse.folder_path.split("%s"))==2 
                                              else folder_browse.folder_path + "/") 
              #folder_browse.root_path + '/' + folder_browse.folder_path + "/" (NOTE: tolta parte per immagine WEB)
        else: # no folder image
           return img # empty!
           
        product_browse=self.browse(cr, uid, item)
        if product_browse.code:
            # codice originale (tutte le cifre)
            try:
                (filename, header) = urllib.urlretrieve(image_path + product_browse.code.replace(" ", "_") + extension) # code image
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
                
            # codice padre (5 cifre):
            if (not img) and product_browse.code and len(product_browse.code)>=5:       
                try:
                    padre = product_browse.code[:5]
                    (filename, header) = urllib.urlretrieve(image_path + padre.replace(" ", "_") + extension) # code image
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''
                    
            # codice padre (3 cifre):
            if (not img) and product_browse.code and len(product_browse.code)>=3:       
                try:
                    padre = product_browse.code[:3]
                    (filename, header) = urllib.urlretrieve(image_path + padre.replace(" ", "_") + extension) # code image
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    img = ''
            
            # immagine vuota (default oppure quella nel modulo che esiste per forza):
            if not img:       
                try:
                    (filename, header) = urllib.urlretrieve(image_path + empty_image) # empty setted up on folder
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                except:
                    (filename, header) = urllib.urlretrieve(tools.config['addons_path'] + '/quotation_photo_fiam/empty.png') # empty with module
                    f = open(filename , 'rb')
                    img = base64.encodestring(f.read())
                    f.close()
                    #img = ''                
        return img
    
    def _get_image(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for item in ids:
            res[item] = self.get_image(cr, uid, item)
        return res                
        
    _columns = {
                'default_photo':fields.function(_get_image, type="binary", method=True),
               }
                
inherit_product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
