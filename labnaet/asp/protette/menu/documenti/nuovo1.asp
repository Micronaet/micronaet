<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/gestione.asp" -->
<%
' *** Edit Operations: declare variables
MM_editAction = CStr(Request("URL"))
If (Request.QueryString <> "") Then
  MM_editAction = MM_editAction & "?" & Request.QueryString
End If
' boolean to abort record edit
MM_abortEdit = false

' query string to execute
MM_editQuery = ""
%>
<%
' *** Insert Record: set variables
If (CStr(Request("MM_insert")) <> "") Then
  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Documenti"
  MM_editRedirectUrl = "afternew.asp"
  MM_fieldsStr  = "txtDocData|value|cboID_tipologia|value|cboProtocollo|value|cboID_lingua|value|txtDocOggetto|value|txtDocDescrizione|value|txtDocNote|value|cboID_cliente|value|select|value|txtDocAccesso|value|hidTimeStamp|value|hidID_azienda|value|hinIDUtete|value|cboApplicazione|value"
  MM_columnsStr = "docData|',none,NULL|ID_tipologia|none,none,NULL|ID_protocollo|none,none,NULL|ID_lingua|none,none,NULL|docOggetto|',none,''|docDescrizione|',none,''|docNote|',none,''|ID_cliente|none,none,NULL|ID_prodotto|none,none,NULL|docAccesso|none,none,NULL|docControllo|',none,''|docAzienda|none,none,NULL|ID_utente|none,none,NULL|docEstensione|',none,''"
  ' create the MM_fields and MM_columns arrays
  MM_fields = Split(MM_fieldsStr, "|")
  MM_columns = Split(MM_columnsStr, "|")
  ' memorizzo nella variabile di sessione il time stamp della videata
  dim t1, t2, t3
  
  if Request.Form("chkIntestazione")="s" then t1="1" else t1="0" 
  if Request.Form("chkNumera")="s" then t2="1" else t2="0"     
  if Request.Form("chkNumeraFax")="s" then t3="1" else t3="0" 
  '                    TIME STAMP                      NUMERA    PROTOCOLLO                       INTEST.  FAX
  Session("TimeStamp")=Request.Form("hidTimeStamp") +"|"+t2+"|"+ Request.Form("cboProtocollo") + "|"+t1+"|"+t3
  ' set the form values
  For i = LBound(MM_fields) To UBound(MM_fields) Step 2
     MM_fields(i+1) = CStr(Request.Form(MM_fields(i)))
  Next
  ' append the query string to the redirect URL
  If (MM_editRedirectUrl <> "" And Request.QueryString <> "") Then
    If (InStr(1, MM_editRedirectUrl, "?", vbTextCompare) = 0 And Request.QueryString <> "") Then
      MM_editRedirectUrl = MM_editRedirectUrl & "?" & Request.QueryString
    Else
      MM_editRedirectUrl = MM_editRedirectUrl & "&" & Request.QueryString
    End If
  End If
End If
%>
<%
' *** Insert Record: construct a sql insert statement and execute it
If (CStr(Request("MM_insert")) <> "") Then
  ' create the sql insert statement
  MM_tableValues = ""
  MM_dbValues = ""
  For i = LBound(MM_fields) To UBound(MM_fields) Step 2
    FormVal = MM_fields(i+1)
    MM_typeArray = Split(MM_columns(i+1),",")
    Delim = MM_typeArray(0)
    If (Delim = "none") Then Delim = ""
    AltVal = MM_typeArray(1)
    If (AltVal = "none") Then AltVal = ""
    EmptyVal = MM_typeArray(2)
    If (EmptyVal = "none") Then EmptyVal = ""
    If (FormVal = "") Then
      FormVal = EmptyVal
    Else
      If (AltVal <> "") Then
        FormVal = AltVal
      ElseIf (Delim = "'") Then  ' escape quotes
        FormVal = "'" & Replace(FormVal,"'","''") & "'"
      Else
        FormVal = Delim + FormVal + Delim
      End If
    End If
    If (i <> LBound(MM_fields)) Then
      MM_tableValues = MM_tableValues & ","
      MM_dbValues = MM_dbValues & ","
    End if
    MM_tableValues = MM_tableValues & MM_columns(i)
    MM_dbValues = MM_dbValues & FormVal
  Next
  MM_editQuery = "insert into " & MM_editTable & " (" & MM_tableValues & ") values (" & MM_dbValues & ")"
  If (Not MM_abortEdit) Then
    ' execute the insert
    Set MM_editCmd = Server.CreateObject("ADODB.Command")
    MM_editCmd.ActiveConnection = MM_editConnection
    MM_editCmd.CommandText = MM_editQuery
    MM_editCmd.Execute
    MM_editCmd.ActiveConnection.Close

    If (MM_editRedirectUrl <> "") Then
      Response.Redirect(MM_editRedirectUrl)
    End If
  End If
End If
%>

