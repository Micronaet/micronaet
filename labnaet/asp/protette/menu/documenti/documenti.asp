<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/librerie/codice/icone.asp" -->
<!--#include virtual="/labnaet/librerie/codice/gestione.asp" -->
<!--#include virtual="/labnaet/librerie/codice/testo.asp" -->

<%
' Dichiarazione delle funzioni utilizzate nella form
dim Puntatore

' Inizio programmazione form
Dim Documenti__qryAzienda
Documenti__qryAzienda = "0" 
if (Session("IDDitta") <> "") then Documenti__qryAzienda = Session("IDDitta")
Dim Documenti__qryUtente
Documenti__qryUtente = "0"
if (Session("Level") <> "") then Documenti__qryUtente = Session("Level")

' analisi dei parametri passati con la form
Dim CondWhere ,CondWhereStd, temp 
' valore iniziale imposto dalla ditta e dal'utente
CondWhereStd="(docAzienda = " + Replace(Documenti__qryAzienda, "'", "''") + ") AND (docAccesso <= " + Replace(Documenti__qryUtente, "'", "''") + ")"
CondWhere=""

select case Request.Form("hidSwitch") ' arrivo dalla videata di ricerca dettagliata
   case 1: ' ricerca avanzata	   
	   ' ****************************************** TESTO *********************************************************
	   ' ***************** Ricerca del testo ***************************
	   temp= Request.Form("txtTesto")
	   if temp <> "" then ' è presente del testo da ricercare
		  CondWhere= CondWhere + " and " & ParseTesto(temp)
	   end if	
	   ' ******************************************** COMBO *******************************************************
	   ' ***************** Ricerca del protocollo **********************
	   temp= Request.Form("cboProtocolli")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_protocollo="+temp+")"
	   end if	
	   ' ***************** Ricerca per la tipologia ********************
	   temp= Request.Form("cboTipologie")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_tipologia="+temp+")"
	   end if	
	   ' ***************** Ricerca per la Lingua ***************************
	   temp= Request.Form("cboLingue")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_lingua="+temp+")"
	   end if	
	   ' ***************** Ricerca per la Categoria della ditta ************
	   temp= Request.Form("cboTipi")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_tipo="+temp+")"
	   end if	
	   ' ***************** Ricerca per la Categoria della ditta ************
	   temp= Request.Form("CboNazioni")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_nazione="+temp+")"
	   end if	
	   ' ***************** Ricerca per il Cliente ************
	   temp= Request.Form("CboClienti")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (ID_cliente="+temp+")"
	   end if	
	   ' **************************** RANGE *************************************************************************** 
	   ' ***************** Ricerca per il numero di protocollo ************
	   temp= Request.Form("txtDalNum")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docNumero>="+Cstr(temp)+")"
	   end if
	   temp= Request.Form("txtalNum")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docNumero<="+Cstr(temp)+")"
	   end if	
	   ' ***************** Ricerca per il numero di fax ************
	   temp= Request.Form("txtDalFax")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docFax>="+Cstr(temp)+")"
	   end if
	   temp= Request.Form("txtalFax")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docFax<="+Cstr(temp)+")"
	   end if	
	   ' ***************** Ricerca per data ************
	   temp= Request.Form("txtDallaData")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docData>=" & DataSQL(temp, Session("Remoto")) & ")"
	   end if
	   temp= Request.Form("txtallaData")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + " and (docData<=" & DataSQL(temp, Session("Remoto")) &")"
	   end if	

       ' ******************** GESTIONE DEI PRODOTTI ************************************************** 
       if GestisceProdotti then 
	      temp= Request.Form("cboProdotto")
	      if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		     CondWhere= CondWhere + " and (ID_prodotto="+temp+")"
	      end if		   

	      temp= Request.Form("cboCategoria")
	      if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		     CondWhere= CondWhere + " and (ID_categoria="+temp+")"
	      end if		   

	      temp= Request.Form("cboProduttore")
	      if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		     CondWhere= CondWhere + " and (ID_produttore="+temp+")"
	      end if		   
	   end if
	   ' *************************************** ORDINAMENTI ************************************************
	   temp= Request.Form("cboOrdine1")
	   ' è presente il nome del protocollo
	   CondWhere =CondWhere + " ORDER BY " & temp & " DESC "	
	   temp= Request.Form("cboOrdine2")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + ", " & temp & " DESC "
	   end if	
	   temp= Request.Form("cboOrdine3")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + ", " & temp & " DESC "
	   end if	   
	   Session("CondWhere")=CondWhere ' memorizzo per i passaggi da videata in videata
       Session("CondWhereDown")=CondWhereStd+CondWhere 'condizione memorizzata per l'eventuale download dei file
	case 2: ' ricerca semplice   	   
	   ' ****************************************** TESTO *********************************************************
	   ' ***************** Ricerca del testo *************************
	   temp= Request.Form("txtTesto")
	   if temp <> "" then ' è presente del testo da ricercare
		  CondWhere= CondWhere + " and " & ParseTesto (temp)  	     
	   end if	   
	   ' *************************************** ORDINAMENTI ************************************************
	   temp= Request.Form("cboOrdine1")
	   'if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
	   CondWhere =CondWhere + " ORDER BY " & temp & " DESC "
	   temp= Request.Form("cboOrdine2")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + ", " & temp & " DESC "
	   end if	
	   temp= Request.Form("cboOrdine3")
	   if (temp <> "") and (temp<>"0") then ' è presente il nome del protocollo
		  CondWhere= CondWhere + ", " & temp & " DESC "
	   end if	
	   Session("CondWhere")=CondWhere ' memorizzo per i passaggi da videata in videata
       Session("CondWhereDown")=CondWhereStd+CondWhere ' condizione memorizzaa per l'eventuale download dei file
	case else  ' videata creata dai passaggi di range dell'elenco (utilizzato anche dalla videata upload questo passaggio)
       CondWhere= Session("CondWhere") ' ricarico nel caso il passaggio della videata venga attivato il valore dei dati form
