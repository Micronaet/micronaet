<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->
<!--#include virtual="/labnaet/librerie/codice/protocollazione.asp" -->

<html>
<head>
<title>Upload documenti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/documenti.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<%
' dimensionamento ed inizializzazione delle variabili
dim iDoc, DalProt,parametri, DevoProtocollare, Fisso, temp
Fisso= 7 ' sono gli elementi che sono fissi all'inizio dell'array passato alla videata
DevoProtocollare=false ' inizializzo a falso
DalProt=0 ' inizializzo a 0
parametri= Split(Replace(Request.Querystring(),"%20"," ") ,"|", -1, 1) 

dim CartellaDiLavoro
select case parametri(0)
       case "1": ' aperto per l'upload
	        CartellaDiLavoro=getCartellaUpload ()
	   case "2": ' aperto per i fax
	        CartellaDiLavoro=getCartellaFax ()	           
end select	     
	
if parametri(2)="1" and parametri(3)<>"0" then ' se è il caso blocco gli N numeri di protocollo (voglio protocollare ed è selezionato il protocollo
  DevoProtocollare=true 
  iDoc=Clng(ubound( parametri)+1-Fisso) ' calcolo il numero di documenti da protocollare
  
  DalProt=BloccaProtocolli(parametri(3), iDoc, MM_SQLDocnaet_STRING)  
end if  

dim i, ID, fso, f1, f2, controllo, file1, file2
' apro la connessione con la tabella dei documenti:
set Documenti = Server.CreateObject("ADODB.Recordset")
with Documenti
    .ActiveConnection = MM_SQLDocnaet_STRING
    .Source = "Documenti"
    .CursorType = 0
    .CursorLocation = 2
    .LockType = 3
    .Open()
	
    controllo =Cstr(now) ' segna l'ora del inserimento
	for i = 0 to ubound( parametri)-fisso ' creo N  registrazioni per poi accogliere successivamente i documenti interessati
	   ' creazione della registrazione  (prima passata)
		   .AddNew()
		   .fields("ID_protocollo").Value=parametri(3) ' ID_protocollo
		   .fields("docData").value= Date  '"01/01/1972" '(date()) ' Data attuale
		   .fields("docAzienda").value=Session("IDDitta")
		   .fields("docAccesso").value=0 ' accessibile a tutti
		   if Session("UserID")="" then Session("UserID")=0 
		   .fields("ID_utente").value=Session("UserID") ' memorizzo l'ID dell'utente che li ha inseriti
		   .fields("docControllo").value=controllo' metto il time stamp attuale per effettuare la query in un momento successivo
		   .fields("docNumero").value=DalProt ' numero di protocollo ****************************** Mettere il giusto valore successivamente)
		   .fields("docDescrizione").value=parametri(i+Fisso) ' salvo il nome del file originale
		   .fields("docEstensione").value= Right(parametri(i+Fisso),len(parametri(i+Fisso))- Instr(1, parametri(i+Fisso) ,".", 0)) ' calcolo l'estensione
		   .fields("ID_cliente").value= Cstr(parametri(4)) ' metto l'ID del cliente
		   .fields("ID_lingua").value= Cstr(parametri(5)) 
		   .fields("ID_tipologia").value= Cstr(parametri(6)) 
		   .Update()
           if DevoProtocollare then DalProt=DalProt+1
	next
	.Close()
	.Source = "SELECT * FROM Documenti WHERE (docControllo='"+ controllo+"')" ' cambio la source prendendo solamente quelli che mi interessano per reimpostargli il nome del file ed il numero di protocollo
	.Open() ' rieseguo la query per ottenere i dati per integrare i file nella base di dati
	.MoveFirst() ' mi posiziono sul primo elemento della lista    
	Set fso = CreateObject("Scripting.FileSystemObject")   
	while not(.EOF)
	     ' creazione della registrazione  (prima passata)
		 f1=getNomeFile(.fields("ID_documento").value, .fields("ID_protocollo").Value,.fields("docAzienda").value,.fields("ID_supporto").value, .fields("docFile").value, .fields("docEstensione").value, Puntatore) 
		 f2=CartellaDiLavoro  & .fields("docDescrizione").value 
		 fso.CopyFile f2,f1
		 if (parametri (1) ="1") then ' elimino il file originale
            fso.DeleteFile(f2)
	     end if
		 .MoveNext()	   
	wend 
end with	  
   Documenti.Close()  
' chiamo la pagina dei documenti per visualizzare solamente quelli che ho appena inserito
Session("CondWhere")  =" and (docControllo='"+ controllo+"') ORDER BY docNumero" ' imposto i parametri per il filtro che verranno utilizzati
' passare il controllo alla videata per la visualizzazione dei documenti
%>
<form name="form1" method="post" action="documenti.asp">
  <br>
  <div align="center"><b><font color="#009933">
<%
Response.Write("Inserimento effettuato correttamente! cliccare sull'immagine per visualizzare il risultato")
%>
    </font></b> </div>
  <br>
  <div align="center">
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/detail.gif" width="48" height="48">
  </div>
</form>
</body>
</html>
