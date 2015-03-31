<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
Dim Clienti__MMColParam
Clienti__MMColParam = "1"
if (Session("IDDitta") <> "") then Clienti__MMColParam = Session("IDDitta")
%>
<%
set Clienti = Server.CreateObject("ADODB.Recordset")
Clienti.ActiveConnection = MM_SQLDocnaet_STRING
Clienti.Source = "SELECT Nazione, Tipo, ID_cliente, cliRagioneSociale, cliPaese, cliProvincia, ID_ditta FROM vwClienti WHERE (ID_ditta = " + Replace(Clienti__MMColParam, "'", "''") & ")"
if Request.QueryString("txtFind")<>"" then    Clienti.Source=Clienti.Source & " and (cliRagioneSociale like '%" & Request.QueryString("txtFind") & "%')"
if (Request.QueryString("cboTipo")<>"") and (Request.QueryString("cboTipo")<>"0") then    Clienti.Source=Clienti.Source & " and (ID_Tipo=" & Request.QueryString("cboTipo") & ")"
if (Request.QueryString("cboNazione")<>"") and (Request.QueryString("cboNazione")<>"0") then    Clienti.Source=Clienti.Source & " and (ID_Nazione=" & Request.QueryString("cboNazione") & ")"
dim ID_Tipo, ID_Nazione
ID_Nazione=Request.QueryString("cboNazione")
ID_Tipo=Request.QueryString("cboTipo")
Clienti.CursorType = 0
Clienti.CursorLocation = 2
Clienti.LockType = 3
Clienti.Open()
Clienti_numRows = 0
%>
<%
set Tipi = Server.CreateObject("ADODB.Recordset")
Tipi.ActiveConnection = MM_SQLDocnaet_STRING
Tipi.Source = "SELECT * FROM Tipi ORDER BY tipDescrizione ASC"
Tipi.CursorType = 0
Tipi.CursorLocation = 2
Tipi.LockType = 3
Tipi.Open()
Tipi_numRows = 0
%>
<%
set Nazionalita = Server.CreateObject("ADODB.Recordset")
Nazionalita.ActiveConnection = MM_SQLDocnaet_STRING
Nazionalita.Source = "SELECT * FROM Nazioni ORDER BY nazDescrizione ASC"
Nazionalita.CursorType = 0
Nazionalita.CursorLocation = 2
Nazionalita.LockType = 3
Nazionalita.Open()
Nazionalita_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = 50
Dim Repeat1__index
Repeat1__index = 0
Clienti_numRows = Clienti_numRows + Repeat1__numRows
%>
<%
'  *** Recordset Stats, Move To Record, and Go To Record: declare stats variables

' set the record count
Clienti_total = Clienti.RecordCount

' set the number of rows displayed on this page
If (Clienti_numRows < 0) Then
  Clienti_numRows = Clienti_total
Elseif (Clienti_numRows = 0) Then
  Clienti_numRows = 1
End If

' set the first and last displayed record
Clienti_first = 1
Clienti_last  = Clienti_first + Clienti_numRows - 1

' if we have the correct record count, check the other stats
If (Clienti_total <> -1) Then
  If (Clienti_first > Clienti_total) Then Clienti_first = Clienti_total
  If (Clienti_last > Clienti_total) Then Clienti_last = Clienti_total
  If (Clienti_numRows > Clienti_total) Then Clienti_numRows = Clienti_total
End If
%>
<%
' *** Recordset Stats: if we don't know the record count, manually count them

If (Clienti_total = -1) Then

  ' count the total records by iterating through the recordset
  Clienti_total=0
  While (Not Clienti.EOF)
    Clienti_total = Clienti_total + 1
    Clienti.MoveNext
  Wend

  ' reset the cursor to the beginning
  If (Clienti.CursorType > 0) Then
    Clienti.MoveFirst
  Else
    Clienti.Requery
  End If

  ' set the number of rows displayed on this page
  If (Clienti_numRows < 0 Or Clienti_numRows > Clienti_total) Then
    Clienti_numRows = Clienti_total
  End If

  ' set the first and last displayed record
  Clienti_first = 1
  Clienti_last = Clienti_first + Clienti_numRows - 1
  If (Clienti_first > Clienti_total) Then Clienti_first = Clienti_total
  If (Clienti_last > Clienti_total) Then Clienti_last = Clienti_total

