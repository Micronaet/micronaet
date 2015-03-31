#!/bin/sh
# Client
python partner_ETL.py ~/ETL/minerals/copenerp.MMI c
# Destination Client
python partner_ETL.py ~/ETL/minerals/copenerp.MMI cd
# Supplier
python partner_ETL.py ~/ETL/minerals/fopenerp.MMI s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

# Articoli
python articoli.py ~/ETL/minerals/artioerp.MMI

