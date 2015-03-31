<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<%
set Nazioni = Server.CreateObject("ADODB.Recordset")
Nazioni.ActiveConnection = MM_SQLDocnaet_STRING
Nazioni.Source = "SELECT * FROM Nazioni ORDER BY nazDescrizione ASC"
Nazioni.CursorType = 0
Nazioni.CursorLocation = 2
Nazioni.LockType = 3
Nazioni.Open()
Nazioni_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Nazioni_numRows = Nazioni_numRows + Repeat1__numRows
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
  <tr> 
    <td colspan="5" bgcolor="#999999"> 
      <div align="center"><b><font color="#FFFFCC">Anagrafica Nazioni</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"><a href="nnazione.asp"><img src="../../../../immagini/sistema/bottoni/icone/lingue.gif" width="27" height="31" border="0" alt="Inserimento nuova nazione"></a></td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="64%" border="0" align="center" height="71">
  <tr bgcolor="#CCCCCC" align="center"> 
    <td colspan="5"> 
      <b><font color="#990000">Elenco Nazioni</font></b>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="20%" align="center"> 
      <b>Lingua</b>
    </td>
    <td width="34%" align="center"> 
      <b>Note</b>
    </td>
    <td colspan="3" align="center"> 
      <b>Operazioni</b>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Nazioni.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="20%"> 
      &nbsp;<%=(Nazioni.Fields.Item("nazDescrizione").Value)%>
    </td>
    <td width="34%"> 
      &nbsp;<%=(Nazioni.Fields.Item("nazNote").Value)%>
    </td>
    <form name="frmElimina" action="dnazioni.asp" method="get">
      <td width="5%" bgcolor="#CCCCCC" align="center"> 
        <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina la nazione">
        <input type="hidden" name="ID_nazione" value="<%=(Nazioni.Fields.Item("ID_nazione").Value)%>">        
      
    </td>
    </form><form name="frmModifica" action="mnazioni.asp" method="get">
      <td width="5%" bgcolor="#CCCCCC" align="center"> 
        <input type="image" border="0" name="imgModifica" src="../../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica i dati della lingua">
        <input type="hidden" name="ID_nazione" value="<%=(Nazioni.Fields.Item("ID_nazione").Value)%>">     
    </td> </form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Nazioni.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Nazioni.Close()
%>
