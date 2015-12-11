<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<title>Mappatura dentale</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script language="JavaScript">

function Hide(divId) {
      document.getElementById(divId).style.display = 'none';
      divId = parseInt(divId) + 40;
      document.getElementById(divId.toString()).style.display = 'none';
}

function Show(divId){
      document.getElementById(divId).style.display='block';
      divId = parseInt(divId) + 40;
      document.getElementById(divId.toString()).style.display = 'block';
}
</script>
<style type="text/css">
<!--
body {
	margin-left: 0px;
	margin-top: 0px;
	margin-right: 0px;
	margin-bottom: 0px;
    font-size: 14px; color: #333333; 
}

table {
      border="1";
      cellspacing="0";
      cellpadding="0";
}

tr {
    font-size: 14px; color: #333333; 
    bordercolor="#333333";
    bgcolor="#FFFFCC";
}
-->
</style>
</head>
<body>

<?php
include('xmlrpc/xmlrpc.inc');

// PARAMETER:
$user = 'admin';
$password = 'admin';
$dbname = 'Poliambulatorio';
$server = "localhost";
$port = "8069";
$type_connection = "http";
$server_url = "http://$server:$port/xmlrpc";

// LOGIN:
$sock = new xmlrpc_client("$server_url/common");

$msg = new xmlrpcmsg("login");
$msg->addParam(new xmlrpcval($dbname, "string"));
$msg->addParam(new xmlrpcval($user, "string"));
$msg->addParam(new xmlrpcval($password, "string"));
$resp = $sock->send($msg);
$val = $resp->value();
$uid = $val->scalarval(); 


// READ:
// Leggo i dati del paziente
$partner_id = $_GET['id'];
$args_read=array(
   new xmlrpcval("id", "string"),
   new xmlrpcval("name", "string"),
);

$sock = new xmlrpc_client("$server_url/object");
$msg=new xmlrpcmsg('execute');
$msg->addParam(new xmlrpcval($dbname, "string"));
$msg->addParam(new xmlrpcval($uid, "int"));
$msg->addParam(new xmlrpcval($password, "string"));
$msg->addParam(new xmlrpcval("res.partner", "string"));
$msg->addParam(new xmlrpcval("read", "string"));
$msg->addParam(new xmlrpcval(array(new xmlrpcval($partner_id, "int")), "array"));
$msg->addParam(new xmlrpcval($args_read, "array"));

$resp = $sock->send($msg);
if ($resp->faultCode()) {
  echo 'Errore: '.$resp->faultString()."\n";
} else {
  $val=$resp->value();
  $ids=$val->scalarval();
  $id=$ids[0]->scalarval();
  $descrizione_patiente= "Paziente: ".$id['name']->scalarval()."<br>";
  //echo "ID paziente: ".$id['id']->scalarval()."<br>";
}
?>
<img src="images/denti.gif" width="307" height="408" hspace="9" vspace="16" border="0" usemap="#denti"><br>

<?php
echo $descrizione_patiente;

// SEARCH:
// Cerco le operazioni
$args_search=array(
                  new xmlrpcval(
                      array(
                         new xmlrpcval("partner_id" , "string"),
                         new xmlrpcval("=","string"),
                         new xmlrpcval($partner_id,"int")),
                  "array"),
                  );

$sock = new xmlrpc_client("$server_url/object");
$msg=new xmlrpcmsg('execute');
$msg->addParam(new xmlrpcval($dbname, "string"));
$msg->addParam(new xmlrpcval($uid, "int"));
$msg->addParam(new xmlrpcval($password, "string"));
$msg->addParam(new xmlrpcval("dentist.operation", "string"));
$msg->addParam(new xmlrpcval("search", "string"));
$msg->addParam(new xmlrpcval($args_search, "array"));

//print "<PRE>" . htmlentities($msg->serialize()) . "</PRE>";

$resp = $sock->send($msg);
if ($resp->faultCode()) {
   echo 'Error: '.$resp->faultString()."\n";
   } 
else {
   $val=$resp->value();
   $ids=$val->scalarval();
}

// Leggo le operazioni appena cercate:
$args_read=array(
   new xmlrpcval("id", "string"),
   new xmlrpcval("name", "string"),
   new xmlrpcval("date", "string"),
   new xmlrpcval("product_id", "string"),
   new xmlrpcval("tooth", "string"),
   new xmlrpcval("state", "string"),
   new xmlrpcval("note", "string"),
);

