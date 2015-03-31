<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/gestione.asp" -->

<%
Dim Protocolli__MMColParam
Protocolli__MMColParam = "1"
if (Session("IDDitta") <> "") then Protocolli__MMColParam = Session("IDDitta")

set Protocolli = Server.CreateObject("ADODB.Recordset")
Protocolli.ActiveConnection = MM_SQLDocnaet_STRING
Protocolli.Source = "SELECT * FROM Protocolli WHERE ID_azienda = " + Replace(Protocolli__MMColParam, "'", "''") + " ORDER BY proDescrizione ASC"
Protocolli.CursorType = 0
Protocolli.CursorLocation = 2
Protocolli.LockType = 3
Protocolli.Open()
Protocolli_numRows = 0

set Tipologie = Server.CreateObject("ADODB.Recordset")
Tipologie.ActiveConnection = MM_SQLDocnaet_STRING
Tipologie.Source = "SELECT * FROM Tipologie ORDER BY tipDescrizione ASC"
Tipologie.CursorType = 0
Tipologie.CursorLocation = 2
Tipologie.LockType = 3
Tipologie.Open()
Tipologie_numRows = 0

set Lingue = Server.CreateObject("ADODB.Recordset")
Lingue.ActiveConnection = MM_SQLDocnaet_STRING
Lingue.Source = "SELECT * FROM Lingue ORDER BY linDescrizione ASC"
Lingue.CursorType = 0
Lingue.CursorLocation = 2
Lingue.LockType = 3
Lingue.Open()
Lingue_numRows = 0

Dim Prodotti__MMColParam
Prodotti__MMColParam = "1"
if (Session("IDditta") <> "") then Prodotti__MMColParam = Session("IDditta")

if GestisceProdotti then
	set Prodotti = Server.CreateObject("ADODB.Recordset")
	Prodotti.ActiveConnection = MM_SQLDocnaet_STRING
	Prodotti.Source = "SELECT ID_prodotto, proDescrizione FROM Prodotti WHERE ID_ditta = " + Replace(Prodotti__MMColParam, "'", "''") + " ORDER BY proDescrizione ASC"
	Prodotti.CursorType = 0
	Prodotti.CursorLocation = 2
	Prodotti.LockType = 3
	Prodotti.Open()
	Prodotti_numRows = 0
	Dim Categorie__MMColParam
	Categorie__MMColParam = "1"
	if (Session("IDditta") <> "") then Categorie__MMColParam = Session("IDditta")
	set Categorie = Server.CreateObject("ADODB.Recordset")
	Categorie.ActiveConnection = MM_SQLDocnaet_STRING
	Categorie.Source = "SELECT * FROM Categorie WHERE ID_ditta = " + Replace(Categorie__MMColParam, "'", "''") + " ORDER BY catDescrizione ASC"
	Categorie.CursorType = 0
	Categorie.CursorLocation = 2
	Categorie.LockType = 3
	Categorie.Open()
	Categorie_numRows = 0
end if
%>
<html>
<head>
<title>Ricerca</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<script language="JavaScript">
<!--
function ImpostaValore()
{
   frmTrova.cboTipi.value=parent.fraCliente.frmTrovaClienti.cboTipi.options[parent.fraCliente.frmTrovaClienti.cboTipi.selectedIndex].value;
   frmTrova.cboNazioni.value=parent.fraCliente.frmTrovaClienti.cboNazioni.options[parent.fraCliente.frmTrovaClienti.cboNazioni.selectedIndex].value;
   frmTrova.cboClienti.value=parent.fraCliente.frmTrovaClienti.cboClienteSel.options[parent.fraCliente.frmTrovaClienti.cboClienteSel.selectedIndex].value;
}

