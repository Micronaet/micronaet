<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
Dim Prodotti__MMColParam
if (Session("IDDitta") <> "") then Prodotti__MMColParam = Cstr(Session("IDDitta")) else Prodotti__MMColParam = "0"
%>
<%
set Prodotti = Server.CreateObject("ADODB.Recordset")
Prodotti.ActiveConnection = MM_SQLDocnaet_STRING
Prodotti.Source = "SELECT * FROM vwProdotti WHERE ID_ditta = " + Replace(Prodotti__MMColParam, "'", "''") 
if Request.QueryString("txtFind")<>"" then    Prodotti.Source=Prodotti.Source & " and (proDescrizione like '%" & Request.QueryString("txtFind") & "%')"
if (Request.QueryString("cboCategoria")<>"") and (Request.QueryString("cboCategoria")<>"0") then    Prodotti.Source=Prodotti.Source & " and (ID_Categoria=" & Request.QueryString("cboCategoria") & ")"
if (Request.QueryString("cboCliente")<>"") and (Request.QueryString("cboCliente")<>"0") then    Prodotti.Source=Prodotti.Source & " and (ID_Cliente=" & Request.QueryString("cboCliente") & ")"
Prodotti.Source=Prodotti.Source + " ORDER BY proDescrizione ASC"

dim ID_Categoria, ID_Cliente
ID_Cliente=Request.QueryString("cboCliente")
ID_Categoria=Request.QueryString("CboCategoria")
Prodotti.CursorType = 0
Prodotti.CursorLocation = 2
Prodotti.LockType = 3
Prodotti.Open()
Prodotti_numRows = 0
%>
<%
Dim Categorie__MMColParam
if (Session("IDditta") <> "") then Categorie__MMColParam = Session("IDditta") else Categorie__MMColParam ="0" %>
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
Dim Ditte__MMColParam
Ditte__MMColParam = "1"
if (Session("IDditta") <> "") then Ditte__MMColParam = Session("IDditta")
%>
<%
set Ditte = Server.CreateObject("ADODB.Recordset")
Ditte.ActiveConnection = MM_SQLDocnaet_STRING
Ditte.Source = "SELECT ID_cliente, cliRagioneSociale, cliIndirizzo, cliPaese, ID_ditta FROM Clienti WHERE ID_ditta = " + Replace(Ditte__MMColParam, "'", "''") + " ORDER BY cliRagioneSociale ASC"
Ditte.CursorType = 0
Ditte.CursorLocation = 2
Ditte.LockType = 3
Ditte.Open()
Ditte_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = 50
Dim Repeat1__index
Repeat1__index = 0
Prodotti_numRows = Prodotti_numRows + Repeat1__numRows
%>
<%
'  *** Recordset Stats, Move To Record, and Go To Record: declare stats variables

' set the record count
Prodotti_total = Prodotti.RecordCount

' set the number of rows displayed on this page
If (Prodotti_numRows < 0) Then
  Prodotti_numRows = Prodotti_total
Elseif (Prodotti_numRows = 0) Then
  Prodotti_numRows = 1
End If

' set the first and last displayed record
Prodotti_first = 1
Prodotti_last  = Prodotti_first + Prodotti_numRows - 1

' if we have the correct record count, check the other stats
If (Prodotti_total <> -1) Then
  If (Prodotti_first > Prodotti_total) Then Prodotti_first = Prodotti_total
  If (Prodotti_last > Prodotti_total) Then Prodotti_last = Prodotti_total
  If (Prodotti_numRows > Prodotti_total) Then Prodotti_numRows = Prodotti_total
End If
%>
<%
' *** Recordset Stats: if we don't know the record count, manually count them

If (Prodotti_total = -1) Then

  ' count the total records by iterating through the recordset
  Prodotti_total=0
  While (Not Prodotti.EOF)
    Prodotti_total = Prodotti_total + 1
    Prodotti.MoveNext
  Wend

  ' reset the cursor to the beginning
  If (Prodotti.CursorType > 0) Then
    Prodotti.MoveFirst
  Else
    Prodotti.Requery
  End If

  ' set the number of rows displayed on this page
  If (Prodotti_numRows < 0 Or Prodotti_numRows > Prodotti_total) Then
    Prodotti_numRows = Prodotti_total
  End If

  ' set the first and last displayed record
  Prodotti_first = 1
  Prodotti_last = Prodotti_first + Prodotti_numRows - 1
  If (Prodotti_first > Prodotti_total) Then Prodotti_first = Prodotti_total
  If (Prodotti_last > Prodotti_total) Then Prodotti_last = Prodotti_total
