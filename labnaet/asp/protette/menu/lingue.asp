<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
set Lingue = Server.CreateObject("ADODB.Recordset")
Lingue.ActiveConnection = MM_SQLDocnaet_STRING
Lingue.Source = "SELECT * FROM Lingue ORDER BY linDescrizione ASC"
Lingue.CursorType = 0
Lingue.CursorLocation = 2
Lingue.LockType = 3
Lingue.Open()
Lingue_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Lingue_numRows = Lingue_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Elenco Lingue</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#FFFFCC">Anagrafica Lingue</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"><a href="nlingua.asp"><img src="../../../immagini/sistema/bottoni/icone/bandiera.gif" width="32" height="23" border="0"></a></td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="56%" border="0" align="center" height="68">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco Lingue</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="27%"> 
      <div align="center"><b>Lingua</b></div>
    </td>
    <td width="44%"> 
      <div align="center"><b>Note</b></div>
    </td>
    <td colspan="3"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Lingue.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="30%" valign="top"> 
      <p>&nbsp;<%=(Lingue.Fields.Item("linDescrizione").Value)%></p>
    </td>
    <td width="56%" valign="top"> 
      <p>&nbsp;<%=(Lingue.Fields.Item("linNote").Value)%></p>
    </td>
    <form name="frmElimina" action="dlingue.asp" method="get">
      <td width="7%" bgcolor="#CCCCCC" align="center" valign="top"> 
          <input type="image" border="0" name="imgElimina" src="../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina l'elemento">
          <input type="hidden" name="ID_lingua" value="<%=(Lingue.Fields.Item("ID_lingua").Value)%>">
    </td></form>
    <form name="frmModifica" action="mlingua.asp" method="get">
      <td width="7%" bgcolor="#CCCCCC" align="center" valign="top"> 
          <input type="image" border="0" name="imgModifica" src="../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica l'elemento">
          <input type="hidden" name="ID_lingua" value="<%=(Lingue.Fields.Item("ID_lingua").Value)%>">
    </td></form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Lingue.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Lingue.Close()
%>
