#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import lxml.html
from django.utils.encoding import smart_str, smart_unicode

print 

def prepara(articolo):
    #import pdb; pdb.set_trace()
    articolo_parse = lxml.html.fromstring(articolo)
    articolo_parse=smart_str(articolo_parse.text_content())
    articolo_parse=articolo_parse.replace("\n\n","**")
    return  articolo_parse + "\n" #+ "\n" + "*"*20 + "\n"
    
inizio='<img src="/images/lente.gif"'
fine="</tr>" 

path = '.'
listing = os.listdir(path)

out_file=open("medicinali.txt", "w")

# Cerco i files che iniziano per index 
articolo=""
for file_index in [infile for infile in listing if infile[:5:].lower()=="index"]:
    index_file=open(file_index, "r")
    trovato=False
    for linea in index_file:
        if inizio in linea:
           trovato=True
           articolo=""
        elif trovato: # non scrivo la prima riga (lente)
           articolo+=linea + "\n"
        if trovato and fine in linea:
           out_file.write(prepara(articolo))
           trovato=False                      

out_file.close()

'''
   Dettagli (lente)
Nome Farmaco: TRILAFON 
Confezione: "4 MG COMPRESSE RIVESTITE"20 COMPRESSE 
Ditta: MSD ITALIA Srl                
Principio attivo: PERFENAZINA 
Regime di fornitura: Ricetta ripetibile, validitÃ  6mesi, ripetibile 10 volte 
Classe di rimborsabilità: C 
Nota AIFA: 
Prezzo €:       11.95 
Prezzo in vigore dal: 05/02/2009 
'''
