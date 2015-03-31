#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import csv, pdb
from datetime import datetime

def Prepare(valore):  
    return valore.strip()

FileInput_ids = ['copenerp.GPB', 'copenerp.FIA']
FileOutput = 'sconti.GPB'

fout = open(FileOutput, 'w')

# Carico in un dict tutte le date di consegna:
lista=[]
try:
    for FileInput in FileInput_ids:
        for line in csv.reader(open(FileInput, 'rb'), delimiter=";"):    
            if len(line):            
               codice= Prepare(line[0])
               descrizione=Prepare(line[1]).title() + "("+  FileInput[-3:] + ")"
               paese=Prepare(line[5]).title()
               CEI=Prepare(line[12]).upper() 
               sconto=Prepare(line[19])
               if CEI=="I": # solo i clienti Ialia
                  lista.append((descrizione, codice, paese, sconto))

    for (descrizione, codice, paese, sconto) in sorted(lista):
        fout.write("%s;%s (%s);%s\n"%(codice, descrizione, paese, sconto))
    fout.close()
except:
    print '>>> [ERROR] Errore gestendo gli sconti cliente!'
    raise 
