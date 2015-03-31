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
' *** Delete Record: declare variables

if (CStr(Request("MM_delete")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Protocolli"
  MM_editColumn = "ID_protocollo"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "pconferma.asp"

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
Dim Protocolli__MMColParam
Protocolli__MMColParam = "1"
if (Request.QueryString("ID_protocollo") <> "") then Protocolli__MMColParam = Request.QueryString("ID_protocollo")
%>
<%
set Protocolli = Server.CreateObject("ADODB.Recordset")
Protocolli.ActiveConnection = MM_SQLDocnaet_STRING
Protocolli.Source = "SELECT * FROM Protocolli WHERE ID_protocollo = " + Replace(Protocolli__MMColParam, "'", "''") + ""
Protocolli.CursorType = 0
Protocolli.CursorLocation = 2
Protocolli.LockType = 3
Protocolli.Open()
Protocolli_numRows = 0
%>
<html>
<head>
<title>Dettaglio lingue</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">
<!--
function MM_goToURL(indirizzo) { //v3.0
  eval("document.location='"+indirizzo+"'");
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000">
<div align="center">
  <table width="50%" border="0" bgcolor="#CCCCCC">
    <tr>
      <td align="center">
        <b><font color="#009933">Eliminazione protocollo</font></b>
      </td>
    </tr>
  </table>
  </div><br>
  
<table width="50%" border="0" align="center">
  <tr> 
    <td width="50%" bgcolor="#FFFFCC"><%=(Protocolli.Fields.Item("proDescrizione").Value)%></td>
    <td width="50%" bgcolor="#CEECFD"><%=(Protocolli.Fields.Item("proNote").Value)%></td>
  </tr>
</table>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="form1">
      
  <table width="50%" border="0" align="center">
    <tr> 
      <td bgcolor="#CCCCCC" align="center"> 
          <input type="submit" name="cdoElimina" value="Elimina">
          <input type="button" name="cdoAnnulla" value="Annulla" onClick="MM_goToURL('protocolli.asp');return false">
        <input type="hidden" name="MM_recordId" value="<%= Protocolli.Fields.Item("ID_protocollo").Value %>">
        <input type="hidden" name="MM_delete" value="true">      
    </td>
  </tr>
</table>
</form>
</body>
</html>
<%
Protocolli.Close()
%>

