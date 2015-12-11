##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse


stock_location = {} # list of 4 location used in this parser
start = 1

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'stock_move': self.stock_move,
            'sign_of_move': self.stock_sign_and_document,
            'company_number': self.company_number,
            'get_sequence': self.get_sequence,
        })

    def adjust_um(self, from_factor, to_factor):        
        return 1.0 / (from_factor / to_factor)

    def get_sequence(self):
        ''' Sequence of record
        '''
        global start
        
        actual=start
        start += 1
        return actual
    
    def load_location(self):
        ''' Load 4 stock location once (used from 2 procedure)
        '''
        global stock_location
        
        type_location=('internal',
                       'in',
                       'out',
                       'production')
        for location in type_location:
            location_ids=self.pool.get('stock.location.type').search(self.cr, self.uid, [('name','=',location)])
            if location_ids:
               stock_location[location]=self.pool.get('stock.location.type').read(self.cr, self.uid, location_ids[0])['location_id'][0] # only the first (no duplication record)
            else:                  
               stock_location[location]=False # TODO errore da comunicare

    def company_number(self, partner_id, type_of='c'):    
        ''' Test the partner_id (of the company), reading the:
            commercial name for duty (if type_of='c') else 
            internal name for duty (if type_of='i') 
        '''
        if partner_id:
           partner_proxy=self.pool.get('res.partner').browse(self.cr, self.uid, partner_id)
           if type_of=="c":
              return partner_proxy.combine_name
           else: # "i"
              return partner_proxy.combine_name_internal
        return ""
               
    def stock_sign_and_document(self, move_browse): #move_id):    
        ''' Search location in and out to decide sign of operation
            supplier to stock,        (+)  XAB  Supplier
            stock to customer,        (-)  XAB  Customer
            stock to production       (-)  VIA  Company
                                 0          1                          2       3      4      5          6               7            8          9  
            return tuple with: (sign, type of doc (VIA or XAB),  document id, q in, q out, hygro,  gg (operazione), mm (operazione),gg (mov), mm (mov),
        '''
        global stock_location
        self.load_location()

        if move_browse:
           try:
               #  FROM     
               if   move_browse.location_id.id == stock_location['in']  and move_browse.location_dest_id.id == stock_location['internal']:          
                  # supplier to stock +  TODO (calculate hygro value)       (***BF***)
                  return (
                      "+", 
                      "XAB", 
                      move_browse.picking_id.partner_id.combine_name if  move_browse.picking_id.partner_id else "NO SUPPL. CODE!", 
                      move_browse.picking_id.origin.split(" ")[0], #move_browse.picking_id.name,
                      # Carico al completo (non epurato dell'umidita')
                      self.adjust_um(move_browse.product_uom.factor, move_browse.product_id.uom_id.factor) * (move_browse.product_qty or 0.0), #* (100.0 - (move_browse.via_hygro or 0.0)) / 100.0, # carico
                      (move_browse.via_hygro or 0.0) * self.adjust_um(move_browse.product_uom.factor, move_browse.product_id.uom_id.factor) * (move_browse.product_qty or 0.0) / 100.0, # scarico (hygro value)
                      move_browse.picking_id.date[8:10] if move_browse.picking_id else "",
                      move_browse.picking_id.date[5:7] if move_browse.picking_id else "",
                      move_browse.date[8:10],
                      move_browse.date[5:7],
                  )
               elif move_browse.location_id.id == stock_location['internal']  and move_browse.location_dest_id.id == stock_location['out']:        
                  # stock to customer - (***BC***)
                  return (
                      "-", 
                      "XAB", 
                      move_browse.picking_id.partner_id.combine_name if move_browse.picking_id.partner_id.combine_name else "NO CUST. CODE!", 
                      move_browse.picking_id.xab_number[3:] if move_browse.picking_id.xab_number else "NO XAB NUM.!", # TODO verificare con un documento se esiste
                      #move_browse.picking_id.origin.split(" ")[0] if move_browse.picking_id.origin else "NO ORIGIN!", #move_browse.picking_id.name,
                      "",                      # carico
                      self.adjust_um(move_browse.product_uom.factor, move_browse.product_id.uom_id.factor) * (move_browse.product_qty or 0.0), # scarico
                      move_browse.picking_id.date[8:10] if move_browse.picking_id.date else "",
                      move_browse.picking_id.date[5:7] if move_browse.picking_id.date else "",
                      move_browse.date[8:10],
                      move_browse.date[5:7],
                  )
               elif move_browse.location_id.id == stock_location['internal']  and move_browse.location_dest_id.id == stock_location['production']: 
                  # stock to production -   (***BP***)
                  return (
                      "-",
                      "VIA", 
                      move_browse.company_id.partner_id.combine_name_internal if move_browse.company_id else "", 
                      move_browse.move_history_ids[0].production_id.via_number[3:] if move_browse.move_history_ids and move_browse.move_history_ids[0].production_id.via_number else "NO VIA NUM.", # TODO test if there's more than one!
                      "",                      # carico
                      self.adjust_um(move_browse.product_uom.factor, move_browse.product_id.uom_id.factor) * (move_browse.product_qty or 0.0), # scarico
                      #move_browse.move_history_ids[0].production_id.date_start[8:10] if move_browse.move_history_ids else "",
                      #move_browse.move_history_ids[0].production_id.date_start[5:7] if move_browse.move_history_ids else "", # MM
                      move_browse.move_dest_id.production_id.date_start[8:10] if move_browse.move_dest_id and move_browse.move_dest_id.production_id else "",
                      move_browse.move_dest_id.production_id.date_start[5:7] if move_browse.move_dest_id and move_browse.move_dest_id.production_id else "",
                      move_browse.move_dest_id.production_id.date_start[8:10] if move_browse.move_dest_id and move_browse.move_dest_id.production_id else "",
                      move_browse.move_dest_id.production_id.date_start[5:7] if move_browse.move_dest_id and move_browse.move_dest_id.production_id else "",
                  )
           except:
               return ("ERR","ERR","ERR","ERR","ERR","ERR", "ERR", "ERR", "ERR","ERR") # error exit
        return ("","","","","","","","","","") # error exit
        
    def stock_move(self,wizard_data=None):
        ''' Root loop function:
            Filter only coal product (in state done)
            movement from in to stock,        (+)
                          stock to out,       (-)
                          stock to production (-)
        '''
        global stock_location
        global start
        
        start = 1
        self.load_location()

        if wizard_data is None: 
            wizard_data = {}
        
        data_filter_domain = []

        if wizard_data:            
            # get wizard data (if launched from there)
            from_date = wizard_data.get('from_date', False)
            to_date = wizard_data.get('to_date', False)
            start = wizard_data.get('start', 1)
            year = wizard_data.get('year', False)
            
            if from_date:
                data_filter_domain = data_filter_domain + [('date','>=', "%s 00:00:00"%(from_date))]
            if to_date:
                data_filter_domain = data_filter_domain + [('date','<=', "%s 23:59:59"%(to_date))]
            if year:
                data_filter_domain = data_filter_domain + [
                    ('date','>=', "%s-01-01 00:00:00" % (year)),
                    ('date','<=', "%s-12-31 23:59:59" % (year))]

        line_ids=self.pool.get('stock.move').search(self.cr, self.uid, data_filter_domain + [
            "&",('is_coal', '=', True),   # wizard data filter + this filter
            "&",('state', '=', 'done'),
            "|","&",  # BF
               ('location_id', '=', stock_location['in']),
               ('location_dest_id', '=',  stock_location['internal']),
            "|","&",  # BP
               ('location_id', '=', stock_location['internal']),
               ('location_dest_id', '=',  stock_location['production']),
            "&",      # BC
               ('location_id', '=', stock_location['internal']),
               ('location_dest_id', '=',  stock_location['out']),
               ],                                                                       
            order="create_date,picking_id") # Check the order before was date but doesn't work...                                                                   
            
        return self.pool.get('stock.move').browse(self.cr, self.uid, line_ids)                
