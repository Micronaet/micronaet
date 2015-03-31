<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<%
' *******************************************
' * Pagina che permette l'eliminazione (3)  *
' * di un utente del data base              *
' *******************************************
'
%>
<%
  dim i
  dim cn, utenti, sqlutenti, comando
  dim Eliminazione
  
  i=0
  'apro la tabella utenti con i valori che mi servono
  sqlutenti="SELECT * FROM utenti WHERE ID_utente=" + cstr(request.querystring("txtUserID")) '" ' ' faccio comparire solo la lista di utenti non eliminabili per proteggere quelli di sistema
  set utenti = Server.CreateObject("ADODB.Recordset")
  utenti.ActiveConnection =MM_SQLDocnaet_STRING' Application("DBDocnaet")
  utenti.Source = sqlutenti
  utenti.CursorType = 0
  utenti.CursorLocation = 2
  utenti.LockType = 3
  utenti.Open()
  %>
<html>
<head>
<title>Dettaglio</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="5">
<% if request.querystring("Submit")="Confermi" then Eliminazione=true Else Eliminazione=False %>

<div align="center">
<% if eliminazione then %>
  <font color="#009933"><b>L'utente descritto è stato eliminato dall'archivio</b></font> 
  <% else %>
<div align="center">
    <table width="35%" border="0" bgcolor="#CCCCCC">
      <tr>
        <td align="center"> <b><font color="#009933">Eliminazione utente</font></b> 
        </td>
    </tr>
  </table>
  </div>
<% end if %>
<br>
  <br>
</div>
<table width="35%" border="0" align="center">
  <tr> 
    <td width="8%">User Name:</td>
    <td width="92%" bgcolor="#FFFFCC"><%=utenti("uteUserName")%></td>
  </tr>
  <tr> 
    <td width="8%">Descrizione:</td>
    <td width="92%" bgcolor="#FFFFCC"><%=utenti("uteDescrizione")%></td>
  </tr>
  <tr> 
    <td width="8%">Administrator:</td>
    <td width="92%" bgcolor="#FFFFCC">
      <input type="checkbox" name="checkbox" value="checkbox" 
	  <%
	    if utenti("uteAdministrator") then 		   response.write("checked")
		%>>
    </td>
  </tr>
</table>

<br>
<% if Eliminazione then %>
      <form name="form3" method="post" action="utenti.asp">
        
  <div align="center"> 
    <table width="15%" border="0" align="center">
      <tr>
        <td align="center"> 
          <input type="image" border="0" name="imageField" src="../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30">
        </td>
      </tr>
    </table>
  </div>
      </form>
<%
' codice vero e proprio per l'eliminazione:
' è stato inserito qui per permettere la precedente visulizzazione dell'utente!
  sqlutenti="DELETE FROM utenti WHERE ID_utente=" + request.querystring("txtUserID")
  set comando = Server.CreateObject("ADODB.Command")
  comando.ActiveConnection =MM_SQLDocnaet_STRING' Application("DBDocnaet")
  comando.CommandText = sqlutenti
  comando.Execute()
%>
<% else %>
<table width="35%" border="0" align="center">
  <tr>
    <td height="10" width="50%" align="center"> 
      <form name="form2" method="get" action="eliminazione.asp">
          <input type="submit" name="Submit" value="Confermi">
          <input type="hidden" name="txtUserID" value="<% =request.querystring("txtUserID") %>">        
      </form>
    </td>
    <td height="10" width="50%" align="center"> 
      <form name="form3" method="post" action="utenti.asp">       
          <input type="submit" name="Submit" value="Annulla">        
      </form>
    </td>
  </tr>
</table>
<% end if %>
</body>
</html>
<%
utenti.close()
' cn=nothing
%>