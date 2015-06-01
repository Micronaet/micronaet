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
    # -------------------------------------------------------------------------
    #                  Open csv file for output the pricelist
    # -------------------------------------------------------------------------
    # Counter:
    total_xls = {}
    
    csv_file = os.path.join(parameters['path']['csv'], parameters['file_csv'])
    err_file = os.path.join(parameters['path']['csv'], parameters['file_err'])

    print "[INFO] Start conversion:"
    print '[INFO] Creating CSV file: %s and ERR: %s' % (csv_file, err_file)
    
    f_out = open(csv_file, 'wt')
    f_err = open(err_file, 'wt')

    format = "%-40s" # partner element
    for field in parameters['field_trace'].values():
        format += field + parameters.get('separator', '')

    if parameters.get('windows', True):
       format += "\r\n"
    else:   
       format += "\n"

    col_to_import = parameters['field_trace'].keys()

    # -------------------------------------------------------------------------
    #                     Loop on all XLS and XLSX files
    # -------------------------------------------------------------------------
    for xls_file in os.listdir(parameters['path']['xls']):
        if xls_file not in total_xls:
            total_xls[xls_file] = [0, 0] # import, error
        extension = xls_file.split(".")[-1].lower()        
        if extension not in ("xlsx", "xls"):
            continue # jump file
         
        # Get file name and path:
        filename = os.path.expanduser(os.path.join(parameters['path']['xls'], xls_file))
        print "[INFO] Export: %s" % filename

        try:
            wb = xlrd.open_workbook(filename)
        except:
            print "[ERROR] Impossibile leggere il file", filename
            continue

        sh = wb.sheet_by_index(0)
        for r in range(0, sh.nrows):
            if r == 0:        
                partner = sh.cell_value(r, 0)  # first col > partner code
                continue
            elif r == 1:                       # jump header and start test first col
                continue #started = True

            try:
                if sh.cell_value(r, 0):
                    total_xls[xls_file][0] += 1
                    format_row = [partner, ] + [float(sh.cell_value(r, c) or '0.0') if c in parameters['float_cols'] else sh.cell_value(r, c) for c in col_to_import]
                    f_out.write(format % tuple(format_row))
            except:
                total_xls[xls_file][1] += 1
                f_err.write("%-40s-Riga:%-10s[%-150s] #%s\r\n" % (partner, r, format_row, sys.exc_info()))
                #print "[ERR] %s) Error exporting line: %s" % (r, sys.exc_info())
    f_out.close()
    print "[INFO] %s" % (total_xls)
    print "[INFO] %s " % (format.replace("%", "[").replace("s", "]").replace("f", "]"))    
    print "[INFO] End conversion"

# -----------------------------------------------------------------------------
#                                  Main code
# -----------------------------------------------------------------------------
if __name__=='__main__':
    main()
