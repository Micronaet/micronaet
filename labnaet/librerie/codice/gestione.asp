<%
' ******************* PARTE RELATIVA AI TEST PER LA GESTIONE DEL PROGRAMMA *******************************
function GestisceOffLine()
   if (mid(Application("Configurazione"),1,1)="1")then 
      if (mid(Session("Configurazione"),1,1)="1") then 
         GestisceOffLine=true         
      else
         GestisceOffLine=false   
      end if      
   else
      GestisceOffLine=false   
   end if
end function

function GestisceOffLineAvvio()
   if (mid(Application("Configurazione"),1,1)="1")then       
      GestisceOffLineAvvio=true
   else
      GestisceOffLineAvvio=false   
   end if
end function

function GestisceProdotti()
   if (mid(Application("Configurazione"),2,1)="1") then
      if (mid(Session("Configurazione"),2,1)="1") then
         GestisceProdotti=true         
      else
         GestisceProdotti=false   
      end if      
   else
      GestisceProdotti=false   
   end if
end function

function GestisceMultiAzienda()
   GestisceMultiAzienda=(mid(Application("Configurazione"),3,1)="1" )
end function

function GestoreAnagrafiche()
   GestoreAnagrafiche=Session("Gestore")
end function
' ******************** PARTE RELATIVA ALLA GESTIONE DELLE PERSONALIZZAZIONI *******************************
' funzione che richiede il numero della check box per ritornare il valore selezionato
' CHECK 1    +   CHECK 2   +  CHECK 3
function InserimentoCheck(valore)
   ' ci sono appena 3 check box nella pagina di inserimento
   if (valore>=1) and (valore<=3) then
      if (mid(Application("Personalizzazioni"),valore,1)="1") then ' testo se la stringa assume valore 1
         InserimentoCheck=true
      else
         InserimentoCheck=false
      end if 
   else
      InserimentoCheck=false
   end if
end function

' CHECK 4    +   CHECK 5   +  CHECK 6
function ModificaCheck(valore)
   ' ci sono appena 3 check box nella pagina di inserimento
   if (valore>=1) and (valore<=3) then
      if (mid(Application("Personalizzazioni"),valore+3,1)="1") then ' testo se la stringa assume valore 1
         ModificaCheck=true
      else
         ModificaCheck=false
      end if 
   else
      ModificaCheck=false
   end if
end function

' CHECK dal 7 al 9 compresi
function DocumentiRighe()
   Valore = mid(Application("Personalizzazioni"),7,3) 
   if Valore>0 then 
      DocumentiRighe=Valore
   else
      DocumentiRighe=50
   end if
end function

function VersioneRidotta(SessioneAvviata)
      if SessioneAvviata then
	     VersioneRidotta=Session("Ridotto")
	  else 
	     if (mid(Application("Personalizzazioni"),10,1)="1") then ' testo se la stringa assume valore 1
            VersioneRidotta=true
         else
            VersioneRidotta=false
         end if 
	  end if	 
end function
%>
