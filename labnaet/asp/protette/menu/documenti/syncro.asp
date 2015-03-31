<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/librerie/codice/protocollazione.asp" -->

<html>
<head>
<title>Syncro documenti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/documenti.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<%
dim CartellaDiLavoro,i, Ricaricata, colore

' inizializzazioni
CartellaDiLavoro=getCartellaSyncro()
if request.form("hidReload")="true" then   
   Ricaricata=true 
else   
   Ricaricata=false
end if   
%>

<table width="100%" border="0">
  <tr> 
    <td colspan="5"> 
      <div align="center"><b>Sincronizzazione documenti:</b></div>
    </td>
  </tr>
  <tr bgcolor="#CEECFD"> 
    <td> 
      <div align="center"><b>Nome File</b></div>
    </td>
    <td width="52%"> 
      <div align="center"><b>Stato</b></div>
    </td>
  </tr>
<%
Dim fso, f, f1, fc, Nome, Estensione, tmp, Esito, CartellaDestinazione, Puntatore, f2

Set fso = CreateObject("Scripting.FileSystemObject")
Set f = fso.GetFolder(CartellaDiLavoro)
Set fc = f.Files   
i=0
For Each f1 in fc
	    i=i+1 
		tmp=Instr(1, f1.name ,".", 0)
        Nome=left(f1.name,tmp) ' estrapolo il nome del file
		Estensione=Right(f1.name,len(f1.name)- tmp) ' estrapolo l'estensione
		 
		if i mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" 
		'Documenti.Source = "SELECT ID_documento, ID_protocollo, docAzienda, ID_supporto, docFile, docEstensione FROM Documenti WHERE (ID_Documento="+Nome+" or docFile='"+Nome+"') and docAzienda="+Session("IDDitta")+ " and docEstensione='"+Estensione+"'"
        set Documenti = Server.CreateObject("ADODB.Recordset")
        with Documenti
             .ActiveConnection = MM_SQLDocnaet_STRING
             .CursorType = 0
             .CursorLocation = 2
             .LockType = 3
        end with
		Documenti.Source = "SELECT * FROM Documenti WHERE (ID_Documento="+Nome+" or docFile='"+Nome+"') and docAzienda="+Session("IDDitta")+ " and docEstensione='"+Estensione+"'"
        Documenti.Open()         
	%>
  <tr> 
    <td bgcolor="<%=colore%>" >
	<%
	if not Ricaricata then
	%>
	<a href="<%=(CartellaDiLavoro + f1.name)%>" target="_blank"><%=f1.name +" (" & Cstr (f1.DateLastModified )+ ")"%></a> 
      &gt;&gt;
	<%end if
    ftemp=getNomeFile(Documenti.Fields.Item("ID_documento"),Documenti.Fields.Item("ID_protocollo"),Session("IDDitta"),Documenti.Fields.Item("ID_supporto"),Documenti.Fields.Item("docFile"),Documenti.Fields.Item("docEstensione"), Puntatore)	
	set f2=fso.getFile(ftemp)
	%>  
	<%if Documenti.Eof then Response.Write("Non trovato") else Response.Write("<a target='_blank' href='file://"+ftemp)+"'>originale (" & Cstr(f2.DateLastModified )+")</a>" %></td>
    <td width="52%" bgcolor="<%=colore%>">
	<% 
	  if not Ricaricata then 
	     Response.Write("Da sincronizzare") 
	  else ' effettuo lo spostamneto 
         if Documenti.EOF then
		    Esito="Non trovato il documento da sincronizzare!"
		 else
		    ' calcolo la cartella del file per copiarlo e cancellarlo
			CartellaDestinazione=Application("CartellaDati") +"\"+Session("IDDitta")+"\" & Cstr(Documenti.Fields("ID_protocollo").value)
            on error resume next
			fso.CopyFile CartellaDiLavoro + f1.name,CartellaDestinazione+ "\" & f1.name			
	        if err then
			   Esito=err.description
			else
			   Esito="Documento "+ f1.name+" sincronizzato!"
			   fso.deletefile CartellaDiLavoro + f1.name
			end if      					
		 end if
		 Documenti.Close()
	     Response.Write(Esito)
	  end if	 
	  %></td>
  </tr>
  <%
	next 	
  %>
</table>
<%if i=0 then %>
<div align="center"><br>
  Nessun documento da sincronizzare! 
  <%else%>
  <br>
</div>
<form name="form1" method="post" action="syncro.asp">
  <div align="center">
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/upload.gif" width="40" height="46" alt="Sincronizza con archivio server">
    <input type="hidden" name="hidReload" value="true">
  </div>
</form>
<%end if%>
</body>
</html>