end select
set Documenti = Server.CreateObject("ADODB.Recordset")
Documenti.ActiveConnection = MM_SQLDocnaet_STRING
dim NomeVista
if GestisceProdotti then NomeVista="vwDocumentiProdotti" else NomeVista="vwDocumenti"
Documenti.Source = "SELECT *  FROM "+NomeVista+" WHERE "+ CondWhereStd+ CondWhere  ' aggiungo la parte std a quella che viene generata di volta in volta
Documenti.CursorType = 0
Documenti.CursorLocation = 2
Documenti.LockType = 3
Documenti.Open()
Documenti_numRows = 0

Dim Repeat1__numRows
Repeat1__numRows = DocumentiRighe ' carico il numero di documenti predefinito per questo sito
Dim Repeat1__index
Repeat1__index = 0
Documenti_numRows = Documenti_numRows + Repeat1__numRows
'  *** Recordset Stats, Move To Record, and Go To Record: declare stats variables
' set the record count
Documenti_total = Documenti.RecordCount
' set the number of rows displayed on this page
If (Documenti_numRows < 0) Then
  Documenti_numRows = Documenti_total
Elseif (Documenti_numRows = 0) Then
  Documenti_numRows = 1
End If
' set the first and last displayed record
Documenti_first = 1
Documenti_last  = Documenti_first + Documenti_numRows - 1
' if we have the correct record count, check the other stats
If (Documenti_total <> -1) Then
  If (Documenti_first > Documenti_total) Then Documenti_first = Documenti_total
  If (Documenti_last > Documenti_total) Then Documenti_last = Documenti_total
  If (Documenti_numRows > Documenti_total) Then Documenti_numRows = Documenti_total
End If
' *** Recordset Stats: if we don't know the record count, manually count them
If (Documenti_total = -1) Then

  ' count the total records by iterating through the recordset
  Documenti_total=0
  While (Not Documenti.EOF)
    Documenti_total = Documenti_total + 1
    Documenti.MoveNext
  Wend

  ' reset the cursor to the beginning
  If (Documenti.CursorType > 0) Then
    Documenti.MoveFirst
  Else
    Documenti.Requery
  End If

  ' set the number of rows displayed on this page
  If (Documenti_numRows < 0 Or Documenti_numRows > Documenti_total) Then
    Documenti_numRows = Documenti_total
  End If

  ' set the first and last displayed record
  Documenti_first = 1
  Documenti_last = Documenti_first + Documenti_numRows - 1
  If (Documenti_first > Documenti_total) Then Documenti_first = Documenti_total
  If (Documenti_last > Documenti_total) Then Documenti_last = Documenti_total

