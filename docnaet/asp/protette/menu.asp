<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/librerie/codice/file.asp" -->
<!--#include virtual="/docnaet/librerie/codice/gestione.asp" -->

<html>
<head>
<title>menu principale</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<style type="text/css">
<!--
@import url(/docnaet/stili/menu.css);
-->
</style>
<base target="mainFrame">
</head>
<body bgcolor="#CCCCCC" text="#000000" leftmargin="0" topmargin="0" vlink="#3399FF" alink="#3399FF">
<table width="125" border="0" cellpadding="1" cellspacing="0">
  <tr bgcolor="#666666"> 
    <td colspan="2"><a href="../../index.asp" target="_top"><font color="#990000"><b><font color="#FFFFFF"><%=Session("ditRagioneSociale")%></font></b></font></a></td>
  </tr>
  <% if Session("IsAdministrator") then %>
  <tr> 
    <td bgcolor="#FFFFCC" colspan="2"> <font color="#990000"><b>Amministrazione 
      </b></font></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="amministrazione/utenti.asp" target="mainFrame"><img src="../../immagini/sistema/bottoni/icone/users.gif" width="22" height="18" vspace="0" hspace="0" border="0"></a> 
    </td>
    <td valign="middle" height="*"><a href="amministrazione/utenti.asp" target="mainFrame">Utenti</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="amministrazione/aziende.asp"><img src="../../immagini/sistema/bottoni/icone/casa.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="amministrazione/aziende.asp">Aziende</a></td>
  </tr>
  <% end if %>
  <% if GestoreAnagrafiche() then %>
  <tr> 
    <td bgcolor="#FFFFCC" bordercolor="#CCCCCC" colspan="2"> 
      <div align="left"><b><font color="#990000">Anagrafiche</font></b></div>
    </td>
  </tr>
  <tr> 
    <td height="22" valign="middle"><a href="menu/protocolli/protocolli.asp"><img src="../../immagini/sistema/bottoni/icone/protocollo.gif" width="18" height="18" border="0"></a> 
    </td>
    <td height="21" valign="middle"><a href="menu/protocolli/protocolli.asp">Protocolli</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/tipologie.asp"><img src="../../immagini/sistema/bottoni/icone/tipologia.gif" width="15" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/tipologie.asp">Tipologia</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"> <a href="menu/lingue.asp"><img src="../../immagini/sistema/bottoni/icone/bandiera.gif" width="20" height="16" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/lingue.asp">Lingue</a></td>
  </tr>
  <tr valign="top"> 
    <td bgcolor="#FFFFCC" colspan="2"> <img src="../../immagini/sistema/bottoni/linee/linea.gif" width="125"></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/clienti/ricerche.asp"><img src="../../immagini/sistema/bottoni/icone/passepartout.gif" width="19" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/clienti/ricerche.asp">Ditte</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/clienti/tipi.asp"><img src="../../immagini/sistema/bottoni/icone/cxconfig.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/clienti/tipi.asp">Tipo di ditta</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/clienti/nazioni.asp"><img src="../../immagini/sistema/bottoni/icone/lingue.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/clienti/nazioni.asp">Nazioni</a></td>
  </tr>
  <%if GestisceProdotti then %>
  <tr valign="top"> 
    <td bgcolor="#FFFFCC" colspan="2"> <img src="../../immagini/sistema/bottoni/linee/linea.gif" width="125"></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/prodotti/ricerche.asp"><img src="../../immagini/sistema/bottoni/icone/cubo.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/prodotti/ricerche.asp">Prodotti</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/prodotti/categorie.asp"><img src="../../immagini/sistema/bottoni/icone/categorie.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="menu/prodotti/categorie.asp">Categorie</a></td>
  </tr>
  <%end if ' gestisce prodotti %>
  <%end if ' gestore anagrafiche%>
  <tr> 
    <td bgcolor="#FFFFCC" colspan="2"> 
      <div align="left"><font color="#990000"><b>Documenti</b></font></div>
    </td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="menu/documenti/nuovo.asp"><img src="../../immagini/sistema/bottoni/icone/aggiorna.gif" width="18" height="18" border="0"></a> 
      <a href="menu/documenti/nuovo.asp"> </a></td>
    <td valign="middle"><a href="menu/documenti/nuovo.asp">Inserimento</a></td>
  </tr>
  
  <tr> 
    <td valign="middle" height="22"><a href="menu/documenti/ricerca.asp"><img src="../../immagini/sistema/bottoni/search.gif" width="20" height="20" border="0"></a> 
      <a href="menu/documenti/ricerca.asp"> </a></td>
    <td valign="middle"><a href="menu/documenti/ricerca.asp">Ricerca avanzata</a></td>
  </tr>
  <tr> 
    <td valign="middle" height="22"> <a href="<%=getCartellaSyncro() %>" target="_blank"><img src="../../immagini/sistema/bottoni/icone/esplora.gif" width="18" height="18" border="0"></a>&nbsp;</td>
    <td valign="middle"><a href="menu/documenti/syncro.asp">Sincro file</a> </td>
  </tr>
  <tr> 
    <td valign="middle" height="22"> <a href="<%=getCartellaUpload() %>" target="_blank"><img src="../../immagini/sistema/bottoni/icone/esplora.gif" width="18" height="18" border="0"></a>&nbsp;</td>
    <td valign="middle"><a href="menu/documenti/upload.asp?apertura=1">Upload 
      file</a> </td>
  </tr>
  <% if GestoreAnagrafiche() then %>
  <tr> 
    <td valign="middle" height="22"><a href="<%=getCartellaFax() %>" target="_blank"><img src="../../immagini/sistema/bottoni/icone/esplora.gif" width="18" height="18" border="0"></a>&nbsp;</td>
    <td valign="middle"><a href="menu/documenti/upload.asp?apertura=2">Upload 
      fax</a> </td>
  </tr>
  <% end if %>
  <tr> 
    <td bgcolor="#FFFFCC" colspan="2"> 
      <div align="left"><font color="#990000"><b>Servizi</b></font></div>
    </td>
  </tr>
  <tr> 
    <td valign="middle" height="22"><a href="../../index.asp" target="_top"><img src="../../immagini/sistema/bottoni/icone/stop.gif" width="18" height="18" border="0"></a> 
    </td>
    <td valign="middle"><a href="../../index.asp" target="_top">Cambio azienda</a></td>
  </tr>
</table>
</body>
</html>