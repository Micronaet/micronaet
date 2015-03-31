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
' *** Delete Record: declare variables

if (CStr(Request("MM_delete")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Lingue"
  MM_editColumn = "ID_lingua"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "conferma.asp"

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
Dim Lingue__MMColParam
Lingue__MMColParam = "1"
if (Request.QueryString("ID_lingua") <> "") then Lingue__MMColParam = Request.QueryString("ID_lingua")
%>
<%
set Lingue = Server.CreateObject("ADODB.Recordset")
Lingue.ActiveConnection = MM_SQLDocnaet_STRING
Lingue.Source = "SELECT * FROM Lingue WHERE ID_lingua = " + Replace(Lingue__MMColParam, "'", "''") + ""
Lingue.CursorType = 0
Lingue.CursorLocation = 2
Lingue.LockType = 3
Lingue.Open()
Lingue_numRows = 0
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
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000">
<div align="center">
  <table width="57%" border="0" bgcolor="#CCCCCC">
    <tr>
      <td align="center"> <b><font color="#009933">Eliminazione lingua</font></b> 
      </td>
    </tr>
  </table>  
</div>
<br>
<table width="57%" border="0" align="center">
  <tr> 
    <td width="28%" bgcolor="#FFFFCC"><%=(Lingue.Fields.Item("linDescrizione").Value)%></td>
    <td width="72%" bgcolor="#CEECFD"><%=(Lingue.Fields.Item("linNote").Value)%></td>
  </tr>
</table>
<br>
<form name="form1" method="POST" action="<%=MM_editAction%>">
      
  <table width="57%" border="0" align="center">
    <tr> 
    <td align="center"> 
          <input type="submit" name="cdoElimina" value="Elimina">
          <input type="button" name="cdoAnnulla" value="Annulla" onClick="MM_goToURL('lingue.asp');return false">
        <input type="hidden" name="MM_delete" value="true">
        <input type="hidden" name="MM_recordId" value="<%= Lingue.Fields.Item("ID_lingua").Value %>">      
    </td>
  </tr>
</table>
</form>
</body>
</html>
<%
Lingue.Close()
%>
