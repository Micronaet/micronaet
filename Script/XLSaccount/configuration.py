#!/usr/bin/python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>)
#
##############################################################################
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

# ----------------------------------------------------------------------------
#         Configuration file for setup importations parameters
# ----------------------------------------------------------------------------

parameters = {
    # --------------------------------
    # Mask: 
    # --------------------------------
    # r"%10s"   string 10 char left
    # r"%-10s"  string 10 char right
    # r"%10.4f" float FFFFF.FFFF  (10 char 4 decimal)
    # r"%02d"   decimal DD format (2 char start with 0)
    # --------------------------------
    
    #'column_separator': "|",   # "" for empty
        
    'field_trace': [
        r"%4.0f",    # 1.  Azienda (numerico)
        r"%4.0f",    # 2.  Anno
        r"%2.0f",    # 3.  Mese
        r"%-50s",    # 4.  Sezione
        r"%4s",      # 5.  Centro di Costo
        r"%-50s",    # 6.  Conto contabile
        #r"%9s",     # 7.  Conto PASSEPARTOUT AZIENDA NNN.NNNNN
        r"%-60s",    # 8.  Descrizione
        r"%-4s",     # 9.  Senso
        r"%15.2f",   # 10. Importo
    ],
    
    'windows': True,   # For end of line \r\n else \n only 
    
    # --------------------------------
    # Path: 
    # --------------------------------
    # work: XLS folder file
    # worked: XLS worked
    # --------------------------------
    'path': {
       #'work': r'/home/thebrush/ETL/impronta',
       #'worked': r'/home/thebrush/ETL/impronta',
       'work': r'c:\mexalbp\dati\etl\XLS',
       'worked': r'c:\mexalbp\dati\etl\CSV',
    },

    # --------------------------------
    # Files: 
    # --------------------------------
    # file_csv: CSV file name
    'file_csv': 'export.csv',
    'start_row': 1,
}
