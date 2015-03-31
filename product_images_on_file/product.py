#########################################################################
# Copyright (C) 2009  Sharoon Thomas, Open Labs Business solutions      #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
from osv import osv, fields
import base64, urllib

class product_image_rules(osv.osv):
    _name = "product.image.rules"
    
    _columns = {
                'name':fields.char('Rule name', size=64, required=True, readonly=False),
                'field':fields.char('Field name', size=64, required=True, readonly=False),
                'from_char': fields.integer('From char'),
                'to_char': fields.integer('From char'),
                'image_type':fields.selection([
                    ('png','.PNG'),
                    ('jpg','.JPG'),
                    ('tif','.TIF'),
                    ('bmp','.BMP'),                    
                ],'Image type', select=True, readonly=False),                
                'sequence': fields.integer('Sequence'),                
               }
               
class product_product_image(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    
    def get_image(self, cr, uid, id, context = None):
        image_list = self.read(cr, uid, id, ['code',], context=context)
        if image_list['code']:
            # try to find completa product_code.PNG
            try:
                (filename, header) = urllib.urlretrieve(image_list['code'])
                f = open(filename , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            # else try to get parent category image    

        # else default empty filename:
        if img = '':        
            img = '' # TODO metto l'immagine tipo vuota!
        return img
    
    def _get_image(self, cr, uid, ids, field_name, arg, context = None):
        '''Search if there is a file name / link for this image:'''
        
        if context is None:
           context={}
           
        res = {}
        for product in ids:
            res[product] = self.get_image(cr, uid, product, context=context)
        return res
    
    _columns = {
        #'filename':fields.char('File Location', size=250),
        'preview':fields.function(_get_image, type="binary", method=True),
    }
product_product_image()
