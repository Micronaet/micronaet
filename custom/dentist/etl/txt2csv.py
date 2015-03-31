import os, pdb
path_root="/home/administrator/ETL/ambulatorio"

for root, dirs, files in os.walk(path_root + "/DB/"): # TODO all subfolder?
    for f in files: # per tutti i file della cartella TXT
      if f in (r'PARAM.TXT', r'SYSTEM2.TXT'): 
        print "\n[INFO] Saltato: ", f
      else:
           
        file_name=f.lower().split(".")
        if len(file_name)==2 and (file_name[1] == ("txt")): 
            tot_righe=0
            tot_record=0
            i_campo=0       
            riga_out=""     
            int_out=""
            elenco_campi={}
            f_txt = open('%s/DB/%s'%(path_root,f), 'r')
            f_csv = open('%s/CSV/%s'%(path_root,f[:-3] + "CSV"), 'w')
            f_trc = open('%s/TRC/%s'%(path_root,f[:-4] ), 'w')
            first=True

            print "\n[INFO] Inizio conversione file: %s", f
            for line in f_txt: # per tutte le righe del file:
                tot_righe+=1
                line=line.replace(";",",").replace("\n","")
                if line:
                   #pdb.set_trace()
                   if line[11:12] != ":": 
                      print "    [ERR] Nome campo non lungo 11!"

                   campo=line[:11].strip()
                   valore=line[12:].strip()

                   if first: # leggo il primo blocco fino all'int. per scrivere trac.                       
                      f_trc.write(campo + "\n") 
                      if int_out:
                        int_out += ";" + campo 
                      else: 
                        int_out = campo
                        
                      elenco_campi[i_campo] = campo
                   else: # controllo che sia il valore consono:
                      if elenco_campi[i_campo] != campo:
                         print "    [ERR] Riga %s: Campo non trovato o non nell'ordine, attuale=%s, effettivo=%"%(tot_righe, campo,elenco_campi[i_campo])
                                      
                   if riga_out: 
                      riga_out += ";" + valore 
                   else: 
                      riga_out = valore
                   i_campo+=1 # incremento (per il controllo)
                else: # riga vuota (scrivo il record)
                   if first: # stampo le intestazioni:
                      f_csv.write(int_out + "\n") 
                      first=False # alla prima interlinea diventa falso
                   f_csv.write(riga_out + "\n") 
                   i_campo=0 # resetto il campo all'internlinea
                   tot_record+=1
                   riga_out=""
                   int_out=""

            # chiudo i files per un nuovo blocco DBF
            f_txt.close()
            f_csv.close()
            f_trc.close()
            print "    [INFO] File: %s [righe %s, colonne %s, record %s]"%(f, tot_righe, len(elenco_campi), tot_record,)
            #import pdb; pdb.set_trace() # Blocco a fine conversione di un file
    break
