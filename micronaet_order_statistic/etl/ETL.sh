#!/bin/bash
# Importazione elenco ordini per dashboard Fiam:
python import.py ocdetoerp.FIA
#python import.py ocdetoerp.GPB

# Importazione scadenze:
python import_scad.py scadoerp.FIA

# Importazione Trend anno attuale e anno precedente:
python import_trend.py trendoerp1.FIA S
python import_trend.py  trendoerp2.FIA N

