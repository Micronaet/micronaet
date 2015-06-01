# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) and the
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#    ########################################################################
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

# Format import string values:
def prepare(valore):  
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    ''' Parse as a date the value
    '''
    if valore: # TODO test correct date format
       return "%s-%s-%s"%(valore[:4],valore[4:6],valore[6:8])
    else:
       return False #time.strftime("%Y/%m/%d")

def prepare_float(valore):
    ''' Parse and strip data for tranform as a float value
    '''
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values        

# Get ID elements:
def get_product_um(self, cr, uid, um):
    ''' Read UM from name (parsed)
    '''
    parse = {'tn': 't',
             'kg': 'kg',
             'nr': 'Unità'} # TODO sono tutte??
    name = parse.get(um.lower(), False) 
    if name:
        um_id = self.pool.get('product.uom').search(cr, uid, [('name', '=', name)])
        if um_id:
           return um_id[0]
    return False    

def get_partner_supplier(self, cr, uid, ref, direction_in):
    ''' Read partner id for a supplier or customer depend on direction_in
    '''
    field_to_search= "mexal_s" if direction_in else "mexal_c"
    partner_id = self.pool.get('res.partner').search(cr, uid, [(field_to_search, '=', ref)])
    if partner_id:
       return partner_id[0]
    return False    

def get_partner_customer(self, cr, uid, ref):
    ''' Read partner id for a partner
    '''
    partner_id = self.pool.get('res.partner').search(cr, uid, [('mexal_c', '=', ref)])
    if partner_id:
       return partner_id[0]
    return False    

def get_product(self, cr, uid, ref):
    ''' Read product id 
    '''
    product_id = self.pool.get('product.product').search(cr, uid, [('mexal_id', '=', ref)])
    if product_id:
       return product_id[0]
    return False    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