$sock = new xmlrpc_client("$server_url/object");
$msg=new xmlrpcmsg('execute');
$msg->addParam(new xmlrpcval($dbname, "string"));
$msg->addParam(new xmlrpcval($uid, "int"));
$msg->addParam(new xmlrpcval($password, "string"));
$msg->addParam(new xmlrpcval("dentist.operation", "string"));
$msg->addParam(new xmlrpcval("read", "string"));
$msg->addParam(new xmlrpcval($ids, "array"));
$msg->addParam(new xmlrpcval($args_read, "array"));

//print "<PRE>" . htmlentities($msg->serialize()) . "</PRE>";

$operazioni_denti=array("11"=>"","12"=>"","13"=>"","14"=>"","15"=>"","16"=>"","17"=>"","18"=>"",
						"21"=>"","22"=>"","23"=>"","24"=>"","25"=>"","26"=>"","27"=>"","28"=>"",
						"31"=>"","32"=>"","33"=>"","34"=>"","35"=>"","36"=>"","37"=>"","38"=>"", 
						"41"=>"","42"=>"","43"=>"","44"=>"","45"=>"","46"=>"","47"=>"","48"=>"", 
						"51"=>"","52"=>"","53"=>"","54"=>"","55"=>"","56"=>"","57"=>"","58"=>"", 
						"61"=>"","62"=>"","63"=>"","64"=>"","65"=>"","66"=>"","67"=>"","68"=>"", 
						"71"=>"","72"=>"","73"=>"","74"=>"","75"=>"","76"=>"","77"=>"","78"=>"", 
						"81"=>"","82"=>"","83"=>"","84"=>"","85"=>"","86"=>"","87"=>"","88"=>"",
                        "*"=>"", "n"=>"");



$resp = $sock->send($msg);
if ($resp->faultCode()) {
  echo 'Error: '.$resp->faultString()."\n";
} else {
  $val=$resp->value();
  $ids=$val->scalarval();
  $id=$ids[0]->scalarval();
  echo "<br><br>";

  foreach ($ids as $item){     
     $elemento=$item->scalarval();
     $prodotto=$elemento['product_id']->scalarval();
     $dente=$elemento['tooth']->scalarval();
     if ($elemento['tooth']){ // solo quelle che hanno i denti TODO controllare se il codice dente è corretto (anche no)!
		 if (is_array($prodotto)) {
            $prodotto_desc=$prodotto[1]->scalarval();
            }
         else {
            $prodotto_desc="non trovato";
            }

		 $operazioni_denti[$dente] = $operazioni_denti[$dente].
                                        "<tr><td>".$elemento['date']->scalarval().
                                        "</td><td>".$prodotto_desc.
                                        "</td><td>".$elemento['name']->scalarval().
                                        "</td><td>".$elemento['note']->scalarval().
                                        "</td><td><img src='images/".$elemento['state']->scalarval().".gif'>".
                                        "</td></tr>";
     }
   }

}
  echo "<br><br>";

echo "Elenco operazioni:";
foreach ($operazioni_denti as $dente=>$operazioni){
    if (!(($dente == "56") or ($dente == "57") or ($dente == "58") or 
          ($dente == "66") or ($dente == "67") or ($dente == "68") or 
          ($dente == "76") or ($dente == "77") or ($dente == "78") or 
          ($dente == "86") or ($dente == "87") or ($dente == "88")))
          echo "<div class='mid' id='$dente' style='DISPLAY: none' >";
          if ($operazioni){
             echo "<table> 
                    <tr><td colspan='5'>Dente: $dente</td></tr>                   
                    <tr><td>Data</td><td>Prodotto</td><td>Operazione</td><td>Note</td><td>Stato</td></tr>                   
                      $operazioni
                   </table>";
             }
          echo "</div>";
}
?>


