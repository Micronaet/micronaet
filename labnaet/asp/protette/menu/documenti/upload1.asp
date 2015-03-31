<%@LANGUAGE="VBSCRIPT"%> 
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/labnaet/librerie/codice/file.asp" -->

<%
dim WorkFolder
select case Request.querystring("apertura")
       case "1": ' aperto per l'upload
	        WorkFolder=getCartellaUpload ()
	   case "2": ' aperto per i fax
	        WorkFolder=getCartellaFax ()	           
end select	   

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

set Lingue = Server.CreateObject("ADODB.Recordset")
Lingue.ActiveConnection = MM_SQLDocnaet_STRING
Lingue.Source = "SELECT ID_lingua, linDescrizione FROM Lingue ORDER BY linDescrizione ASC"
Lingue.CursorType = 0
Lingue.CursorLocation = 2
Lingue.LockType = 3
Lingue.Open()
Lingue_numRows = 0

set Tipologia = Server.CreateObject("ADODB.Recordset")
Tipologia.ActiveConnection = MM_SQLDocnaet_STRING
Tipologia.Source = "SELECT ID_tipologia, tipDescrizione FROM Tipologie ORDER BY tipDescrizione ASC"
Tipologia.CursorType = 0
Tipologia.CursorLocation = 2
Tipologia.LockType = 3
Tipologia.Open()
Tipologia_numRows = 0

' Codice utente per operazioni caricamento dati videata
   Dim fso, f, f1, fc, s
   Set fso = CreateObject("Scripting.FileSystemObject")
   Set f = fso.GetFolder(WorkFolder)
   Set fc = f.Files   
%>

<html>
<head>
<title>Upload documenti</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script type="text/javascript" language="JavaScript">
<!--
function SelezionaTutti (Elenco, Valore, Tot)
{
    if (Tot=="0" )
	{
	   alert ("Nessun elemento selezionabile!");
	     
	}
	else
	{
	    if (Tot=="1")
		{
		    Elenco.checked=Valore; // metto il check per l'unico
		}
		else
		{
 		    for (var i=0;i<Elenco.length;i++)
	        {
		        Elenco[i].checked =Valore;
	        }
		} 
	}	
}

function ImpostaValore()
{
   frmTrova.cboClienti.value=parent.fraCliente.frmTrovaClienti.cboClienteSel.options[parent.fraCliente.frmTrovaClienti.cboClienteSel.selectedIndex].value;
}

function InserimentoDocumenti (Selezioni, frmUpload, Tot) {
  var indirizzo="";
	
  if (frmUpload.cboProtocollo.value=="0") 
  {
	 alert ("Inserire necessariamente il protocollo!");		
  }
  else
  {			
	if (Tot=="0" )
	{
	   alert ("Nessun elemento selezionabile!");
	}
	else
	{
	    indirizzo=""; // azzero l'indirizzo
	    if (Tot=="1")
		{   // caso in cui c'è appena una voce
		    if (Selezioni.checked)		
			{			    
			    indirizzo="|" + Selezioni.value;			
			}			
		}
		else
		{			         
			for (var i=0;i<Selezioni.length;i++)
			{
			    if (Selezioni(i).checked)
				{
				   indirizzo += "|" + Selezioni(i).value;
				}  
			}
     	}
		// genero la stringa con i parametri della form di selezione
		if (indirizzo!="" )
		{  // ci sono degli elementi selezionati 
		   ImpostaValore(); // leggo dal frame di sopra il valore del cliente
		   indirizzo="confupload.asp?" + "<%=Request.querystring("apertura")%>"+ "|" + (frmUpload.chkElimino.checked? "1" : "0") + "|" + (frmUpload.chkDevoProtocollare.checked? "1" : "0") + "|"+ frmUpload.cboProtocollo.value+ "|"+ parent.fraCliente.frmTrovaClienti.cboClienteSel.options[parent.fraCliente.frmTrovaClienti.cboClienteSel.selectedIndex].value +"|"+ frmUpload.cboLingua.value+ "|"+ frmUpload.cboTipologia.value + indirizzo;  //parent.fraCliente.frmTrovaClienti.cboClienteSel
		   //window.location=indirizzo; veccio codice
		   parent.location=indirizzo;
		}
		else 
		{
		   alert ("Non sono stati selezionati elementi!");
		}
		
	}		
  }	
  return false; // non ritorno mai il controllo all'azione del form							  
}    

