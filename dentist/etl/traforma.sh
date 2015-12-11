#!/bin/sh
rm ./dbf2txt.sh
rm ./db_list.txt

mkdir /home/administrator/ETL/ambulatorio/DB
mkdir /home/administrator/ETL/ambulatorio/CSV
mkdir /home/administrator/ETL/ambulatorio/TRC

ls /home/administrator/ETL/ambulatorio/MACH2/*.DBF > ./db_list.txt
python ./convert.py
chmod +x ./dbf2txt.sh
./dbf2txt.sh
python txt2csv.py > ./esito.txt
nano ./esito.txt

rm ./dbf2txt.sh
rm ./db_list.txt

