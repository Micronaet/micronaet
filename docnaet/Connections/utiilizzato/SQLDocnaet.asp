<%
' FileName="Connection_odbc_conn_dsn.htm"
' Type="ADO"
' HTTP="false"
' Catalog=""
' Schema=""
MM_SQLDocnaet_STRING = "dsn=Docnaet;uid=panchemicals;pwd=pnchmcls;" 
if Session("Remoto")=TRUE then MM_SQLDocnaet_STRING = "dsn=DocnaetMDB;"
%>
