<%
server.execute ("controllo.asp")

%>
<html>
<head>
<title>--&lt;[Docnaet]&gt;--</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<frameset rows="<%
  if Session("Ridotto") then  ' imposto l'altezza della prima riga di frame (visibile o invisibile)
     Response.Write("0") 
  else Response.Write("80")
  end if  
  %>,*" cols="*" frameborder="NO" border="0" framespacing="0"> 
  <frame name="topFrame" scrolling="NO" noresize src="titolo.asp" >
  <frameset cols="125,*" frameborder="NO" border="0" framespacing="0" rows="*"> 
    <frame name="leftFrame" noresize scrolling="VERTICAL" src="menu.asp">
    <frame name="mainFrame" src="centrale.asp">
  </frameset>
</frameset>
<noframes>
<body bgcolor="#FFFFFF" text="#000000">
</body>
</noframes> 
</html>
