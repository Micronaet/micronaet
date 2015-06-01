#!/usr/bin/env python
# -*- coding: windows-1251 -*-
from pyExcelerator import *
import os
     
# Functions:
def print_line(sigla_azienda, anno, mese, file_out, row):
    file_out.write("%6s%6s%6s%6s%26s%25s%13.2f%13.2f%13.2f%13.2f%13.2f\n"%(str(int(float(sigla_azienda))).ljust(6), 
                                                                           str(int(float(anno))).ljust(6), 
                                                                           str(int(float(mese))).ljust(6), 
                                                                           row[0].replace("0","").ljust(6), 
                                                                           row[1].ljust(26), 
                                                                           row[2].ljust(25), 
                                                                           float(row[3]), 
                                                                           float(row[4]), 
                                                                           float(row[5]), 
                                                                           float(row[6]), 
                                                                           float(row[7]),
                                                                           ))
    return
     
path = '.'
listing = os.listdir(path)
file_out = open("prestiti.txt", "w")
row=[]

print "Files read:"               
for file_xls in [infile for infile in listing if infile[-3:].lower()=="xls"]:
    sigla_azienda, descrizione, anno = "", "", ""
    old_row=0
    for sheet_name, values in parse_xls(file_xls, 'cp1251'): 
        for row_idx, col_idx in sorted(values.keys()):  
            #if col_idx==0:
            #    import pdb; pdb.set_trace()          
            v = values[row_idx, col_idx]
            if isinstance(v, unicode):
                v = v.encode('cp866', 'backslashreplace')
            else:
                v = str(v)

            # Read parameters for setup default data for this XLS file:                
            if row_idx==3 and col_idx==1: sigla_azienda = v  # get sigla azienda
            if row_idx==3 and col_idx==2: descrizione = v    # get descrizione azienda
            if row_idx==4 and col_idx==1: anno = v           # get anno
            if row_idx==5 and col_idx==1: mese = v           # get mese

            if row_idx >= 13: # Data are over 13 line
                if row_idx != old_row:
                    if len(row) == 8 and row[3] != '0.0':  # line is long 8 and there's one value in first import column?
                        print_line(sigla_azienda, anno, mese, file_out, row)
                    old_row = row_idx
                    row = []
                row.append(v)
          
    print file_xls, "-", sigla_azienda.split(".")[0], "-", descrizione
file_out.close()    
