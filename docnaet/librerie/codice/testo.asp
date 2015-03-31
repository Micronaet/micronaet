<%
' ************************************************************************************************************************
' ******************************** LIBRERIA PER GESTIRE LE FUNZIONI DI MANIPOLAZIONE TESTI *******************************
' ************************************************************************************************************************

' ******* Funzione alla quale si passa la stringa di ricerca testo nel documento e ritorna la cond where in SQL (tabella Documenti)
private function ParseTesto(Completo) 
   dim temp, risultato, trovato ' variabili temporanee
   dim oldi,i,l ' contatori e archiviatori
   
   oldi=1 ' parto dalla prima posizione
   i=1 ' inizializzo il contatore
   l=len(Completo) ' imposto il limite massimo
   risultato="" ' azzero la stringa che contiene la parte di query
   while (i<=l) ' faccio passare tutti i caratteri alla ricerca degli operatori logici
       if mid(Completo,i,1)= " " then ' trovato uno spazio'
          trovato=0 ' faccio finta non ci sia l'AND o l'OR
	         if mid(completo,i,5)=" AND " then
                    ' trovato l'and
                    temp=mid(Completo,oldi,i-oldi) ' memorizzo il token
                    risultato=risultato + "((docOggetto like '%"+temp+"%') or (docDescrizione like '%"+temp+"%') or (docNote like '%"+temp+"%')) and "
                    i=i+5 ' salto la parola AND 
                    oldi=i ' mi ricordo della posizione di i 
                    trovato=1 ' ho trovato che è un AND
			  end if
              if mid(completo,i,4)=" OR " then
                    ' trovato l'or
                    temp=mid(Completo,oldi,i-oldi) ' memorizzo il token
                    risultato=risultato + "((docOggetto like '%"+temp+"%') or (docDescrizione like '%"+temp+"%') or (docNote like '%"+temp+"%')) or "
                    i=i+4 ' salto la parola AND 
                    oldi=i ' mi ricordo della posizione di i 
                    trovato=1 ' ho trovato che è un OR
			   else
			        i=i+1 ' effettuato in collettivo per tutte le istruzioni eventualmente precedenti
               end if
		else
		   i=i+1   
        end if 		
   wend
   temp=mid(Completo,oldi,i-oldi) ' memorizzo il token
   risultato=risultato + "((docOggetto like '%"+temp+"%') or (docDescrizione like '%"+temp+"%') or (docNote like '%"+temp+"%')) "   
   ParseTesto=risultato
end function

private function DataSQL (Valore, Remoto)
   if Remoto then
      DataSQL="#"+Cstr(month(Valore))+"/"+Cstr(day(Valore))+"/"+Cstr(year(Valore))+"#"
   '   DataSQL= "CONVERT(DATETIME, '" & year(Valore) & "-" & month(Valore) & "-" & day(Valore) & " 00:00:00', 102)"
   else
      DataSQL= "CONVERT(DATETIME, '" & year(Valore) & "-" & month(Valore) & "-" & day(Valore) & " 00:00:00', 102)"
   end if	  
end function
%>
