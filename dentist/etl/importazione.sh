#!/bin/sh
python partner.py /home/administrator/ETL/ambulatorio/CSV/F_ANAGRA.CSV
python product.py /home/administrator/ETL/ambulatorio/CSV/F_CATEGO.CSV /home/administrator/ETL/ambulatorio/CSV/F_LISTIN.CSV

python operation.py /home/administrator/ETL/ambulatorio/CSV/F_SCHEOP.CSV /home/administrator/ETL/ambulatorio/CSV/F_LISTIN.CSV

