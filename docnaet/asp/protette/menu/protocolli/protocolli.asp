<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/file.asp" -->
<%
Dim Protocolli__MMColParam
Protocolli__MMColParam = "1"
if (Session("IDDitta") <> "") then Protocolli__MMColParam = Session("IDDitta")
%>
<%
set Protocolli = Server.CreateObject("ADODB.Recordset")
Protocolli.ActiveConnection = MM_SQLDocnaet_STRING
Protocolli.Source = "SELECT * FROM Protocolli WHERE ID_azienda = " + Replace(Protocolli__MMColParam, "'", "''") + " ORDER BY proDescrizione ASC"
Protocolli.CursorType = 0
Protocolli.CursorLocation = 2
Protocolli.LockType = 3
Protocolli.Open()
Protocolli_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Protocolli_numRows = Protocolli_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Elenco Protocolli</title>
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
      <div align="center"><b><font color="#FFFFCC">Anagrafica Protocolli</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"><a href="nprotocollo.asp"><img src="../../../../immagini/sistema/bottoni/icone/protocollo.gif" width="27" height="27" alt="Nuovo protocollo" border="0"></a></td>
    <td width="20%" height="29">
      <div align="center"><a href="<%=Application("CartellaDati") & "\" & Cstr(Session("IDDitta"))+"\modelli\"%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/esplora.gif" width="27" height="26" border="0" alt="Cartella modelli standard"></a></div>
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="56%" border="0" align="center" height="68">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="8"> 
      <div align="center"><b><font color="#990000">Elenco Protocolli</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="35%"> 
      <div align="center"><b>Lingua</b></div>
    </td>
    <td width="40%"> 
      <div align="center"><b>Note</b></div>
    </td>
    <td width="15%"><b>Pross.</b></td>
    <td colspan="5"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Protocolli.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="35%" valign="top"> 
      <p>&nbsp;<%=(Protocolli.Fields.Item("proDescrizione").Value)%></p>
    </td>
    <td width="37%" valign="top"> 
      <p>&nbsp;<%=(Protocolli.Fields.Item("proNote").Value)%></p>
    </td>
    <td width="15%" valign="top"><%=(Protocolli.Fields.Item("proProssimo").Value)%></td>
    <form name="frmElimina" action="dprotocollo.asp" method="get">
      <td width="3%" bgcolor="#CCCCCC" align="center" valign="top"> 
          <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina il protocollo">
          <input type="hidden" name="ID_protocollo" value="<%=(Protocolli.Fields.Item("ID_protocollo").Value)%>">
      </td></form>
    <form name="frmModifica" action="mprotocollo.asp" method="get">
      <td width="3%" bgcolor="#CCCCCC" align="center" valign="top"> 
        <div align="center"> 
          <input type="image" border="0" name="imgModifica" src="../../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica il protocollo">
          <input type="hidden" name="ID_protocollo" value="<%=(Protocolli.Fields.Item("ID_protocollo").Value)%>">
        </div>
    </td></form>
    <td width="3%" bgcolor="#CCCCCC" align="center" valign="top"><a href="<%=getcartellaModello(Protocolli.fields("ID_protocollo").value,Session("IDDitta"))%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/esplora.gif" width="21" height="20" alt="Esplora cartella dei modelli" border="0"></a></td>
    <form name="frmModelli" method="post" action="modelli.asp">
      <td width="3%" bgcolor="#CCCCCC" align="center" valign="top">
        <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/icone/modelli.gif" width="18" height="21" alt="Gestione modelli">
        <input type="hidden" name="ID_protocollo" value="<%=(Protocolli.Fields.Item("ID_protocollo").Value)%>" >
        <input type="hidden" name="proDescrizione" value="<%=(Protocolli.Fields.Item("proDescrizione").Value)%>" >
      </td></form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Protocolli.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Protocolli.Close()
%>
