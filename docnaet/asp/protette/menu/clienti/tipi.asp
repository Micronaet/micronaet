<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<%
set Tipi = Server.CreateObject("ADODB.Recordset")
Tipi.ActiveConnection = MM_SQLDocnaet_STRING
Tipi.Source = "SELECT * FROM Tipi ORDER BY tipDescrizione"
Tipi.CursorType = 0
Tipi.CursorLocation = 2
Tipi.LockType = 3
Tipi.Open()
Tipi_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Tipi_numRows = Tipi_numRows + Repeat1__numRows
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
      <div align="center"><b><font color="#FFFFCC">Anagrafica tipi di ditte</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"> <a href="ntipi.asp"><img src="../../../../immagini/sistema/bottoni/icone/cxconfig.gif" width="31" height="31" border="0"></a> 
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="64%" border="0" align="center" height="84">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco tipo di ditte</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="20%"> 
      <div align="center"><b>Tipo</b></div>
    </td>
    <td width="34%"> 
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
While ((Repeat1__numRows <> 0) AND (NOT Tipi.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="20%" valign="top" height="31"> 
      <p>&nbsp;<%=(Tipi.Fields.Item("tipDescrizione").Value)%></p>
    </td>
    <td width="34%" valign="top" height="31"> 
      <p>&nbsp;<%=(Tipi.Fields.Item("tipNote").Value)%></p>
    </td>
    <form name="frmElimina" action="dtipi.asp" method="get">
      <td width="5%" bgcolor="#CCCCCC" align="center" valign="top" height="31"> 
          <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina il tipo di ditta">
          <input type="hidden" name="ID_tipo" value="<%=(Tipi.Fields.Item("ID_tipo").Value)%>">        
    </td></form>
    <form name="frmModifica" action="mtipi.asp" method="get">
      <td width="5%" bgcolor="#CCCCCC" align="center" valign="top" height="31"> 
          <input type="image" border="0" name="imgModifica" src="../../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica i dati del tipo di ditta">
          <input type="hidden" name="ID_tipo" value="<%=(Tipi.Fields.Item("ID_tipo").Value)%>">        
    </td></form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Tipi.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Tipi.Close()
%>