<%
set Lingua = Server.CreateObject("ADODB.Recordset")
Lingua.ActiveConnection = MM_SQLDocnaet_STRING
Lingua.Source = "SELECT ID_lingua, linDescrizione, linNote FROM Lingue ORDER BY linDescrizione ASC"
Lingua.CursorType = 0
Lingua.CursorLocation = 2
Lingua.LockType = 3
Lingua.Open()
Lingua_numRows = 0
%>
<%
set Tipologia = Server.CreateObject("ADODB.Recordset")
Tipologia.ActiveConnection = MM_SQLDocnaet_STRING
Tipologia.Source = "SELECT * FROM Tipologie ORDER BY tipDescrizione ASC"
Tipologia.CursorType = 0
Tipologia.CursorLocation = 2
Tipologia.LockType = 3
Tipologia.Open()
Tipologia_numRows = 0
%>
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
set Applicazioni = Server.CreateObject("ADODB.Recordset")
Applicazioni.ActiveConnection = MM_SQLDocnaet_STRING
Applicazioni.Source = "SELECT * FROM Applicazioni ORDER BY ID_applicazione ASC"
Applicazioni.CursorType = 0
Applicazioni.CursorLocation = 2
Applicazioni.LockType = 3
Applicazioni.Open()
Applicazioni_numRows = 0
%>
<%
if GestisceProdotti then
%>
<%
Dim Prodotti__MMColParam
Prodotti__MMColParam = "1"
if (Session("IDditta") <> "") then Prodotti__MMColParam = Session("IDditta")
%>
<%
set Prodotti = Server.CreateObject("ADODB.Recordset")
Prodotti.ActiveConnection = MM_SQLDocnaet_STRING
Prodotti.Source = "SELECT * FROM Prodotti WHERE ID_ditta = " + Replace(Prodotti__MMColParam, "'", "''") + " ORDER BY proDescrizione ASC"
Prodotti.CursorType = 0
Prodotti.CursorLocation = 2
Prodotti.LockType = 3
Prodotti.Open()
Prodotti_numRows = 0
%>
<%
end if
%>
<html>
<head>
<title>Dettaglio</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript" type="text/javascript">
<!--
function ImpostaValore()
{
   frmModifica.cboID_cliente.value=parent.fraCliente.frmTrovaClienti.cboClienteSel.options[parent.fraCliente.frmTrovaClienti.cboClienteSel.selectedIndex].value;
}

function ValidateForm()
{
   if (isNaN(document.frmModifica.txtDocAccesso.value) ) 
   {
	  alert ("Inserire il livello di accesso!");
	  return false;	  
   }
   else
   {
       if (document.frmModifica.txtDocAccesso.value<0 || document.frmModifica.txtDocAccesso.value>10) 
	   {
	      alert ("Il livello di accesso deve essere per forza compreso tra 0 e 10!");
		  return false;
	   }
	   else
	   {
	       if (document.frmModifica.cboProtocollo.value=="" || document.frmModifica.cboProtocollo.value=="0")
		   {
		       alert ("Inserire necessariamente il protocollo!");
			   return false;
		   }
		   else
		   {
		       if (!(document.frmModifica.txtDocData.value))
			   {
			      // mettere il codice per effettuare la verifica della data!
			      alert ("Inserire la data di protocollazione del documento!");
				  return false;
			   }  
			   else
			   {
			      ImpostaValore(); // metto l'ID eventuale del cliente
			      // posso effettuare l'inserimento
			      return true;
			   }	  
		   }
	   } 
   }	       
}

function SetData(Elemento)
{
  var d = new Date();
  Elemento.value= d.getDate() + "/" + (d.getMonth()+1)  + "/" + d.getYear();
}

//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" topmargin="1" leftmargin="1">
  <table width="100%" border="0" bordercolor="#666666" cellpadding="0">
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmModifica" target="_parent">
    <tr> 
      <td colspan="5"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"> 
          &nbsp;&nbsp;Informazioni documento &nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"></b></div>
      </td>
    </tr>
    <tr> 
      <td width="12%" bgcolor="#FFFFCC" rowspan="2"> <b>Protocollazione:</b> <br>
      </td>
      <td bgcolor="#CEECFD" rowspan="2" width="10%"> 
        <input type="checkbox" name="chkNumera" value="s" <% if InserimentoCheck(1) then Response.Write("checked") %>>
        Numera <br>
        <input type="checkbox" name="chkNumeraFax" value="s" <% if InserimentoCheck(2) then Response.Write("checked") %>>
        Fax <br>
        <input type="checkbox" name="chkIntestazione" value="s" <% if InserimentoCheck(3) then Response.Write("checked") %>>
        Intestazione <br>
      </td>
      <td bgcolor="#CEECFD" width="30%">&nbsp;data * 
        <input type="text" name="txtDocData" size="14" value="<%=date()%>" onDblClick="SetData(this);">
      </td>
      <td width="7%" bgcolor="#CEECFD"> &nbsp;tipologia </td>
      <td width="41%" bgcolor="#CEECFD"> 
        <select name="cboID_tipologia">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Tipologia.EOF)
