<html>
  <head>
    <title>GPB clienti</title>
    <style type="text/css">
<!--
<?php 
  $browser=strtoupper($_GET["browser"]); 
  if ($browser == "BROWSER")
     {$h_font="font-size: 13px;";
      $b_table_w="800px";}
  elseif ($browser == "IPHONE")
     {$h_font="font-size: 24px;";
      $b_table_w="100%";}
  elseif ($browser == "BB")
     {$h_font="font-size: 9px;";
      $b_table_w="100%";}
  else
     {$h_font="font-size: 12px;";
      $b_table_w="100%";}
?>
body,td,th {<?php echo $h_font; ?> color: #333333; font-family: Verdana, Arial, Helvetica, sans-serif;}
body {background-color: #FFFFFF; margin: 0px;}
.style9 {color: #FFFFFF; font-weight: bold; }
.style10 {color: #FFFFFF}
.styleRed {color: #FF0000; }
.styleGreen {color: #008800; }
a:link {color: #FFFFFF;}
a:visited {color: #FFFFFF;}
a:hover {color: #FFFF33;}
a:active {color: #FFFFFF;}
.style13 {<?php echo $h_font; ?> color: #FFFFFF; font-weight: bold; }
.tr_stileP {background-color: #FFFFFF; }
.tr_stileD {background-color: #FFFFCC; }
-->
</style>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"></head>
<body>
<table width="<?php echo $b_table_w; ?>" border="1" cellpadding="0" cellspacing="0" bordercolor="#333333">
 <tr align="center" bgcolor="#666666">
 <td height="20"><span class="style9"><a href="cust_find.php">Ricerca:</a></span></td>
 <td height="30" colspan="4" align="left"><span class="style9">Cod.:<?php echo strtoupper($_GET["codice"]); ?><br>
  Desc.:<?php echo strtoupper($_GET["descrizione"]); ?></span><span class="style10"></span><span class="style10"></span></td>
 </tr>
 <tr align="center" bgcolor="#003366">
  <td height="20"><span class="style13">Codice</span></td>
  <td height="20"><span class="style13">Descrizione</span></td>
  <td height="20"><span class="style13">Sconto</span></td>
 </tr>
<?php
$fndcod = strtoupper($_GET["codice"]);
$iscod= ($fndcod != '');
$fnddesc = strtoupper($_GET["descrizione"]);
$isdesc= ($fnddesc != '');
$fd = fopen ("sconti.GPB", "r");
$cont=0;
while (!feof ($fd)) {
 $buffer = fgetcsv($fd, 4096, ";"); 
 $poscod=strripos(" $buffer[0]", $fndcod);
 $posdesc=strripos(" $buffer[1]", $fnddesc);
 if ((!$iscod || ($poscod > 0)) && (!$isdesc || ($posdesc > 0)) ){        
   ++$cont;   
   if (($cont % 2)==0) {
      $stile= "class='tr_stileD'";} 
   else {
      $stile= "class='tr_stileP'";} 

   echo "<tr $stile>";
   for ($i = 0; $i < 3; ++$i){
    if ($buffer[$i] == ""){$buffer[$i] = " ";}
    if ($i >= 2) {echo "<td align='right'>";} else {echo "<td>";}
    if ($buffer[2]>0){
        echo "<span class='styleGreen' $stile>$buffer[$i]</span></td>";} 
    else {echo "<span class='styleRed' $stile>$buffer[$i]</span></td>";}
    }
   echo  "</tr>";
   }
}
echo "<tr bgcolor='#003366'><td colspan='5' height='20'><span class='style13'>Record trovati: $cont</span></td></tr>";
fclose ($fd);?>
</table>
</body>
<html>

