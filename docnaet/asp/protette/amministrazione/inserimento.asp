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
' *** Redirect if username exists
MM_flag="MM_insert"
If (CStr(Request(MM_flag)) <> "") Then
  MM_dupKeyRedirect="errore.asp"
  MM_rsKeyConnection=MM_SQLDocnaet_STRING
  MM_dupKeyUsernameValue = CStr(Request.Form("UserName"))
  MM_dupKeySQL="SELECT uteUserName FROM Utenti WHERE uteUserName='" & MM_dupKeyUsernameValue & "'"
  MM_adodbRecordset="ADODB.Recordset"
  set MM_rsKey=Server.CreateObject(MM_adodbRecordset)
  MM_rsKey.ActiveConnection=MM_rsKeyConnection
  MM_rsKey.Source=MM_dupKeySQL
  MM_rsKey.CursorType=0
  MM_rsKey.CursorLocation=2
  MM_rsKey.LockType=3
  MM_rsKey.Open
  If Not MM_rsKey.EOF Or Not MM_rsKey.BOF Then 
    ' the username was found - can not add the requested username
    MM_qsChar = "?"
    If (InStr(1,MM_dupKeyRedirect,"?") >= 1) Then MM_qsChar = "&"
    MM_dupKeyRedirect = MM_dupKeyRedirect & MM_qsChar & "requsername=" & MM_dupKeyUsernameValue
    Response.Redirect(MM_dupKeyRedirect)
  End If
  MM_rsKey.Close
End If
%>
<%
' *** Insert Record: set variables
If (CStr(Request("MM_insert")) <> "") Then
  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Utenti"
  MM_editRedirectUrl = "conferma.asp"
  MM_fieldsStr  = "UserName|value|Descrizione|value|Livello|value|checkbox|value|Password|value"
  MM_columnsStr = "uteUserName|',none,''|uteDescrizione|',none,''|uteLivello|none,none,NULL|uteAdministrator|none,1,0|utePassword|',none,''"
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
	
	' creazione della cartella riservata all'utente per gli upload *************************************************
	Dim fso, f, temp
    Set fso = CreateObject("Scripting.FileSystemObject")
    ' creo la cartella dell'utente
	temp=Cstr(Application("UsersFolder"))& CStr(Request.Form("UserName"))
	if not(fso.Folderexists(temp)) then Set f = fso.CreateFolder(temp)
    ' creo la cartella dell'upload
	temp=Cstr(Application("UsersFolder"))& CStr(Request.Form("UserName")) & "\upload"
	if not(fso.Folderexists(temp)) then Set f = fso.CreateFolder(temp)
    ' creo la cartella del download
	temp=Cstr(Application("UsersFolder"))& CStr(Request.Form("UserName")) & "\download"
	if not(fso.Folderexists(temp)) then Set f = fso.CreateFolder(temp)
    ' creo la cartella del syncro
	temp=Cstr(Application("UsersFolder"))& CStr(Request.Form("UserName")) & "\syncro"
	if not(fso.Folderexists(temp)) then Set f = fso.CreateFolder(temp)
    ' **************************************************************************************************************
	
    If (MM_editRedirectUrl <> "") Then
      Response.Redirect(MM_editRedirectUrl)
    End If
  End If

End If
%>
<html>
<head>
<TITLE>Inserimento dati</TITLE>
<script language="JavaScript">
<!--
function MM_findObj(n, d) { //v4.0
  var p,i,x;  if(!d) d=document; if((p=n.indexOf("?"))>0&&parent.frames.length) {
    d=parent.frames[n.substring(p+1)].document; n=n.substring(0,p);}
  if(!(x=d[n])&&d.all) x=d.all[n]; for (i=0;!x&&i<d.forms.length;i++) x=d.forms[i][n];
  for(i=0;!x&&d.layers&&i<d.layers.length;i++) x=MM_findObj(n,d.layers[i].document);
  if(!x && document.getElementById) x=document.getElementById(n); return x;
}

function MM_validateForm() { //v4.0
  var i,p,q,nm,test,num,minimo,massimo,errors='',args=MM_validateForm.arguments;
  for (i=0; i<(args.length-2); i+=3) { test=args[i+2]; val=MM_findObj(args[i]);
    if (val) { nm=val.name; if ((val=val.value)!="") {
      if (test.indexOf('isEmail')!=-1) { p=val.indexOf('@');
        if (p<1 || p==(val.length-1)) errors+='- '+nm+' deve contenere un indirizzo e-mail.\n';
      } else if (test!='R') {        
        if (test.indexOf('inRange') != -1) { p=test.indexOf(':');
          minimo=test.substring(8,p); massimo=test.substring(p+1);		  
          if ((parseInt(val)<parseInt(minimo)) || (parseInt(val)>parseInt(massimo)) || isNaN(val)) errors+='- '+nm+' deve contenere un numero tra '+minimo+' e '+massimo+'.\n';		  
    } } } else if (test.charAt(0) == 'R') errors += '- '+nm+' è richiesto.\n'; }
  } 
  if (document.form1.Password.value!=document.form1.Password2.value) {
      errors+='- Password non coincidenti!\n';
  }
  if (errors) alert('Errori pre inserimento:\n'+errors);
  document.MM_returnValue = (errors == '');
}

function MM_goToURL() { //v3.0
  var args=MM_goToURL.arguments;
  eval("document.location='"+args[0]+"'");
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/docnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="5">
<div align="center">
  <table width="29%" border="0" bgcolor="#CCCCCC">
    <tr>
      <td align="center">
        <b><font color="#009933">Inserimento utente</font></b>
      </td>
    </tr>
  </table>
  </div>
<form name="form1" method="POST" action="<%=MM_editAction%>">
  <table width="29%" border="0" align="center">
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">User Name:</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="text" name="UserName" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Descrizione:</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="text" name="Descrizione" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Livello (1:10)</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="text" name="Livello" value="0" size="2" maxlength="2" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Administrator</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="checkbox" name="checkbox" value="checkbox">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Password</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="password" name="Password" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="25%" bgcolor="#FFFFCC">Retype Pwd</td>
      <td width="75%" bgcolor="#CEECFD"> 
        <input type="password" name="Password2" OnFocus="this.select()">
      </td>
    </tr>
  </table>
  <p> 
    <input type="hidden" name="MM_insert" value="true">
  </p>
  <table width="29%" border="0" align="center">
    <tr align="center" bgcolor="#CCCCCC"> 
      <td width="34%"> 
        <input type="submit" name="Submit" value="Inserimento" onClick="MM_validateForm('UserName','','R','Descrizione','','R','Livello','','RinRange1:10','Password','','R','Password2','','R');return document.MM_returnValue">
      </td>
      <td width="33%"> 
        <input type="reset" name="Submit2" value="Reset">
      </td>
      <td width="33%"> 
        <input type="button" name="Submit3" value="Annulla" onClick=" MM_goToURL('utenti.asp');return false">
      </td>
    </tr>
  </table>  
</form>
</body>
</html>

