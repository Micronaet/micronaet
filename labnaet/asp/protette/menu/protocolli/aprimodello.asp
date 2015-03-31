<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->

<%' **********************************************************************************************************************
	' Verifico che il file segnalato sia presente altrimenti lo creo copiando il file vuoto dell'applicativo selezionato *
	dim  Commento, f1
    f1=CreoModelloCompleto(Request.QueryString("ID_protocollo"),Cstr(Session("IDDitta")),Request.QueryString("ID_Lingua"), Request.QueryString("ID_applicazione"),Request.QueryString("ID_Tipologia"), Commento) 
    %>
<html>
<head>
<title>Apertura o creazione del modello</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000">
<table width="36%" border="0" align="center" height="71">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Resoconto operazione</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="24%" bgcolor="#CEECFD">Commento:</td>
    <td width="76%" bgcolor="#FFFFCC"><%=Commento%></td>
  </tr>
</table>
<p align="center"><a href="<%=f1%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/modelli.gif" width="26" height="32" border="0" alt="Apertura file"></a></p>
</body>
</html>