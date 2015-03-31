<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/librerie/codice/gestione.asp" -->

<html>
<head>
<title>Titolo</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="0" topmargin="0">
<table width="100%" height="80" border="0">
  <tr> 
    <td width="80" valign="top" bgcolor="#FFFFFF" > <object classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" codebase="http://download.macromedia.com/pub/shockwave/cabs/flash/swflash.cab#version=5,0,0,0" width="80" height="73">
        <param name=movie value="../../immagini/sistema/animazioni/micronaet.swf">
        <param name=quality value=high>
        <embed src="../../immagini/sistema/animazioni/micronaet.swf" quality=high pluginspage="http://www.macromedia.com/shockwave/download/index.cgi?P1_Prod_Version=ShockwaveFlash" type="application/x-shockwave-flash" width="80" height="73">
        </embed> 
      </object></td>
    <td width="281" valign="top"> 
      <table width="100%" border="0">
        <tr> 
          <td width="20%">Utente: </td>
          <td width="80%"> 
            <% =Session("UserDescription") & " (lev. " & Session("Level") & ")" %>
          </td>
        </tr>
        <tr> 
          <td width="20%">Data:</td>
          <td width="80%"> 
            <% =date() %>
          </td>
        </tr>
        <tr> 
          <td width="20%">Versione:</td>
          <td width="80%"> 
            <% =Application("Versione") %>
          </td>
        </tr>
      </table>
    </td>
    <td width="309" valign="top"> 
      <table width="100%" border="0">
        <tr> 
          <td bgcolor="#999999"> 
            <div align="center"><b><font color="#333333"> <font color="#FFFFCC"> 
              <% ="[" + Application("Ditta") + "]" %>
              </font> </font></b></div>
          </td>
        </tr>
        <tr> 
          <td> 
            <div align="center"><b>&lt;<a href="../../index.asp" target="_top"><font color="#990000"><%=Session("ditRagioneSociale")%></font></a>&gt; </b> </div>
          </td>
        </tr>
        <tr> 
          <td align="center"> <font color="#990000"> 
            <%
		      dim Attivazione
			  Attivazione="Abilitazione:"
		      if GestisceOffLine then Attivazione =Attivazione + " Off-line" else Attivazione=Attivazione +" On-line "
			  if GestisceProdotti then Attivazione=Attivazione + " Prodotti"
			  if GestisceMultiAzienda then Attivazione=Attivazione + " Multiazienda"			  
			  Response.Write(Attivazione)
			 %>
            </font></td>
        </tr>
      </table>      
      
    </td>
    <td width="585" align="right"><img src="../../immagini/sistema/bottoni/icone/<%if Session("Remoto") then Response.Write("portatile.gif") else Response.Write("rete.gif")%>" width="31" height="31"></td>
  </tr>
</table>
</body>
</html>
