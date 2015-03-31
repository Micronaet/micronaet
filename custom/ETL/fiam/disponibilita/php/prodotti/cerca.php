<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<?php
function getBrowser()
{   $u_agent = $_SERVER['HTTP_USER_AGENT'];
    if(preg_match('/iPhone/i',$u_agent))
    {   $bname = 'iPhone';
        $ub = "IPHONE";}
    elseif(preg_match('/BlackBerry/i',$u_agent))
    {   $bname = 'BlackBerry';
        $ub = "BB";}
    else
    {   $bname = 'Browser';
        $ub = "BROWSER";}
    return array(
        'userAgent' => $u_agent,
        'name'      => $bname,
        'sigla'     => $ub,
    );
}
$ua=getBrowser();
$yourbrowser= $ua['sigla'];

$filename="./esito.txt";
$d="";
$tot="0";
if (file_exists($filename)){
   $fd = fopen ($filename, "r");
   while (!feof ($fd)) {
	 $buffer = fgetcsv($fd, 4096, ";"); 
	 $d=$buffer[0];
	 $tot=$buffer[1];
	 }
   }
?> 

<head>
<title>GPB: Ricerca esistenza</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">
	<!--
		function setFocus()
		{
			document.frmCerca.codice.focus();
		}
	// -->
</script>
<style type="text/css">
<!--
body,td,th {
	font-size: xx-small;
	color: #333333;
	font-family: Verdana, Arial, Helvetica, sans-serif;
}
body {
	background-color: #FFFFFF;
	margin-left: 0px;
	margin-top: 0px;
	margin-right: 0px;
	margin-bottom: 0px;
}
input {
	font-family: Verdana, Arial, Helvetica, sans-serif;
	font-size: x-small;
}
.style1 {
	color: #FFFFFF;
	font-weight: bold;
}
-->
</style></head>
<body onLoad="codice.focus();">


<table width="350" border="1" cellpadding="0" cellspacing="0" bordercolor="#333333">
<form name="frmCerca" method="get" action="stato.php">
  <tr align="center" bgcolor="#003300">
    <td height="40" colspan="3"><span class="style1">GPB: RICERCA ESISTENZA PRODOTTI<br>(agg.:<?php echo " " . $d; ?> - tot. <?php echo " " . $tot; ?>)<br>
    [<?php echo $yourbrowser; ?>]
</span></td>
    </tr>
  <tr bgcolor="#003366">
    <td height="40"><span class="style1">&nbsp;Codice</span></td>
    <td height="40" colspan="2" align="center"><input name="codice" type="text" id="codice"></td>
  </tr>
  <tr bgcolor="#003366">
    <td height="40"><span class="style1">&nbsp;Descrizione</span></td>
    <td height="40" colspan="2" align="center"><input name="descrizione" type="text" id="descrizione"></td>
  </tr>
  <tr align="center" bgcolor="#003300">
    <td height="35" colspan="3"><input type="submit" name="Submit" value="Cerca">
      <input type="hidden" name="browser" value="<?php echo $yourbrowser; ?>"></td>

    </tr>
</form>
</table>
      <script language="JavaScript">
	setFocus();
</script>
</body>
</html>