function CheckSelection(frm, Nuova) { 
  if ((frm.cboOrdine1.value != frm.cboOrdine2.value) && (frm.cboOrdine1.value != frm.cboOrdine3.value) &&(frm.cboOrdine2.value != frm.cboOrdine3.value || frm.cboOrdine2.value==0 || frm.cboOrdine2.value==0) ) 
  {  
     ImpostaValore(); // imposto i valori dell'eventuale scelta del cliente
     switch (Nuova) {
       case 1:  // Nuova finestra
               frmTrova.hidNuovaFinestra.value='1' ;frmTrova.target='_blank'; return true;
       case 0: // Stessa finestra
	           frmTrova.hidNuovaFinestra.value='0' ;frmTrova.target='_parent'; return true;
       case 2: // frame documenti
	           frmTrova.hidNuovaFinestra.value='0' ;frmTrova.target='fraDocumenti'; return true;
	 }
  }
  else {
     alert ("I valori dell'ordinamento sono doppi! Correggerli.");	 
	 return false;
  }	 
}

function GestisciDblClick(OggettoChiamante, OggettoAbbinato)
{
  var valdef="";
  if  (OggettoChiamante.name=="txtDallaData" || OggettoChiamante.name=="txtAllaData")
  {
      var d;
          d = new Date();
          valdef = d.getDate() + "/" + (d.getMonth()+1)  + "/" + d.getYear();		  
  }
  else
  {
      valdef="1"
  }
  if (OggettoAbbinato.value=="") 
  {
     OggettoChiamante.value=valdef;
  }
  else
  {
     OggettoChiamante.value=OggettoAbbinato.value;
  }
}
//-->
</script>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body leftmargin="1" topmargin="1">
<form action="documenti.asp" name="frmTrova" method="post" target="_parent">
  <table width="100%" border="0">
  <% if not Session("Ridotto") then  %>    
    <tr> 
      <td colspan="6"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"> 
          &nbsp;&nbsp;Informazioni documento&nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"></b></div>
      </td>
    </tr>
	<% end if %>
    <tr bgcolor="#CEECFD"> 
      <td width="16"> 
        <p align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"></b></p>
      </td>
      <td align="center" width="290">Testo</td>
      <td width="309"> 
        <div align="center">Protocollo</div>
      </td>
      <td bgcolor="#CEECFD" width="309"> 
        <div align="center">Tipologia</div>
      </td>
      <td width="309"> 
        <div align="center">Lingua</div>
      </td>
    </tr>
    <tr bgcolor="#FFFFCC"> 
      <td bgcolor="#FFFFCC" colspan="2"> 
        <div align="left"> 
          <input type="text" name="txtTesto" size="40">
        </div>
      </td>
      <td width="309"> 
        <div align="left"> 
          <select name="cboProtocolli">
            <option value="0">Selezionare...</option>
            <%
While (NOT Protocolli.EOF)
%>
            <option value="<%=(Protocolli.Fields.Item("ID_protocollo").Value)%>"><%=(Protocolli.Fields.Item("proDescrizione").Value)%></option>
            <%
  Protocolli.MoveNext()
Wend
If (Protocolli.CursorType > 0) Then
  Protocolli.MoveFirst
Else
  Protocolli.Requery
End If
%>
          </select>
        </div>
      </td>
      <td width="309"> 
        <div align="left"> 
          <select name="cboTipologie">
            <option value="0">Selezionare...</option>
            <%
While (NOT Tipologie.EOF)
%>
            <option value="<%=(Tipologie.Fields.Item("ID_tipologia").Value)%>"><%=(Tipologie.Fields.Item("tipDescrizione").Value)%></option>
            <%
  Tipologie.MoveNext()
Wend
If (Tipologie.CursorType > 0) Then
  Tipologie.MoveFirst
Else
  Tipologie.Requery
End If
%>
          </select>
        </div>
      </td>
      <td width="309"> 
        <div align="left"> 
          <select name="cboLingue">
            <option value="0">Selezionare...</option>
            <%
While (NOT Lingue.EOF)
%>
            <option value="<%=(Lingue.Fields.Item("ID_lingua").Value)%>"><%=(Lingue.Fields.Item("linDescrizione").Value)%></option>
            <%
  Lingue.MoveNext()
