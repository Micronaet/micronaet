**************************************************************
1. Creare nuovo DB
2. Installare i moduli: CRM, Project, Sale, Auto_backup
3. Installare le personalizzazioni: base_fiam
4. Installare lingua italiana
5. Importante: importare l'esenzione a mano per extra cee

**************************************************************
ETL una tantum 
1. Importazione anagrafiche semplici: 
     python ./anagrafiche_ETL.py 
2. Importazione utenti (abbina anche tutti i gruppi dell'admin: 
     python crea_utenti.py utenti.csv 
3. Importazione DB access CRM (crea tutti i partner potenziali, crea le leads ricavate dal DB fiere)
     python ETL_contact.py expo.csv 

**************************************************************
ETL giornaliero (CRONE script ETL.sh)
Passaggi dello script:
1. Importa i listini base fiam (4 modelli)
     python articoli.py artioerp.FIA
     python pickle_custom_pl.py partoerp.FIA

2. Importa i clienti, le destinazioni, (abbinando il listino
     python partner_ETL.py copenerp.FIA c
     python partner_ETL.py copenerp.FIA cd

3. (Importa i fornitori, le destinazioni fornitore)
     python partner_ETL.py fopenerp.FIA s
     python partner_ETL.py fopenerp.FIA sd  (per ora sospeso, controllare extra dati)

4. Importa le annotazioni
     python note_ETL.py ANNOT.FIA

5. Ogni tanto aggiornamento gruppi prodotti
   python batch_group_update.py  (messo anche nel batch schedulato)

6. Importo le particolarità nel listino già esistente!
     python particolarita.py partoerp.FIA

 
***************************************************************
ETL mensile
1. Eliminare eventuali listini creati con particolarità che ora non esistono più (il cliente usa il base solo)
   (effettuare dopo la creazione del file pickle)
   python pulisci_listini.py 
