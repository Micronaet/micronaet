<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
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
  MM_editTable = "Clienti"
  MM_editColumn = "ID_cliente"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "ricerche.asp"
  MM_fieldsStr  = "textfield|value|textfield2|value|textfield3|value|textfield4|value|textfield5|value|select2|value|textfield7|value|textfield8|value|textfield9|value|select|value|textfield6|value"
  MM_columnsStr = "cliRagioneSociale|',none,''|cliIndirizzo|',none,''|cliCAP|',none,''|cliPaese|',none,''|cliProvincia|',none,''|ID_nazione|none,none,NULL|cliTelefono|',none,''|cliFax|',none,''|cliEmail|',none,''|ID_tipo|none,none,NULL|cliCodice|',none,''"

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
' *** Delete Record: declare variables

if (CStr(Request("MM_delete")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Clienti"
  MM_editColumn = "ID_cliente"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "cconferma.asp"

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
' *** Delete Record: construct a sql delete statement and execute it

If (CStr(Request("MM_delete")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  ' create the sql delete statement
  MM_editQuery = "delete from " & MM_editTable & " where " & MM_editColumn & " = " & MM_recordId

  If (Not MM_abortEdit) Then
    ' execute the delete
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
Dim Clienti__MMColParam
Clienti__MMColParam = "1"
if (Request.QueryString("ID_cliente") <> "") then Clienti__MMColParam = Request.QueryString("ID_cliente")
%>
<%
Dim Clienti__MMColParam1
Clienti__MMColParam1 = "1"
if (Session("IDDitta") <> "") then Clienti__MMColParam1 = Session("IDDitta")
%>
<%
set Clienti = Server.CreateObject("ADODB.Recordset")
Clienti.ActiveConnection = MM_SQLDocnaet_STRING
Clienti.Source = "SELECT *  FROM Clienti  WHERE (ID_cliente = " + Replace(Clienti__MMColParam, "'", "''") + ") and (ID_ditta = " + Replace(Clienti__MMColParam1, "'", "''") + ")"
Clienti.CursorType = 0
Clienti.CursorLocation = 2
Clienti.LockType = 3
Clienti.Open()
Clienti_numRows = 0
%>
<%
set Tipo = Server.CreateObject("ADODB.Recordset")
Tipo.ActiveConnection = MM_SQLDocnaet_STRING
Tipo.Source = "SELECT * FROM Tipi ORDER BY tipDescrizione ASC"
Tipo.CursorType = 0
Tipo.CursorLocation = 2
Tipo.LockType = 3
Tipo.Open()
Tipo_numRows = 0
%>
<%
set Nazione = Server.CreateObject("ADODB.Recordset")
Nazione.ActiveConnection = MM_SQLDocnaet_STRING
Nazione.Source = "SELECT * FROM Nazioni ORDER BY nazDescrizione ASC"
Nazione.CursorType = 0
Nazione.CursorLocation = 2
Nazione.LockType = 3
Nazione.Open()
Nazione_numRows = 0
%>
<html>
<head>
<title>Dettaglio Cliente</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script type="text/javascript" language="JavaScript">
<!--
// *********************************** FUNZIONE PER CONFERMA ELIMINAZIONE ********************************++
function Conferma(Domanda) 
{
   if (!frmUpdate.textfield.value)
   {
       alert('Inserire almeno la Ragione sociale!');
       return false;
   }
   else
   {
       var risposta;
       risposta=confirm(Domanda);
       return risposta;
   }
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="4"> 
      <div align="center"><b><font color="#FFFFCC">Dettaglio Cliente</font></b></div>
    </td>
  </tr>
  <tr> 
    <td width="25%" height="29">&nbsp; </td>
    <td width="25%" height="29">&nbsp;</td>
    <td width="25%" height="29">&nbsp;</td>
    <td width="25%" height="29" align="center"> 
      <form name="frmElimina" method="POST" action="<%=MM_editAction%>">
        <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="24" height="24" alt="Elimina ditta..." onClick="return Conferma('Confermi l\'eliminazione della ditta?');">
        <input type="hidden" name="MM_delete" value="true">
        <input type="hidden" name="MM_recordId" value="<%= Clienti.Fields.Item("ID_cliente").Value %>">
      </form>
    </td>
  </tr>
</table>
<br>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmUpdate">
  <table width="69%" border="0" align="center" height="71">
    <tr bgcolor="#CCCCCC"> 
      <td colspan="6"> 
        <div align="center"><b><font color="#990000">Modifica Cliente</font></b></div>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD"> 
        <div align="left">Ragione Sociale</div>
      </td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <div align="left"> 
          <input value="<%=(Clienti.Fields.Item("cliRagioneSociale").Value)%>" type="text" name="textfield" size="40">
        </div>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td rowspan="3" bgcolor="#CEECFD">Indirizzo</td>
      <td bgcolor="#CCCCCC"><font color="#006633">Via</font></td>
      <td bgcolor="#FFFFCC"> 
        <input value="<%=(Clienti.Fields.Item("cliIndirizzo").Value)%>" type="text" name="textfield2" size="40">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="17%" height="22" valign="middle" bgcolor="#CCCCCC"> <font color="#006633">Cap, 
        Paese, Prov.<br>
        </font></td>
      <td width="64%" height="22" valign="top" bgcolor="#FFFFCC"> 
        <input value="<%=(Clienti.Fields.Item("cliCAP").Value)%>" type="text" name="textfield3" size="6">
        <input value="<%=(Clienti.Fields.Item("cliPaese").Value)%>" type="text" name="textfield4" size="30">
        <input value="<%=(Clienti.Fields.Item("cliProvincia").Value)%>" type="text" name="textfield5" size="6">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="17%" height="22" valign="middle" bgcolor="#CCCCCC"><font color="#006633">Nazione 
        </font></td>
      <td width="64%" height="22" valign="top" bgcolor="#FFFFCC"> 
        <select name="select2">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Nazione.EOF)
%>
          <option value="<%=(Nazione.Fields.Item("ID_nazione").Value)%>" <%if ((Nazione.Fields.Item("ID_nazione").Value) = (Clienti.Fields.Item("ID_nazione").Value)) then Response.Write("SELECTED")%> ><%=(Nazione.Fields.Item("nazDescrizione").Value)%></option>
          <%
  Nazione.MoveNext()
Wend
If (Nazione.CursorType > 0) Then
  Nazione.MoveFirst
Else
  Nazione.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD">Telefono</td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <input value="<%=(Clienti.Fields.Item("cliTelefono").Value)%>" type="text" name="textfield7" size="30">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD">Fax</td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <input value="<%=(Clienti.Fields.Item("cliFax").Value)%>" type="text" name="textfield8" size="30">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD">E-mail</td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <input value="<%=(Clienti.Fields.Item("cliEmail").Value)%>" type="text" name="textfield9" size="30">
        &nbsp; 
        <% if ""<>(Clienti.Fields.Item("cliEmail").Value) then %>
        <a href="mailto:<%=(Clienti.Fields.Item("cliEmail").Value)%>"><img src="../../../../immagini/sistema/bottoni/icone/posta.gif" width="32" height="32" border="0"></a> 
        <%
		   end if
		%>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD">Tipo</td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <select name="select">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Tipo.EOF)
%>
          <option value="<%=(Tipo.Fields.Item("ID_tipo").Value)%>" <%if ((Tipo.Fields.Item("ID_tipo").Value) = (Clienti.Fields.Item("ID_tipo").Value)) then Response.Write("SELECTED") %> ><%=(Tipo.Fields.Item("tipDescrizione").Value)%></option>
          <%
  Tipo.MoveNext()
Wend
If (Tipo.CursorType > 0) Then
  Tipo.MoveFirst
Else
  Tipo.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="19%" bgcolor="#CEECFD">Codice gest.</td>
      <td bgcolor="#FFFFCC" colspan="2"> 
        <input value="<%=(Clienti.Fields.Item("cliCodice").Value)%>" type="text" name="textfield6" size="20">
      </td>
    </tr>
  </table>
  <p align="center"> 
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/icone/aggiorna.gif" width="31" height="32"onClick="return Conferma('Confermi l\'aggiornamento della ditta?');">
  </p>
  <input type="hidden" name="MM_update" value="true">
  <input type="hidden" name="MM_recordId" value="<%= Clienti.Fields.Item("ID_cliente").Value %>">
</form>
<table width="100%" border="0">
  <tr> 
    <td bgcolor="#999999" height="30"> 
      <div align="right"><a href="javascript:window.history.back()"><img src="../../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></div>
    </td>
  </tr>
</table>

<p><br>
</p>
<p>&nbsp;</p>
</body>
</html>
<%
Clienti.Close()
%>
<%
Tipo.Close()
%>
<%
Nazione.Close()
%>
