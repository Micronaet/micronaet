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
' *** Update Record: set variables

If (CStr(Request("MM_update")) <> "" And CStr(Request("MM_recordId")) <> "") Then

  MM_editConnection = MM_SQLDocnaet_STRING
  MM_editTable = "Spedito"
  MM_editColumn = "ID_spedizione"
  MM_recordId = "" + Request.Form("MM_recordId") + ""
  MM_editRedirectUrl = "aconferma.asp"
  MM_fieldsStr  = "Prossimo|value"
  MM_columnsStr = "speProssimo|none,none,NULL"

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
Dim Contatori__MMColParam
Contatori__MMColParam = "1"
if (Request.QueryString("IDDitta") <> "") then Contatori__MMColParam = Request.QueryString("IDDitta")
%>
<%
set Contatori = Server.CreateObject("ADODB.Recordset")
Contatori.ActiveConnection = MM_SQLDocnaet_STRING
Contatori.Source = "SELECT * FROM Spedito WHERE ID_Ditta = " + Replace(Contatori__MMColParam, "'", "''") + ""
Contatori.CursorType = 0
Contatori.CursorLocation = 2
Contatori.LockType = 3
Contatori.Open()
Contatori_numRows = 0
%>
<html>
<head>
<title>Modifica</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">
<!--
function goToURL(indirizzo) { //v3.0
  eval("document.location='"+indirizzo+"'");
}

function MM_findObj(n, d) { //v4.0
  var p,i,x;  if(!d) d=document; if((p=n.indexOf("?"))>0&&parent.frames.length) {
    d=parent.frames[n.substring(p+1)].document; n=n.substring(0,p);}
  if(!(x=d[n])&&d.all) x=d.all[n]; for (i=0;!x&&i<d.forms.length;i++) x=d.forms[i][n];
  for(i=0;!x&&d.layers&&i<d.layers.length;i++) x=MM_findObj(n,d.layers[i].document);
  if(!x && document.getElementById) x=document.getElementById(n); return x;
}

function MM_validateForm() { //v4.0
  var i,p,q,nm,test,num,min,max,errors='',args=MM_validateForm.arguments;
  for (i=0; i<(args.length-2); i+=3) { test=args[i+2]; val=MM_findObj(args[i]);
    if (val) { nm=val.name; if ((val=val.value)!="") {
      if (test.indexOf('isEmail')!=-1) { p=val.indexOf('@');
        if (p<1 || p==(val.length-1)) errors+='- '+nm+' must contain an e-mail address.\n';
      } else if (test!='R') {
        if (isNaN(val)) errors+='- '+nm+' must contain a number.\n';
        if (test.indexOf('inRange') != -1) { p=test.indexOf(':');
          min=test.substring(8,p); max=test.substring(p+1);
          if (val<min || max<val) errors+='- '+nm+' must contain a number between '+min+' and '+max+'.\n';
    } } } else if (test.charAt(0) == 'R') errors += '- '+nm+' is required.\n'; }
  } if (errors) alert('The following error(s) occurred:\n'+errors);
  document.MM_returnValue = (errors == '');
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
  <table width="30%" border="0" bgcolor="#CCCCCC">
    <tr> 
      <td align="center"> <b><font color="#009933">Modifica contatori</font></b></td>
    </tr>
  </table>
</div>
<form ACTION="<%=MM_editAction%>" METHOD="POST" name="frmModifica">
  <table width="30%" border="0" align="center">
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Contatore:</td>
      <td width="57%" bgcolor="#CEECFD"> <font color="#666666"><b><%=(Contatori.Fields.Item("speDescrizione").Value)%> </b></font></td>
    </tr>
    <tr> 
      <td width="43%" bgcolor="#FFFFCC">Prossimo:</td>
      <td width="57%" bgcolor="#CEECFD"> 
        <input value="<%=(Contatori.Fields.Item("speProssimo").Value)%>" type="text" name="Prossimo" OnFocus="this.select()">
      </td>
    </tr>
  </table>
  <br>
  <table width="30%" border="0" align="center">
    <tr> 
      <td> 
        <div align="center"> 
          <input type="submit" name="Submit" value="Modifica" onClick="MM_validateForm('Prossimo','','RisNum');return document.MM_returnValue">
        </div>
      </td>
      <td> 
        <div align="center"> 
          <input type="reset" name="Submit2" value="Reimposta">
        </div>
      </td>
      <td> 
        <div align="center"> 
          <input type="button" name="Submit3" value="Annulla" onClick="goToURL('aziende.asp');return false;">
        </div>
      </td>
    </tr>
  </table>
  <input type="hidden" name="MM_recordId" value="<%= Contatori.Fields.Item("ID_spedizione").Value %>">
  <input type="hidden" name="MM_update" value="true">
</form>
<p>&nbsp;</p>
</body>
</html>
<%
Contatori.Close()
%>