End If
%>
<%
' *** Move To Record and Go To Record: declare variables

Set MM_rs    = Documenti
MM_rsCount   = Documenti_total
MM_size      = Documenti_numRows
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
Documenti_first = MM_offset + 1
Documenti_last  = MM_offset + MM_size
If (MM_rsCount <> -1) Then
  If (Documenti_first > MM_rsCount) Then Documenti_first = MM_rsCount
  If (Documenti_last > MM_rsCount) Then Documenti_last = MM_rsCount
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
<title>Documenti trovati</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/documenti.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<% 
dim colore, tempData
%>
<%
if Documenti_total <>0 then 
%>
<table width="100%" border="1" cellpadding="1" cellspacing="1">
  <tr> 
    <td width="15%" align="center" valign="middle" bgcolor="#FFFFCC"> 
      <table border="0" align="center" width="100" height="27" cellpadding="0" cellspacing="0" bordercolor="#FFFFCC" bgcolor="#FFFFCC">
        <tr bgcolor="#FFFFCC"> 
          <td width="23%" align="center" height="25"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_moveFirst%>"><img src="../../../../immagini/sistema/bottoni/icone/First.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="31%" align="center" height="25" bordercolor="#FFFFCC"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_movePrev%>"><img src="../../../../immagini/sistema/bottoni/icone/Previous.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="23%" align="center" height="25"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveNext%>"><img src="../../../../immagini/sistema/bottoni/icone/Next.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
          <td width="23%" align="center" height="25"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveLast%>"><img src="../../../../immagini/sistema/bottoni/icone/Last.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
        </tr>
      </table>
    </td>
    <td width="55%" height="27" align="center" valign="middle" bgcolor="#CEECFD">Documenti 
      da&nbsp;<%=(Documenti_first)%> a&nbsp;<%=(Documenti_last)%> di&nbsp;<%=(Documenti_total)%> 
    </td>
    <td width="30%" height="27" align="right" bgcolor="#FFFFCC"> 
      <%'if Request.Form("hidNuovaFinestra")="0" then %>
      <a href="downloadok.asp"><img src="../../../../immagini/sistema/bottoni/download1.gif" width="23" height="26" border="0"></a> 
      &nbsp; <a href="easyfind.asp"><img src="../../../../immagini/sistema/bottoni/icone/lente.gif" width="23" height="23" border="0" alt="Ricerca semplice"></a> 
      &nbsp; <a href="ricerca.asp"><img src="../../../../immagini/sistema/bottoni/search.gif" width="23" height="23" border="0" alt="Ricerca avanzata"></a> 
      <%'end if%>
    </td>
  </tr>
</table>
<table width="100%" border="0" cellpadding="0" cellspacing="2">
  <tr> 
    <td width="90"> 
      <div align="center"><b>Oper.</b></div>
    </td>
    <td width="10%"> 
      <div align="center"><b>Num </b></div>
    </td>
    <td width="12%"> 
      <div align="center"><b>Protocollo</b></div>
    </td>
    <td width="26%"> 
      <div align="center"><b>Oggetto</b></div>
    </td>
    <td width="24%"> 
      <div align="center"><b>Descrizione</b></div>
    </td>
    <td width="20%"> 
      <div align="center"><b>Ditta</b></div>
    </td>
  </tr>
  <%
  else
  %>
  <tr>
    <td colspan="6"> Nessun documento trovato, perfezionare la ricerca </td>
  </tr>
  <%	 
  end if
  %>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Documenti.EOF)) 
if Repeat1__numRows mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  

%>
  <tr bgcolor=<%=colore%>> 
    <td width="90" align="center"> <a href="modifica.asp?ID_documento=<%=(Documenti.Fields.Item("ID_documento").Value)%>&ID_cliente=<%
	    'if (Documenti.Fields.Item("ID_cliente").Value=0) then Response.Write("0") else Response.Write(Documenti.Fields.Item("ID_cliente").Value)
		Response.Write(Documenti.Fields.Item("ID_cliente").Value)		%>"><img src="../../../../immagini/sistema/bottoni/open.gif" width="18" height="21" border="0"></a> 
      <a href="file://<%=getNomeFile(Documenti.Fields.Item("ID_documento"),Documenti.Fields.Item("ID_protocollo"),Session("IDDitta"),Documenti.Fields.Item("ID_supporto"),Documenti.Fields.Item("docFile"),Documenti.Fields.Item("docEstensione"), Puntatore)
