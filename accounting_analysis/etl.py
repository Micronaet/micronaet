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
import osv

# Utility: #####################################################################
class etl(osv.osv):
    """ Utility class for generic import and format
    """
    def prepare_date(valore):
        ''' Get ISO accounting YYYYMMAA format, return Postgres/OpenERP ISO format
        '''
        if valore and len(valore)==8: # TODO test correct date format
           return "%s-%s-%s"%(valore[:4],valore[4:6]valore[6:8])
        else:
           return time.strftime("%Y-%m-%d")

    def prepare_float(valore):
        ''' Generate a float element from accounting text value
        '''
        valore=valore.strip() 
        if valore: # TODO test correct date format       
           return float(valore.replace(",","."))
        else:
           return 0.0   # for empty values
           
    def prepare(valore):  
        ''' Generic preparation for decode text coming from Windows 
        '''
        valore=valore.decode('cp1252')
        valore=valore.encode('utf-8')
        return valore.strip()

    def shortcut(valore=''): 
        ''' used for code the title (partner or contact), ex.: Sig.ra > SIGRA
        '''
        if valore:
           valore = valore.upper()
           valore = valore.replace('.','')
           valore = valore.replace(' ','')
           return valore
           
class utility(osv.osv):
    """ Utility function for manage OpenERP Object in simple ETL operations
    """           
    # PRODUCT: #################################################################
    def get_tax_id(self,cr,uid,description):
    # get ID of tax from description value
    return sock.execute(dbname, uid, pwd, 'account.tax', 'search', [('description', '=', description),])[0]

    def get_uom(sock,dbname,uid,pwd,name,data):
        # Create if not exist name: 'name' UOM with data: data{}
        uom_id = sock.execute(dbname, uid, pwd, 'product.uom', 'search', [('name', '=', name),]) 
        if len(uom_id): 
           return uom_id[0] # take the first
        else:
           return sock.execute(dbname,uid,pwd,'product.uom','create',data)  

    def get_uom_categ(sock,dbname,uid,pwd,categ):
        # Create categ. for UOM
        cat_id = sock.execute(dbname, uid, pwd, 'product.uom.categ', 'search', [('name', '=', categ),]) 
        if len(cat_id): 
           return cat_id[0] # take the first
        else:
           return sock.execute(dbname,uid,pwd,'product.uom.categ','create',{'name': categ,})  

    # PARTNER: #################################################################
    def get_language(sock,dbname,uid,pwd,name):
        # get Language if exist (use english name request 
        return sock.execute(dbname, uid, pwd, 'res.lang', 'search', [('name', '=', name),])[0]

    def create_title(sock,dbname,uid,pwd,titles,table):
        # Create standard title for partner (procedure batch from tupla, set up from user)
        for title in titles:
            title_id = sock.execute(dbname, uid, pwd, 'res.partner.title', 'search', [('name', '=', title)])
            if not len(title_id):            
               title_id=sock.execute(dbname,uid,pwd, 'res.partner.title', 'create',{'name': title, 
                                                                                   'domain': table, 
                                                                                   'shortcut': ShortCut(title),
                                                                                  })  

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
