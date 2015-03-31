<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<html>
<%
' controllo se il programma viene attivato con la versione breve
if Request.Form("chkRidotto")="1" then 
   Session("Ridotto")=TRUE
else
   Session("Ridotto")=FALSE
end if   
      
Dim utente, password, selezioneutente, utenti, ditte, selezioneditta
on error resume next
utente = Request.Form("txtUserName")
if utente="" then
   utente="*"
else
   utente=rtrim(utente)
end if
password = Request.Form("txtPassword")
if password="" then
   password="*"
else
   password=rtrim(password)
end if
if err then
   response.redirect ("../errore.asp?Descrizione=Errore+nella+ricerca+dei+parametri+di+autenticazione&Numero=na&Url=index.asp")
end if
selezioneutente="SELECT *  FROM Utenti  WHERE uteUserName = '" & utente & "' and utePassword='" & password & "'"
set utenti = Server.CreateObject("ADODB.Recordset")
utenti.ActiveConnection = MM_SQLDocnaet_STRING
utenti.Source = selezioneutente
utenti.CursorType = 0
utenti.CursorLocation = 2
utenti.LockType = 3
utenti.Open()
if err then
   response.redirect ("../errore.asp?Descrizione=Errore+in+fase+di+accesso+a+tabella+utenti&Numero=na&Url=index.asp")
end if

selezioneditta="SELECT * FROM Ditte WHERE ID_ditta=" & cstr(request.form("cboDitta"))
set ditte = Server.CreateObject("ADODB.Recordset")
ditte.ActiveConnection = MM_SQLDocnaet_STRING
ditte.Source = selezioneditta
ditte.CursorType = 0
ditte.CursorLocation = 2
ditte.LockType = 3
ditte.open()
if err then
   response.redirect ("../errore.asp?Descrizione=Errore+in+fase+di+accesso+a+tabella+ditte&Numero=na&Url=index.asp")
end if
%>

<head>
<title>Autenticazione</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">

</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>

<body bgcolor="#FFFFFF" text="#000000">
<% 
   'Costanti del programma
   const SUCCESS = 0
   const ERROR = 1
   const WARNING = 2
   const INFORMATION = 4
   const AUDIT_SUCCESS = 8
   const AUDIT_FAILURE = 16

if utenti.EOF then ' non c'è quell'utente o password errata
   dim WshShell
   set WshShell = Server.CreateObject("WScript.Shell")
   wshshell.Logevent AUDIT_FAILURE, "User: " + utente + " failed to log!" + vbcr + " - date: " + Cstr(date) +vbcr + " - time: " + Cstr(time) +vbcr + " - Remote IP: " + Request.ServerVariables("REMOTE_HOST") 
   set wshshell=nothing
%>
<p align="center"><b><font color="#FF0000">Utente inesistente o password errata 
  </font></b></p>
<p align="center"><a href="../index.asp"><img src="../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></p>
  <%
else
    Session("UserName")= utenti("uteUserName")
    Session("UserID")= utenti("ID_utente")
	Session("UserDescription")=utenti("uteDescrizione")
    Session("IsAutenticated")=TRUE
    Session("ISAdministrator")=utenti("uteAdministrator")
	Session("Level")=utenti("uteLivello")
	Session("IDDitta")=request.form("cboDitta") ' memorizzo la ditta di riferimento
	Session("ditRagioneSociale")=ditte("ditRagioneSociale")
	Session("Password")=request.form("txtPassword")
	Session("Configurazione")=utenti("uteConfigurazione")
	Session("IPAddress")=Request.ServerVariables("REMOTE_HOST") 
	Session("Gestore")=utenti("uteGestore")
    response.redirect("protette/homepage.asp")
end if
%>
</body>
</html>
<%
utenti.Close()
ditte.close()
%>