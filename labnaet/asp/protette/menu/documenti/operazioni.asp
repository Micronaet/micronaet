<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/librerie/codice/intestazione.asp" -->
<!--#include virtual="/labnaet/librerie/codice/protocollazione.asp" -->

<%
dim Opzione

' **********************************************************************************************************************************
' ********************* DUPLICAZIONE DELLA REGISTRAZIONE ***************************************************************************
' **********************************************************************************************************************************

if Request.Form("imgDuplica.x") <>"" then
   Opzione="Duplicazione"
   dim DuplicoFile, controllo, Comando, temp, Errore, IDNewDoc, Puntatore, tempDocFile

   DuplicoFile= (Request.Form("radiobutton")="Duplico" )
   controllo=Cstr(now()) ' memorizzo il time stamp
   set Duplicazione = Server.CreateObject("ADODB.Command")
   with Duplicazione
        .ActiveConnection = MM_SQLDocnaet_STRING
		' ************* creazione del record duplicato con la duplicazione anche del file *******************************
		if DuplicoFile then ' la duplicazione già funziona correttamente in quanto il docFile viene creato vuoto dall' Add New (nome file poi mi arriva dalla precedente chiamata)
		   
		   ' ************* verifico se è necessario la riprotocollazione
		   Riprotocollo=(Request.Form("chkRiprotocolla")="1") ' è stato checkato il riprotocollo
		   if Riprotocollo then ' devo assegnare il numero di fax
		      NuovoProtocollo= BloccaProtocolli (Request.Form("hidIDProtocollo"),1, MM_SQLDocnaet_STRING) ' blocco 1 numero di protocollo per l'ID attuale)
		      tempV1= Cstr(NuovoProtocollo)' valore da assegnare
		   else ' non devo assegnare il numero di fax
              tempV1= "docNumero" ' valore da assegnare
		   end if
		   
		   ' ************* verifico se è necessaria la rifaxazione
		   RiFaxo=(Request.Form("chkRifax")="1") ' è stato checkato il riprotocollo
		   if (Riprotocollo) or (RiFaxo) then 
		      ValoreData=Date
		      tempVD= "'"+Cstr(ValoreData) +"' AS EspData "
		   else 
		      tempVD= "docData" 
		   end if	  
		   
		   if RiFaxo then ' devo assegnare il numero di fax
		      NuovoProtocolloFax= BloccaProtocolliSpedizioni("Fax",Session("IDDitta"), 1, MM_SQLDocnaet_STRING) ' cattturo il numero di fax
  		      tempV2= Cstr(NuovoProtocolloFax) + " as EspFax "' valore da assegnare
		   else	  
              tempV2= "docFax" ' valore da assegnare
		   end if
		   
		   Comando="INSERT INTO Documenti (ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote, docData, docAccesso, docAzienda, docNumero, docFax, ID_utente, docControllo, docEstensione) SELECT ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote," +  tempVD + ", docAccesso, docAzienda, "+  tempV1 + " AS EspNumero, "+ tempV2 +", " _
		           + Cstr(Session("UserID")) + " as Espr3, '" + controllo + "' AS Espr1, docEstensione FROM Documenti WHERE ID_documento = " + Cstr(Request.Form("hidID_Documento"))		      
           '   Comando="INSERT INTO Documenti (ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote, docData, docAccesso, docAzienda, docNumero, docFax, ID_utente, docControllo, docEstensione) SELECT ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote, docData, docAccesso, docAzienda, docNumero, docFax, " _
		   '        + Cstr(Session("UserID")) + " as Espr3, '" + controllo + "' AS Espr1, docEstensione FROM Documenti WHERE ID_documento = " + Cstr(Request.Form("hidID_Documento"))
		   ' se è richiesta la duplicazione del file non faccio niente
           .CommandText =Comando
		else
		' ************* Creazione del record duplicato senza la duplicazione del file ***********************************
		   ' se non è richiesta la duplicazione del file metto il campo ID vecchio nel campo docFile
		   if Request.Form("hiddocFile")<>"" then ' il file era già un puntatore
		      tempDocFile=Cstr(Request.Form("hiddocFile")) ' metto nel nome del file il vecchio file puntato
		   else
		      tempDocFile=Cstr(Request.Form("hidID_Documento")) ' metto il valore dell' ID documento precedente
		   end if	  		      
		   
		   Comando="INSERT INTO Documenti (ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote, docData, docFile, docAccesso, docAzienda, docNumero, docFax, ID_utente, docControllo, docEstensione) SELECT ID_prodotto,ID_protocollo, ID_lingua, ID_tipologia, ID_supporto, ID_cliente, docOggetto, docDescrizione, docNote, docData, '"+  _
		           tempDocFile +"' AS Espr5, docAccesso, docAzienda, docNumero, docFax, "+ Cstr(Session("UserID")) + " as Espr3, '" + controllo + "' AS Espr1, docEstensione FROM Documenti WHERE ID_documento = " + Cstr(Request.Form("hidID_Documento"))
		   .CommandText =Comando
		end if 
		' ************ FINE ***********************************************************************************************  
		.Execute() 	 
		.ActiveConnection.Close()  
   end with   
   ' parte per eseguire l'eventuale duplicazione del file e attivazione
   set NuovoDocumento = Server.CreateObject("ADODB.Recordset")
   with NuovoDocumento
       .ActiveConnection = MM_SQLDocnaet_STRING
       .Source = "SELECT * FROM Documenti WHERE docControllo = '" + controllo + "'"
       .CursorType = 0
       .CursorLocation = 2
       .LockType = 3
       .Open()
	   IDNewDoc=Cstr(.Fields.Item("ID_documento"))
	   ' ********************* Duplicazione effettiva del file nel (deve rimanere in questa zona) ****************************
       if DuplicoFile then
          ' nel caso sia da duplicare il file devo copiare il vecchio nel nuovo e, dopo la modifica caricare l'intestazioe
          dim Forg, Fnew, fso
          Forg=Request.Form("hidNomeFile") ' leggo il nome del file originale dalla videata precedente
		  Fnew=getNomeFile(.Fields.Item("ID_documento"),.Fields.Item("ID_protocollo"),Session("IDDitta"),.Fields.Item("ID_supporto"),.Fields.Item("docFile"),.Fields.Item("docEstensione"), Puntatore)
		  Set fso = CreateObject("Scripting.FileSystemObject")   
		  on error resume next
		  fso.CopyFile Forg, Fnew
		  ' rimetto gli attributi in lettura scrittura  	    
		  Set Fattr = fso.GetFile(Fnew)
          Fattr.attributes =0    
	      Errore=Err.description		  
       end if	  
	   .ActiveConnection.Close()
   end with	   
   ' redirect sulla pagina per la modifica dei dati tecnici
   Response.redirect ("modifica.asp?ID_documento="+ IDNewDoc+"&ID_Cliente="+Cstr(Request.Form("hidID_Cliente")) ) ' mando la pagina alla videata delle modifiche per eventuali correzioni da fare   
