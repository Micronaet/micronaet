#!/bin/sh
# connect mexal data folder
#sudo mount -t cifs //192.168./pdf /home/administrator/pdf -o user=administrator,password=,gid=administrator,uid=administrator
# get 4 anagraphic CSV files and ANNOT.FIA files
#cp 

# Invoice line
python invoice_line_ETL.py /home/administrator/ETL/panchemicals/venduto.PAL

# Listini
python articoli.py /home/administrator/ETL/ERPanagrart.PAN /home/administrator/ETL/panchemicals/ERPricettepan.PAN
# Client
python partner_ETL.py /home/administrator/ETL/panchemicals/copenerp.PAN c
# Destination Client
python partner_ETL.py /home/administrator/ETL/panchemicals/copenerp.PAN cd
# Supplier
python partner_ETL.py /home/administrator/ETL/panchemicals/fopenerp.PAN s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

#python articoli.py ERPricettepan.csv
# Creati dopo i clienti perche' fanno delle valutazioni con i listini
# (devo avere già abbinato il listino modello e quello di base)
python articoli.py /home/administrator/ETL/ERPanagrart.csv /home/administrator/ETL/panchemicals/ERPricettepan.csv

# Mexal Note, linked to client / customer
#python note_ETL.py ANNOT.FIA

# Update group of product
#python batch_group_update.py

# Load PL partic. per client list
#partner_reset_pricelist.py (fare la prima volta)
#partner_setup_pricelist.py (fare la prima volta)  <<< dopo aver creato il listino per L'italia (e settato l'ID)
python pickle_custom_pl.py partoerp.PAN
python particolarita.py partoerp.PAN
