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
    # Import mask:
    # --------------------------------    
    'separator': '',      # Separator
        
    'field_trace': {
        0: r"%-20s",           # Code
        1: r"%-60s",           # Description
        2: r"%-20s",           # Code 2
        3: r"%20.3f",          # Available
        5: r"%20.3f",          # Price
        6: r"%20.3f",          # Pricelist
    },
    'float_cols': [3, 5, 6],

    # --------------------------------
    # Path:
    # --------------------------------
    'path': {
       'xls': r'/home/thebrush/ETL/ISER/listini',
       'csv': r'/home/thebrush/ETL/ISER/listini/csv',
       'history': r'/home/thebrush/ETL/ISER/listini/history',
       #'xls': r'c:\mexalbp\dati\etl\XLS',
       #'csv': r'c:\mexalbp\dati\etl\CSV',
       #'history': r'c:\mexalbp\dati\etl\history',       
    },

    # --------------------------------
    # Files out info: 
    # --------------------------------
    'file_csv': 'export.csv',
    'file_err': 'error.csv',
    'windows': False,           # For end of line \r\n else \n only 
}
