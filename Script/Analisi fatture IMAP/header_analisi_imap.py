#!/usr/bin/python
# -*- encoding: utf-8 -*-
# Before export data with sprix 549
# Elaboration
# Auto open CSV files
import os
import sys
import imaplib
import email
import subprocess

# Access IMAP folder:
mail = imaplib.IMAP4_SSL('imap.gmail.com')
mail.login('zipperr.fatture@gmail.com', 'password')
mail.list()

mail.select("inbox") # Connect to inbox.

# Read file for get list of invoice and create a CSV output:
f_in = open("ftmail.ZPR","r")
f_out = open("ftmail.csv","w")
formato_csv = "%s,%06d,%s,%s,%s,%s\n" # Num. fattura, Esito, Descrizione, Note

# intestazione:
f_out.write("%s,%s,%s,%s,%s,%s\n" % (
    "Documento", "Numero", "Stato", "Cliente", "Descrizione", "Note", ))

for line in f_in:
    invoice = int(line[:6].strip())
    customer = line[16:46].strip().replace(",", ".")
    to_mexal = line[47:107].strip()
    documento = line[108:110].strip().upper()
    
    # Case: Mexal address not exist:
    if not to_mexal:
        f_out.write(formato_csv % (
            documento, invoice, "Warning", customer,
            "Invio manuale", "Manca indirizzo email nel gestionale"))
        continue
        
    if documento == "FT":
        subject = "Fattura n. %06d" % invoice
    else:
        subject = "Nota accredito n. %06d" % invoice
        
    try:
        error = "Errore cercando di leggere l'oggetto del messaggio"
        result, data = mail.uid(
            'search', None, '(HEADER Subject "%s")' % subject)
        
        # Case: Subject not found in mail
        if result != "OK":
            f_out.write(formato_csv % (
                documento, invoice, "Error", customer,
                "Non si riesce a leggere mail con oggetto: %s" % subject, ""))
            continue

        error = "Errore cercando di leggere il messaggio"
        try:
            latest_email_uid = data[0].split()[-1]
            result, data = mail.uid('FETCH', latest_email_uid, 
                '(BODY.PEEK[HEADER.FIELDS (To)] RFC822.SIZE)')
        except:
            f_out.write(formato_csv % (
                documento, invoice, "Error", customer, 
                "Mexal: %s" % to_mexal, error))
            continue    
            
        # Case: mail not reached from server 
        if result != "OK":
            f_out.write(formato_csv % (
                documento, invoice, "Error", customer,
                "Messaggio inesistente, oggetto: %s" % subject, ""))    
            continue

        error = "Errore cercando di leggere l'oggetto del messaggio"
        to_send = data[0][1].split()[1][1:-1]

        error = "Errore scrivendo il record su Excel"
        # Case: Info
        if to_mexal == to_send:
            record = (
                documento, invoice, "", customer,
                "Invio: %s" % to_mexal, "")
                
        else: # Case: Warning (address non correct)
            record = (
                documento, invoice, "Warning", customer,
                "Invio mail non corretta [Mexal: %s] [Email: %s]" % (
                    to_mexal, to_send), 
                "Non corrispondono gli indirizzi!")            
        f_out.write(formato_csv % record)

    except:
        # Case: of generic error:
        f_out.write(formato_csv % (
            documento, invoice, "Error", customer, "", error))
        continue    

f_in.close()
f_out.close()    

#os.system('./ftmail.csv')
