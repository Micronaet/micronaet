#!/bin/sh
# connect mexal data folder
#sudo mount -t cifs //192.168./pdf /home/administrator/pdf -o user=administrator,password=,gid=administrator,uid=administrator
# get 4 anagraphic CSV files
#cp 

# Client
python partner_ETL.py /home/administrator/ETL/micronaet/copenerp.csv c
# Destination Client
python partner_ETL.py /home/administrator/ETL/micronaet/copenerp.csv cd
# Supplier
python partner_ETL.py /home/administrator/ETL/micronaet/fopenerp.csv s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

