<%

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL FILE *******************
function getNomeFile(IDDoc, IDProt,IDAz, IDSupp, NomeFile, Estensione, Puntatore) 
    dim temp
	
    If IDSupp="" then  ' non mi trovo sul supporto	   
	   temp=Application("CartellaDati") + "\"+ Cstr(IDAz) + "\" + Cstr(IDProt) + "\"
	else    ' c'è il supporto
	   'temp=Application("CartellaDati") + "\"+IDAz + "\" + IDProt + "\"
       temp=Application("CartellaDati") +"\"+ Cstr(IDAz) + "\" + Cstr(IDProt) + "\"	   
	end if   
    if (NomeFile= "") or (VarType(NomeFile)=vbNull)  then  	   ' il file è originale
       Puntatore=false
	   getNomeFile =temp & Cstr(IDDoc) &  "." & Estensione
	else  ' il file è un puntatore
           Puntatore=true
	   getNomeFile =temp & Cstr(NomeFile) & "." & Estensione     
	end if		
end function

function getNomeFileDocnaet(IDDoc, IDProt,IDAz, IDSupp, NomeFile, Estensione, Puntatore) 
    dim temp
	
    If IDSupp="" then  ' non mi trovo sul supporto	   
	   temp= Cstr(IDAz) + "\" + Cstr(IDProt) + "\"
	else    ' c'è il supporto
	   'temp=IDAz + "\" + IDProt + "\"
       temp= Cstr(IDAz) + "\" + Cstr(IDProt) + "\"	   
	end if   
    if (NomeFile= "") or (VarType(NomeFile)=vbNull)  then  	   ' il file è originale
       Puntatore=false
	   getNomeFileDocnaet=temp & Cstr(IDDoc) &  "." & Estensione
	else  ' il file è un puntatore
           Puntatore=true
	   getNomeFileDocnaet=temp & Cstr(NomeFile) & "." & Estensione     
	end if		
end function

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL FILE *******************
function getNomeFileBatch(IDDoc, IDProt,IDAz, IDSupp, NomeFile, Estensione, Puntatore) 
'    dim temp, Nome

'    Nome=getNomeFile(IDDoc, IDProt,IDAz, IDSupp, NomeFile, Estensione, Puntatore) 
'    temp=Application("CartellaDati") +"\"+ Cstr(IDAz) + "\" + Cstr(IDProt) + "\" & Cstr(IDDoc) &  ".bat" 

'    Set fso = CreateObject("Scripting.FileSystemObject")
'    fso.CreateTextFile (temp)
'    Set f1 = fso.GetFile(temp)
'    Set t1 = f1.OpenAsTextStream(2, 0)
'    t1.Write Nome+ vbcrlf
'    t1.Close
'    getNomeFileBatch=temp
end function

function getOnlyFile(IDDoc, NomeFile, Estensione) 
	
    if (NomeFile= "") or (VarType(NomeFile)=vbNull)  then  	   ' il file è originale
	   getOnlyFile =Cstr(IDDoc) &  "." & Estensione
	else  ' il file è un puntatore
	   getOnlyFile =Cstr(NomeFile) & "." & Estensione     
	end if		
end function
' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO DA UTILIZZARE ****************
function CreoModelloCompleto(IDProt,IDAz,IDLingua, Estensione, IDTipologia, Commento) 
	' Verifico che il file segnalato sia presente altrimenti lo creo copiando il file vuoto dell'applicativo selezionato *
	dim fso, f1, fm, fstd
	' parte di creazione fisica delle tabelle:
    Set fso = CreateObject("Scripting.FileSystemObject")
	f1=getNomeModelloAziendaleCompleto(Request.QueryString("ID_protocollo"),Cstr(Session("IDDitta")),Request.QueryString("ID_Lingua"), Request.QueryString("ID_applicazione"), Request.QueryString("ID_Tipologia")) 
    fm=getNomeModelloAziendale(Request.QueryString("ID_applicazione"), IDAz)
	fstd=getNomeModelloVuoto(Request.QueryString("ID_applicazione"))
	If (fso.FileExists(f1)) Then
       ' esiste il file
	   Commento= "Il documento era già presente."
    Else
	   if (fso.FileExists(fm)) then 
	      fso.CopyFile fm,f1
		  Commento="Il documento non esisteva è stato generato dal modello dell'azienda."
	   else
	      if (fso.FileExists(fstd)) then 
		     fso.CopyFile fstd,fm ' copio il file standard nei modelli dell'azienda
	         fso.CopyFile fm,f1 ' copio il modello dell'azienda nel modello nuovo
		     Commento="Il documento non esisteva è stato generato dal modello generico."
		  else
		     Commento="Non è possibile aprire il modello."
		  end if
	   end if
    End If
    CreoModelloCompleto=f1 ' memorizzo il nome per tornarlo al chiamante (per l'eventuale apertura
