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
  MM_editTable = "Tipologie"
  MM_editColumn = "ID_tipologia"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "tconferma.asp"
  MM_fieldsStr  = "txtDescrizione|value|txtNote|value"
  MM_columnsStr = "tipDescrizione|',none,''|tipNote|',none,''"

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
Dim Tipologie__MMColParam
Tipologie__MMColParam = "1"
if (Request.QueryString("ID_tipologia") <> "") then Tipologie__MMColParam = Request.QueryString("ID_tipologia")
%>
<%
set Tipologie = Server.CreateObject("ADODB.Recordset")
Tipologie.ActiveConnection = MM_SQLDocnaet_STRING
Tipologie.Source = "SELECT * FROM Tipologie WHERE ID_tipologia = " + Replace(Tipologie__MMColParam, "'", "''") + ""
Tipologie.CursorType = 0
Tipologie.CursorLocation = 2
Tipologie.LockType = 3
Tipologie.Open()
Tipologie_numRows = 0
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

function validateForm(Oggetto) { //v4.0
    if (!Oggetto.value) 
	{
	   alert ('Inserire necessariamente il nome della tipologia!');
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
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="10">
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmInserimento">
  <div align="center">
    <table width="28%" border="0" bgcolor="#CCCCCC">
      <tr>
        <td align="center"> <b><font color="#009933">Modifica Tipologia</font></b> 
        </td>
    </tr>
  </table>  <br>
</div>
  <table width="28%" border="0" align="center">
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Tipologia:</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input value="<%=(Tipologie.Fields.Item("tipDescrizione").Value)%>" type="text" name="txtDescrizione">
        <input type="hidden" name="hiddenField" value="<%=(Tipologie.Fields.Item("ID_tipologia").Value)%>">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Note:</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input value="<%=(Tipologie.Fields.Item("tipNote").Value)%>" type="text" name="txtNote">
      </td>
    </tr>
  </table>
  <div align="center"><br>
  </div>
  <table width="28%" border="0" align="center">
    <tr bgcolor="#CCCCCC"> 
      <td align="center"> 
        <input type="submit" name="Submit" value="Aggiorna" onClick="return validateForm(txtDescrizione);">
      </td>
      <td align="center"> 
        <input type="reset" name="Submit2" value="Ripresenta">
      </td>
      <td align="center"> 
        <input type="button" name="Submit3" value="Annulla" onClick="goToURL('tipologie.asp');return false">
      </td>
    </tr>
  </table>

  <input type="hidden" name="MM_update" value="true">
  <input type="hidden" name="MM_recordId" value="<%= Tipologie.Fields.Item("ID_tipologia").Value %>">
</form>
</body>
</html>
<%
Tipologie.Close()
%>

