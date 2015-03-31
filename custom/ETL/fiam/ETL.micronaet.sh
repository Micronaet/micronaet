#!/bin/sh
# connect mexal data folder
#sudo mount -t cifs //192.168./pdf /home/administrator/pdf -o user=administrator,password=,gid=administrator,uid=administrator
# get 4 anagraphic CSV files and ANNOT.FIA files
#cp 

cd /home/administrator/Launchpad/openerp/addons-micronaet/custom/ETL/fiam/

# Parte per la FIAM: ###########################################################
# Listini
python articoli.py /home/administrator/ETL/fiam/artioerp.FIA
# Save a pickle list of clients with PL partic.
python pickle_custom_pl.py /home/administrator/ETL/fiam/partoerp.FIA

# Client
python partner_ETL.py /home/administrator/ETL/fiam/copenerp.FIA c
# Destination Client
python partner_ETL.py /home/administrator/ETL/fiam/copenerp.FIA cd
# Supplier
python partner_ETL.py /home/administrator/ETL/fiam/fopenerp.FIA s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

# Mexal Note, linked to client / customer
python note_ETL.py /home/administrator/ETL/fiam/ANNOT.FIA

# Update group of product
python batch_group_update.py

# Load PL partic. per client list
python particolarita.py /home/administrator/ETL/fiam/partoerp.FIA  

# Statistics:
cd statistiche
./stat.sh

# Parte per la GPB: ############################################################
# Listini
python articoli.py /home/administrator/ETL/fiam/artioerp.GPB
# Save a pickle list of clients with PL partic.
python pickle_custom_pl.py /home/administrator/ETL/fiam/partoerp.GPB

# Client
python partner_ETL.py /home/administrator/ETL/fiam/copenerp.GPB c
# Destination Client
python partner_ETL.py /home/administrator/ETL/fiam/copenerp.GPB cd
# Supplier
python partner_ETL.py /home/administrator/ETL/fiam/fopenerp.GPB s
# Destination Supplier
#python partner_ETL.py fopenerp.csv sd

# Mexal Note, linked to client / customer
python note_ETL.py /home/administrator/ETL/fiam/ANNOT.GPB

# Update group of product
python batch_group_update.GPB.py

# Load PL partic. per client list
python particolarita.py /home/administrator/ETL/fiam/partoerp.GPB

# Statistics:
#cd statistiche
#./stat.sh

# Metto l'etichetta base sui clienti italia che non l'hanno
python ./partner_set_label.py