else

' **********************************************************************************************************************************
' ************************************************* ELIMINAZIONE DEL FILE **********************************************************
' **********************************************************************************************************************************

   if Request.Form("imgElimina.x") <>"" then
       Opzione="Eliminazione"
	   ' sono nella parte della cancellazione
	   set cmdEliminazione=Server.CreateObject ("ADODB.Command")	
	   with cmdEliminazione
		  .ActiveConnection = MM_SQLDocnaet_STRING
		  .CommandText="DELETE Documenti WHERE ID_documento=" & Request.Form("hidID_Documento")
		  .Execute() ' aggiorno la tabella attuale al nuovo valore perr il prossimo protocollo lanciando il comando
		  .ActiveConnection.Close() ' chiudo l'eventuale connessiona aperta
	   end with	 
	   Response.redirect("documenti.asp") ' ritorno alla pagina dei documenti        
   else  
' **********************************************************************************************************************************
' ************************************************* BLOCCO IN SOLA LETTURA DEL FILE ************************************************
' **********************************************************************************************************************************

      if Request.Form ("imgProteggi.x") then
	      Opzione="Proteggi file"
		  ' sono nella parte di protezione
		  dim Responso, F
		  
		  Forg=Request.Form("hidNomeFile2") ' leggo il nome del file originale dalla videata precedente
		  Set fso = CreateObject("Scripting.FileSystemObject")   
		  if fso.FileExists(Forg) then	     
			 Responso="Documento Bloccato"      
			 Set F = fso.GetFile(forg)
			 F.attributes =1      	    
		  else
			  Responso="Non posso bloccare un file inesistente!"
		  end if
	  else
' **********************************************************************************************************************************	  
' ************************************************ RICARICAMENTO DELLE INTESTAZIONI O RIPROTOCOLLAZIONE ****************************
' **********************************************************************************************************************************

          dim NumProt, FileNuovo, Errore1
		  Scelta=4
		  FileNuovo=Request.Form("hidNomeFile")
	      if Request.Form("chkProtocolla") <>"" then ' devo impostare il numero di protocollo perchè viene spedito via fax
		     Opzione="Protocollazione "
             NumProt= BloccaProtocolliSpedizioni("Fax",Session("IDDitta"), 1, MM_SQLDocnaet_STRING)
             AssegnaProtocolloFaxDocumento "ID_documento=" + Request.Form("hidID_Documento"),NumProt, MM_SQLDocnaet_STRING
			 Responso="Protocollato!"
		  end if
		  if Request.Form("chkRicarica") <>"" then ' devo 
		     Opzione=Opzione+ "Ricaricamento intestazione"
			 Errore1= CaricaIntestazione ("ID_documento =" & Cstr(Request.Form("hidID_Documento")), FileNuovo, MM_SQLDocnaet_STRING)
			 if Errore1="" then Responso=Responso + "Caricamento eseguito!" else Responso=Responso + vbcr + " Errore:" + Errore1
		  end if
	  end if	  
   end if
end if
%>

<html>
<head>
<title>Transito</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" topmargin="1" leftmargin="1">
<br>
<table width="36%" border="0" align="center">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Resoconto operazione: <%=Opzione%></font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="24%" bgcolor="#CEECFD">Responso</td>
    <td width="76%" bgcolor="#FFFFCC"><%=Responso%></td>
  </tr>
</table>
<% if Scelta=4 then %>
<br>
<div align="center"><a href="<%=FileNuovo%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="27" height="32" border="0" alt="Apertura del documento"></a> 
</div>
<% end if %>
<br>
<table width="36%" border="0" align="center">
  <tr> 
    <td bgcolor="#999999" height="30"> 
      <div align="right"><a href="javascript:window.history.back()"><img src="../../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></div>
    </td>
  </tr>
</table>
</body>
</html>