End If
%>
<%
' *** Move To Record and Go To Record: declare variables

Set MM_rs    = Clienti
MM_rsCount   = Clienti_total
MM_size      = Clienti_numRows
MM_uniqueCol = ""
MM_paramName = ""
MM_offset = 0
MM_atTotal = false
MM_paramIsDefined = false
If (MM_paramName <> "") Then
  MM_paramIsDefined = (Request.QueryString(MM_paramName) <> "")
End If
%>
<%
' *** Move To Record: handle 'index' or 'offset' parameter
if (Not MM_paramIsDefined And MM_rsCount <> 0) then
  ' use index parameter if defined, otherwise use offset parameter
  r = Request.QueryString("index")
  If r = "" Then r = Request.QueryString("offset")
  If r <> "" Then MM_offset = Int(r)
  ' if we have a record count, check if we are past the end of the recordset
  If (MM_rsCount <> -1) Then
    If (MM_offset >= MM_rsCount Or MM_offset = -1) Then  ' past end or move last
      If ((MM_rsCount Mod MM_size) > 0) Then         ' last page not a full repeat region
        MM_offset = MM_rsCount - (MM_rsCount Mod MM_size)
      Else
        MM_offset = MM_rsCount - MM_size
      End If
    End If
  End If
  ' move the cursor to the selected record
  i = 0
  While ((Not MM_rs.EOF) And (i < MM_offset Or MM_offset = -1))
    MM_rs.MoveNext
    i = i + 1
  Wend
  If (MM_rs.EOF) Then MM_offset = i  ' set MM_offset to the last possible record
End If
%>
<%
' *** Move To Record: if we dont know the record count, check the display range
If (MM_rsCount = -1) Then
  ' walk to the end of the display range for this page
  i = MM_offset
  While (Not MM_rs.EOF And (MM_size < 0 Or i < MM_offset + MM_size))
    MM_rs.MoveNext
    i = i + 1
  Wend
  ' if we walked off the end of the recordset, set MM_rsCount and MM_size
  If (MM_rs.EOF) Then
    MM_rsCount = i
    If (MM_size < 0 Or MM_size > MM_rsCount) Then MM_size = MM_rsCount
  End If
  ' if we walked off the end, set the offset based on page size
  If (MM_rs.EOF And Not MM_paramIsDefined) Then
    If (MM_offset > MM_rsCount - MM_size Or MM_offset = -1) Then
      If ((MM_rsCount Mod MM_size) > 0) Then
        MM_offset = MM_rsCount - (MM_rsCount Mod MM_size)
      Else
        MM_offset = MM_rsCount - MM_size
      End If
    End If
  End If
  ' reset the cursor to the beginning
  If (MM_rs.CursorType > 0) Then
    MM_rs.MoveFirst
  Else
    MM_rs.Requery
  End If
  ' move the cursor to the selected record
  i = 0
  While (Not MM_rs.EOF And i < MM_offset)
    MM_rs.MoveNext
    i = i + 1
  Wend
End If
%>
<%
' *** Move To Record: update recordset stats

' set the first and last displayed record
Clienti_first = MM_offset + 1
Clienti_last  = MM_offset + MM_size
If (MM_rsCount <> -1) Then
  If (Clienti_first > MM_rsCount) Then Clienti_first = MM_rsCount
  If (Clienti_last > MM_rsCount) Then Clienti_last = MM_rsCount
End If

' set the boolean used by hide region to check if we are on the last record
MM_atTotal = (MM_rsCount <> -1 And MM_offset + MM_size >= MM_rsCount)
%>
<%
' *** Go To Record and Move To Record: create strings for maintaining URL and Form parameters

' create the list of parameters which should not be maintained
MM_removeList = "&index="
If (MM_paramName <> "") Then MM_removeList = MM_removeList & "&" & MM_paramName & "="
MM_keepURL="":MM_keepForm="":MM_keepBoth="":MM_keepNone=""

