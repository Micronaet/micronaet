<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/gestione.asp" -->
<%
    Session("Remoto")=FALSE
    set Ditte = Server.CreateObject("ADODB.Recordset")
    Ditte.ActiveConnection = MM_SQLDocnaet_STRING

    Ditte.Source = "SELECT * FROM Ditte ORDER BY ditLicenziataria DESC, ditRagioneSociale ASC"
    Ditte.CursorType = 0
    Ditte.CursorLocation = 2
    Ditte.LockType = 3
    Ditte.Open()
    Ditte_numRows = 0
%>
<html>
<head>
    <title>Docnaet</title>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    <style type="text/css">
    <!--
        @import url(/docnaet/stili/homepage.css);
        .style1 {color: #FFFFFF}
    -->
    </style>
</head>

<body bgcolor="#FFFFFF" text="#000000" leftmargin="0" topmargin="0">
<table width="100%" border="0" align="center" height="100%" bgcolor="#FFFFFF" bordercolor="#FFFFFF" cellpadding="0" cellspacing="0">
  <tr bgcolor="#FFFFFF"> 
    <td align="center" height="120" bgcolor="#CEECFD" width="2%"><b><font color="#990000"><br></font></b></td>
    <td align="center" height="120" width="98%"><b><font color="#990000"><img src="immagini/sistema/bottoni/icone/<%if Session("Remoto") then Response.Write("portatile.gif") else Response.Write("rete.gif")%>" width="31" height="31"><br>
      <%if Session("Remoto") then Response.Write("Remote logon") else Response.Write("Net logon") %><br></font></b></td>
  </tr>
  <tr align="center" valign="top"> 
    <td bgcolor="#CEECFD" width="2%">&nbsp; </td>
    <td width="98%" bgcolor="#CCCCCC"><br>
    	 
      <form name="form1" method="post" action="asp/autenticazione.asp" target="_top">
        <table border="0" align="center" height="141" cellspacing="0" cellpadding="0">
          <tr bgcolor="#000000" align="center"> 
            <td colspan="4" height="27"><font color="#990000"><b><font color="#FFFFCC">Autenticazione</font></b></font></td>
          </tr>
          <tr bgcolor="#666666"> 
            <td width="5" height="27" bgcolor="#666666">&nbsp;</td>
            <td width="105" height="27" bgcolor="#666666"><font color="#FFCC00">User 
              Name:</font></td>
            <td width="138" height="27"> 
              <input type="text" name="txtUserName" value="<%=Session("UserName")%>" onFocus="this.select()">
            </td>
            <td width="5" height="27">&nbsp; </td>
          </tr>
          <tr bgcolor="#666666"> 
            <td width="5" height="30" bgcolor="#666666">&nbsp;</td>
            <td width="105" height="30" bgcolor="#666666"><font color="#FFCC00">Password:</font></td>
            <td width="138" height="30"> 
              <input type="password" name="txtPassword" value="<%= Session("Password") %>" onFocus="this.select()">
            </td>
            <td width="5" height="30">&nbsp; </td>
          </tr>
          <tr bgcolor="#666666"> 
            <td width="5" height="30" bgcolor="#666666">&nbsp;</td>
            <td width="105" height="30" bgcolor="#666666"><font color="#FFCC00">Ditta</font></td>
            <td width="138" height="30"> 
              <select name="cboDitta">
                <%
                    While (NOT Ditte.EOF)
                %>
                <option value="<%=(Ditte.Fields.Item("ID_ditta").Value)%>"><%=(Ditte.Fields.Item("ditRagioneSociale").Value)%></option>
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
            <td width="5" height="30">&nbsp; </td>
          </tr>
          <tr> 
            <td align="center" bgcolor="#CEECFD" width="5" >&nbsp;</td>
            <td align="center" bgcolor="#CEECFD" width="105" > 
              <input type="checkbox" name="chkRidotto" value="1" checked>Ridotto </td>
            <td align="center" bgcolor="#CEECFD" valign="middle" > 
              <input type="image" border="0" name="imageField" src="immagini/sistema/bottoni/icone/chiave.gif" width="30" height="30">
            </td>
            <td align="center" bgcolor="#CEECFD" width="5" >&nbsp; </td>
          </tr>
        </table>
        <br>
        <br>
      </form>
    </td>
  </tr>
  <tr bgcolor="#999999"> 
    <td height="60" width="2%" bgcolor="#CEECFD">&nbsp;</td>
    <td height="60" width="98%" bgcolor="#FFFFFF"><span class="style1"> </span></td>
  </tr>
</table>
<script language="JavaScript">
    document.forms[0].elements[0].focus();
</script>
</body>
</html>
<%
    Ditte.Close()
%>
