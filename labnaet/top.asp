<%@LANGUAGE="VBSCRIPT"%>
<!--#include file="librerie/codice/gestione.asp" -->
<html>
<head>
<title>Docnaet</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
</head>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="0" topmargin="0">
<table width="100%" border="0" align="center" height="100%" bgcolor="#FFFFFF" bordercolor="#FFFFFF" cellpadding="0" cellspacing="0">
  <tr> 
    <td height="120" width="98%" bgcolor="#CCCCCC"> 
      <div align="center"> 
        <p><b>---&lt;[ Labn&aelig;t ]&gt;--- <br>
          Gestore unico documenti<br>
          Ver. 2.0 del 06/12/2002</b></p>
        <object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0" width="77" height="58" align="middle">
          <param name=movie value="immagini/sistema/animazioni/micronaet.swf">
          <param name=quality value=high>
          <param name="BGCOLOR" value="#FFFFCC">
          <embed src="immagini/sistema/animazioni/micronaet.swf" quality=high pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" width="77" height="58" align="middle" bgcolor="#FFFFCC">
          </embed> 
        </object> </div>
    </td>
    <td height="120" width="2%" align="center" valign="middle" bgcolor="#CEECFD"><br>
      <br>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td valign="top" width="98%"><font color="#333333"></font> 
	  <br>
      <p align="center"><font color="#333333"> Programma di document management<br>
        concesso in licenza a<br>
        <%=Application("Ditta")%></font> 
      <p align="center"><font color="#333333"><img src= <% =Application("Logo") %> ><br>
        </font></p>
      <font color="#333333"></font> </td>
    <td bgcolor="#CEECFD" valign="top" width="2%">&nbsp;</td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td valign="middle" align="center" height="60" bgcolor="#CCCCCC" width="98%">
	<% if GestisceOffLineAvvio then %>
	<a href="login.asp?Remoto=1" target="rightFrame"><img src="immagini/sistema/bottoni/icone/portatile.gif" width="30" height="32" border="0" alt="login remoto"></a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
	<% end if %>
	<a href="login.asp?Remoto=0" target="rightFrame"><img src="immagini/sistema/bottoni/icone/rete.gif" width="31" height="31" border="0" alt="login in rete"></a></td>
    <td bgcolor="#CEECFD" valign="top" height="60" width="2%">&nbsp;</td>
  </tr>
  
</table>
</body>
</html>