<!-- MAPPATURA IMMAGINE DENTALE: ******************************************* -->
<map name="denti" id="denti">
  <!--Quardante 4 -->
  <area shape="rect" coords="68,234,97,263" alt="48" onMouseOut ="javascript:Hide('48')" href="#" onMouseOver ="javascript:Show('48')">
  <area shape="rect" coords="68,264,99,289" alt="47"  onMouseOut ="javascript:Hide('47')" href="#" onMouseOver ="javascript:Show('47')">
  <area shape="poly" coords="77,318,68,295,97,289,102,296,103,311" alt="46" onMouseOut ="javascript:Hide('46')" href="#" onMouseOver ="javascript:Show('46')">
  <area shape="circle" coords="94,327,13" alt="45" onMouseOut ="javascript:Hide('45')" href="#" onMouseOver ="javascript:Show('45')">
  <area shape="poly" coords="98,356,114,346,117,338,108,332,101,339,92,340,91,347" alt="44" onMouseOut ="javascript:Hide('44')" href="#" onMouseOver ="javascript:Show('44')">
  <area shape="circle" coords="113,360,12" alt="43" onMouseOut ="javascript:Hide('43')" href="#" onMouseOver ="javascript:Show('43')">
  <area shape="poly" coords="118,374,125,366,128,360,135,358,138,366,137,376,132,382,136,382"  alt="42" onMouseOut ="javascript:Hide('42')" href="#" onMouseOver ="javascript:Show('42')">
  <area shape="poly" coords="155,363,146,363,136,380,144,385,154,384" alt="41" onMouseOut ="javascript:Hide('41')" href="#" onMouseOver ="javascript:Show('41')">

  <!--Quardante 3 -->
  <area shape="rect" coords="156,362,173,386" alt="31" onMouseOut ="javascript:Hide('31')" href="#" onMouseOver ="javascript:Show('31')">
  <area shape="rect" coords="174,360,189,382" alt="32" onMouseOut ="javascript:Hide('32')" href="#" onMouseOver ="javascript:Show('32')">
  <area shape="circle" coords="199,362,11" alt="33" onMouseOut ="javascript:Hide('33')" href="#" onMouseOver ="javascript:Show('33')">
  <area shape="poly" coords="198,335,213,339,222,344,221,356,212,359,208,353,198,350,194,342" alt="34" onMouseOut ="javascript:Hide('34')" href="#" onMouseOver ="javascript:Show('34')">
  <area shape="poly" coords="208,317,233,322,226,343,212,337,204,332" alt="35" onMouseOut ="javascript:Hide('35')" href="#" onMouseOver ="javascript:Show('35')">
  <area shape="rect" coords="212,295,243,318" alt="36" onMouseOut ="javascript:Hide('36')" href="#" onMouseOver ="javascript:Show('36')">
  <area shape="rect" coords="216,268,246,295" alt="37" onMouseOut ="javascript:Hide('37')" href="#" onMouseOver ="javascript:Show('37')">
  <area shape="rect" coords="214,238,250,268" alt="38" onMouseOut ="javascript:Hide('38')" href="#" onMouseOver ="javascript:Show('38')">

  <area shape="rect" coords="68,178,99,207" alt="18" onMouseOut ="javascript:Hide('18')" href="#" onMouseOver ="javascript:Show('18')">
  <area shape="rect" coords="66,152,102,178" alt="17" onMouseOut ="javascript:Hide('17')" href="#" onMouseOver ="javascript:Show('17')">
  <area shape="rect" coords="74,125,105,151" alt="16" onMouseOut ="javascript:Hide('16')" href="#" onMouseOver ="javascript:Show('16')">
  <area shape="poly" coords="84,103,93,105,106,116,101,123,81,124,76,118" alt="15" onMouseOut ="javascript:Hide('15')" href="#" onMouseOver ="javascript:Show('15')">
  <area shape="poly" coords="92,83,108,90,115,99,112,108,100,107,89,102,86,94" alt="14" onMouseOut ="javascript:Hide('14')" href="#" onMouseOver ="javascript:Show('14')">
  <area shape="poly" coords="123,92,126,82,115,69,105,74,98,82,106,88,114,92" alt="13" onMouseOut ="javascript:Hide('13')" href="#" onMouseOver ="javascript:Show('13')">
  <area shape="poly" coords="136,84,128,84,117,69,125,60,136,58,139,64,142,78" alt="12" onMouseOut ="javascript:Hide('12')" href="#" onMouseOver ="javascript:Show('12')">
  <area shape="poly" coords="154,82,159,72,161,56,151,54,138,56,139,62,144,78" alt="11" onMouseOut ="javascript:Hide('11')" href="#" onMouseOver ="javascript:Show('11')">

  <area shape="poly" coords="169,82,179,69,182,62,174,56,164,55,160,65,161,79" alt="21" onMouseOut ="javascript:Hide('21')" href="#" onMouseOver ="javascript:Show('21')">
  <area shape="poly" coords="181,87,192,85,205,70,196,62,183,60,178,73,178,79" alt="22" onMouseOut ="javascript:Hide('22')" href="#" onMouseOver ="javascript:Show('22')">
  <area shape="poly" coords="194,96,197,81,206,71,218,74,222,83,211,92,202,98" alt="23" onMouseOut ="javascript:Hide('23')" href="#" onMouseOver ="javascript:Show('23')">
  <area shape="poly" coords="206,107,207,96,222,85,231,91,235,100,218,109,212,110" alt="24" onMouseOut ="javascript:Hide('24')" href="#" onMouseOver ="javascript:Show('24')">
  <area shape="poly" coords="211,126,211,116,218,110,231,103,240,110,242,119,235,125,222,128" alt="25" onMouseOut ="javascript:Hide('25')" href="#" onMouseOver ="javascript:Show('25')">
  <area shape="poly" coords="216,151,215,134,225,127,241,126,248,136,246,152,234,156,222,156" alt="26" onMouseOut ="javascript:Hide('26')" href="#" onMouseOver ="javascript:Show('26')">
  <area shape="rect" coords="218,157,248,181" alt="27" onMouseOut ="javascript:Hide('27')" href="#" onMouseOver ="javascript:Show('27')">
  <area shape="rect" coords="215,181,251,206" alt="28" onMouseOut ="javascript:Hide('28')" href="#" onMouseOver ="javascript:Show('28')">
