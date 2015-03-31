<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<%
set Tipologie = Server.CreateObject("ADODB.Recordset")
Tipologie.ActiveConnection = MM_SQLDocnaet_STRING
Tipologie.Source = "SELECT * FROM Tipologie ORDER BY tipDescrizione"
Tipologie.CursorType = 0
Tipologie.CursorLocation = 2
Tipologie.LockType = 3
Tipologie.Open()
Tipologie_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Tipologie_numRows = Tipologie_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Elenco Lingue</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#FFFFCC">Anagrafica Tipologie</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"><a href="ntipologia.asp"><img src="../../../immagini/sistema/bottoni/icone/tipologia.gif" width="23" height="31" border="0" alt="Nuova tipologia di documento"></a></td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="58%" border="0" align="center" height="68">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco Tipologie</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="28%"> 
      <div align="center"><b>Tipologia</b></div>
    </td>
    <td width="51%"> 
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
While ((Repeat1__numRows <> 0) AND (NOT Tipologie.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="28%" valign="top"> 
      <p>&nbsp;<%=(Tipologie.Fields.Item("tipDescrizione").Value)%></p>
    </td>
    <td width="51%" valign="top"> 
      <p>&nbsp;<%=(Tipologie.Fields.Item("tipNote").Value)%></p>
    </td>
    <form name="frmElimina" action="dtipologie.asp" method="get">
      <td width="10%" bgcolor="#CCCCCC" align="center" valign="top"> 
          <input type="image" border="0" name="imgElimina" src="../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21">
          <input type="hidden" name="ID_tipologia" value="<%=(Tipologie.Fields.Item("ID_tipologia").Value)%>">
      </td></form>
    <form name="frmModifica" action="mtipologia.asp" method="get">
      <td width="11%" bgcolor="#CCCCCC" align="center" valign="top"> 
          <input type="image" border="0" name="imgModifica" src="../../../immagini/sistema/bottoni/open.gif" width="20" height="21">
          <input type="hidden" name="ID_tipologia" value="<%=(Tipologie.Fields.Item("ID_tipologia").Value)%>">
    </td></form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Tipologie.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Tipologie.Close()
%>
