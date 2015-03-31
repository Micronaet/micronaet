<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/file.asp" -->
<!--#include virtual="/docnaet/librerie/codice/intestazione.asp" -->
<%
dim parametri, Errore
Errore=""
Set DocumentiIntestazione = Server.CreateObject("ADODB.Recordset")
with DocumentiIntestazione ' creo la vista per recuperare i dati intestazione e nome file  
     .ActiveConnection = MM_SQLDocnaet_STRING
     .Source = "SELECT * FROM vwCopertinaFax WHERE ID_documento='"+Cstr(Request.Form("hidID_Documento"))+"'"
     .CursorType = 0
     .CursorLocation = 2
     .LockType = 3
 	 .Open()
     FileNuovo=getNomeFile(.fields("ID_documento").value,.fields("ID_protocollo").value,Session("IDDitta"),.fields("ID_supporto").value, .fields("docFile").value, .fields("docEstensione").value, Puntatore)
end with
DocumentiIntestazione.ActiveConnection.Close()
' Creazione e personalizzazione dell'intestazione
Errore= CaricaIntestazione (DocumentiIntestazione, FileNuovo)
Response.redirect (Request.Form("hidNomeFile"))
%>

<html>
<head>
<title>Dettaglio</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>

<body bgcolor="#FFFFFF" text="#000000" topmargin="1" leftmargin="1">
Pagina di transito
</body>
</html>

