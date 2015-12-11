# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

from openerp.osv import osv, fields

# Utility function: ############################################################
# Conversion function:
def prepare(valore):  
    valore=valore.decode('cp1252')
    valore=valore.encode('utf-8')
    return valore.strip()

def prepare_date(valore):
    valore=valore.strip()
    if len(valore)==8:
       if valore: # TODO test correct date format
          return valore[:4] + "-" + valore[4:6] + "-" + valore[6:8]
    return False

def prepare_float(valore):
    valore=valore.strip() 
    if valore: # TODO test correct date format       
       return float(valore.replace(",","."))
    else:
       return 0.0   # for empty values

# ID function:
def get_partner_id(self, cr, uid, ref, c_o_s, context=None):
    ''' Get OpenERP ID for res.partner with passed accounting reference
    '''
    if c_o_s.lower() not in ("c","s"):
        return False
        
    item_id = self.pool.get('res.partner').search(cr, uid, [('mexal_' + c_o_s.lower(), '=', ref)], context=context)
    if item_id:
       return item_id[0]
    return False

def browse_partner_id(self, cr, uid, item_id, context=None):
    ''' Return browse obj for partner id
    '''
    browse_ids = self.pool.get('res.partner').browse(cr, uid, [item_id], context=context)
    if browse_ids:
       return browse_ids[0]
    return False

def get_product_id(self, cr, uid, ref, context=None):
    ''' Get OpenERP ID for product.product with passed accounting reference
    '''
    item_id = self.pool.get('product.product').search(cr, uid, [('default_code', '=', ref)], context=context)
    if item_id:
       return item_id[0]
    return False

def browse_product_id(self, cr, uid, item_id, context=None):
    ''' Return browse obj for product id
    '''
    browse_ids = self.pool.get('product.product').browse(cr, uid, [item_id], context=context)
    if browse_ids:
       return browse_ids[0]
    return False

class statistic_invoice(osv.osv):
    ''' Object that contain invoice for month for partner (only for statistics
    '''
    _name = 'etl.accounting.invoice'
    _description = 'Statistic invoice'
    _order = 'name'
    
    # Scheduled action: ########################################################
    def schedule_etl_accounting_invoice(self, cr, uid, path, file_name, verbose=False, context=None):
        ''' Import deadline from accounting
        '''
        import logging, sys, os
        _logger = logging.getLogger('accounting_analysis_invoice')

        # Open CSV passed file (see arguments) mode: read / binary, delimiation char 
        tot_col = 0
        counter={'tot': 0, 'new':0, 'upd':0, 'order':0} # tot negative (jump N lines)

        try: 
            file_input=os.path.join(os.path.expanduser(path),file_name)
            rows = open(file_input,'rb') 
        except:
            _logger.error("Problem open file: [%s, %s]"%(path, file_name))
            return
        
        line_pool=self # TODO remove
        
        # Remove all previous
        invoice_ids = self.search(cr, uid, [], context=context) 
        response = self.unlink(cr, uid, invoice_ids, context=context) 

        try: # generic error:
            for row in rows:
                line=row.split(";")
                if tot_col==0:
                   tot_col=len(line)
                   _logger.info("Start import [%s] Cols: %s"%(file_input, tot_col,))
                   
                if not (len(line) and (tot_col==len(line))): # salto le righe vuote e le righe con colonne diverse
                    _logger.error("Line: %s - Empty line or different cols [Org: %s - This %s]"%(counter['tot'],tot_col,len(line)))
                    continue 

                counter['tot']+=1 
                try: # master error:
                    csv_id=0       # Codice cliente di mexal forma (NNN.NNNNN)
                    partner_ref = prepare(line[csv_id])
                    csv_id+=1      # Month (integer)
                    month = prepare(line[csv_id]).strip()
                    csv_id+=1      # Year (interger)
                    year = prepare(line[csv_id]).strip()
                    csv_id+=1      # Amount
                    total = prepare_float(line[csv_id]) 
                    
                    date="%s-%s-01"%(year,month)
                    
                    partner_id = get_partner_id(self, cr, uid, partner_ref, "c", context=context)
                     
                    if not partner_id:
                       _logger.error("Line: %s - Partner not found: %s (jumped)"%(counter['tot'],partner_ref))
                       continue
 
                    partner_proxy = browse_partner_id(self, cr, uid, partner_id, context=context)
 
                    # TODO calcolare in base al fido scoperto_c = get_partner_info(sock, uid, pwd, partner_id) # TODO solo per i clienti (fare fornitori)
                    
                    name = "%s [%s]: %s (%s EUR)"%(partner_proxy.name, partner_ref, "%s-%s"%(year, month), total)
                    data={'name': name,
                          'partner_id': partner_id,
                          'date': date,
                          'total': total,
                          }
                          
                    try:
                        invoice_id = self.create(cr, uid, data, context=context)
                        if verbose: _logger.info("Line: %s - Invoice insert: %s"%(counter['tot'],name))
                    except:
                       _logger.error("Line: %s - Error creating invoice: %s (jumped)"%(counter['tot'],name))
                except:
                    _logger.error("Line: %s - Generic error import this line"%(counter['tot'],))
                           
        except:
            _logger.error("Line: %s - Generic error!"%(counter['tot'],))

        _logger.info("End importation invoice [%s]"%(counter,))
        return

    _columns = {
        'name':fields.char('Descrizione', size=64, required=False, readonly=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=False),
        'total': fields.float('Importo', digits=(16, 2)),
        #'type_document':fields.selection([('ft','Fattura'),
        #                                  ('oc','Ordine'),
        #                                  ('bc','DDT'),
        #                                 ],'Tipo doc.', select=True),
        'date': fields.date('Date', help="Start of the month"),
    }
    _defaults = {
        'total': lambda *a: 0.0,
    }
statistic_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
