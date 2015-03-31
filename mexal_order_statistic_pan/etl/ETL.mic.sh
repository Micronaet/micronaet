#!/bin/bash
# Importazione elenco ordini per dashboard Fiam:
python import.py /home/administrator/ETL/ocdetoerp.PAN
#python import.py ocdetoerp.GPB

# Importazione scadenze:
python import_scad.py /home/administrator/ETL/scadoerp.PAL

python import_fatturato.py /home/administrator/ETL/fatmeseoerp.PAL
#python import_product.py /home/administrator/ETL/fatmesartoerp.PAL
