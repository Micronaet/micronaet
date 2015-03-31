<%@LANGUAGE="VBSCRIPT"%>
<!--#include virtual="/labnaet/Connections/SQLDocnaet.asp" -->
<%
set Aziende = Server.CreateObject("ADODB.Recordset")
Aziende.ActiveConnection = MM_SQLDocnaet_STRING
Aziende.Source = "SELECT * FROM Ditte ORDER BY ditRagioneSociale ASC"
Aziende.CursorType = 0
Aziende.CursorLocation = 2
Aziende.LockType = 3
Aziende.Open()
Aziende_numRows = 0
%>
<%
Dim Repeat1__numRows
Repeat1__numRows = -1
Dim Repeat1__index
Repeat1__index = 0
Aziende_numRows = Aziende_numRows + Repeat1__numRows

%>
<html>
<head>
<title>Elenco aziende installate</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="javascript">
<!--
function isEliminabile(PossoEliminare) {
    if (PossoEliminare) {
	      return true;	   
	} else 
	{     alert('La ditta selezionata non si può eliminare!');
	      return false;
	}
}
// -->
</script>
</head>
<style type="text/css">
<!--
@import url(/labnaet/stili/homepage.css);
-->
</style>
<body bgcolor="#FFFFFF" text="#000000" leftmargin="1" topmargin="1">
<table width="100%" border="0" height="52">
  <tr bgcolor="#999999"> 
    <td colspan="5"> 
      <div align="center"><b><font color="#FFFFCC">Aziende Installate</font></b></div>
    </td>
  </tr>
  <tr> 
    <td> 
      <div align="center"><a href="naziende.asp"><img src="../../../immagini/sistema/bottoni/icone/casa.gif" width="26" height="25" border="0" alt="Inserimento nuova azienda"></a> 
      </div>
    </td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
    <td width="20%" height="29">&nbsp;</td>
  </tr>
</table>
<br>
<table width="65%" border="0" align="center" height="68">
  <tr bgcolor="#CCCCCC"> 
    <td colspan="9"> 
      <div align="center"><b><font color="#990000">Elenco Azienda</font></b></div>
    </td>
  </tr>
  <tr bgcolor="#FFFFFF"> 
    <td colspan="2" align="center"> 
      <div align="center"></div>
      <b>Ragione Sociale</b></td>
    <td width="19%"> 
      <div align="center"><b>Paese</b></div>
    </td>
    <td width="24%"><b>Note</b></td>
    <td colspan="4"> 
      <div align="center"><b>Operazioni</b></div>
    </td>
  </tr>
  <% 
dim colore
%>
  <% 
While ((Repeat1__numRows <> 0) AND (NOT Aziende.EOF)) 
if Repeat1__index mod 2=0 then colore="#CEECFD" else colore="#FFFFCC" ' decido il colore della riga  %>
  <tr bgcolor=<%=colore%>> 
    <td width="13%" valign="middle" align="center" bgcolor="#F0F0F0"> 
      <p><img src="../../../immagini/sistema/logo/aziende/<%=(Aziende.Fields.Item("ID_ditta").Value)%>.gif" width="100" height="30"></p>
    </td>
    <td width="32%" valign="top"><%=(Aziende.Fields.Item("ditRagioneSociale").Value)%></td>
    <td width="19%" valign="top"> 
      <p><%=(Aziende.Fields.Item("ditPaese").Value)%></p>
    </td>
    <td width="24%" valign="top"><%=(Aziende.Fields.Item("ditNote").Value)%></td>
    <form name="frmElimina" action="daziende.asp" method="get">
      <td width="4%" bgcolor="#CCCCCC" align="center" valign="top"> 
        <input type="image" border="0" name="imgElimina" src="../../../immagini/sistema/bottoni/icone/cestino.gif" width="20" height="21" onClick=" return isEliminabile(<%if Aziende.Fields.Item("ditLicenziataria").Value then Response.Write("false") else Response.Write("true")%>);"; alt="Elimina la ditta">
        <input type="hidden" name="ID_ditta" value="<%=(Aziende.Fields.Item("ID_ditta").Value)%>">
      </td>
    </form>
    <form name="frmModifica" action="maziende.asp" method="get">
      <td width="4%" bgcolor="#CCCCCC" align="center" valign="top"> 
        <input type="image" border="0" name="imgModifica" src="../../../immagini/sistema/bottoni/open.gif" width="20" height="21" alt="Modifica i dati della ditta">
        <input type="hidden" name="ID_ditta" value="<%=(Aziende.Fields.Item("ID_ditta").Value)%>">
      </td>
    </form>
    <td width="2%" bgcolor="#CCCCCC" align="center" valign="top"><a href="contatori.asp?IDDitta=<%=(Aziende.Fields.Item("ID_ditta").Value)%>"><img src="../../../immagini/sistema/bottoni/icone/contatori1.gif" width="20" height="22" alt="Contatori aziendali" border="0"></a></td>
    <td width="2%" bgcolor="#CCCCCC" align="center" valign="top"><a href="importazione.asp?ID_ditta=<%=(Aziende.Fields.Item("ID_ditta").Value)%>&AziSigla=<%=(Aziende.Fields.Item("ditSigla").Value)%>"><img src="../../../immagini/sistema/bottoni/icone/importazione.gif" width="20" height="23" border="0"></a></td>
  </tr>
  <% 
  Repeat1__index=Repeat1__index+1
  Repeat1__numRows=Repeat1__numRows-1
  Aziende.MoveNext()
Wend
%>
</table>
</body>
</html>
<%
Aziende.Close()
%>
