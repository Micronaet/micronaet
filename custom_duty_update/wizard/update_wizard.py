# -*- encoding: utf-8 -*-
##############################################################################
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
import os
from osv import fields,osv
import logging


# Create log object:
_logger = logging.getLogger(__name__)

class product_custom_duty_update_wizard(osv.osv_memory):
    """ Update duty value depend on product category
    """
    _name = 'product.custom.duty.update.wizard'
    
    def action_update(self, cr, uid, ids, context = None):
        """
        The cancel action for workflow
        @param cr: cursor to database
        @param user: id of current user
        @param ids: list of record ids on which business flow executes
        @param *args: other arguments 
       
        @return: return True if all constraints satisfied, False otherwise
        """
        if context is None:
           context = {}
       
        wiz_browse = self.browse(cr, uid, ids[0], context = context)
        #wiz_browse.update:

        path = os.path.join(os.path.expanduser("~"), "etl", "fiam", "duty")
        try: 
            os.mkdir(path)
        except:
            pass # no error (maybe present)
                
        log_file_in = os.path.join(path, "product_duty.csv")
        log_file_out = os.path.join(path, "no_product_duty.csv")
        log_file_upd = os.path.join(path, "updated_product_duty.csv")
        
        f_in = open(log_file_in, "w")
        f_out = open(log_file_out, "w")
        f_upd = open(log_file_upd, "w")

        header = "Codice;Descrizione;Categoria doganale (tassa);Fornitore;Costo USD;Dazio attuale;Dazio nuovo;Error\n"
        f_in.write(header)
        f_out.write(header)
        f_upd.write(header)
        
        # Export all product that will be updated:
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [], context = context)
        for product in product_pool.browse(cr, uid, product_ids, context = context):
            try:
                error = ""
                supplier = ""
                dazi = 0.0
                tax = 0.0
                price_usd = 0.0
                if len(product.seller_ids) == 1:
                    pricelist_ref = False
                    supplier = product.seller_ids[0].name.name
                    tot = 0
                    country_id = product.seller_ids[0].name.country.id # save current country
                   
                    if product.duty_id and product.duty_id.tax_ids:
                        # TODO check nation!!                       
                        # loop for find current country_id
                        # no_tax = True
                        # for country in product.duty_id.tax_ids:
                        #     if country.country.id == country_id:
                        #         tax = country.tax
                        #         no_tax = False
                        # if no_tax:
                        #     error = "Non trovato il codice nazione per questo fornitore nella categoria doganale"
                        
                        tax = (product.duty_id.tax_ids[0].tax / 100.0) 
                        
                    for pricelist in product.seller_ids[0].pricelist_ids:
                        if pricelist.is_active:
                            price_usd = pricelist.price_usd
                            dazi = price_usd * tax 
                            tot += 1
                            
                            # update if present and update checked
                            if dazi: 
                                if wiz_browse.update:
                                    product_pool.write(cr, uid, product.id, {'dazi': dazi, }, context = context)
                                
                                # Log in file:
                                f_upd.write("'%s;%s;%s (%10.3f);%s;'%10.3f;'%10.3f;'%10.3f;%s\n" % (
                                    product.default_code.encode('ascii', 'ignore') if product.default_code else "Nessun codice",
                                    product.name.encode('ascii', 'ignore') if product.name else "Nessun nome",
                                    product.duty_id.name.encode('ascii', 'ignore') if product.duty_id else "Nessuna categoria",
                                    tax,
                                    supplier,
                                    price_usd,
                                    product.dazi, # dazi_eur
                                    dazi, # new 
                                    "", ))

                    if tot > 1:
                        error = "Troppe voci attive di listino"
                    elif not tot:
                        error = "Nessuna voce di listino"
                else:
                    error = "Nessuna fornitore"

                if not wiz_browse.update: # create only for no update                               
                    if error:
                        f = f_out
                    else:
                        f = f_in
                                           
                    f.write("'%s;%s;%s (%10.3f);%s;'%10.3f;'%10.3f;'%10.3f;%s\n"%(
                        product.default_code.encode('ascii', 'ignore') if product.default_code else "Nessun codice",
                        product.name.encode('ascii', 'ignore') if product.name else "Nessun nome",
                        product.duty_id.name.encode('ascii', 'ignore') if product.duty_id else "Nessuna categoria",
                        tax,
                        supplier,
                        price_usd,
                        product.dazi, # dazi_eur
                        dazi, # new 
                        error.encode('ascii', 'ignore'), ))
            except:
                _logger.error("Errore esportando la riga, saltata!")
        f_in.close()
        f_out.close()
        f_upd.close()
        return True #{'type': 'ir.actions.act_window.close', }

    _columns = {
        'update':fields.boolean('Update', required = False, help = "Update values, else export a list of product and value that will be updated"),
    }
               
    _defaults = {
        'update': lambda *x: False,
    }
                
product_custom_duty_update_wizard()                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
