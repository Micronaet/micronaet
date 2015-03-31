**************************************************************
1. Creare nuovo DB
2. Installare i moduli: CRM, Auto_backup
3. Installare le personalizzazioni: base_panchemicals
4. Installare lingua italiana
5. Importante: importare l'esenzione a mano per extra cee

**************************************************************
ETL una tantum 
1. Importazione anagrafiche semplici: 
     python ./anagrafiche_ETL.py 
2. Importazione utenti (abbina anche tutti i gruppi dell'admin: 
     python crea_utenti.py utenti.csv 

**************************************************************
ETL giornaliero (CRONE script ETL.sh)
Passaggi dello script:
1. Importa i listini base fiam (4 modelli)
     python articoli.py artioerp.csv

2. Importa i clienti, le destinazioni, (abbinando il listino
     python partner_ETL.py copenerp.csv c
     python partner_ETL.py copenerp.csv cd

3. (Importa i fornitori, le destinazioni fornitore)
     python partner_ETL.py fopenerp.csv s
     python partner_ETL.py fopenerp.csv sd  (per ora sospeso, controllare extra dati)