End If
%>
<%
' *** Move To Record and Go To Record: declare variables
Set MM_rs    = Prodotti
MM_rsCount   = Prodotti_total
MM_size      = Prodotti_numRows
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
Prodotti_first = MM_offset + 1
Prodotti_last  = MM_offset + MM_size
If (MM_rsCount <> -1) Then
  If (Prodotti_first > MM_rsCount) Then Prodotti_first = MM_rsCount
  If (Prodotti_last > MM_rsCount) Then Prodotti_last = MM_rsCount
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
<title>Elenco Prodotti</title>
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
      <td width="59" align="center"><a href="nprodotto.asp"><img src="../../../../immagini/sistema/bottoni/icone/cubo1.gif" width="30" height="32" alt="Inserimento nuovo cliente" border="0"></a></td>
      <td width="59" align="center"> 
        <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/search.gif" width="31" height="31" alt="Ricerca in funzione dei parametri impostati">
      </td>
      <td width="30%">Testo: 
        <input type="text" name="txtFind" value="<%=Request("txtFind")%>" size="30">
      </td>
      <td width="30%">Categoria: 
        <select name="cboCategoria">
          <option value="0" selected>Tutti...</option>
          <%
While (NOT Categorie.EOF)
%>
          <option value="<%=(Categorie.Fields.Item("ID_categoria").Value)%>" <%if ID_categoria-(Categorie.Fields.Item("ID_categoria").Value)=0 then Response.Write ("SELECTED")%>><%=(Categorie.Fields.Item("catDescrizione").Value)%></option>
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
      <td width="30%">Ditta: 
        <select name="cboCliente">
          <option value="0" selected>Tutti...</option>
          <%
While (NOT Ditte.EOF)
%>
          <option value="<%=(Ditte.Fields.Item("ID_cliente").Value)%>" <%if ID_cliente-(Ditte.Fields.Item("ID_cliente").Value)=0 then Response.Write ("SELECTED")%>><%=(Ditte.Fields.Item("cliRagioneSociale").Value)%></option>
          <%
  Ditte.MoveNext()
Wend
If (Ditte.CursorType > 0) Then
  Ditte.MoveFirst
Else
  Ditte.Requery
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
      <div align="center"><b><font color="#FFFFCC">Anagrafica Prodotti</font></b></div>
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
      &nbsp;<font color="#990000">Prodotti</font><font color="#990000"> dal <b><%=(Prodotti_first)%></b> al <b><%=(Prodotti_last)%></b> su <b><%=(Prodotti_total)%></b> </font></td>
    <td width="16%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="21%" height="29">&nbsp; </td>
  </tr>
</table>
<input type="hidden" name="ID_prodotto" value="">
<br>
<table width="73%" border="0" align="center" height="71">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#990000">Elenco Prodotti</font></b></div>
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
While ((Repeat1__numRows <> 0) AND (NOT Prodotti.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="8%" bgcolor="<%=colore%>"> 
      <p align="center">&nbsp;<a href="dettprodotto.asp?ID_prodotto=<%=(Prodotti.Fields.Item("ID_prodotto").Value)%>"><img src="../../../../immagini/sistema/bottoni/open.gif" width="25" height="26" border="0"></a></p>
    </td>
    <td width="43%"><%=(Prodotti.Fields.Item("proDescrizione").Value)%></td>
    <td width="35%"> 
      <p><%=(Prodotti.Fields.Item("cliRagioneSociale").Value)%>&nbsp&nbsp&nbsp <%=(Prodotti.Fields.Item("cliPaese").Value)%></p>
    </td>
    <td align="left" width="14%"><%=(Prodotti.Fields.Item("catDescrizione").Value)%> </td>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Prodotti.MoveNext()
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
      &nbsp;<font color="#990000">Prodotti</font><font color="#990000"> dal <b><%=(Prodotti_first)%></b> al <b><%=(Prodotti_last)%></b> su <b><%=(Prodotti_total)%></b> </font></td>
    <td width="16%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="21%" height="29">&nbsp; </td>
  </tr>
</table>
<p>&nbsp;</p>
</body>
</html>
<%
Prodotti.Close()
%>
<%
Categorie.Close()
%>
<%
Ditte.Close()
%>
