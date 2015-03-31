<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/gestione.asp" -->
<%
dim fso,fldr,f1,i, temp, Puntatore, temp1, colore

set Documenti = Server.CreateObject("ADODB.Recordset")
with Documenti
	.ActiveConnection = MM_SQLDocnaet_STRING
	
	if GestisceProdotti then NomeVista="vwDocumentiProdotti" else NomeVista="vwDocumenti"
	
	.Source = "SELECT *  FROM "+NomeVista+" WHERE "+Session("CondWhereDown")  ' aggiungo la parte std a quella che viene generata di volta in volta
	.CursorType = 0
	.CursorLocation = 2
	.LockType = 3
	.Open()
	Documenti_numRows = 0

    ' inizializzazioni:
    Set fso = CreateObject("Scripting.FileSystemObject")
    Percorso=getCartellaDownload 
    fso.CreateTextFile (Percorso+"download.htm")
    Set f1 = fso.GetFile(Percorso+"download.htm")
    Set t1 = f1.OpenAsTextStream(2, 0)         
	' creo il file html
	t1.write "<html><head><title>Documenti</title><meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'></head><body bgcolor='#FFFFFF' text='#000000'></body>"
    t1.write "<table width='900' border='0' cellspacing='2' cellpadding='0'>"
	t1.write "<tr bgcolor='#CEECFD' align='center'><td colspan='2'><font face='Lucida Sans Unicode' size='2'><b>Elenco documenti estrapolati dal programma docnaet</b></font></td></tr>"
		
	i=0
    While (NOT .EOF)
       i=i+1
	   ' ricavo il nome del file
	   temp1=getOnlyFile (.Fields.Item("ID_documento"),.Fields.Item("docFile"),.Fields.Item("docEstensione")) 
	   
       ' scrivo la riga descrittiva del documento nel file di testo
	   temp= ""
	   if not isnull(.Fields.Item("docNumero").Value) then temp=temp +Cstr(Documenti.Fields.Item("docNumero").Value) else temp=temp+"?"
	   if not isnull(.Fields.Item("docData").Value) then temp=temp+ " del " + Cstr(Documenti.Fields.Item("docData").Value)
       if not isnull(.Fields.Item("proDescrizione").Value) then temp=temp+" (<b>"+ .Fields.Item("proDescrizione").Value+"</b>)"
       if not isnull(.Fields.Item("docOggetto").Value) then temp=temp+" "+left(.Fields.Item("docOggetto").Value,40)
       if not isnull(.Fields.Item("cliRagioneSociale").Value) then temp=temp+" "+.Fields.Item("cliRagioneSociale").Value
	   temp=temp+ vbcrlf
	   
	   if i mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  
   
       t1.Write  "<tr  bgcolor="+colore+"><td width='200'><a target ='_blank' href='"+temp1+"'><font face='Lucida Sans Unicode' size='2'>"+Cstr(i)+ ") "+temp1+"</font></a></td><td width='700'><font face='Lucida Sans Unicode' size='2'>"+temp +  "</font></td></tr>"	   	   
	   ' copia effettiva del documento nella cartella di download
	   temp=getNomeFile(.Fields.Item("ID_documento"),.Fields.Item("ID_protocollo"),Session("IDDitta"),.Fields.Item("ID_supporto"),.Fields.Item("docFile"),.Fields.Item("docEstensione"), Puntatore)
	   If (fso.FileExists(temp)) then 
	      If (fso.FileExists(Percorso+temp1)) then fso.deletefile percorso+temp1 ,true ' elimino il file se già presente nella cartella
	      fso.CopyFile temp,Percorso+temp1
	   end if  	   
	   .MoveNext()
    Wend     
	t1.write "</table></html>" ' chiudo il file html
    t1.Close
end with
%>
<html>
<head>
<title>Download Documenti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" topmargin="1" leftmargin="1">
<p align="center"><font color="#006633"><br>
  Download effettuato con successo!<br>
  <br>
  </font></p>
<table width="278" border="0" cellspacing="0" cellpadding="0" align="center">
  <tr align="center"> 
    <td><a href="<%=Percorso+"download.htm"%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/anteprima.gif" width="28" height="31" border="0"></a></td>
    <td><font color="#006633"><a href="<%=Percorso%>" target="_blank"><img src="../../../../immagini/sistema/bottoni/icone/esplora.gif" width="27" height="26" border="0"></a></font></td>
    <td><font color="#006633"><a href="javascript:window.history.back()"><img src="../../../../immagini/sistema/bottoni/icone/freccia.gif" width="22" height="30" border="0"></a></font></td>
  </tr>
</table>
</body>
</html>