</map>

<!-- DOT per i denti con operazioni -->
<?php
$posizione_dot= array(
	"11"  => "left: 152px; top: 56px; width: 28px; height: 23px;",
	"12"  => "left: 123px; top: 63px; width: 28px; height: 23px;",
	"13"  => "left: 102px; top: 76px; width: 28px; height: 23px;",
	"14"  => "left: 82px; top: 96px; width: 28px; height: 23px;",
	"15"  => "left: 71px; top: 121px; width: 28px; height: 23px;",
	"16"  => "left: 64px; top: 149px; width: 28px; height: 23px;",
	"17"  => "left: 77px; top: 167px; width: 28px; height: 23px;",
	"18"  => "left: 77px; top: 194px; width: 28px; height: 23px;",
	"21"  => "left: 181px; top: 55px; width: 28px; height: 23px;",
	"22"  => "left: 210px; top: 64px; width: 28px; height: 23px;",
	"23"  => "left: 229px; top: 78px; width: 28px; height: 23px;",
	"24"  => "left: 243px; top: 96px; width: 28px; height: 23px;",
	"25"  => "left: 255px; top: 118px; width: 28px; height: 23px;",
	"26"  => "left: 263px; top: 149px; width: 28px; height: 23px;",
	"27"  => "left: 265px; top: 179px; width: 28px; height: 23px;",
	"28"  => "left: 265px; top: 204px; width: 28px; height: 23px;",
	"31"  => "left: 168px; top: 406px; width: 28px; height: 23px;",
	"32"  => "left: 191px; top: 403px; width: 28px; height: 23px;",
	"33"  => "left: 216px; top: 389px; width: 28px; height: 23px;",
	"34"  => "left: 234px; top: 370px; width: 28px; height: 23px;",
	"35"  => "left: 246px; top: 347px; width: 28px; height: 23px;",
	"36"  => "left: 259px; top: 317px; width: 28px; height: 23px;",
	"37"  => "left: 264px; top: 290px; width: 28px; height: 23px;",
	"38"  => "left: 267px; top: 262px; width: 28px; height: 23px;",
	"41"  => "left: 146px; top: 406px; width: 28px; height: 23px;",
	"42"  => "left: 122px; top: 401px; width: 28px; height: 23px;",
	"43"  => "left: 95px; top: 387px; width: 28px; height: 23px;",
	"44"  => "left: 81px; top: 369px; width: 28px; height: 23px;",
	"45"  => "left: 72px; top: 347px; width: 28px; height: 23px;",
	"46"  => "left: 63px; top: 320px; width: 28px; height: 23px;",
	"47"  => "left: 58px; top: 288px; width: 28px; height: 23px;",
	"48"  => "left: 57px; top: 258px; width: 28px; height: 23px;",
    );

foreach ($operazioni_denti as $dente=>$operazioni){
    if (is_numeric($dente)) {
       if ($dente >= 51 and $dente <= 85){
          $dotdente=$dente - 40;  
          }
       else {
          $dotdente=$dente - 0;  
        }
          if ($operazioni){
                echo "<div id='dot$dotdente' style='position:absolute; ".$posizione_dot[$dotdente]."'><img src='images/denti/".$dotdente.".png' href='#' onMouseOut=\"javascript:Hide('$dente')\" onMouseOver =\"javascript:Show('$dente')\"></div>";
                }
             echo "</div>";
       }
    }
?>
</body>
</html>