Wend
If (Lingue.CursorType > 0) Then
  Lingue.MoveFirst
Else
  Lingue.Requery
End If
%>
          </select>
        </div>
      </td>
    </tr>
  </table>
  <table width="100%" border="0">
  <% if not Session("Ridotto") then  %>    
    <tr> 
      <td colspan="5"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/Last.gif" width="18" height="13">&nbsp;&nbsp;Range&nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/First.gif" width="18" height="13"></b></div>
      </td>
    </tr>
  <% end if %>
    <tr> 
      <td width="46" bgcolor="#CEECFD" align="center"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/Last.gif" width="18" height="13"><img src="../../../../immagini/sistema/bottoni/First.gif" width="18" height="13"></b></div>
      </td>
      <td width="365" bgcolor="#CEECFD" align="center">Prot.</td>
      <td width="411" bgcolor="#CEECFD" align="center">Fax</td>
      <td width="415" bgcolor="#CEECFD" align="center">Data</td>
    </tr>
    <tr> 
      <td bgcolor="#FFFFCC" align="left" colspan="2"> 
        <div align="left">Dal 
          <input type="text" name="txtDalNum" size="5" onDblClick="GestisciDblClick(frmTrova.txtDalNum, frmTrova.txtAlNum);">
          al 
          <input type="text" name="txtAlNum" size="5" onDblClick="GestisciDblClick(frmTrova.txtAlNum,frmTrova.txtDalNum);">
        </div>
      </td>
      <td width="25%" bgcolor="#FFFFCC" align="left"> 
        <div align="left">Dal 
          <input type="text" name="txtDalFax" size="5" onDblClick="GestisciDblClick(frmTrova.txtDalFax,frmTrova.txtAlFax);" >
          al 
          <input type="text" name="txtAlFax" size="5" onDblClick="GestisciDblClick(frmTrova.txtAlFax,frmTrova.txtDalFax);" >
          <input type="hidden" name="cboTipi" value="0">
          <input type="hidden" name="cboNazioni" value="0">
          <input type="hidden" name="cboClienti" value="0">
        </div>
      </td>
      <td width="50%" bgcolor="#FFFFCC" align="left"> 
        <div align="left">Dalla 
          <input type="text" name="txtDallaData" size="10" onDblClick="GestisciDblClick(frmTrova.txtDallaData,frmTrova.txtAllaData);" >
          alla 
          <input type="text" name="txtAllaData" size="10" onDblClick="GestisciDblClick(frmTrova.txtAllaData,frmTrova.txtDallaData);">
        </div>
      </td>
    </tr>
  </table>
  <% if GestisceProdotti then %>
  <table width="100%" border="0">
  <% if not Session("Ridotto") then  %>    
    <td colspan="7"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/cubo.gif" width="18" height="18">&nbsp;&nbsp;Informazioni 
          Prodotto&nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/cubo.gif" width="18" height="18"></b></div>
    </td>
  <% end if %>
    <tr bgcolor="#CEECFD"> 
      <td width="10%" bgcolor="#CEECFD"> 
        <p><b><img src="../../../../immagini/sistema/bottoni/icone/cubo.gif" width="18" height="18">&nbsp;</b> 
          Prodotto </p>
      </td>
      <td width="20%" bgcolor="#FFFFCC">
        <select name="cboProdotto">
          <option value="0" selected>Selezionare...</option>
          <%
While (NOT Prodotti.EOF)
%>
          <option value="<%=(Prodotti.Fields.Item("ID_prodotto").Value)%>"><%=(Prodotti.Fields.Item("proDescrizione").Value)%></option>
          <%
  Prodotti.MoveNext()
Wend
If (Prodotti.CursorType > 0) Then
  Prodotti.MoveFirst
Else
  Prodotti.Requery
