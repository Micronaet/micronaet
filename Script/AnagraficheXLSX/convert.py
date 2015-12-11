#!/usr/bin/python
# -*- encoding: utf-8 -*-
''' This script require installation of library xlrd:

pip install xlrp --upgrade
sudo easy_install openpyxl

Call script passing file name (full path)
'''

import sys
import os
from openpyxl.reader.excel import load_workbook


# Parameters:
#CSV_SEPARATOR = '\t'
#CSV_CR = '\r\n'


trace = ['codice',      # 1.  Codice
         'descrizione', # 2.  Descrizione
         'codice2',     # 3.  Codice secondario
         'scorta',      # 4.  Scorta
         'riordino',    # 5.  Livello di riordino
         'acquisto',    # 6.  Prezzo acquisto
         'interno',     # 7.  Listino interno
         'fornitore',   # 8.  Listino fornitore
         'base',        # 9.  Base 100
         'scala',       # 10. Scala sconti (esplosa con i succ. valori:)
         'sconto1p',    # 11. Sconto percentule (1)
         'sconto1',     # 12. Sconto valore (1)
         'sconto2p',    # 13. Sconto percentule (2)
         'sconto2',     # 14. Sconto valore (2)
         'sconto3p',    # 15. Sconto percentule (3)
         'sconto3',     # 16. Sconto valore (3)
         #'sconto4p',    # 17. Sconto percentule (4)
         #'sconto4',     # 18. Sconto valore (4)
        ] 

        
#        "   1     2     3    4    5    6    7    8    9   10   11   12   13   14   15   16   17   18  "
format = "%-20s;%-50s;%-15s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;%20s;\r\n"#%20s;%20s;\r\n"


def main():    
    # Get file name and path:
    filename = sys.argv[1]
    path = os.path.dirname(filename)
    wb = load_workbook(filename = filename)
    csv_file = os.path.join(path, 'convert.csv')# % sheet.title
    
    data_is_started = False
    for sheet in wb.worksheets:        
        print 'Creating CSV file: %s' % csv_file
        fd = open(csv_file, 'wt')
        
        # Read all rows:
        r = 0
        for row in sheet.rows:
            r += 1
            print "Row: %s" % (r)
            values=[]
            
            # Read all cols:
            c = 0        
            for cell in row:
                c += 1
                value = cell.value
                if value is None:
                    value=''
                if not isinstance(value, unicode):
                    value = unicode(value)
                value = value.encode('utf8')
                values.append(value)

                if c >= len(trace): # last line
                    break
                
            # Write row in CSV file:    
            #csv_row = CSV_SEPARATOR.join(values)
            #import pdb; pdb.set_trace()
            if len(values) != len(trace):
                print "Line jumped, not enought elemtents!"
                continue
                
            csv_row = format % tuple(values)
            if data_is_started:
                fd.write(csv_row)
                #fd.write(CSV_CR)
            elif not any(values): # 1st empty line
                data_is_started = True # write next line    
        fd.close()

if __name__=='__main__':
    main()
