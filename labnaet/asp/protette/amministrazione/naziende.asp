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
' *** Redirect if username exists
MM_flag="MM_insert"
If (CStr(Request(MM_flag)) <> "") Then
  MM_dupKeyRedirect="aerrore.asp"
  MM_rsKeyConnection=MM_SQLDocnaet_STRING
  MM_dupKeyUsernameValue = CStr(Request.Form("txtDescrizione"))
  MM_dupKeySQL="SELECT ditRagioneSociale FROM Ditte WHERE ditRagioneSociale='" & MM_dupKeyUsernameValue & "'"
  MM_adodbRecordset="ADODB.Recordset"
  set MM_rsKey=Server.CreateObject(MM_adodbRecordset)
  MM_rsKey.ActiveConnection=MM_rsKeyConnection
  MM_rsKey.Source=MM_dupKeySQL
  MM_rsKey.CursorType=0
  MM_rsKey.CursorLocation=2
  MM_rsKey.LockType=3
  MM_rsKey.Open
  If Not MM_rsKey.EOF Or Not MM_rsKey.BOF Then 
    ' the username was found - can not add the requested username
    MM_qsChar = "?"
    If (InStr(1,MM_dupKeyRedirect,"?") >= 1) Then MM_qsChar = "&"
    MM_dupKeyRedirect = MM_dupKeyRedirect & MM_qsChar & "requsername=" & MM_dupKeyUsernameValue
    Response.Redirect(MM_dupKeyRedirect)
  End If
  MM_rsKey.Close
End If
%>
<%
' *** Insert Record: set variables

If (CStr(Request("MM_insert")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Ditte"
  MM_editRedirectUrl = "aconferma.asp"
  MM_fieldsStr  = "txtDescrizione|value|txtPaese|value|txtNote|value"
  MM_columnsStr = "ditRagioneSociale|',none,''|ditPaese|',none,''|ditNote|',none,''"

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

	' creazione della cartella riservata alla ditta *************************************************
' completare con la parte che recupera l'ID della ditta appena creata
'	Dim fso, f, temp
'    Set fso = CreateObject("Scripting.FileSystemObject")
'	temp=Cstr(Application("UploadFolder"))& CStr(Request.Form("UserName"))
'	if not(fso.Folderexists(temp)) then Set f = fso.CreateFolder(temp)
    ' **************************************************************************************************************


    If (MM_editRedirectUrl <> "") Then
      Response.Redirect(MM_editRedirectUrl)
    End If
  End If

End If
%>
<html>
<head>
<title>Inserimento azienda</title>
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
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="10">
<div align="center"> 
  <table width="37%" border="0" bgcolor="#CCCCCC">
    <tr> 
      <td align="center"> <b><font color="#009933">Inserimento azienda</font></b> 
      </td>
    </tr>
  </table>
</div>
<form name="frmInserimento" method="POST" action="<%=MM_editAction%>">
  <table width="37%" border="0" align="center">
    <tr> 
      <td width="30%" bgcolor="#FFFFCC">Ragione sociale:</td>
      <td width="70%" bgcolor="#CEECFD"> 
        <input type="text" name="txtDescrizione" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="30%" bgcolor="#FFFFCC">Paese:</td>
      <td width="70%" bgcolor="#CEECFD"> 
        <input type="text" name="txtPaese">
      </td>
    </tr>
    <tr> 
      <td width="30%" bgcolor="#FFFFCC">Note:</td>
      <td width="70%" bgcolor="#CEECFD"> 
        <input type="text" name="txtNote" OnFocus="this.select()">
      </td>
    </tr>
  </table>
  <br>
  <table width="37%" border="0" align="center">
    <tr> 
      <td align="center"> 
        <input type="submit" name="Submit" value="Inserisci" onClick="return validateForm(txtDescrizione,txtPaese);">
      </td>
      <td align="center"> 
        <input type="reset" name="Submit2" value="Reinserici" onclick="">
      </td>
      <td align="center"> 
        <input type="button" name="Submit3" value="Annulla" onClick="goToURL('aziende.asp');return false">
      </td>
    </tr>
  </table>
  <p> 
    <input type="hidden" name="MM_insert" value="true">
  </p>
</form>
</body>
</html>