%>
          <option value="<%=(Tipologia.Fields.Item("ID_tipologia").Value)%>"><%=(Tipologia.Fields.Item("tipDescrizione").Value)%></option>
          <%
  Tipologia.MoveNext()
Wend
If (Tipologia.CursorType > 0) Then
  Tipologia.MoveFirst
Else
  Tipologia.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr> 
      <td bgcolor="#CEECFD" width="30%">&nbsp;protocollo * 
        <select name="cboProtocollo">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Protocolli.EOF)
%>
          <option value="<%=(Protocolli.Fields.Item("ID_protocollo").Value)%>"><%=(Protocolli.Fields.Item("proDescrizione").Value)%></option>
          <%
  Protocolli.MoveNext()
Wend
If (Protocolli.CursorType > 0) Then
  Protocolli.MoveFirst
Else
  Protocolli.Requery
End If
%>
        </select>
      </td>
      <td width="7%" bgcolor="#CEECFD">&nbsp;lingua </td>
      <td width="41%" bgcolor="#CEECFD"> 
        <select name="cboID_lingua">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Lingua.EOF)
%>
          <option value="<%=(Lingua.Fields.Item("ID_lingua").Value)%>"><%=(Lingua.Fields.Item("linDescrizione").Value)%></option>
          <%
  Lingua.MoveNext()
Wend
If (Lingua.CursorType > 0) Then
  Lingua.MoveFirst
Else
  Lingua.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr> 
      <td rowspan="3" bgcolor="#FFFFCC" valign="top" width="12%"><b><br>
        Dettagli:</b></td>
      <td width="10%" bgcolor="#CEECFD" valign="top"> &nbsp;oggetto </td>
      <td bgcolor="#CEECFD" colspan="3"> 
        <textarea name="txtDocOggetto" cols="80" rows="3"></textarea>
      </td>
    </tr>
    <tr> 
      <td width="10%" bgcolor="#CEECFD" valign="top"> &nbsp;descrizione </td>
      <td colspan="3" bgcolor="#CEECFD"> 
        <textarea name="txtDocDescrizione" cols="80" rows="3"></textarea>
      </td>
    </tr>
    <tr> 
      <td width="10%" bgcolor="#CEECFD" valign="top"> &nbsp;note </td>
      <td colspan="3" bgcolor="#CEECFD"> 
        <textarea name="txtDocNote" cols="80" rows="3"></textarea>
        <input type="hidden" name="cboID_cliente" value="0">
      </td>
    </tr>
    <% if GestisceProdotti then %>
    <tr> 
      <td width="12%" bgcolor="#FFFFCC"><b>Prodotto:</b></td>
      <td colspan="4" bgcolor="#CEECFD"> &nbsp; 
        <select name="select">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Prodotti.EOF)
%>
          <option value="<%=(Prodotti.Fields.Item("ID_prodotto").Value)%>"><%=(Prodotti.Fields.Item("proDescrizione").Value)%></option>
          <%
  Prodotti.MoveNext()
Wend
If (Prodotti.CursorType > 0) Then
  Prodotti.MoveFirst
Else
  Prodotti.Requery
End If
%>
        </select>
      </td>
    </tr>
    <% end if %>
    <tr> 
      <td width="12%" bgcolor="#FFFFCC"><b>Accesso liv.*:</b></td>
      <td bgcolor="#CEECFD" colspan="2"> &nbsp; 
        <input type="text" name="txtDocAccesso" size="5" value="0">
        <input type="hidden" name="hidTimeStamp" value="<%=Now()%>">
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 
        <input type="hidden" name="hidID_azienda" value="<%=Session("IDDitta")%>">
        <input type="hidden" name="hinIDUtete" value="<%=Session("UserID")%>">
      </td>
      <td bgcolor="#CEECFD" colspan="2"> Applicazione 
        <select name="cboApplicazione">
          <%
While (NOT Applicazioni.EOF)
%>
          <option value="<%=(Applicazioni.Fields.Item("appEstensione").Value)%>"><%=(Applicazioni.Fields.Item("appNome").Value)%></option>
          <%
  Applicazioni.MoveNext()
Wend
If (Applicazioni.CursorType > 0) Then
  Applicazioni.MoveFirst
Else
  Applicazioni.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr align="center" bgcolor="#CEECFD"> 
      <td colspan="5"> 
        <input type="image" border="0" name="imgAggiorna" src="../../../../immagini/sistema/bottoni/icone/aggiorna.gif" width="30" height="30" alt="Aggiorna i dati..." onClick="return ValidateForm();">
        <input type="hidden" name="MM_insert" value="true">
      </td>
    </tr>
</form>  </table>

<table width="100%" border="0">
  <tr> 
    <td bgcolor="#999999" height="30"> 
      <div align="right"><a href="javascript:window.history.back()"><img src="../../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></div>
    </td>
  </tr>
</table>
</body>
</html>

<%
Lingua.Close()
%>
<%
Tipologia.Close()
%>
<%
Protocolli.Close()
%>
<%
Applicazioni.Close()
%>
<%
if GestisceProdotto then Prodotti.Close()%>