end function
' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO DA UTILIZZARE ****************
function getNomeModello(IDProt,IDAz,IDLingua, Estensione, IDTipologia) 
    dim temp, fso, tempStd, tempVuoto

    temp=getNomeModelloAziendaleCompleto(IDProt, IDAz, IDLingua, Estensione, IDTipologia) ' nome del file con modello completo
    tempStd=getNomeModelloAziendale(Estensione, IDAz) ' nome del file aziendale standard
	tempVuoto=getNomeModelloVuoto(Estensione) ' file vuoto (c'è per creazione iniziale

    ' mi assicuro dell'esistenza del file
    set fso=Server.CreateObject("Scripting.FileSystemObject")	 
    if fso.FileExists(temp) then
       getNomeModello=temp
    else
	   if fso.FileExists(tempStd) then
	      getNomeModello=tempStd
	   else
	      getNomeModello=tempVuoto
	   end if	  
    end if
end function

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO COMPLETO ****************
function getNomeModelloAziendaleCompleto(IDProt,IDAz,IDLingua, Estensione, IDTipologia) 
    dim temp, fso

    temp=Application("CartellaDati") + "\" + Cstr(IDAz) + "\" + Cstr(IDProt) + "\modelli\"
    if (IDLingua <>"") then 
       temp =temp + Cstr(IDLingua) +  "." 
    else
       temp =temp + "0." 
    end if
    if (IDTipologia <>"") then 
       temp =temp + Cstr(IDTipologia) +  "." + Estensione
    else
       temp =temp + "0." + Estensione
    end if
    getNomeModelloAziendaleCompleto=temp
end function

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO AZIENDALE ****************
function getNomeModelloAziendale(Estensione, IDAz) 
    dim temp, fso

    temp=Application("CartellaDati") + "\" + Cstr(IDAz) + "\modelli\0." + Estensione
    getNomeModelloAziendale=temp
end function

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO VUOTO ****************
function getNomeModelloVuoto( Estensione) 
    getNomeModelloVuoto=Application("CartellaDati") & "\modelli\0." & Estensione
end function

' **************  FUNZIONE PER IL CALCOLO DEL NOME DEL MODELLO ****************
function getcartellaModello(IDProt,IDAz)     
    getcartellaModello=Application("CartellaDati") & "\" & Cstr(IDAz) & "\" & IDProt & "\modelli\"    
end function

' ***************  FUNZIONE PER IL CALCOLO DELLA CARTELLA DI UPLOAD  **********
function getCartellaUpload ()
   getCartellaUpload=Application("UsersFolder") &  Session("UserName") & "\upload\"
end function

' ***************  FUNZIONE PER IL CALCOLO DELLA CARTELLA DI DOWNLOAD  **********
function getCartellaDownload ()
   getCartellaDownload=Application("UsersFolder") &  Session("UserName") & "\download\"
end function

' ************** FUNZIONE PER AVERE IL NOME DELLA CARTELLA USATA PER LA SINCRONIZZAZIONE ***********
function getCartellaSyncro()
   getCartellaSyncro=Application("UsersFolder") &  Session("UserName") & "\syncro\"
end function

' ***************  FUNZIONE PER IL CALCOLO DELLA CARTELLA DI UPLOAD  **********
function getCartellaFax ()
   getCartellaFax =Application("FaxFolder")
end function

' ***************  funzione per la creazione del nuovo file *************************
function GeneraFileNuovo(Controllo,IDDitta,Puntatore, StringaConnessione)
   Set DocumentiIntestazione = Server.CreateObject("ADODB.Recordset")
   with DocumentiIntestazione ' creo la vista per recuperare i dati intestazione e nome file  
     .ActiveConnection = StringaConnessione
     .Source = "SELECT * FROM Documenti WHERE docControllo='"+Cstr(Controllo)+"'"
     .CursorType = 0
     .CursorLocation = 2
     .LockType = 3
 	 .Open()

     dim FileNuovo, FileModello, fso
     FileNuovo=getNomeFile(.fields("ID_documento").value,.fields("ID_protocollo").value,IDDitta,.fields("ID_supporto").value, .fields("docFile").value, .fields("docEstensione").value, Puntatore)
     FileModello=getNomeModello(.fields("ID_protocollo").value,IDDitta,.fields("ID_lingua").value, .fields("docEstensione").value,.fields("ID_tipologia").value) 
	 set fso=Server.CreateObject("Scripting.FileSystemObject")
	 fso.CopyFile FileModello, FileNuovo 
   end with
   GeneraFileNuovo=FileNuovo
end function

%>


	
