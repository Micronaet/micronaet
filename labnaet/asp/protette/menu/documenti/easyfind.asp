<%@LANGUAGE="VBSCRIPT"%> 
<html>
<head>
<title>Ricerca</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
</head>
<script language="JavaScript">
<!--
function CheckSelection(frm, Nuova) { 
  if ((frm.cboOrdine1.value != frm.cboOrdine2.value) && (frm.cboOrdine1.value != frm.cboOrdine3.value) &&(frm.cboOrdine2.value != frm.cboOrdine3.value || frm.cboOrdine2.value==0 || frm.cboOrdine2.value==0) ) {  
     if (Nuova) 
	 {
        frm.hidNuovaFinestra.value='1' ;
		frm.target='_blank'; 		
	 }
	 else
	 {
	    frm.hidNuovaFinestra.value='0' ;
		frm.target='_self'; 
	 }
     return true;
	 }
  else {
     alert ("I valori dell'ordinamento sono doppi! Correggerli.");	 
	 return false;
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
<form action="documenti.asp" name="frmTrova" method="post">
  <table width="100%" border="0">
    <tr> 
      <td colspan="2"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"> 
          &nbsp;&nbsp;Informazioni documento &nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/fogli.gif" width="16" height="18"></b></div>
      </td>
    </tr>
    <tr bgcolor="#CEECFD"> 
      <td> 
        <p>Testo da ricercare</p>
      </td>
    </tr>
    <tr bgcolor="#FFFFCC"> 
      <td>         
          <input type="text" name="txtTesto" size="80">
        <a href="ricerca.asp">avanzata</a> </td>
    </tr>
  </table>
  <br>
  <br>
  <table width="100%" border="0">
    <tr> 
      <td colspan="3"> 
        <div align="center"><b><img src="../../../../immagini/sistema/bottoni/icone/ordinamento.gif" width="18" height="18">&nbsp;&nbsp;Ordinamento&nbsp;&nbsp;<img src="../../../../immagini/sistema/bottoni/icone/ordinamento.gif" width="18" height="18"></b></div>
      </td>
    </tr>
    <tr bgcolor="#CEECFD"> 
      <td> 
        <div align="center">1&deg; livello</div>
      </td>
      <td> 
        <div align="center">2&deg;livello</div>
      </td>
      <td> 
        <div align="center">3&deg; livello</div>
      </td>
    </tr>
    <tr bgcolor="#FFFFCC"> 
      <td> 
        <div align="center"> 
          <select name="cboOrdine1">
            <option value="docData">Data</option>
			<option value="docNumero">Num. prot.</option>
            <option value="docFax">Num. fax</option>
            
          </select>
        </div>
      </td>
      <td> 
        <div align="center"> 
          <select name="cboOrdine2">
            <option value="0">Nessuno...</option>
            <option value="docNumero">Num. prot.</option>
            <option value="docFax">Num. fax</option>
            <option value="docData">Data</option>
          </select>
        </div>
      </td>
      <td> 
        <div align="center"> 
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
  <p align="center"> 
    <input type="hidden" name="hidSwitch" value="2">
    <input type="hidden" name="hidNuovaFinestra" value="0">
	<input type="image" border="0" name="imageField" src="../../../../immagini/sistema/bottoni/icone/lente.gif" width="31" height="31" onClick="return CheckSelection(document.frmTrova,false);">
    &nbsp;&nbsp;&nbsp;<input type="image" border="0" name="imageField2" src="../../../../immagini/sistema/bottoni/icone/easyfind2.gif" width="31" height="31" onClick="return CheckSelection(document.frmTrova,true);">
  </p>
</form>
</body>
</html>
