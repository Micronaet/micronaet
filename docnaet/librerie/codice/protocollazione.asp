<%
' *********************************************************
' **** FUNZIONI RIGUARDANTI LA GESTIONE DEI PROTOCOLLI ****
' *********************************************************

' funzione che sposta il contatore prossimo di 'Numero' protocolli restituendo il valore del primo riferito all'ID passato **********************
function BloccaProtocolli(ID, Numero, StringaConnessione)
  dim Protocolli, Primo, AggiornaProtocolli
  
  ' leggo il primo numero
  Set Protocolli = Server.CreateObject("ADODB.Recordset")
  with Protocolli  
     ' trovo il valore del prossimo numero di protocollo
     .ActiveConnection = StringaConnessione
     .Source = "SELECT proProssimo FROM Protocolli WHERE ID_protocollo="+Cstr(ID)
     .CursorType = 0
     .CursorLocation = 2
     .LockType = 3
 	 .Open()
	 ' incremento il valore del prossimo protocollo di una unità
 	 Primo=Clng(.fields("proProssimo").value) 'memorizzo il prossimo valore di protocollo da assegnare ai documenti
     .ActiveConnection.Close ' chiudo la connessione alla tabella dei protocolli
   end with
   
   ' aggiorno al numero nuovo in funzione del numero di docuemnti da riservare
   set AggiornaProtocolli=Server.CreateObject ("ADODB.Command")	
   AggiornaProtocolli.ActiveConnection = StringaConnessione
   AggiornaProtocolli.CommandText="UPDATE Protocolli SET proProssimo=" & Cstr(Primo+Numero)  & " WHERE (ID_protocollo="+Cstr(ID) + ")"
   AggiornaProtocolli.Execute() ' aggiorno la tabella attuale al nuovo valore perr il prossimo protocollo lanciando il comando
   AggiornaProtocolli.ActiveConnection.Close() ' chiudo l'eventuale connessiona aperta
   BloccaProtocolli=Primo
end function

' funzione che aggiorna il documento con il time stamp passato con il numero di protocollo passato nell'archivio puntato dalla stringa di connessione ***
function AssegnaProtocolloDocumento (Controllo,Protocollo, StringaConnessione)
   dim AggiornaDocumenti
   
   set AggiornaDocumenti=Server.CreateObject ("ADODB.Command")	
   AggiornaDocumenti.ActiveConnection = StringaConnessione
   AggiornaDocumenti.CommandText="UPDATE Documenti SET docNumero=" & Cstr(Protocollo)  & " WHERE (docControllo='"+Cstr(Controllo) + "')"
   AggiornaDocumenti.Execute() ' aggiorno la tabella attuale al nuovo valore perr il prossimo protocollo lanciando il comando
   AggiornaDocumenti.ActiveConnection.Close() ' chiudo l'eventuale connessiona aperta      
end function

' Blocca alcuni numeri dei protocolli di spedizione *****************************************************************************************************
function BloccaProtocolliSpedizioni(Descrizione,IDDitta, Numero, StringaConnessione)
  dim Primo, Protocolli, AggiornaProtocolli
   
  Set Protocolli = Server.CreateObject("ADODB.Recordset")
  with Protocolli  
     ' trovo il valore del prossimo numero di protocollo
     .ActiveConnection = StringaConnessione
     .Source = "SELECT speProssimo FROM Spedito WHERE speDescrizione='"+Descrizione+"' and ID_ditta="+Cstr(IDDitta)
     .CursorType = 0
     .CursorLocation = 2
     .LockType = 3
 	 .Open()
 	
	 ' incremento il valore del prossimo protocollo di una unità
 	 Primo=Clng(.fields("speProssimo").value) 'memorizzo il prossimo valore di protocollo da assegnare ai documenti
     .ActiveConnection.Close ' chiudo la connessione alla tabella dei protocolli
  end with

  set AggiornaProtocolli=Server.CreateObject ("ADODB.Command")	
  AggiornaProtocolli.ActiveConnection = StringaConnessione
  AggiornaProtocolli.CommandText="UPDATE Spedito SET speProssimo=" & Cstr(Primo+Numero)  & " WHERE (speDescrizione='"+Descrizione+"' and ID_ditta="+Cstr(IDDitta)+")"
  AggiornaProtocolli.Execute() ' aggiorno la tabella attuale al nuovo valore perr il prossimo protocollo lanciando il comando
  AggiornaProtocolli.ActiveConnection.Close() ' chiudo l'eventuale connessiona aperta
  BloccaProtocolliSpedizioni=Primo
end function

' Aggiorna il documento con il time stamp passato con il numero di protocollo fax passato nell'archivio puntato dalla stringa di connessione ***
function AssegnaProtocolloFaxDocumento (Controllo, Protocollo, StringaConnessione)
  dim AggiornaDocumenti
  
  ' assegno il numero di protocollo al documento appena creato
  set AggiornaDocumenti=Server.CreateObject ("ADODB.Command")	
  AggiornaDocumenti.ActiveConnection = StringaConnessione
  AggiornaDocumenti.CommandText="UPDATE Documenti SET docFax=" & Cstr(Protocollo)  & " WHERE ("+Controllo+")"
  AggiornaDocumenti.Execute() ' aggiorno la tabella attuale al nuovo valore perr il prossimo protocollo lanciando il comando
  AggiornaDocumenti.ActiveConnection.Close() ' chiudo l'eventuale connessiona aperta    
end function
%>