//-->
</script>
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/documenti.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<form action="confupload.asp" name="frmTrova" method="post" target="_parent">
  <table width="100%" border="0">
    <tr> 
      <td colspan="5"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"> 
          &nbsp;&nbsp;Informazioni documento &nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"></b></div>
      </td>
    </tr>
    <tr valign="top" align="center" bgcolor="#CEECFD"> 
      <td width="15%">File</td>
      <td width="30%">Protocollo</td>
      <td width="30%">Lingua</td>
      <td width="30%">Tipologia </td>
      <td width="5%">Importa</td>
    </tr>
    <tr valign="top" bgcolor="#FFFFCC"> 
      <td width="15%"> 
        <input type="checkbox" name="chkElimino" value="checkbox" checked>
        Eliminazione originale <br>
        <input type="checkbox" name="chkDevoProtocollare" value="checkbox" checked>
        Assegnazione numero</td>
      <td align="right" width="30%" bgcolor="#FFFFCC"> 
        <p align="left"> 
          <select name="cboProtocollo">
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
        </p>
      </td>
      <td width="30%" align="right"> 
        <div align="left"> 
          <select name="cboLingua">
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
          <br>
        </div>
      </td>
      <td width="30%"> 
        <div align="left"> 
          <select name="cboTipologia">
            <option value="0">Selezionare...</option>
            <%
While (NOT Tipologia.EOF)
%>
            <option value="<%=(Tipologia.Fields.Item("ID_tipologia").Value)%>"><%=(Tipologia.Fields.Item("tipDescrizione").Value)%></option>
            <%
  Tipologia.MoveNext()
Wend
If (Tipologia.CursorType > 0) Then
  Tipologia.MoveFirst
Else
  Tipologia.Requery
End If
%>
          </select>
          <input type="hidden" name="cboTipi" value="0">
          <input type="hidden" name="cboNazioni" value="0">
          <input type="hidden" name="cboClienti" value="0">
        </div>
      </td>
      <td width="5%" align="center"> 
        <input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/upload.gif" onClick="return InserimentoDocumenti(frmElenco.chkSelezione, frmTrova, frmElenco.hidNumero.value);" width="30" height="32">
      </td>
    </tr>
  </table>
</form>

<form name="frmElenco">
  <table width="100%" border="0">
    <tr> 
      <td colspan="6"> 
        <div align="center"><b>
		<% if Request.querystring("apertura")="1" then ' cartella utente %>
		<img src="../../../../immagini/sistema/bottoni/icone/users.gif" width="21" height="18"> 
		<% else %>
          <img src="../../../../immagini/sistema/bottoni/icone/fax.gif" height="18" width="27"> 
          <% end if %>
          &nbsp;&nbsp;Condizioni importazione (cartella: <%=WorkFolder %>) &nbsp;&nbsp;
  		<% if Request.querystring("apertura")="1" then ' cartella utente %>
        <img src="../../../../immagini/sistema/bottoni/icone/users.gif" width="21" height="18">
		<% else %>
        <img src="../../../../immagini/sistema/bottoni/icone/fax.gif" height="18" width="27"> 
        <% end if %>     
		</b></div>   
      </td>
    </tr>
	<tr bgcolor="#CEECFD"> 
      <td width="5%"> 
        <div align="center"><b>Sel.</b></div>
      </td>
      <td width="43%"> 
        <div align="center"><b>Nome File</b></div>
      </td>
      <td width="52%"> 
        <div align="center"><b>Dimensione</b></div>
      </td>
    </tr>
    <% dim i, colore
     i=0
     For Each f1 in fc
	    i=i+1 
		if i mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" 
	%>
    <tr> 
      <td width="5%" bgcolor="<%=colore%>" > 
        <div align="center"> 
          <input type="checkbox" name="chkSelezione" value="<%=f1.ShortName%>">
        </div>
      </td>
      <td width="43%" bgcolor="<%=colore%>"><a href="<%=(WorkFolder + f1.name)%>" target="_blank"><%=f1.name %></a></td>
      <td width="52%" bgcolor="<%=colore%>"><%= f1.DateCreated%> <%= " (size: " & int(f1.size /1024) & " kbyte.)"%></td>
    </tr>
    <%
    next 
%>
  </table>
  <p> 
    <input type="hidden" name="hidNumero" value="<%=i%>">
  </p>
  <table width="100%" border="0">
    <tr bgcolor="#CCCCCC"> 
      <td width="25%"> </td>
      <td width="25%"> 
        <div align="center"> 
          <input type="button" name="btnSeleziona" value="Tutti" onClick="SelezionaTutti(frmElenco.chkSelezione, true,frmElenco.hidNumero.value);">
        </div>
      </td>
      <td width="25%"> 
        <div align="center"> 
          <input type="button" name="btnDeseleziona" value="Nessuno" onClick="SelezionaTutti(frmElenco.chkSelezione,false,frmElenco.hidNumero.value);">
        </div>
      </td>
      <td width="25%"></td>
    </tr>
  </table>
</form>
</body>
</html>
<%
Protocolli.Close()
%>
<%
Lingue.Close()
%>
<%
Tipologia.Close()
%>
