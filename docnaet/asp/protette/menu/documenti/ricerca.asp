<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/librerie/codice/gestione.asp" -->

<html>
<head>
<title>Untitled Document</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<frameset rows="<% if Session("Ridotto") then Response.Write("65,200,*") else Response.Write("85,*,0") %>" frameborder="NO" border="0" framespacing="0"> 
  <frame name="fraCliente" src="ricerca2.asp">
  <frame name="fraRimanente" src="ricerca1.asp">
  <frame name="fraDocumenti" src="vuoto.asp">
<frame src="UntitledFrame-3"><frame src="UntitledFrame-4"></frameset>
<noframes><body bgcolor="#FFFFFF" text="#000000">
</body></noframes>
</html>
