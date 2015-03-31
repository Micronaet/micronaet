<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
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
  MM_editTable = "Protocolli"
  MM_editRedirectUrl = "pconferma.asp"
  MM_fieldsStr  = "txtDescrizione|value|ID_azienda|value|txtNote|value|proProssimo|value|select|value"
  MM_columnsStr = "proDescrizione|',none,''|ID_azienda|none,none,NULL|proNote|',none,''|proProssimo|none,none,NULL|ID_applicazione|none,none,NULL"

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
set Applicazioni = Server.CreateObject("ADODB.Recordset")
Applicazioni.ActiveConnection = MM_SQLDocnaet_STRING
Applicazioni.Source = "SELECT * FROM Applicazioni ORDER BY ID_applicazione ASC"
Applicazioni.CursorType = 0
Applicazioni.CursorLocation = 2
Applicazioni.LockType = 3
Applicazioni.Open()
Applicazioni_numRows = 0
%>
<%
' *** Insert Record: set variables

If (CStr(Request("MM_insert")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
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
  dim NomeProtocollo, Note
  NomeProtocollo=  CStr(Request("txtDescrizione")) ' deve esistere
  Note=  CStr(Request("txtNote"))
  MM_editQuery = "insert into Protocolli (proDescrizione, proProssimo, proNote, ID_azienda) values ('"+NomeProtocollo+"',1,'"+note+"',"+Session("IDDitta")+")"

  If (Not MM_abortEdit) Then
    ' execute the insert
    Set MM_editCmd = Server.CreateObject("ADODB.Command")
    MM_editCmd.ActiveConnection = MM_editConnection
    MM_editCmd.CommandText = MM_editQuery
    MM_editCmd.Execute
    MM_editCmd.ActiveConnection.Close
' *******************************************************************************************************	
	' dopo l'inserimento creo la cartella sul server con il nuovo protocollo
	dim fso, fldr, f1 , Percorso, t1, TabProtocolli, IDProt

	' recupero l'ID del protocollo appena creato: *******
    Connessione1=MM_SQLDocnaet_STRING
    set TabProtocolli=Server.CreateObject("ADODB.Recordset")
    with TabProtocolli
	     .ActiveConnection=MM_rsKeyConnection
         .Source="SELECT ID_protocollo FROM Protocolli WHERE ID_azienda="+Cstr(Session("IDDitta"))+" and proDescrizione='" & NomeProtocollo & "'"
         .CursorType=0
         .CursorLocation=2
         .LockType=3
         .Open()
         If (Not (.EOF)) Or (Not (.BOF)) Then 
	        IDProt=TabProtocolli.Fields.Item("ID_protocollo").value   
		 else
		    ' il nome del protocollo non viene trovato	
	     end if
         .Close()
	end with
	' parte di creazione fisica delle tabelle:
    Set fso = CreateObject("Scripting.FileSystemObject")
	Percorso=Application("CartellaDati")+"\"+Cstr(Session("IDDitta"))+"\"+Cstr(IDProt)
	Set fldr = fso.CreateFolder(Percorso)'' creo la cartella del protocollo
	set fldr=fso.CreateFolder(Percorso+"\modelli") ' creo la tabella che accoglierà i modelli
	set fldr=fso.CreateFolder(Percorso+"\eliminati") ' creo la tabella dove sposto i file eliminati (CESTINO)
    ' Creo il file di testo contenente la documentazione della cartella di protocollo
	fso.CreateTextFile (Percorso+"\nome.txt")
    Set f1 = fso.GetFile(Percorso+"\nome.txt")
    Set t1 = f1.OpenAsTextStream(2, 0)
    t1.Write "Protocollo: " + NomeProtocollo + vbcrlf
	t1.Write "Note: " + Note
    t1.Close
    
'*******************************************************************************************************
	
	
    If (MM_editRedirectUrl <> "") Then      Response.Redirect(MM_editRedirectUrl)
  End If
End If
%>
<html>
<head>
<title>Inserimento protocollo</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">
<!--
function goToURL(indirizzo) { //v3.0
  eval("document.location='"+indirizzo+"'");
}

function validateForm(Oggetto) { //v4.0
    if (!Oggetto.value) 
	{
	   alert ('Inserire necessariamente il nome del protocollo!');
	   return false;
    }
	else 
	{
	   return true;
	}
}
//-->
</script>
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
      <td align="center"> <b><font color="#009933">Inserimento protocollo</font></b> 
      </td>
    </tr>
  </table>
</div>
<form name="frmInserimento" method="POST" action="<%=MM_editAction%>">
  <table width="40%" border="0" align="center">
    <tr> 
      <td width="32%" bgcolor="#FFFFCC">Protocollo:</td>
      <td width="68%" bgcolor="#CEECFD"> 
        <input type="text" name="txtDescrizione">
        <input type="hidden" name="ID_azienda" value="<%=Session("IDDitta")%>">
      </td>
    </tr>
    <tr> 
      <td width="32%" bgcolor="#FFFFCC">Note:</td>
      <td width="68%" bgcolor="#CEECFD"> 
        <input type="text" name="txtNote">
        <input type="hidden" name="proProssimo" Value="1">
      </td>
    </tr>
    <tr> 
      <td width="32%" bgcolor="#FFFFCC">Documento default</td>
      <td width="68%" bgcolor="#CEECFD"> 
        <select name="select">
          <%
While (NOT Applicazioni.EOF)
%>
          <option value="<%=(Applicazioni.Fields.Item("ID_applicazione").Value)%>"><%=(Applicazioni.Fields.Item("appNome").Value)%></option>
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
  <br>
  <table width="40%" border="0" align="center" bgcolor="#CCCCCC">
    <tr> 
      <td align="center"> 
        <input type="submit" name="Submit" value="Inserisci" onClick="return validateForm(frmInserimento.txtDescrizione);">
      </td>
      <td align="center"> 
        <input type="reset" name="Submit2" value="Reinserici" onclick="">
      </td>
      <td align="center"> 
        <input type="button" name="Submit3" value="Annulla" onClick="goToURL('protocolli.asp');return false">
      </td>
    </tr>
  </table>
  <p> 
    <input type="hidden" name="MM_insert" value="true">
  </p>
</form>
</body>
</html>
<%
Applicazioni.Close()
%>

