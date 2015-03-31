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
  MM_editTable = "Categorie"
  MM_editColumn = "ID_categoria"
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
Dim Categorie__MMColParam
Categorie__MMColParam = "1"
if (Session("IDditta") <> "") then Categorie__MMColParam = Session("IDditta")
%>
<%
set Categorie = Server.CreateObject("ADODB.Recordset")
Categorie.ActiveConnection = MM_SQLDocnaet_STRING
Categorie.Source = "SELECT * FROM Categorie WHERE ID_ditta = " + Replace(Categorie__MMColParam, "'", "''") + " ORDER BY catDescrizione ASC"
Categorie.CursorType = 0
Categorie.CursorLocation = 2
Categorie.LockType = 3
Categorie.Open()
Categorie_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Categorie_numRows = Categorie_numRows + Repeat1__numRows
%>
<html>
<head>
<title>Elenco Lingue</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script type="text/javascript" language="JavaScript">
<!--
// *********************************** FUNZIONE PER CONFERMA ELIMINAZIONE ********************************++
function Conferma() 
{
       risposta=confirm('Confermi l\'eliminazione della categoria?');
       return risposta;   
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#FFFFCC">Anagrafica categorie</font></b></div>
    </td>
  </tr>
  <tr> 
    <td align="center"> <a href="ncategorie.asp"><img src="../../../../immagini/sistema/bottoni/icone/categorie2.gif" width="30" height="30" border="0"></a> 
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="64%" border="0" align="center" height="84">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco categories</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="20%"> 
      <div align="center"><b>Tipo</b></div>
    </td>
    <td width="34%"> 
      <div align="center"><b>Note</b></div>
    </td>
    <td colspan="3"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Categorie.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="20%" valign="top" height="31"> 
      <p>&nbsp;<%=(Categorie.Fields.Item("catDescrizione").Value)%></p>
    </td>
    <td width="34%" valign="top" height="31"> 
      <p>&nbsp;<%=(Categorie.Fields.Item("catNote").Value)%></p>
    </td>
    <form name="frmElimina" action="<%=MM_editAction%>" method="POST">
      <td width="5%" bgcolor="#CCCCCC" align="center" valign="top" height="31"> 
        <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" alt="Elimina il tipo di ditta" onClick="return Conferma();">
        <input type="hidden" name="MM_delete" value="true">
        <input type="hidden" name="MM_recordId" value="<%= Categorie.Fields.Item("ID_categoria").Value %>">
    </td> </form>
    <form name="frmModifica" action="mcategorie.asp" method="get">
      <td width="5%" bgcolor="#CCCCCC" align="center" valign="top" height="31"> 
        <input type="image" border="0" name="imgModifica" src="../../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica i dati del tipo di ditta">
        <input type="hidden" name="ID_categoria" value="<%=(Categorie.Fields.Item("ID_categoria").Value)%>">
    </td> </form>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Categorie.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Categorie.Close()
%>

