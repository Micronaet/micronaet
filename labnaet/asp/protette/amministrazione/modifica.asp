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
' *** Update Record: set variables

If (CStr(Request("MM_update")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Utenti"
  MM_editColumn = "ID_utente"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "conferma.asp"
  MM_fieldsStr  = "Descrizione|value|Livello|value|Administrator|value|Gestore|value|Password|value"
  MM_columnsStr = "uteDescrizione|',none,''|uteLivello|none,none,NULL|uteAdministrator|none,1,0|uteGestore|none,1,0|utePassword|',none,''"

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
' *** Update Record: construct a sql update statement and execute it

If (CStr(Request("MM_update")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  ' create the sql update statement
  MM_editQuery = "update " & MM_editTable & " set "
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
      MM_editQuery = MM_editQuery & ","
    End If
    MM_editQuery = MM_editQuery & MM_columns(i) & " = " & FormVal
  Next
  MM_editQuery = MM_editQuery & " where " & MM_editColumn & " = " & MM_recordId

  If (Not MM_abortEdit) Then
    ' execute the update
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
Dim Utenti__MMColParam
Utenti__MMColParam = "1"
if (Request.QueryString("txtUserName") <> "") then Utenti__MMColParam = Request.QueryString("txtUserName")
%>
<%
set Utenti = Server.CreateObject("ADODB.Recordset")
Utenti.ActiveConnection = MM_SQLDocnaet_STRING
Utenti.Source = "SELECT * FROM Utenti WHERE ID_utente = " + Replace(Utenti__MMColParam, "'", "''") + ""
Utenti.CursorType = 0
Utenti.CursorLocation = 2
Utenti.LockType = 3
Utenti.Open()
Utenti_numRows = 0
%>
<html>
<head>
<title>Modifica</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
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
  if (document.frmModifica.Password.value!=document.frmModifica.Password2.value) {
      errors+='- Password non coincidenti!\n';
  }
  if (errors) alert('Errori pre inserimento:\n'+errors);
  document.MM_returnValue = (errors == '');
}

function MM_goToURL(indirizzo) { //v3.0
  eval("document.location='"+indirizzo+"'");
}
//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="5">
<div align="center"> 
  <table width="30%" border="0" bgcolor="#CCCCCC">
    <tr> 
      <td align="center"> <b><font color="#009933">Modifica utente</font></b> 
      </td>
    </tr>
  </table>
</div>
<form name="frmModifica" method="POST" action="<%=MM_editAction%>">
  <table width="30%" border="0" align="center">
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">User Name:</td>
      <td width="57%" bgcolor="#CEECFD"> <font color="#666666"><b><%=(Utenti.Fields.Item("uteUserName").Value)%> </b></font></td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Descrizione:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input value="<%=(Utenti.Fields.Item("uteDescrizione").Value)%>" type="text" name="Descrizione" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Livello:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input type="text" name="Livello" size="2" maxlength="2" value="<%=(Utenti.Fields.Item("uteLivello").Value)%>" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Administrator:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input  type="checkbox" name="Administrator" value="checkbox" <%If Utenti.Fields.Item("uteAdministrator").Value Then Response.Write("CHECKED") else Response.Write("")%>>
      </td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Gestore:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input type="checkbox" name="Gestore" value="checkbox" <% If Utenti.Fields.Item("uteGestore").Value Then Response.Write("CHECKED")%>>
      </td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Password:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input type="password" name="Password" value="<%=(Utenti.Fields.Item("utePassword").Value)%>" OnFocus="this.select()">
      </td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Retype Password:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input type="password" name="Password2" value="<%=(Utenti.Fields.Item("utePassword").Value)%>" OnFocus="this.select()">
      </td>
    </tr>
  </table>
  <br>
  <table width="30%" border="0" align="center">
    <tr> 
      <td> 
        <div align="center"> 
          <input type="submit" name="Submit" value="Modifica" onClick="MM_validateForm('UserName','','R','Descrizione','','R','Livello','','RinRange1:10','Password','','R','Password2','','R');return document.MM_returnValue">
        </div>
      </td>
      <td> 
        <div align="center"> 
          <input type="reset" name="Submit2" value="Reimposta">
        </div>
      </td>
      <td> 
        <div align="center"> 
          <input type="button" name="Submit3" value="Annulla" onClick=" MM_goToURL('utenti.asp');return false">
        </div>
      </td>
    </tr>
  </table>
  <input type="hidden" name="MM_update" value="true">
  <input type="hidden" name="MM_recordId" value="<%= Utenti.Fields.Item("ID_utente").Value %>">
</form>
<p>&nbsp;</p>
</body>
</html>
<%
Utenti.Close()
%>
