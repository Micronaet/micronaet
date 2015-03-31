<%

function CaricaIntestazione (Controllo, FileNuovo, StringaConnessione)
    dim DocumentiIntestazione, gWord, temp, temp1, temp2
	
    Set DocumentiIntestazione = Server.CreateObject("ADODB.Recordset")
    DocumentiIntestazione.ActiveConnection = StringaConnessione
    DocumentiIntestazione.Source = "SELECT * FROM vwCopertinaFax WHERE " + Controllo 
    DocumentiIntestazione.CursorType = 0
    DocumentiIntestazione.CursorLocation = 2
    DocumentiIntestazione.LockType = 3
 	DocumentiIntestazione.Open()
    	
    if right(FileNuovo,3)="DOC" then
		Set gWord = CreateObject("Word.Application")
		gWord.Documents.Open (FileNuovo)
		on error resume next
		With gWord.ActiveDocument.Tables(1)   
			   if not isnull(DocumentiIntestazione.fields("docFax").value) then
				  .Cell(1,2).Range =  "Fax n.: "  +Cstr( DocumentiIntestazione.fields("docFax").value)
			   end if	  
			   if not isnull(DocumentiIntestazione.fields("ditPaese").value) then
				  .Cell(2,1).Range =  Cstr( DocumentiIntestazione.fields("ditPaese").value) + ", " + Cstr(Date())
			   end if	  
			   temp="Prot. " + Cstr(DocumentiIntestazione.fields("proDescrizione").value) + ": " + Cstr(DocumentiIntestazione.fields("docNumero").value) 
			   if  not isnull(DocumentiIntestazione.fields("tipDescrizione").value) then
				  temp=temp + vbcr+ "Tipologia: " +Cstr(DocumentiIntestazione.fields("tipDescrizione").value) 
			   end if
			   if not isnull(DocumentiIntestazione.fields("uteDescrizione").value) then
				   temp=temp+vbcr + "Rif.: "+ Cstr(DocumentiIntestazione.fields("uteDescrizione").value)
			   end if
			   .Cell(3,1).Range =  temp
			   if not isnull(DocumentiIntestazione.fields("cliRagioneSociale").value) then
				   temp1="Destinazione: " +Cstr(DocumentiIntestazione.fields("cliRagioneSociale").value)
			   end if
			   if not isnull(DocumentiIntestazione.fields("cliPaese").value) then
				  temp1=temp1+vbcr+ Cstr(DocumentiIntestazione.fields("cliPaese").value)
			   end if
			   if not isnull(DocumentiIntestazione.fields("cliTelefono").value) then
				  temp1=temp1+vbcr + "Tel.:"+ Cstr(DocumentiIntestazione.fields("cliTelefono").value) 
			   end if
			   if not isnull(DocumentiIntestazione.fields("cliFax").value )  then
				  temp1=temp1+ vbcr+ "Fax: "+ Cstr(DocumentiIntestazione.fields("cliFax").value)
			   end if
			   if not isnull(DocumentiIntestazione.fields("cliEmail").value) then
				  temp1=temp1+vbcr + "E-mail: " + cstr(DocumentiIntestazione.fields("cliEmail").value)
			   end if
			   .Cell(3,2).Range = temp1
			   if not isnull(DocumentiIntestazione.fields("docOggetto").value) then
				  .Cell(4,1).Range =  "OGGETTO: "+ Cstr(DocumentiIntestazione.fields("docOggetto").value)	 
			   end if	  
		End With
		gWord.ActiveDocument.Save()
		gWord.ActiveDocument.Close()
		gWord.Quit()
		if Err.number= 0 then 
			   CaricaIntestazione="" 
		else 
			   CaricaIntestazione=Err.Description
			   Err.clear
		end if
    else
        CaricaIntestazione="Non posso caricare una intestazione Word su un file non .DOC"
    end if
	DocumentiIntestazione.ActiveConnection.Close()
end function
%>