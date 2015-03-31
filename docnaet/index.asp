<html>
<head>
<title>--<[ Docnaet ]>--</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>

<frameset cols="50%,50%" frameborder="NO" border="0" framespacing="0"> 
  <frame name="leftFrame" scrolling="NO" noresize src="top.asp" >
  <frame name="rightFrame" scrolling="NO" noresize src="login.asp?Remoto=<%if Session("Remoto") then Response.Write("1") else Response.Write("0") %>">
</frameset>
<noframes><body bgcolor="#FFFFFF" text="#000000">

</body></noframes>
</html>
