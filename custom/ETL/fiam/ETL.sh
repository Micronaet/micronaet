#!/bin/sh
# connect mexal data folder
#sudo mount -t cifs //192.168./pdf /home/administrator/pdf -o user=administrator,password=,gid=administrator,uid=administrator
# get 4 anagraphic CSV files and ANNOT.FIA files
#cp 

cd /home/administrator/lp/openerp/addons-micronaet/custom/ETL/fiam/

# Parte per la FIAM: ###########################################################
# Listini
python articoli.py artioerp.FIA
# Save a pickle list of clients with PL partic.
python pickle_custom_pl.py partoerp.FIA

# Client
python partner_ETL.py /home/administrator/etl/fiam/copenerp.FIA c
# Destination Client
python partner_ETL.py /home/administrator/etl/fiam/copenerp.FIA cd
# Supplier
python partner_ETL.py /home/administrator/etl/fiam/fopenerp.FIA s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

# Mexal Note, linked to client / customer
python note_ETL.py ANNOT.FIA

# Update group of product
python batch_group_update.py

# Load PL partic. per client list
python particolarita.py partoerp.FIA  

# Statistics:
cd statistiche
./stat.sh

# Parte per la GPB: ############################################################
# Listini
python articoli.py artioerp.GPB
# Save a pickle list of clients with PL partic.
python pickle_custom_pl.py partoerp.GPB

# Client
python partner_ETL.py copenerp.GPB c
# Destination Client
python partner_ETL.py copenerp.GPB cd
# Supplier
python partner_ETL.py fopenerp.GPB s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

# Mexal Note, linked to client / customer
python note_ETL.py ANNOT.GPB

# Update group of product
python batch_group_update.GPB.py

# Load PL partic. per client list
python particolarita.py partoerp.GPB

# Statistics:
#cd statistiche
#./stat.sh

#Spostato sotto home etl
#cd /home/administrator/lp/micronaet/report_store_value/etl
#python ./esistenze.py esistoerprogr

# Imposto etichette Italia se non ci sono
python ./partner_set_label.py

