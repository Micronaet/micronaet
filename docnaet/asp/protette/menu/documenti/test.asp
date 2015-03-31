<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/file.asp" -->

<%
dim WorkFolder
	        WorkFolder=getCartellaUpload ()
         %>

<html>
<head>
<title>Upload documenti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<%=WorkFolder%>
</body>
</html>
