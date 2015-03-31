<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/librerie/codice/icone.asp" -->
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
' *** Update Record: set variables

If (CStr(Request("MM_update")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Documenti"
  MM_editColumn = "ID_documento"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "documenti.asp"
  MM_fieldsStr  = "cboID_tipologia|value|txtDocData|value|txtDocNumero|value|txtDocFax|value|cboID_lingua|value|txtDocOggetto|value|txtDocDescrizione|value|txtDocNote|value|cboID_cliente|value|select|value|txtDocAccesso|value"
  MM_columnsStr = "ID_tipologia|none,none,NULL|docData|',none,NULL|docNumero|none,none,NULL|docFax|none,none,NULL|ID_lingua|none,none,NULL|docOggetto|',none,''|docDescrizione|',none,''|docNote|',none,''|ID_cliente|none,none,NULL|ID_prodotto|none,none,NULL|docAccesso|none,none,NULL"

  ' create the MM_fields and MM_columns arrays
  MM_fields = Split(MM_fieldsStr, "|")
  MM_columns = Split(MM_columnsStr, "|")
  
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
' *** Update Record: construct a sql update statement and execute it

If (CStr(Request("MM_update")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  ' create the sql update statement
  MM_editQuery = "update " & MM_editTable & " set "
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
      MM_editQuery = MM_editQuery & ","
    End If
    MM_editQuery = MM_editQuery & MM_columns(i) & " = " & FormVal
  Next
  MM_editQuery = MM_editQuery & " where " & MM_editColumn & " = " & MM_recordId

  If (Not MM_abortEdit) Then
    ' execute the update
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
Dim DettaglioDoc__MMColParam
DettaglioDoc__MMColParam = "1"
if (Request.QueryString("ID_documento") <> "") then DettaglioDoc__MMColParam = Request.QueryString("ID_documento")
%>
<%
set DettaglioDoc = Server.CreateObject("ADODB.Recordset")
DettaglioDoc.ActiveConnection = MM_SQLDocnaet_STRING
DettaglioDoc.Source = "SELECT * FROM Documenti WHERE ID_documento = " + DettaglioDoc__MMColParam 'Replace(DettaglioDoc__MMColParam, "'", "''") + ""
DettaglioDoc.CursorType = 0
DettaglioDoc.CursorLocation = 2
DettaglioDoc.LockType = 3
DettaglioDoc.Open()
DettaglioDoc_numRows = 0
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
<script type="text/javascript" language="JavaScript">
<!--
// *********************************** FUNZIONE PER CONFERMA ELIMINAZIONE ********************************++
function ImpostaValore()
{
   frmModifica.cboID_cliente.value=parent.fraCliente.frmTrovaClienti.cboClienteSel.options[parent.fraCliente.frmTrovaClienti.cboClienteSel.selectedIndex].value;
}

function Conferma(Domanda) 
{
   var risposta;
   risposta=confirm(Domanda);
   ImpostaValore();
   return risposta;
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
<%
   dim NomeFilePuntato, Puntatore
   NomeFilePuntato=getNomeFile(DettaglioDoc.Fields.Item("ID_documento"),DettaglioDoc.Fields.Item("ID_protocollo"),Session("IDDitta"),DettaglioDoc.Fields.Item("ID_supporto"),DettaglioDoc.Fields.Item("docFile"),DettaglioDoc.Fields.Item("docEstensione"), Puntatore)
%>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmModifica" target="_parent">
  <table width="100%" border="0" bordercolor="#666666" cellpadding="0">
    <tr> 
      <td width="12%" bgcolor="#FFFFCC" rowspan="2"><b>Protocollazione:</b></td>
      <td bgcolor="#CEECFD" colspan="2"> &nbsp;protocollo: <b><font color="#990000"> 
        <% While (NOT Protocolli.EOF)
  if ((Protocolli.Fields.Item("ID_protocollo").Value) -(DettaglioDoc.Fields.Item("ID_protocollo").Value)=0) then 
     Response.Write(Protocolli.Fields.Item("proDescrizione").Value)
  end if	 
  Protocolli.MoveNext()
Wend
If (Protocolli.CursorType > 0) Then
  Protocolli.MoveFirst
Else
  Protocolli.Requery
End If
%>
        &nbsp;</font></b><br>
      </td>
      <td width="7%" bgcolor="#CEECFD"> &nbsp;tipologia </td>
      <td width="43%" bgcolor="#CEECFD"> 
        <select name="cboID_tipologia">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Tipologia.EOF)
%>
          <option value="<%=(Tipologia.Fields.Item("ID_tipologia").Value)%>" <%if ((Tipologia.Fields.Item("ID_tipologia").Value) -(DettaglioDoc.Fields.Item("ID_tipologia").Value)=0) then Response.Write("SELECTED") : Response.Write("")%> ><%=(Tipologia.Fields.Item("tipDescrizione").Value)%></option>
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
      <td bgcolor="#CEECFD" colspan="2">&nbsp;data 
        <input value="<%=(DettaglioDoc.Fields.Item("docData").Value)%>" type="text" name="txtDocData" size="14">
        &nbsp;&nbsp;&nbsp;&nbsp;n. 
        <input value="<%=(DettaglioDoc.Fields.Item("docNumero").Value)%>" type="text" name="txtDocNumero" size="6">
        &nbsp;&nbsp;&nbsp;fax. 
        <input value="<%=(DettaglioDoc.Fields.Item("docFax").Value)%>" type="text" name="txtDocFax" size="6">
      </td>
      <td bgcolor="#CEECFD" width="7%">&nbsp;lingua </td>
      <td bgcolor="#CEECFD" width="43%"> 
        <select name="cboID_lingua">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Lingua.EOF)
%>
          <option value="<%=(Lingua.Fields.Item("ID_lingua").Value)%>" <%if ((Lingua.Fields.Item("ID_lingua").Value) -(DettaglioDoc.Fields.Item("ID_lingua").Value)=0) then Response.Write("SELECTED") : Response.Write("")%> ><%=(Lingua.Fields.Item("linDescrizione").Value)%></option>
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
      <td bgcolor="#CEECFD" width="8%" valign="top"> &nbsp;oggetto </td>
      <td bgcolor="#CEECFD" colspan="3"> 
        <textarea name="txtDocOggetto" cols="80" rows="3"><%=(DettaglioDoc.Fields.Item("docOggetto").Value)%></textarea>
      </td>
    </tr>
    <tr> 
      <td bgcolor="#CEECFD" width="8%" valign="top"> &nbsp;descrizione </td>
      <td bgcolor="#CEECFD" colspan="3"> 
        <textarea name="txtDocDescrizione" cols="80" rows="3"><%=(DettaglioDoc.Fields.Item("docDescrizione").Value)%></textarea>
      </td>
    </tr>
    <tr> 
      <td bgcolor="#CEECFD" width="8%" valign="top"> &nbsp;note </td>
      <td bgcolor="#CEECFD" colspan="3"> 
        <textarea name="txtDocNote" cols="80" rows="3"><%=(DettaglioDoc.Fields.Item("docNote").Value)%></textarea>
      </td>
    </tr>
    <%if GestisceProdotti then %>
    <tr> 
      <td width="12%" bgcolor="#FFFFCC"><b>Prodotto:</b></td>
      <td colspan="4" bgcolor="#CEECFD"> &nbsp; 
        <select name="select">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Prodotti.EOF)
%>
          <option value="<%=(Prodotti.Fields.Item("ID_prodotto").Value)%>" <%if ((Prodotti.Fields.Item("ID_prodotto").Value) -(DettaglioDoc.Fields.Item("ID_prodotto").Value)=0) then Response.Write("SELECTED") : Response.Write("")%> ><%=(Prodotti.Fields.Item("proDescrizione").Value)%></option>
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
      <td width="12%" bgcolor="#FFFFCC"><b>Accesso liv.:</b></td>
      <td colspan="4" bgcolor="#CEECFD"> &nbsp; 
        <input value="<%=(DettaglioDoc.Fields.Item("docAccesso").Value)%>" type="text" name="txtDocAccesso" size="5">
        <%if not GestisceProdotti then %>
        <input type="hidden" name="select" value="<%=DettaglioDoc.Fields.Item("ID_prodotto").Value %>">
        <% end if %>
        <input type="hidden" name="cboID_cliente" value="<%=(DettaglioDoc.Fields.Item("ID_cliente").Value)%>">
      </td>
    </tr>
    <tr bgcolor="#999999" align="center"> 
      <td colspan="5"> 
        <input type="hidden" name="MM_recordId" value="<%= DettaglioDoc.Fields.Item("ID_documento").Value %>">
        <input type="hidden" name="MM_update" value="true">
        <input type="image" border="0" name="imgAggiorna" src="../../../../immagini/sistema/bottoni/icone/aggiorna.gif" width="30" height="30" alt="Aggiorna i dati..."  onClick="return Conferma('Confermi l\'aggiornamento dell\'elemento?');">
      </td>
    </tr>
  </table>
  </form>
<table width="100%" border="0" height="58">
  <tr bgcolor="#999999" align="center"> 
    <td width="68" valign="middle" align="center"> <a href="file://<%=NomeFilePuntato%>" target="_blank"><img src="<%=GetImmagine(DettaglioDoc.Fields.Item("docEstensione").value, Puntatore)%>" width="20" height="20" border="0" alt="Apri documento..." name="imgNuovo"></a>&nbsp; 
    </td>
    <td width="237" valign="middle"> 
      <%  if ((ucase(DettaglioDoc.Fields.Item("docEstensione").value)= "DOC") or DettaglioDoc.Fields.Item("docFax").value=0) then %>
      <form name="frmRicarica" method="post" action="operazioni.asp" target="_parent">
        <table width="100%" border="0" cellpadding="0" cellspacing="0">
          <tr bgcolor="#999999"> 
            <td rowspan="2" width="17%" valign="top"> 
              <input type="image" border="0" name="imgRicarica" src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="20" height="20" alt="Opera sul documento...">
              <input type="hidden" name="hidID_Documento" value="<%= DettaglioDoc.Fields.Item("ID_documento").Value %>">
              <input type="hidden" name="hidNomeFile" value="<%=NomeFilePuntato%>">
            </td>
            <td width="83%"> 
              <% if (ucase(DettaglioDoc.Fields.Item("docEstensione").value)= "DOC") then %>
              <input type="checkbox" name="chkRicarica" value="chkRicarica" <% if ModificaCheck(1) then Response.Write("checked") %>>
              <font color="#FFFFCC">Ricarica intestazione</font> 
              <% else %>
              <font color="#FFFFCC">Intestazione non gestita</font> 
              <% end if %>
            </td>
          </tr>
          <tr> 
            <td width="83%" bgcolor="#999999"> 
              <% if (DettaglioDoc.Fields.Item("docFax").value=0) then  %>
              <input type="checkbox" name="chkProtocolla" value="chkProtocolla" <% if ModificaCheck(2) then Response.Write("checked") %>>
              <font color="#FFFFCC">Prot. fax</font> 
              <% else %>
              <font color="#FFFFCC">Già assengato il fax</font> 
              <% end if %>
            </td>
          </tr>
        </table>
      </form>
      <%	end if 	%>
    </td>
    <td width="309" valign="middle"> 
      <form name="frmDuplica" method="post" action="operazioni.asp" target="_parent">
        <table width="100%" border="0" height="100%" cellpadding="0" cellspacing="0">
          <tr bgcolor="#999999" bordercolor="#999999"> 
            <td rowspan="2" valign="top" width="30" align="center"> 
              <input type="image" border="0" name="imgDuplica" src="../../../../immagini/sistema/bottoni/icone/duplica.gif" width="20" height="20" alt="Duplicazione documento..." onClick="return Conferma('Confermi la duplicazione dell\'elemento?');">
              <input type="hidden" name="hidID_Documento" value="<%= DettaglioDoc.Fields.Item("ID_documento").Value %>">
              <input type="hidden" name="hidID_Cliente" value="<%= DettaglioDoc.Fields.Item("ID_cliente").Value %>">
              <input type="hidden" name="hiddocFile" value="<% if Puntatore then Response.Write(DettaglioDoc.Fields.Item("docFile").Value) else Response.Write("") %>">
              <input type="hidden" name="hidNomeFile" value="<%=NomeFilePuntato%>">
              <input type="hidden" name="hidIDProtocollo" value="<%=DettaglioDoc.Fields.Item("ID_protocollo").Value%>">
            </td>
            <td width="27" valign="top"> 
              <input type="radio" name="radiobutton" value="Duplico" checked>
              <font color="#FFFFCC"> </font></td>
            <td width="253"><font color="#FFFFCC">Con duplicazione <font color="#FFFFCC">file 
              <br>
              <input type="checkbox" name="chkRiprotocolla" value="1" <% if ModificaCheck(3) then Response.Write("checked") %>>
              <font color="#FFFFCC">Riprotocolla</font></font></font></td>
          </tr>
          <tr bgcolor="#999999" bordercolor="#999999"> 
            <td colspan="2"> 
              <input type="radio" name="radiobutton" value="NonDuplico">
              <font color="#FFFFCC"> Senza duplicazione file</font></td>
          </tr>
          <tr bgcolor="#999999" bordercolor="#999999"> 
            <td valign="top" width="30" align="center">&nbsp;</td>
            <td colspan="2">&nbsp; </td>
          </tr>
        </table>
      </form>
    </td>
    <td width="309" valign="middle" bgcolor="#999999"> 
      <form name="frmBlocca" method="post" action="operazioni.asp" target="_parent">
        <input type="image" border="0" name="imgProteggi" src="../../../../immagini/sistema/bottoni/icone/lucchetto.gif" width="16" height="20" alt="Marca il file in sola lettura" onClick="return Conferma('Confermi il blocco del file?');">
        <input type="hidden" name="hidID_Documento2" value="<%=DettaglioDoc.Fields.Item("ID_documento").Value %>">
        <input type="hidden" name="hidNomeFile2" value="<%=NomeFilePuntato%>">
      </form>
    </td>
    <td width="284" valign="middle"> 
      <form name="frmElimina" method="post" action="operazioni.asp" target="_parent">
        <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="20" alt="Elimina registrazione..." onClick="return Conferma('Confermi l\'eliminazione dell\'elemento?');">
        <input type="hidden" name="hidID_Documento" value="<%=DettaglioDoc.Fields.Item("ID_documento").Value %>">
      </form>
    </td>
    <td width="24" valign="middle"><a href="javascript:window.history.back()"><img src="../../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></td>
  </tr>
</table>
</body>
</html>
<%
DettaglioDoc.Close()
%>
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
if GestisceProdotto then Prodotti.Close()
%>
