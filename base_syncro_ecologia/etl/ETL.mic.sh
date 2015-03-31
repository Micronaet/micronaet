#!/bin/sh
# Client
python partner_ETL.py /home/administrator/ETL/ecologia/copenerp.ECO c
# Destination Client
python partner_ETL.py /home/administrator/ETL/ecologia/copenerp.ECO cd
# Supplier
python partner_ETL.py /home/administrator/ETL/ecologia/fopenerp.ECO s
# Destination Supplier

