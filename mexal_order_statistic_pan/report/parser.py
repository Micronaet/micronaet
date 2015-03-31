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

from report import report_sxw
from report.report_sxw import rml_parse

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'product_list':self.product_list,
        })

    def product_list(self, objects):
        products={}
        for order in self.pool.get('statistic.header').browse(self.cr, self.uid, [i.id for i in objects]):
            for item in order.line_ids:
                if item.code in products:
                   products[item.code][0]+=item.quantity or 0.0
                   products[item.code][1]+=item.quantity_ok or 0.0
                else:          
                   products[item.code]=[item.quantity or 0.0, item.quantity_ok or 0.0]                
       
        products_sorted=[]       
        for k in sorted(products.iterkeys()):
            products_sorted.append([k, products[k][0], products[k][1]])
        return products_sorted
