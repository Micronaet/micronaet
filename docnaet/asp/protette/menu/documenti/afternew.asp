<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/file.asp" -->
<!--#include virtual="/docnaet/librerie/codice/intestazione.asp" -->
<!--#include virtual="/docnaet/librerie/codice/protocollazione.asp" -->
<%
' ******************** Operazioni sull'archivio **********************
dim parametri, Errore,NumProt1, NumProt2
Errore=""
parametri=split (Session("TimeStamp"),"|", -1, 1) '1) time stamp  2) Check protocollo   3) ID_protocollo   4) Intestazione 5) Numero il fax

' PROTOCOLLAZIONE DEL DOCUMENTO ************************************************************************	
if parametri(1)="1"  then ' verifico se è selezionata l'opzione protocolla
   NumProt1= BloccaProtocolli (parametri(2),1, MM_SQLDocnaet_STRING)   ' blocco 1 numero di protocollo
   ' assegno il numero di protocollo al documento appena creato
   AssegnaProtocolloDocumento parametri(0),NumProt1,MM_SQLDocnaet_STRING
end if

' PROTOCOLLAZIONE DEL NUMERO DI FAX ***********************************************************************
if parametri(4)="1"  then ' verifico se è selezionata l'opzione fax
   NumProt2= BloccaProtocolliSpedizioni("Fax",Session("IDDitta"), 1, MM_SQLDocnaet_STRING)
   AssegnaProtocolloFaxDocumento "docControllo='"+Cstr(parametri(0)) + "'",NumProt2, MM_SQLDocnaet_STRING
end if

' CREAZIONE DEL FILE *****************************************************************************************
FileNuovo=GeneraFileNuovo(parametri(0),Session("IDDitta"),Puntatore, MM_SQLDocnaet_STRING)

' Creazione e personalizzazione dell'intestazione
if parametri(3) ="1" then 
   Errore= CaricaIntestazione ("docControllo='"+ Cstr(parametri(0)) +"'", FileNuovo, MM_SQLDocnaet_STRING)
end if
%>

<html>
<head>
<title>Dettaglio</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" topmargin="10" leftmargin="1">
<table width="36%" border="0" align="center" height="71">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Resoconto operazione</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF">
    <td width="40%" bgcolor="#CEECFD">Inserimento</td>
    <td width="60%" bgcolor="#FFFFCC">Effettuato con successo</td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="40%" bgcolor="#CEECFD"> 
      <div align="left">Protocollazione</div>
    </td>
    <td width="60%" bgcolor="#FFFFCC"> 
      <div align="left"><%=NumProt1%></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="40%" bgcolor="#CEECFD">Fax:</td>
    <td width="60%" bgcolor="#FFFFCC"><%=NumProt2%></td>
  </tr>
  <% if Errore<>"" then %>
  <tr bgcolor="#FFFFFF"> 
    <td width="40%" bgcolor="#CEECFD"><font color="#FF0000">Errore generando l'intestazione:</font></td>
    <td width="60%" bgcolor="#FFFFCC" valign="top"><%=Errore%></td>
  </tr>
  <% end if %>
</table>
<br>
<p align="center"><a href="<%=FileNuovo%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="27" height="32" border="0" alt="Apertura del documento"></a> 
</p>
</body>
</html>

