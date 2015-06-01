#!/usr/bin/python
# -*- encoding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
###############################################################################
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################
# This script require installation of library xlrd:
#
# pip install xlrp --upgrade
# sudo easy_install openpyxl
#
# Call script passing file name (full path)
###############################################################################
import sys
import os
import xlrd

def main():    
    if len(sys.argv) != 2:
        print "Use:\n\n\tpython ./subtotals.py file.xls"
        sys.exit()
    xls_file = sys.argv[1]
    
    if parameters.get('windows', True):
       end_of_line = "\r\n"
    else: 
       end_of_line = "\n"
       
    wb = xlrd.open_workbook(xls_file)
    sh = wb.sheet_by_index(0)

    old_key = False
    total = 0.0
    for r in range(0, sh.nrows):
        if not old_key:
            old_key = (sh.cell_value(r, 1),  sh.cell_value(r, 2), sh.cell_value(r, 3))            
            
        if old_key != (sh.cell_value(r, 1),  sh.cell_value(r, 2), sh.cell_value(r, 3)):
            print "KEY: %s TOTAL: %s" % (old_key, total)
            total = 0.0
            old_key = (sh.cell_value(r, 1),  sh.cell_value(r, 2), sh.cell_value(r, 3))       

        total += sh.cell_value(r, 3)) if sh.cell_value(r, 6) == "D" else -sh.cell_value(r, 3))
 
if __name__=='__main__':
    main()
