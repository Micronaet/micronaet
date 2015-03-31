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
  MM_editTable = "Ditte"
  MM_editColumn = "ID_ditta"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "aconferma.asp"

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
<title>Eliminazione azienda</title>
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
  <table width="54%" border="0" bgcolor="#CCCCCC">
    <tr>
      <td align="center"> <b><font color="#009933">Eliminazione azienda</font></b> 
      </td>
    </tr>
  </table>
</div>
<br>
<div align="center"></div>
<table width="54%" border="0" align="center">
  <tr> 
    <td width="36%" bgcolor="#FFFFCC"><%=(Aziende.Fields.Item("ditRagioneSociale").Value)%></td>
    <td width="64%" bgcolor="#CEECFD"><%=(Aziende.Fields.Item("ditNote").Value)%></td>
  </tr>
</table>
<br>
<table width="54%" border="0" align="center">
  <tr> 
    <td> 
      <form ACTION="<%=MM_editAction%>" METHOD="POST" name="form1">
        <div align="center"> 
          <input type="submit" name="cdoElimina" value="Elimina">
          <input type="button" name="cdoAnnulla" value="Annulla" onClick="MM_goToURL('aziende.asp');return false">
        </div>
        <input type="hidden" name="MM_delete" value="true">
        <input type="hidden" name="MM_recordId" value="<%= Aziende.Fields.Item("ID_ditta").Value %>">
      </form>
    </td>
  </tr>
</table>
<p>&nbsp;</p>
</body>
</html>
<%
Aziende.Close()
%>
