<html>
<head>
<title>Modifica Documento</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>

<frameset rows="80,*" frameborder="NO" border="0" framespacing="0"> 
  <frame name="fraCliente" src="ricerca2.asp?setIDCliente=<%=Request.QueryString("ID_cliente")%>" >
  <frame name="fraModifica" src="modifica1.asp<%="?ID_documento="+Request.QueryString("ID_documento")%>">
</frameset>
<noframes><body bgcolor="#FFFFFF" text="#000000">

</body></noframes>
</html>
