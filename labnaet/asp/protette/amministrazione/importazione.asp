<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
' ********** ciclo per aggiornare le ditte già esistenti **********************
set Aggiornamento = Server.CreateObject("ADODB.Command")
Aggiornamento.ActiveConnection = MM_SQLDocnaet_STRING
Aggiornamento.CommandText ="UPDATE vwMicEsistenti INNER JOIN Clienti ON (vwMicEsistenti.ID_Ditta = Clienti.ID_ditta) AND (vwMicEsistenti.CKY_CNT = Clienti.cliCodice) SET Clienti.cliRagioneSociale = vwMicEsistenti.CDS_RAGSOC_COGN, Clienti.cliIndirizzo = vwMicEsistenti.CDS_INDIR, Clienti.cliPaese = vwMicEsistenti.CDS_LOC, Clienti.cliCAP = vwMicEsistenti.CDS_CAP, Clienti.cliProvincia = vwMicEsistenti.CDS_PROV, Clienti.cliTelefono = vwMicEsistenti.CDS_TEL_TELEX, Clienti.cliFax = vwMicEsistenti.CDS_FAX, Clienti.cliEmail = vwMicEsistenti.CDS_INET, Clienti.ID_nazione = vwMicEsistenti.ID_Nazione, Clienti.ID_tipo = vwMicEsistenti.ID_Tipo" 
Aggiornamento.execute
'Aggiornamento.CommandText ="INSERT INTO Clienti ( cliRagioneSociale, cliIndirizzo, cliCAP, cliPaese, cliProvincia, cliTelefono, cliFax, cliEmail, ID_tipo, ID_nazione, ID_ditta ) SELECT vwClientiNuovi.CDS_RAGSOC_COGN, vwClientiNuovi.CDS_INDIR, vwClientiNuovi.CDS_CAP, vwClientiNuovi.CDS_LOC, vwClientiNuovi.CDS_PROV, vwClientiNuovi.CDS_TEL_TELEX, vwClientiNuovi.CDS_FAX, vwClientiNuovi.CDS_INET, vwClientiNuovi.ID_Tipo, vwClientiNuovi.ID_Nazione, vwClientiNuovi.ID_Ditta FROM vwClientiNuovi ORDER BY  vwClientiNuovi.CDS_RAGSOC_COGN" 
'Aggiornamento.execute
%>
<html>
<head>
<title>Sincronizzazione ditta</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="5">
<p>Aggiornamento effettuato</p>
<p>&nbsp; </p>
</body>
<%
Tipi.Close()
%>
