<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
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
  MM_editTable = "Ditte"
  MM_editColumn = "ID_ditta"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "aconferma.asp"
  MM_fieldsStr  = "txtDescrizione|value|txtNote|value|txtNote2|value"
  MM_columnsStr = "ditRagioneSociale|',none,''|ditNote|',none,''|ditPaese|',none,''"

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
Dim Aziende__MMColParam
Aziende__MMColParam = "1"
if (Request.QueryString("ID_ditta") <> "") then Aziende__MMColParam = Request.QueryString("ID_ditta")
%>
<%
set Aziende = Server.CreateObject("ADODB.Recordset")
Aziende.ActiveConnection = MM_SQLDocnaet_STRING
Aziende.Source = "SELECT * FROM Ditte WHERE ID_ditta = " + Replace(Aziende__MMColParam, "'", "''") + ""
Aziende.CursorType = 0
Aziende.CursorLocation = 2
Aziende.LockType = 3
Aziende.Open()
Aziende_numRows = 0
%>
<html>
<head>
<title>Inserimento lingua</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">
<!--
function goToURL(indirizzo) { //v3.0
  eval("document.location='"+indirizzo+"'");
}

function validateForm(Oggetto, Oggetto1) { //v4.0
    if (!(Oggetto.value && Oggetto1.value) )
	{
	   alert ('Inserire necessariamente ragione sociale e paese!');
	   return false;
    }
	else 
	{
	   return true;
	}
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="10">
<div align="center">
  <table width="52%" border="0" bgcolor="#CCCCCC">
    <tr>
      <td align="center"> <b><font color="#009933">Modifica azienda</font></b> 
      </td>
    </tr>
  </table>
</div>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmInserimento">
  <table width="52%" border="0" align="center">
    <tr> 
      <td width="21%" bgcolor="#FFFFCC">Ragione Sociale:</td>
      <td width="79%" bgcolor="#CEECFD"> 
        <input value="<%=(Aziende.Fields.Item("ditRagioneSociale").Value)%>" type="text" name="txtDescrizione" OnFocus="this.select()">
        <input type="hidden" name="hiddenField" value="<%=(Aziende.Fields.Item("ID_ditta").Value)%>">
      </td>
    </tr>
    <tr> 
      <td width="21%" bgcolor="#FFFFCC">Paese:</td>
      <td width="79%" bgcolor="#CEECFD">
        <input value="<%=(Aziende.Fields.Item("ditPaese").Value)%>" type="text" name="txtNote2" onFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="21%" bgcolor="#FFFFCC">Note:</td>
      <td width="79%" bgcolor="#CEECFD"> 
        <input value="<%=(Aziende.Fields.Item("ditNote").Value)%>" type="text" name="txtNote" onFocus="this.select()">
      </td>
    </tr>
  </table>
  <div align="center"><br>
  </div>
  <table width="52%" border="0" align="center">
    <tr bgcolor="#CCCCCC"> 
      <td align="center"> 
          <input type="submit" name="Submit" value="Aggiorna" onClick="return validateForm(txtDescrizione,txtNote2);">        
      </td>
      <td align="center"> 
          <input type="reset" name="Submit2" value="Ripresenta">        
      </td>
      <td align="center"> 
          
        <input type="button" name="Submit3" value="Annulla" onClick="goToURL('aziende.asp');return false">       
      </td>
    </tr>
  </table>
  <p> </p>
  <input type="hidden" name="MM_recordId" value="<%= Aziende.Fields.Item("ID_ditta").Value %>">
  <input type="hidden" name="MM_update" value="true">
</form>
</body>
</html>
<%
Aziende.Close()
%>
