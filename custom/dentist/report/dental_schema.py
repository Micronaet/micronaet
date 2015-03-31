##############################################################################
#
# Copyright (c) 2008-2012 SIA "Micronaet s.r.l." (http://www.micronaet.it) 
#               All Rights Reserved.
#               General contacts <riolini@micronaet.it>
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

def get_array_list(self, item_id, side, is_order):        
    ''' Calculate array for dental position: u(p) or d(own)
        at least 1 line is returned (for graphic rapresentation)
        item_id: id of partner (is_order=False) or id of order (is_order=True)
        side: U or D, stand for Up or Down 
        is_order: True of False (for select res.partner obj or res.order)
        
        return: array list of represented operations
    '''
    
    # Function for this procedure:
    def get_id(tooth):
        ''' return position of tooth in line ex.:
            11 - 18 (from 1 to 8)   also for 51 - 55
            21 - 28 (from 9 to 17)  also for 61 - 65
            T (is 0)
            31 - 38 (from 1 to 8)   also for 71 - 75
            41 - 48 (from 9 to 17)  also for 81 - 85
        '''
        if tooth in ("*", "up", "down"): # All teeth (upper or lower side)
           return 0
        elif tooth[:1] in ("1", "4", "5", "8"):
           return int(tooth[1:2])
        elif tooth[:1] in ("2", "3", "6", "7"):
           return 8 + int(tooth[1:2])

    # Start procedure:
    total_list=[] # list that is represented on dental schema report
   
    #      T   8  7  6  5  4  3  2  1 | 1  2  3  4  5  6  7  8  
    level=[0,  0, 0, 0, 0, 0, 0, 0,  0, 0, 0, 0, 0, 0, 0, 0, 0,] # max level for tooth
    max_level=0 # level number max (for indexing lines)
    side_description={'up': " (sup.)", 'down': " (inf.)"}
    
    if is_order: 
       # TODO
       tooth_ids=self.pool.get('sale.order.line').search(self.cr, self.uid, [('order_id', '=', item_id),('discarded','=',False)])
       tooth_list_ids = self.pool.get('sale.order.line').browse(self.cr, self.uid, tooth_ids)
        
    else: # is partner
       tooth_ids = self.pool.get('dentist.operation').search(self.cr, self.uid, [('partner_id', '=', item_id),])
       tooth_list_ids = self.pool.get('dentist.operation').browse(self.cr, self.uid, tooth_ids)

    for tooth in tooth_list_ids:
        if tooth.tooth: # jump if no teeth!
            if (side.upper()=="U" and (tooth.tooth[:1] in ("u", "1", "2", "5", "6", "*",))) or (side.upper()=="D" and (tooth.tooth[:1] in ("d", "3", "4", "7", "8",))): 
               pos = get_id(tooth.tooth)
               level[pos] += 1
               current_level = level[pos]
               if level[pos] > max_level:
                  empty=['', '','','','','','','','', '','','','','','','','',] # empty line for append 
                  total_list.append(empty)
                  max_level=current_level

               if is_order:
                  tooth_date = ""
               else:   
                  tooth_date = tooth.date and "%s-%s"%(tooth.date[5:7],tooth.date[2:4]) # tooth.date[8:10],
                  
               one_side = side_description[tooth.tooth] if tooth.tooth in ("up", "down") else ""   
               if tooth.tooth[:1] in ("5", "6", "7", "8"): # milk teeth
                  code_tooth = "%s%s*"%(tooth.product_id.code.lower(), one_side) if is_order else "%s*%s\n%s"%(tooth.product_id.code.lower(), one_side, tooth_date)
               else: # normal teeth
                  code_tooth = "%s%s"%(tooth.product_id.code.upper(), one_side) if is_order else "%s%s\n%s"%(tooth.product_id.code.upper(), one_side, tooth_date)
               total_list[current_level-1][pos]=code_tooth 
        else: # TODO raise some error?
           pass 
       
    if max_level==0:          
       total_list.append(['', '','','','','','','','', '','','','','','','','',]) # return a blank line
      
    total_list.reverse()
    return total_list
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
