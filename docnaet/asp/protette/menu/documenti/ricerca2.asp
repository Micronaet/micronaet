<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/docnaet/Connections/SQLDocnaet.asp" -->
<!--#include virtual="/docnaet/librerie/codice/gestione.asp" -->

<%
' controllo se la videata è un richiamo per applicare i filtri e riproporre le scelte
dim IDTipo, IDNazione, TXTCliente, IDCliente, setID
' assegno i valori avuti in precedenza
setID=Request.QueryString("setIDCliente")
if setID<>"" then ' sono nel caso in cui devo settare il valore che mi è stato impostato
    IDTipo="0"
	IDNazione="0"
    IDCliente=setID ' imposto l'ID a quello che ha messo la maschera di prima
else
   ' faccio il solito ragionamento che facevo prima
    IDTipo=Request.Form("cboTipi")
	if IDTipo="" then IDTipo="0"
	
	IDNazione=Request.Form("cboNazioni")
	if IDNazione="" then IDNazione="0"
	
	TXTCliente=Request.Form("txtCliente")
	if TXTCliente="" then TXTCliente=""
	
	IDCliente=Request.Form("cboClienteSel")
	if IDCliente="" then IDCliente="0"
end if
%>
<%
Dim ColParam
ColParam = "1"
if (Session("IDDitta") <> "") then ColParam = Session("IDDitta")

' crazione della condizione WHERE
CondizioneWhere="ID_ditta = " + ColParam 
if TXTCliente<>"" then
   CondizioneWhere=CondizioneWhere + " and cliRagioneSociale like '%"+TXTcliente+"%'"
end if
if IDNazione<>"0" then
   CondizioneWhere=CondizioneWhere + " and ID_nazione ="+IDNazione
end if
if IDTipo<>"0" then
   CondizioneWhere=CondizioneWhere + " and ID_tipo="+ IDTipo
end if

set Clienti = Server.CreateObject("ADODB.Recordset")
Clienti.ActiveConnection = MM_SQLDocnaet_STRING
Clienti.Source = "SELECT * FROM Clienti WHERE "+CondizioneWhere+" ORDER BY cliRagioneSociale ASC"
Clienti.CursorType = 0
Clienti.CursorLocation = 2
Clienti.LockType = 3
Clienti.Open()
Clienti_numRows = 0

set Tipi = Server.CreateObject("ADODB.Recordset")
Tipi.ActiveConnection = MM_SQLDocnaet_STRING
Tipi.Source = "SELECT * FROM Tipi ORDER BY tipDescrizione ASC"
Tipi.CursorType = 0
Tipi.CursorLocation = 2
Tipi.LockType = 3
Tipi.Open()
Tipi_numRows = 0

set Nazioni = Server.CreateObject("ADODB.Recordset")
Nazioni.ActiveConnection = MM_SQLDocnaet_STRING
Nazioni.Source = "SELECT * FROM Nazioni ORDER BY nazDescrizione ASC"
Nazioni.CursorType = 0
Nazioni.CursorLocation = 2
Nazioni.LockType = 3
Nazioni.Open()
Nazioni_numRows = 0
%>
<html>
<head>
<title>Ricerca</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script type="text/javascript" language="JavaScript">
<!--
// *********************************** FUNZIONE PER CONFERMA ELIMINAZIONE ********************************++
function Rinfresca() 
{
   frmTrovaClienti.submit(); 
}
//-->
</script>
</head>

<style type="text/css">
<!--
@import url(../../../../stili/homepage.css);
-->
</style>
<body leftmargin="1" topmargin="1">
    
  <table width="100%" border="0">