End If
%>
        </select>
      </td>
      <td width="10%" bgcolor="#CEECFD">Categoria</td>
      <td width="20%" bgcolor="#FFFFCC"> 
        <select name="cboCategoria">
          <option value="0" selected>Selezionare...</option>
          <%
While (NOT Categorie.EOF)
%>
          <option value="<%=(Categorie.Fields.Item("ID_categoria").Value)%>"><%=(Categorie.Fields.Item("catDescrizione").Value)%></option>
          <%
  Categorie.MoveNext()
Wend
If (Categorie.CursorType > 0) Then
  Categorie.MoveFirst
Else
  Categorie.Requery
End If
%>
        </select>
      </td>
      <td width="10%" bgcolor="#CEECFD">Produttore </td>
      <td width="30%" bgcolor="#FFFFCC"> 
        <select name="cboProduttore">
          <option value="0" selected>Selezionare...</option>          
        </select>
      </td>
    </tr>
  </table>
  <% end if %>
  <table width="100%" border="0">
    <% if not Session("Ridotto") then  %>
    <tr> 
      <td colspan="4"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/ordinamento.gif" width="18" height="18">&nbsp;&nbsp;Ordinamento&nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/ordinamento.gif" width="18" height="18"></b></div>
      </td>
    </tr>
    <% end if %>
    <tr bgcolor="#CCCCCC"> 
      <td width="25%"> 
        <div align="left"><b><img src="../../../../immagini/sistema/bottoni/icone/ordinamento.gif" width="18" height="18"> 
          </b>Ordinamento<b> </b></div>
      </td>
      <td align="center" width="25%"> 
        <div align="left">1&deg;&nbsp; 
          <select name="cboOrdine1">
            <option value="docData">Data</option>
            <option value="docNumero">Num. prot.</option>
            <option value="docFax">Num. fax</option>
          </select>
        </div>
      </td>
      <td width="25%"> 
        <div align="left">2&deg; &nbsp;
          <select name="cboOrdine2">
            <option value="0">Nessuno...</option>
            <option value="docNumero">Num. prot.</option>
            <option value="docFax">Num. fax</option>
            <option value="docData">Data</option>
          </select>
        </div>
      </td>
      <td width="25%"> 
        <div align="center">3&deg; &nbsp;
          <select name="cboOrdine3">
            <option value="0">Nessuno...</option>
            <option value="docNumero">Num. prot.</option>
            <option value="docFax">Num. fax</option>
            <option value="docData">Data</option>
          </select>
        </div>
      </td>
    </tr>
  </table>

<table width="100%" border="0" cellspacing="0" cellpadding="0">
  <tr>
    <td align="center" bgcolor="#CEECFD"> 
      <% if Session("Ridotto") then %>
    <input type="image" border="0" name="imageField22" src="../../../../immagini/sistema/bottoni/icone/trova3.gif" width="36" height="36" onClick="return CheckSelection(document.frmTrova, 2);" alt="Trova i documenti con i filtri associati aprendo nell'attuale finestra">
    &nbsp;&nbsp;&nbsp;&nbsp; 
    <% end if %>
    <input type="hidden" name="hidSwitch" value="1">
    <input type="image" border="0" name="imageField2" src="../../../../immagini/sistema/bottoni/icone/trova2.gif" width="36" height="35" onClick="return CheckSelection(document.frmTrova, 1);" alt="Trova i documenti con i filtri associati aprendo un'altra finestra">
    &nbsp;&nbsp;&nbsp;&nbsp; 
    <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/search.gif" width="35" height="35" onClick="return CheckSelection(document.frmTrova, 0);" alt="Trova i documenti con i filtri associati">
    <input type="hidden" name="hidNuovaFinestra" value="0">
    </td>
  </tr>
</table>
</form></body>
</html>
<%
Protocolli.Close()
Tipologie.Close()
Lingue.Close()
if GestisceProdotti then
   Prodotti.Close()
   Categorie.Close()
end if   
%>