%>" target="_blank"> <img src="../../../../immagini/sistema/logo/documenti/ie.gif" width="20" height="20" border="0"></a> 
<a href="labnaet://<%=getNomeFileDocnaet(Documenti.Fields.Item("ID_documento"),Documenti.Fields.Item("ID_protocollo"),Session("IDDitta"),Documenti.Fields.Item("ID_supporto"),Documenti.Fields.Item("docFile"),Documenti.Fields.Item("docEstensione"), Puntatore)
%>"> <img src="<%=GetImmagine(Documenti.Fields.Item("docEstensione").value, Puntatore)%>" width="20" height="20" border="0"></a> 
    </td>
    <td width="10%"> 
      <%if isnull(Documenti.Fields.Item("docData").Value) then
	       tempData=""
		else
		   tempData=" del " + Cstr(Documenti.Fields.Item("docData").Value)
		end if   
	    if isnull(Documenti.Fields.Item("docNumero").Value) then 
	       Response.Write("?" + tempData) 
		else 
		   Response.Write(Cstr((Documenti.Fields.Item("docNumero").Value)) + tempData)
		end if   
	  %>
    </td>
    <td width="12%"><%=(Documenti.Fields.Item("proDescrizione").Value)%></td>
    <td width="26%"><%=(Documenti.Fields.Item("docOggetto").Value)%></td>
    <td width="24%"><%=(Documenti.Fields.Item("docDescrizione").Value)%></td>
    <td width="20%"><%=(Documenti.Fields.Item("cliRagioneSociale").Value)%><%="("+(Documenti.Fields.Item("tipDescrizione").Value)+")"%><%="("+(Documenti.Fields.Item("nazDescrizione").Value)+")"%></td>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Documenti.MoveNext()
Wend
%>
</table>
<%

if Documenti_total <>0 then 
%>
<table width="100%" border="1" cellpadding="1" cellspacing="1">
  <tr> 
    <td width="15%" align="center" valign="middle" bgcolor="#FFFFCC"> 
      <table border="0" align="center" width="100" height="27" cellpadding="0" cellspacing="0" bgcolor="#FFFFCC">
        <tr bgcolor="#FFFFCC"> 
          <td width="23%" align="center" height="25"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_moveFirst%>"><img src="../../../../immagini/sistema/bottoni/icone/First.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="31%" align="center" height="25"> 
            <% If MM_offset <> 0 Then %>
            <a href="<%=MM_movePrev%>"><img src="../../../../immagini/sistema/bottoni/icone/Previous.gif" border=0></a> 
            <% End If ' end MM_offset <> 0 %>
          </td>
          <td width="23%" align="center" height="25"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveNext%>"><img src="../../../../immagini/sistema/bottoni/icone/Next.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
          <td width="23%" align="center" height="25"> 
            <% If Not MM_atTotal Then %>
            <a href="<%=MM_moveLast%>"><img src="../../../../immagini/sistema/bottoni/icone/Last.gif" border=0></a> 
            <% End If ' end Not MM_atTotal %>
          </td>
        </tr>
      </table>
    </td>
    <td width="55%" align="center" valign="middle" bgcolor="#CEECFD">Documenti 
      da&nbsp;<%=(Documenti_first)%> a&nbsp;<%=(Documenti_last)%> di&nbsp;<%=(Documenti_total)%> 
    </td>
    <td width="30%" align="right" bgcolor="#FFFFCC" valign="middle"><a href="easyfind.asp"> 
      </a> 
      <%'if Request.Form("hidNuovaFinestra")="0" then %>
      <a href="downloadok.asp"><img src="../../../../immagini/sistema/bottoni/download1.gif" width="23" height="26" border="0"></a> 
      &nbsp; <a href="easyfind.asp"><img src="../../../../immagini/sistema/bottoni/icone/lente.gif" width="23" height="23" border="0" alt="Ricerca semplice"></a> 
      &nbsp; <a href="ricerca.asp"><img src="../../../../immagini/sistema/bottoni/search.gif" width="23" height="23" border="0" alt="Ricerca avanzata"></a> 
      <%'end if%>
    </td>
  </tr>
</table>
<%
end if
%>
</body>
</html>
<%
Documenti.Close()
%>
