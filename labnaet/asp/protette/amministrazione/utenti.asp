<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
Dim Utenti__MMColParam
Utenti__MMColParam = "0"
if (Request("MM_EmptyValue") <> "") then Utenti__MMColParam = Request("MM_EmptyValue")
%>
<%
set Utenti = Server.CreateObject("ADODB.Recordset")
Utenti.ActiveConnection = MM_SQLDocnaet_STRING
Utenti.Source = "SELECT * FROM Utenti WHERE uteNonEliminabile = " + Replace(Utenti__MMColParam, "'", "''") + " ORDER BY uteUserName ASC"
Utenti.CursorType = 0
Utenti.CursorLocation = 2
Utenti.LockType = 3
Utenti.Open()
Utenti_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Utenti_numRows = Utenti_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Utenti</title>
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
      <div align="center"><b><font color="#FFFFCC">Gestione Utenti</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"> 
      <a href="inserimento.asp"><img src="../../../immagini/sistema/bottoni/icone/users.gif" width="31" height="25" border="0" alt="Inserimento nuovo utente"></a>
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<p> </p>
<table width="56%" border="0" align="center" height="63">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="8"> 
      <div align="center"><b><font color="#990000">Elenco Utenti</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="24%"> 
      <div align="center"><b>User Name</b></div>
    </td>
    <td width="41%"><b>Descrizione</b></td>
    <td width="41%"> 
      <div align="center"><b>Liv.</b></div>
    </td>
    <td width="6%"> 
      <div align="center"><b>Adm</b></div>
    </td>
    <td width="7%"><b>Gestore</b></td>
    <td colspan="3"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
  </tr>
  <% 
dim colore
While ((Repeat1__numRows <> 0) AND (NOT Utenti.EOF)) 
%>
  <%  ' ciclo per inserire i dati nella tabella ASP
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="30%" height="25" valign="top"> 
      <p>&nbsp;<%=(Utenti.Fields.Item("uteUserName").Value)%></p>
    </td>
    <td width="30%" height="25" valign="top"><%=(Utenti.Fields.Item("uteDescrizione").Value)%></td>
    <td width="10%" height="25" valign="top"> 
      <p align="center"><%=(Utenti.Fields.Item("uteLivello").Value)%></p>
    </td>
    <td width="3%" height="25" valign="top"> 
      <div align="center"> 
        <input type="checkbox" name="checkbox" value="checkbox" <% if Utenti.Fields.Item("uteAdministrator").value then Response.Write("checked") else Response.Write("") %>>
      </div>
    </td>
    <td width="7%" height="25" valign="top" align="center"> 
      <input type="checkbox" name="checkbox2" value="checkbox" <% if Utenti.Fields.Item("uteGestore").value then Response.Write("checked") %>>
    </td>
    <form name="frmElimina" action="eliminazione.asp" method="get">
      <td bgcolor="#CCCCCC" height="25" align="center" valign="top"> 
        <input type="image" border="0" name="imageField" src="../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina l'utente">
        <input type="hidden" name="txtUserID" value="<%=utenti("ID_utente")%>">
      </td>
    </form>
    <form name="frmModifica" action="modifica.asp" method="get">
      <td bgcolor="#CCCCCC" height="25" align="center" valign="top"> 
        <input type="image" border="0" name="imgModifica" src="../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica i dati dell'utente">
        <input type="hidden" name="txtUserName" value="<%=utenti("ID_utente")%>">
      </td>
	  </form>
      <form name="frmSincronizza" action="syncro.asp" method="get">
      <td bgcolor="#CCCCCC" height="25" align="center" valign="top"> 
        <input type="image" border="0" name="imageField2" src="../../../immagini/sistema/bottoni/icone/portatile.gif" width="21" height="22">
        <input type="hidden" name="ID_utente" value="<%=utenti("ID_utente")%>">
        <input type="hidden" name="uteDescrizione" value="<%=(Utenti.Fields.Item("uteDescrizione").Value)%>">
      </td>
    </form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Utenti.MoveNext()
Wend
%>
</table>
<p>&nbsp;</p>
</body>
</html>
<%
Utenti.Close()
%>
