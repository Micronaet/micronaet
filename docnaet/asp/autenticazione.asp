<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<html>
<%
    Dim utente, password, selezioneutente, utenti, ditte, selezioneditta, documento_id, cliente_id

    ' **************** CONTROLLO LA MODALITA' DI CHIAMATA DELLA VIDEATA ********
    ' 1. La videata puo' essere aperta passando dal form di login (normale)
    ' 2. La videata puo' essere aperta passando ID_documento, ID_azienda, ID_utente
    '    per fare caricare direttamente una scheda documento senza richiedere il
    '    login utente
    
    if Request.QueryString("token") = "T" then ' possible unificarlo
        automatica = True
    else
        automatica = False
    end if    
            
    on error resume next ' gestito errore con test di "err"
    if automatica then ' **** VERSIONE CARICAMENTO DA APERTURA RAPIDA DOCUMENTO ***
        Session("Ridotto")=TRUE

        ' **** DOCUMENTO ******************************************************* 
        documento_id = Request.QueryString("document_id") 
        if documento_id = "" then
            documento_id = "0"
        else
            documento_id = rtrim(documento_id)
        end if
        ' Verifica esistenza documento:
        set documento = Server.CreateObject("ADODB.Recordset")
        documento.ActiveConnection = MM_SQLDocnaet_STRING
        documento.Source = "SELECT * FROM Documenti WHERE ID_documento = " & documento_id                 
        documento.CursorType = 0
        documento.CursorLocation = 2
        documento.LockType = 3
        documento.Open()    
        test = documento("ID_documento")   ' genera errore se non esiste       
        if err then
           response.redirect ("../errore.asp?Descrizione=Errore+il+documento+non+esiste&Numero=na&Url=index.asp")
        end if
        
        ' **** CLIENTE *********************************************************
        cliente_id = Request.QueryString("client_id")     
        if cliente_id = "" then
            cliente_id = "0"
        else
            cliente_id = rtrim(cliente_id)
        end if
        if err then
           response.redirect ("../errore.asp?Descrizione=Errore+nella+ricerca+del+parametro+documento+o+cliente+da+aprire&Numero=na&Url=index.asp")
        end if
        ' ****** UTENTE ********************************************************
        utente = Request.QueryString("user_id")           
        if utente = "" then
            utente = "0"
        else
            utente = rtrim(utente)
        end if
        if err then
           response.redirect ("../errore.asp?Descrizione=Errore+nella+ricerca+dei+parametri+di+autenticazione+automatici&Numero=na&Url=index.asp")
        end if
         ' **** DITTA **********************************************************
        ditta = Request.QueryString("company_id")        
        if ditta = "" then
            ditta = "0"
        else
            ditta = rtrim(ditta)
        end if
        if err then
           response.redirect ("../errore.asp?Descrizione=Errore+nella+ricerca+dei+parametri+di+autenticazione+automatici+per+la+ditta&Numero=na&Url=index.asp")
        end if

        selezioneutente = "SELECT * FROM Utenti WHERE ID_utente = " & utente 
        selezioneditta = "SELECT * FROM Ditte WHERE ID_ditta =" & ditta
        
    else ' ********* VERSIONE CARICAMENTO DA FORM DI AUTENTICAZIONE **********
        ' controllo se il programma viene attivato con la versione breve
        if Request.Form("chkRidotto")="1" then 
            Session("Ridotto")=TRUE
        else
            Session("Ridotto")=FALSE
        end if   
              
        ' **** UTENTE **********************************************************
        utente = Request.Form("txtUserName")              
        if utente = "" then
            utente = "*"
        else
            utente = rtrim(utente)
        end if
        password = Request.Form("txtPassword")
        ' **** DITTA ***********************************************************
        if password = "" then
            password = "*"
        else
            password = rtrim(password)
        end if
        ditta = cstr(request.form("cboDitta")) 
        if err then
           response.redirect ("../errore.asp?Descrizione=Errore+nella+ricerca+dei+parametri+di+autenticazione&Numero=na&Url=index.asp")
        end if

        selezioneutente = "SELECT * FROM Utenti WHERE uteUserName = '" & utente & "' and utePassword='" & password & "'"
        selezioneditta = "SELECT * FROM Ditte WHERE ID_ditta=" & ditta
    end if ' automatica    

    ' *************************** PARTE COMUNE DI CARICAMENTO DATI *************
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
    @import url(/docnaet/stili/homepage.css);
-->
</style>

<body bgcolor="#FFFFFF" text="#000000">
<% 
    'Costanti del programma
    'const SUCCESS = 0
    'const ERROR = 1
    'const WARNING = 2
    'const INFORMATION = 4
    'const AUDIT_SUCCESS = 8
    'const AUDIT_FAILURE = 16

    if utenti.EOF then ' non c'è quell'utente o password errata
    '   dim WshShell
    '   set WshShell = Server.CreateObject("WScript.Shell")
    '   wshshell.Logevent AUDIT_FAILURE, "User: " + utente + " failed to log!" + vbcr + " - date: " + Cstr(date) +vbcr + " - time: " + Cstr(time) +vbcr + " - Remote IP: " + Request.ServerVariables("REMOTE_HOST") 
    '   set wshshell=nothing
%>
        <p align="center"><b><font color="#FF0000">Utente inesistente o password errata</font></b></p>
        <p align="center"><a href="../index.asp"><img src="../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></p>
  <%
    else
        ' *** Settaggio parametri per autorizzare le navigazioni successive: ***
        ' > parte comune alle due modalità:
        Session("UserName") = utenti("uteUserName")
        Session("UserID") = utenti("ID_utente")
	    Session("UserDescription") = utenti("uteDescrizione")
        Session("IsAutenticated") = TRUE
        Session("ISAdministrator") = utenti("uteAdministrator")
	    Session("Level") = utenti("uteLivello")
	    Session("IDDitta") = ditta ' ditte("ID_ditta") 'request.form("cboDitta") ' memorizzo la ditta di riferimento
	    Session("ditRagioneSociale") = ditte("ditRagioneSociale")
	    Session("Password") = utenti("utePassword") ' request.form("txtPassword")
	    Session("Configurazione") = utenti("uteConfigurazione")
	    Session("IPAddress") = Request.ServerVariables("REMOTE_HOST") 
	    Session("Gestore") = utenti("uteGestore")
	    
	    ' *************** Caricamento da form: *********************************
        if automatica then ' **** Caricamento rapido ***************************        
            'response.redirect("protette/menu/documenti/modifica.asp?ID_documento=" + documento_id + "&ID_cliente=" + cliente_id)
            response.redirect("protette/automatico.asp?ID_documento=" + documento_id + "&ID_cliente=" + cliente_id)
        else ' *************** Caricamento home page ***************************
            response.redirect("protette/homepage.asp")
        end if    
    end if
%>
</body>
</html>
<%
    utenti.Close()
    ditte.close()
%>
