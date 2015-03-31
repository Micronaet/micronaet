#/bin/bash
cd /home/administrator/lp/openerp/addons-micronaet/custom/ETL/fiam/disponibilita/
python ./prepara.py
wput --ascii ./esistoerp.GPB ftp://ftpgpb:tenerogpb@www.gpb.it/httpdocs/

