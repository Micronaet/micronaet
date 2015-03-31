<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
set Lingue = Server.CreateObject("ADODB.Recordset")
Lingue.ActiveConnection = MM_SQLDocnaet_STRING
Lingue.Source = "SELECT ID_lingua, linDescrizione FROM Lingue ORDER BY linDescrizione ASC"
Lingue.CursorType = 0
Lingue.CursorLocation = 2
Lingue.LockType = 3
Lingue.Open()
Lingue_numRows = 0
%>
<%
set Applicazioni = Server.CreateObject("ADODB.Recordset")
Applicazioni.ActiveConnection = MM_SQLDocnaet_STRING
Applicazioni.Source = "SELECT ID_applicazione, appNome, appEstensione FROM Applicazioni ORDER BY ID_applicazione ASC"
Applicazioni.CursorType = 0
Applicazioni.CursorLocation = 2
Applicazioni.LockType = 3
Applicazioni.Open()
Applicazioni_numRows = 0
%>
<%
set Tipologia = Server.CreateObject("ADODB.Recordset")
Tipologia.ActiveConnection = MM_SQLDocnaet_STRING
Tipologia.Source = "SELECT ID_tipologia, tipDescrizione FROM Tipologie ORDER BY tipDescrizione ASC"
Tipologia.CursorType = 0
Tipologia.CursorLocation = 2
Tipologia.LockType = 3
Tipologia.Open()
Tipologia_numRows = 0
%>
<html>
<head>
<title>Inserimento lingua</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="10">
<div align="center"> 
  <table width="40%" border="0" bgcolor="#CCCCCC">
    <tr> 
      <td align="center"> <b><font color="#009933">Gestione modelli per protocollo: 
        <%=Request.Form("proDescrizione")%> </font></b></td>
    </tr>
  </table>
</div>
<form name="frmInserimento" action="aprimodello.asp" method="get">
  <table width="40%" border="0" align="center">
    <tr>
      <td bgcolor="#FFFFCC" width="23%">Lingua:</td>
      <td bgcolor="#CEECFD"> 
        <select name="ID_Lingua">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Lingue.EOF)
%>
          <option value="<%=(Lingue.Fields.Item("ID_lingua").Value)%>"><%=(Lingue.Fields.Item("linDescrizione").Value)%></option>
          <%
  Lingue.MoveNext()
Wend
If (Lingue.CursorType > 0) Then
  Lingue.MoveFirst
Else
  Lingue.Requery
End If
%>
        </select>
      </td>
    </tr>
    <tr>
      <td bgcolor="#FFFFCC" width="23%">Tipologia:</td>
      <td bgcolor="#CEECFD"> 
        <select name="ID_Tipologia">
          <option value="0" SELECTED>Selezionare...</option>
          <%
While (NOT Tipologia.EOF)
%>
          <option value="<%=(Tipologia.Fields.Item("ID_tipologia").Value)%>"><%=(Tipologia.Fields.Item("tipDescrizione").Value)%></option>
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
      <td bgcolor="#FFFFCC" width="23%">Documento:</td>
      <td bgcolor="#CEECFD"> 
        <select name="ID_applicazione">
          <%
While (NOT Applicazioni.EOF)
%>
          <option value="<%=(Applicazioni.Fields.Item("appEstensione").Value)%>"><%=(Applicazioni.Fields.Item("appNome").Value)%></option>
          <%
  Applicazioni.MoveNext()
Wend
If (Applicazioni.CursorType > 0) Then
  Applicazioni.MoveFirst
Else
  Applicazioni.Requery
End If
%>
        </select>
      </td>
    </tr>
  </table>
  <p align="center">
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/icone/modelli.gif" width="26" height="32">
    <input type="hidden" name="ID_protocollo" value="<%=Request.Form("ID_protocollo")%>">
  </p>
</form>
</body>
</html>
<%
Lingue.Close()
%>
<%
Applicazioni.Close()
%>
<%
Tipologia.Close()
%>
