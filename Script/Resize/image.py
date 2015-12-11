#!/usr/bin/python
# -*- coding: utf-8 -*-
################################################################################
# Programma per ridimensionare immagini PNG da una cartella all'altra          #
# Utilizzando mogrify (che deve essere preventivamente installato sul sistema  #
# La dimensione dell'immagine e' proporzionata con una scala cm./px che va     #
# data come input                                                              #
#                                                                              #
# Copyright (2013) Micronaet S.r.l.                                            #
# Developer: TheBrush                                                          #
#                                                                              #  
# Installazione Mogrify: sudo apt-get install imagemagick                      #
################################################################################

import pdb, os
from PIL import Image

#conversion_rate = 3.5 #px/mm
conversion_rate = 3.3 #px/mm
formato = "png"

cartella_in = "/home/thebrush/ETL/Resize/55px"
cartella_out = "/home/thebrush/ETL/web55px"
cartella_csv = "/home/thebrush/ETL/Resize"
prodotti = "immagini.csv"

lista_prodotti={}

prima_riga=True
product_max = 0.0
product_min = 0.0
produc_code_max = ""
produc_code_min = ""

for riga in open(os.path.join(cartella_csv, prodotti), "r"):
    if prima_riga: #salto la prima riga
        prima_riga=False
        continue 
    r = riga.strip().split(";") #creo una lista dividendo ogni elemento tutte le volte che trovo un ;
    product_height = float(r[8].replace(",", ".") or '0')  # save height    
    product_width  = float(r[9].replace(",", ".") or '0')  # save width
    if product_height:
        if product_height > product_max:
            product_max = product_height
            product_code_max = r[0]
        if product_height < product_min or not product_min:
            product_min = product_height
            product_code_min = r[0]

        lista_prodotti [r[0].lower()] = product_height
    
print "*"*50    
print "Massima altezza mm.:", product_max, product_code_max 
print "Minima altezza mm.:", product_min,  product_code_min
print "*"*50    

#import pdb; pdb.set_trace()
image_max = 0.0
image_min = 0.0
produc_code_max = ""
produc_code_min = ""
for nome_file in os.listdir(cartella_in): # faccio passare tutta la cartella_in, facendola diventare una lista e gni singolo elemento diventa il nome_file
    try:
        if nome_file.split(".")[-1].lower() == formato:
            code = nome_file.split(".")[0]
            if code in lista_prodotti: 
                file_in = os.path.join(cartella_in, nome_file)
                img = Image.open(file_in)
                # get the image's width and height in pixels
                width, height = img.size
                
                if height > image_max:
                    image_max = height
                    product_code_max = code
                if height < image_min or not image_min:
                    image_min = height
                    product_code_min = code

                new_height = lista_prodotti[code] * conversion_rate  # in proporzione all'altezza
                new_width =  new_height / height  * width             # in proporzione
                if new_width > 55.0:
                   print "Jump: ", code
                else:   
                    dimensione = str(new_height).split(".")[0]
                    #import pdb; pdb.set_trace()
                    comando = "convert '%s' -geometry x%s '%s'" %(os.path.join(cartella_in, nome_file), dimensione, os.path.join(cartella_out, nome_file))
                    print comando
                    os.system(comando) # lo lancio
                    print "%s;H.: %s;[%s : %s];[%s : %s];"%(code, lista_prodotti[code], width, height, new_width, new_height)
            else:
                 print "WARN: Saltata immagine senza dimensioni: %s"%(code,)       
    except:
        print "Errore: Convertendo il file %s" %(nome_file,)

print "*"*50    
print "Massima altezza px.:", image_max, product_code_max  
print "Minima altezza px.:", image_min, product_code_min
print "*"*50    

