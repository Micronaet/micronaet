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
from configuration import parameters

def main():    
    if len(sys.argv) != 2:
        print "Use:\n\n\tpython ./convert.py file.xls"
        sys.exit()
    xls_file = sys.argv[1]
    
    if parameters.get('windows', True):
       end_of_line = "\r\n"
    else:   
       end_of_line = "\n"
       
    format = ""
    for f in parameters['field_trace']:
        format += f + parameters.get('column_separator', '')
    max_col = len(parameters['field_trace'])

    # Get file name and path:
    filename = os.path.join(parameters['path']['work'], xls_file)

    wb = xlrd.open_workbook(filename)
    sh = wb.sheet_by_index(0)

    csv_file = os.path.join(parameters['path']['worked'], parameters['file_csv'])
    print 'Creating CSV file: %s' % csv_file
    f_out = open(csv_file, 'wt')

    csv_field_len = 0
    for r in range(0, sh.nrows):    
        if r < parameters['start_row']:
            continue # jump N lines            
        format_row = [sh.cell_value(r, c) for c in range(0, max_col)]
        csv_row = format % tuple(format_row)
        if not csv_field_len: # save first row len (for test other)
            csv_field_len = len(csv_row)
            
        f_out.write(csv_row + end_of_line)
        print "%04d: %s%s" %(
           r,
           "# ERR lun. %s [OK: %s]" % (len(csv_row), csv_field_len) if len(csv_row) != csv_field_len else "",
           csv_row,
        )
    f_out.close()

    print "\nTRACE:", "*" * 60
    print "\nLunghezza riga:", csv_field_len, " + extra char: ", len(end_of_line), "Total:", csv_field_len + len(end_of_line)
    print "\nTracciato record:\n\n", format.replace ("%", "  ").replace("f", "\t(float)\n").replace("s", "\t(string)\n").replace("d", "\t(decimal)\n")
    print "\nFile letto:", filename
    print "File create:", csv_file
    print "\n"
 
if __name__=='__main__':
    main()
