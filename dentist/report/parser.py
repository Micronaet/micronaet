##############################################################################
#
# Copyright (c) 2008-2010 SIA "KN dati". (http://kndati.lv) All Rights Reserved.
#                    General contacts <info@kndati.lv>
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
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
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

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'group_list': self.get_line_list,
            'tooth_list': self.get_list,
            'total_discarded': self.get_total_discarded, # TODO for preview
        })

    def get_total_discarded(self, order_id):
        ''' Jump discarder lines
        '''
        line_ids=self.pool.get('sale.order.line').search(self.cr, self.uid, [('order_id', '=', order_id)])
        
        total=0.0       
        for line in self.pool.get('sale.order.line').browse(self.cr, self.uid, line_ids):
            if not line.discarded:
               total+=line.price_unit * (1-(line.discount or 0.0)/100.0)
        return total
        
    def get_line_list(self, order_id):
        ''' Calculate the list of lines group by product_code
        '''
        # TODO da finire il debug
        res=[]        
        line_ids=self.pool.get('sale.order.line').search(self.cr, self.uid, [('order_id', '=', order_id),('discarded','=',False)], order="product_id")
                
        total_q=0.0
        total_price=0.0
        current_id=0
        old_name=""
        old_code=""
        i=-1
        #import pdb; pdb.set_trace()
        for line in self.pool.get('sale.order.line').browse(self.cr, self.uid, line_ids):
           if i==-1:
              i=0
           if current_id==0: # prima volta
              current_id=line.product_id.id
              old_name=line.name
              old_code=line.product_id.code
           if line.product_id.id==current_id:
              total_q += line.product_uom_qty or 0.0
              total_price += (line.price_subtotal or 0.0 * line.product_uom_qty or 0.0) #price_unit
           else: 
              i+=1
              nuovo=[total_q, old_code, old_name,  total_price]
              res.append(nuovo)
              total_q=line.product_uom_qty or 0.0
              total_price=(line.price_subtotal or 0.0 * line.product_uom_qty or 0.0)
              current_id=line.product_id.id
              old_name=line.name
              old_code=line.product_id.code
        if i>=0:
           nuovo=[total_q, line.product_id.code, line.name,  total_price]
           res.append(nuovo)
        return res                    
        
    def get_list(self, order_id, side):        
        ''' Calculate array for dental posizion:  u(p) or d(own)
            at least 1 line is returned (for graphic rapresentation)
        '''
        from dental_schema import get_array_list
        return get_array_list(self, order_id, side, True) 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:        
