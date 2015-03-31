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
' *** Insert Record: set variables

If (CStr(Request("MM_insert")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Prodotti"
  MM_editRedirectUrl = "pconferma.asp"
  MM_fieldsStr  = "txtDescrizione|value|txtNote|value|cboClienti|value|txtCodifica|value|cboCategorie|value|txtCodiceCX|value|hidID_azienda|value"
  MM_columnsStr = "proDescrizione|',none,''|proNote|',none,''|ID_cliente|none,none,NULL|proCodifica|',none,''|ID_categoria|none,none,NULL|proCodice|',none,''|ID_ditta|none,none,NULL"

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
  MM_editTable = "Prodotti"
  MM_editColumn = "ID_prodotto"
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
Dim Prodotti__MMColParam
Prodotti__MMColParam = "1"
if (Request.QueryString("ID_prodotto") <> "") then Prodotti__MMColParam = Request.QueryString("ID_prodotto")
%>
<%
set Prodotti = Server.CreateObject("ADODB.Recordset")
Prodotti.ActiveConnection = MM_SQLDocnaet_STRING
Prodotti.Source = "SELECT * FROM Prodotti WHERE ID_prodotto = " + Replace(Prodotti__MMColParam, "'", "''") + ""
Prodotti.CursorType = 0
Prodotti.CursorLocation = 2
Prodotti.LockType = 3
Prodotti.Open()
Prodotti_numRows = 0
%>
<%
Dim Categorie__MMColParam
Categorie__MMColParam = "1"
if (Session("IDditta") <> "") then Categorie__MMColParam = Session("IDditta")
%>
<%
set Categorie = Server.CreateObject("ADODB.Recordset")
Categorie.ActiveConnection = MM_SQLDocnaet_STRING
Categorie.Source = "SELECT ID_categoria, catDescrizione, ID_ditta FROM Categorie WHERE ID_ditta = " + Replace(Categorie__MMColParam, "'", "''") + " ORDER BY catDescrizione ASC"
Categorie.CursorType = 0
Categorie.CursorLocation = 2
Categorie.LockType = 3
Categorie.Open()
Categorie_numRows = 0
%>
<%
Dim Clienti__MMColParam
Clienti__MMColParam = "1"
if (Session("IDditta") <> "") then Clienti__MMColParam = Session("IDditta")
%>
<%
set Clienti = Server.CreateObject("ADODB.Recordset")
Clienti.ActiveConnection = MM_SQLDocnaet_STRING
Clienti.Source = "SELECT ID_cliente, cliRagioneSociale, cliPaese, ID_ditta FROM Clienti WHERE ID_ditta = " + Replace(Clienti__MMColParam, "'", "''") + " ORDER BY cliRagioneSociale ASC"
Clienti.CursorType = 0
Clienti.CursorLocation = 2
Clienti.LockType = 3
Clienti.Open()
Clienti_numRows = 0
%>
<html>
<head>
<title>Dettaglio Cliente</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script type="text/javascript" language="JavaScript">
<!--
// *********************************** FUNZIONE PER CONFERMA ELIMINAZIONE ********************************++
function Conferma(Blocco) 
{
   var risposta;
   if (Blocco.txtDescrizione.value=='')
   {
       alert('Inserire almeno la descrizione del prodotto!');
       return false;
   }
   else
   {
       risposta=confirm('Confermi l\'inserimento del prodotto?');
       return risposta;
   }
}
function ConfermaDelete(Messaggio) 
{
       risposta=confirm(Messaggio);
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
    <td colspan="4"> 
      <div align="center"><b><font color="#FFFFCC">Modifica Prodotto</font></b></div>
    </td>
  </tr>
</table>
<table width="100%" border="0" height="52">
  <tr> 
    <td width="25%" height="29">&nbsp; </td>
    <td width="25%" height="29">&nbsp;</td>
    <td width="25%" height="29">&nbsp;</td>
    <td width="25%" height="29" align="center"> 
      <form name="frmElimina" method="POST" action="<%=MM_editAction%>">
        <input type="image" border="0" name="imgElimina" src="../../../../immagini/sistema/bottoni/icone/cestino.gif" width="24" height="24" alt="Elimina prodotto..." onClick="return ConfermaDelete('Confermi l\'eliminazione del prodotto?');">
        <input type="hidden" name="MM_delete" value="true">
        <input type="hidden" name="MM_recordId" value="<%= Prodotti.Fields.Item("ID_prodotto").Value %>">
      </form>
    </td>
  </tr>
</table>
<br>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmUpdate">
  <table width="69%" border="0" align="center" height="71">
    <tr bgcolor="#CCCCCC"> 
      <td colspan="5"> 
        <div align="center"><b><font color="#990000">Modifica Prodotto</font></b></div>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="13%" bgcolor="#CEECFD"> 
        <div align="left">Descrizione</div>
      </td>
      <td bgcolor="#FFFFCC" width="87%"> 
        <div align="left"> 
          <input value="<%=(Prodotti.Fields.Item("proDescrizione").Value)%>"  type="text" name="txtDescrizione" size="50">
        </div>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td bgcolor="#CEECFD" width="13%">Ditta </td>
      <td bgcolor="#FFFFCC" width="87%"> 
        <select name="cboClienti">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Clienti.EOF)
%>
          <option value="<%=(Clienti.Fields.Item("ID_cliente").Value)%>" <%if (CStr(Clienti.Fields.Item("ID_cliente").Value) = CStr(Prodotti.Fields.Item("ID_cliente").Value)) then Response.Write("SELECTED") : Response.Write("")%> ><%=(Clienti.Fields.Item("cliRagioneSociale").Value)%></option>
          <%
  Clienti.MoveNext()
Wend
If (Clienti.CursorType > 0) Then
  Clienti.MoveFirst
Else
  Clienti.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td bgcolor="#CEECFD" width="13%">Categoria</td>
      <td valign="middle" bgcolor="#FFFFCC" width="87%"> 
        <select name="cboCategorie">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Categorie.EOF)
%>
          <option value="<%=(Categorie.Fields.Item("ID_categoria").Value)%>" <%if (CStr(Categorie.Fields.Item("ID_categoria").Value) = CStr(Prodotti.Fields.Item("ID_categoria").Value)) then Response.Write("SELECTED") : Response.Write("")%> ><%=(Categorie.Fields.Item("catDescrizione").Value)%></option>
          <%
  Categorie.MoveNext()
Wend
If (Categorie.CursorType > 0) Then
  Categorie.MoveFirst
Else
  Categorie.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="13%" bgcolor="#CEECFD">Note</td>
      <td bgcolor="#FFFFCC" width="87%"> 
        <input value="<%=(Prodotti.Fields.Item("proNote").Value)%>"  type="text" name="txtNote" size="50">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="13%" bgcolor="#CEECFD">Codifica</td>
      <td bgcolor="#FFFFCC" width="87%"> 
        <input value="<%=(Prodotti.Fields.Item("proCodifica").Value)%>" type="text" name="txtCodifica" size="20">
      </td>
    </tr>
    <tr bgcolor="#FFFFFF"> 
      <td width="13%" bgcolor="#CEECFD">Codice gest.</td>
      <td bgcolor="#FFFFCC" width="87%"> 
        <input value="<%=(Prodotti.Fields.Item("proCodice").Value)%>" type="text" name="txtCodiceCX" size="20">
        <input type="hidden" name="hidID_azienda" value="<%=Session("IDDitta")%>" >
      </td>
    </tr>
  </table>
  <p align="center"> 
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/icone/aggiorna.gif" width="31" height="32" onClick="return Conferma(document.frmUpdate);">
    <input type="hidden" name="MM_insert" value="true">
  </p>
</form>
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
Prodotti.Close()
%>
<%
Categorie.Close()
%>
<%
Clienti.Close()
%>

