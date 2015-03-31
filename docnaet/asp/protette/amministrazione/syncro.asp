<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<%
Dim Regole__MMColParam
Regole__MMColParam = "1"
if (Request.Form("ID_utente") <> "") then Regole__MMColParam = Request.Form("ID_utente")
%>
<%
set Regole = Server.CreateObject("ADODB.Recordset")
Regole.ActiveConnection = MM_SQLDocnaet_STRING
Regole.Source = "SELECT * FROM dbo.Regole WHERE ID_utente = " + Replace(Regole__MMColParam, "'", "''") + " ORDER BY ID_regola ASC"
Regole.CursorType = 0
Regole.CursorLocation = 2
Regole.LockType = 3
Regole.Open()
Regole_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Regole_numRows = Regole_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Regole di Sincronizzazione</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
</head>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="0" topmargin="0">
<table width="100%" border="0" height="52" dwcopytype="CopyTableRow">
  <tr bgcolor="#999999"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#FFFFCC">Gestione Regole Utente: <font color="#990000"><%=Request.QueryString("uteDescrizione")%></font></font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"> <a href="inserimento.asp"><img src="../../../immagini/sistema/bottoni/icone/portatile.gif" width="30" height="32" border="0" alt="Inserimento nuovo utente"></a> 
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="600" border="0" cellpadding="0" cellspacing="0" align="center">
  <tr align="center"> 
    <td><b>Regola</b></td>
    <td><b>Operazioni</b></td>
  </tr>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Regole.EOF)) 
%>
  <tr> 
    <td><%=(Regole.Fields.Item("regNome").Value)%></td>
    <td><a href="../menu/documenti/syncro.asp?ID_regola=<%=(Regole.Fields.Item("ID_regola").Value)%>"><img src="../../../immagini/sistema/bottoni/icone/syncro.gif" width="26" height="31" border="0" alt="Creazione regola"></a> 
    </td>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Regole.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Regole.Close()
%>