' add the URL parameters to the MM_keepURL string
For Each Item In Request.QueryString
  NextItem = "&" & Item & "="
  If (InStr(1,MM_removeList,NextItem,1) = 0) Then
    MM_keepURL = MM_keepURL & NextItem & Server.URLencode(Request.QueryString(Item))
  End If
Next

' add the Form variables to the MM_keepForm string
For Each Item In Request.Form
  NextItem = "&" & Item & "="
  If (InStr(1,MM_removeList,NextItem,1) = 0) Then
    MM_keepForm = MM_keepForm & NextItem & Server.URLencode(Request.Form(Item))
  End If
Next

' create the Form + URL string and remove the intial '&' from each of the strings
MM_keepBoth = MM_keepURL & MM_keepForm
if (MM_keepBoth <> "") Then MM_keepBoth = Right(MM_keepBoth, Len(MM_keepBoth) - 1)
if (MM_keepURL <> "")  Then MM_keepURL  = Right(MM_keepURL, Len(MM_keepURL) - 1)
if (MM_keepForm <> "") Then MM_keepForm = Right(MM_keepForm, Len(MM_keepForm) - 1)

' a utility function used for adding additional parameters to these strings
Function MM_joinChar(firstItem)
  If (firstItem <> "") Then
    MM_joinChar = "&"
  Else
    MM_joinChar = ""
  End If
End Function
%>
<%
' *** Move To Record: set the strings for the first, last, next, and previous links

MM_keepMove = MM_keepBoth
MM_moveParam = "index"

' if the page has a repeated region, remove 'offset' from the maintained parameters
If (MM_size > 0) Then
  MM_moveParam = "offset"
  If (MM_keepMove <> "") Then
    params = Split(MM_keepMove, "&")
    MM_keepMove = ""
    For i = 0 To UBound(params)
      nextItem = Left(params(i), InStr(params(i),"=") - 1)
      If (StrComp(nextItem,MM_moveParam,1) <> 0) Then
        MM_keepMove = MM_keepMove & "&" & params(i)
      End If
    Next
    If (MM_keepMove <> "") Then
      MM_keepMove = Right(MM_keepMove, Len(MM_keepMove) - 1)
    End If
  End If
End If

' set the strings for the move to links
If (MM_keepMove <> "") Then MM_keepMove = MM_keepMove & "&"
urlStr = Request.ServerVariables("URL") & "?" & MM_keepMove & MM_moveParam & "="
MM_moveFirst = urlStr & "0"
MM_moveLast  = urlStr & "-1"
MM_moveNext  = urlStr & Cstr(MM_offset + MM_size)
prev = MM_offset - MM_size
If (prev < 0) Then prev = 0
MM_movePrev  = urlStr & Cstr(prev)
%>
<html>
<head>
<title>Elenco Clienti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/menu.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<form name="form1" method="get" action="ricerche.asp">
  <table width="100%" border="0">
    <tr> 
      <td width="59" align="center"><a href="ncliente.asp"><img src="../../../../immagini/sistema/bottoni/icone/passepartout.gif" width="32" height="29" alt="Inserimento nuovo cliente" border="0"></a></td>
      <td width="59" align="center"> 
        <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/search.gif" width="31" height="31" alt="Ricerca in funzione dei parametri impostati">
      </td>
      <td width="30%">Testo: 
        <input type="text" name="txtFind" value="<%=Request("txtFind")%>" size="30">
      </td>
      <td width="30%">Tipo: 
        <select name="cboTipo" onChange="form1.submit();">
          <option value="0">Tutti...</option>
          <%
While (NOT Tipi.EOF)
%>
          <option value="<%=(Tipi.Fields.Item("ID_tipo").Value)%>" <%if ID_tipo-(Tipi.Fields.Item("ID_tipo").Value)=0 then Response.Write ("SELECTED")%>><%=(Tipi.Fields.Item("tipDescrizione").Value)%></option>
          <%
  Tipi.MoveNext()
Wend
If (Tipi.CursorType > 0) Then
  Tipi.MoveFirst
Else
  Tipi.Requery
End If
%>
        </select>
      </td>
      <td width="30%">Nazionalita: 
        <select name="cboNazione" onChange="form1.submit();">
          <option value="0">Tutti...</option>
          <%