<form action="ricerca2.asp" name="frmTrovaClienti" method="post">
    <% if not Session("Ridotto") then  %>    
  <tr> 
      <td colspan="6"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/passepartout.gif" width="18" height="17">&nbsp;&nbsp;Informazioni 
          cliente&nbsp;&nbsp; <img src="../../../../immagini/sistema/bottoni/icone/passepartout.gif" width="18" height="17"></b></div>
      </td>
    </tr>
	<% end if %>
    <tr bgcolor="#CEECFD" align="center"> 
      <td width="18" bgcolor="#CEECFD"> 
        <p align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/passepartout.gif" width="18" height="17"></b></p>
      </td>
      <td width="271" bgcolor="#CEECFD">Cliente</td>
      <td width="231">Categoria</td>
      <td width="231">Nazione</td>
      <td width="482" bgcolor="#CEECFD">Elenco clienti</td>
    </tr>
    <tr bgcolor="#FFFFCC"> 
      <td bgcolor="#FFFFCC" colspan="2" align="center"> 
        <div align="left"> 
          <input type="text" name="txtCliente" size="25" value="<%Response.Write(TXTCliente)%>" onChange="Rinfresca();">
        </div>
      </td>
      <td width="231" align="center"> 
        <select name="cboTipi" onChange="Rinfresca();">
          <option value="0">Selezionare...</option>
          <%
While (NOT Tipi.EOF)
%>
          <option value="<%=(Tipi.Fields.Item("ID_tipo").Value)%>" <%if Tipi.Fields.Item("ID_tipo").Value-IDTipo=0 then Response.Write("selected")%> ><%=(Tipi.Fields.Item("tipDescrizione").Value)%></option>
          <%
  Tipi.MoveNext()
Wend
If (Tipi.CursorType > 0) Then
  Tipi.MoveFirst
Else
  Tipi.Requery
End If
%>
        </select>
      </td>
      <td width="231" align="center"> 
        <select name="cboNazioni" onChange="Rinfresca();">
          <option value="0">Selezionare...</option>
          <%
While (NOT Nazioni.EOF)
%>
          <option value="<%=(Nazioni.Fields.Item("ID_nazione").Value)%>" <%if (Nazioni.Fields.Item("ID_nazione").Value)-IDNazione=0 then REsponse.Write("selected")%>><%=(Nazioni.Fields.Item("nazDescrizione").Value)%></option>
          <%
  Nazioni.MoveNext()
Wend
If (Nazioni.CursorType > 0) Then
  Nazioni.MoveFirst
Else
  Nazioni.Requery
End If
%>
        </select>
      </td>
      <td width="482" bgcolor="#CEECFD"> 
        <input type="image" border="0" name="imgRefresh" src="../../../../immagini/sistema/bottoni/icone/Last.gif" width="18" height="13">
        <% if (Clienti.EOF) then %>
        <font color="#FF0000">Nessuna ditta</font> 
        <input type="hidden" name="cboClienti" value="0">
        <input type="hidden" name="cboClienteSel" value="0">
        <% else %>
        <select name="cboClienteSel">
          <option value="0">Selezionare...</option>
          <%
		  dim tempID, tempRS, tempI
		  tempI=0 
While (NOT Clienti.EOF)
          tempI=tempI+1 ' incremento il contatore
		  ' memorizzo i dati in quanto passo avanti con il record set
		  tempID=(Clienti.Fields.Item("ID_cliente").Value)
		  tempRS=(Clienti.Fields.Item("cliRagioneSociale").Value)
		  Clienti.MoveNext()
%>
          <option value="<%=tempID%>" <%
		        if (tempID-IDCliente=0) then 
				   Response.Write("selected")
				else
				   if tempI=1 and Clienti.EOF then 
				      Response.Write("selected")
				   end if	  
				end if   
				   %>><%=tempRS%></option>
          <%  
Wend ' fine del ciclo

If (Clienti.CursorType > 0) Then
  Clienti.MoveFirst
Else
  Clienti.Requery
End If
%>
        </select>
        <%end if %>
        <input type="hidden" name="setIDCliente" value="0">
      </td>
    </tr>
</form>  </table>  

</body>
</html>
<%
Clienti.Close()
%>
<%
Tipi.Close()
%>
<%
Nazioni.Close()
%>