While (NOT Nazionalita.EOF)
%>
          <option value="<%=(Nazionalita.Fields.Item("ID_nazione").Value)%>" <%if (ID_Nazione-(Nazionalita.Fields.Item("ID_nazione").Value)=0) then Response.Write ("SELECTED")%>><%=(Nazionalita.Fields.Item("nazDescrizione").Value)%></option>
          <%
  Nazionalita.MoveNext()
Wend
If (Nazionalita.CursorType > 0) Then
  Nazionalita.MoveFirst
Else
  Nazionalita.Requery
End If
%>
        </select>
      </td>
    </tr>
  </table>
</form>
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="4"> 
      <div align="center"><b><font color="#FFFFCC">Anagrafica Clienti</font></b></div>
    </td>
  </tr>
  <tr> 
    <td width="43%"> 
      <table border="0" width="100" align="left">
        <tr> 
          <td width="25" align="center"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_moveFirst%>"><img src="../../../../immagini/sistema/bottoni/First.gif" border=0 width="18" height="13"></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="25" align="center"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_movePrev%>"><img src="../../../../immagini/sistema/bottoni/Previous.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="25" align="center"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveNext%>"><img src="../../../../immagini/sistema/bottoni/Next.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
          <td width="25" align="center"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveLast%>"><img src="../../../../immagini/sistema/bottoni/Last.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
        </tr>
      </table>
      &nbsp;<font color="#990000">Clienti dal <b><%=(Clienti_first)%></b> al <b><%=(Clienti_last)%></b> su <b><%=(Clienti_total)%></b> </font></td>
    <td width="16%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="21%" height="29">&nbsp; </td>
  </tr>
</table>
<input type="hidden" name="ID_cliente" value="">
<br>
<table width="73%" border="0" align="center" height="71">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco Clienti</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td width="8%"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
    <td width="43%"> 
      <div align="center"><b>Ragione Sociale</b></div>
    </td>
    <td width="35%"> 
      <div align="center"><b>Paese</b></div>
    </td>
    <td colspan="2" width="14%"> 
      <div align="center"><b>Tipo</b></div>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Clienti.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="8%" bgcolor="<%=colore%>"> 
      <p align="center">&nbsp;<a href="dettcliente.asp?ID_cliente=<%=(Clienti.Fields.Item("ID_cliente").Value)%>"><img src="../../../../immagini/sistema/bottoni/open.gif" width="25" height="26" border="0"></a></p>
    </td>
    <td width="43%"><%=(Clienti.Fields.Item("cliRagioneSociale").Value)%></td>
    <td width="35%"> 
      <p><%=(Clienti.Fields.Item("cliPaese").Value)%>&nbsp<%=(Clienti.Fields.Item("cliProvincia").Value)%>&nbsp <%=(Clienti.Fields.Item("Nazione").Value)%></p>
    </td>
    <td align="left" width="14%"><%=(Clienti.Fields.Item("Tipo").Value)%> </td>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Clienti.MoveNext()
Wend
%>
</table>
<br>
<br>
<table width="100%" border="0" height="52">
  <tr> 
    <td width="43%"> 
      <table border="0" width="100" align="left">
        <tr> 
          <td width="25" align="center"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_moveFirst%>"><img src="../../../../immagini/sistema/bottoni/First.gif" border=0 width="18" height="13"></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="25" align="center"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_movePrev%>"><img src="../../../../immagini/sistema/bottoni/Previous.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="25" align="center"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveNext%>"><img src="../../../../immagini/sistema/bottoni/Next.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
          <td width="25" align="center"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveLast%>"><img src="../../../../immagini/sistema/bottoni/Last.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
        </tr>
      </table>
      &nbsp;<font color="#990000">Clienti dal <b><%=(Clienti_first)%></b> al <b><%=(Clienti_last)%></b> su <b><%=(Clienti_total)%></b> </font></td>
    <td width="16%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="21%" height="29">&nbsp; </td>
  </tr>
</table>
<p>&nbsp;</p>
</body>
</html>
<%
Clienti.Close()
%>
<%
Tipi.Close()
%>
<%
Nazionalita.Close()
%>
