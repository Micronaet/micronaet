#!/bin/bash
echo "Ricerca lettere A"
for i in {1..254}
do
   wget "http://farmaco.agenziafarmaco.it/index.php?SEARCH=yes&S_DESCR_SPECIALITA=a&S_SOSTANZA=&S_DITTA=&SSN=&DSNOTA_AIFA=&GRUPPO_RICETTA=&PAGE=$i"
done

echo "Ricerca lettere E"
for i in {1..218}
do
   wget "http://farmaco.agenziafarmaco.it/index.php?SEARCH=yes&S_DESCR_SPECIALITA=e&S_SOSTANZA=&S_DITTA=&SSN=&DSNOTA_AIFA=&GRUPPO_RICETTA=&PAGE=$i"
done

echo "Ricerca lettere I"
for i in {1..250}
do
   wget "http://farmaco.agenziafarmaco.it/index.php?SEARCH=yes&S_DESCR_SPECIALITA=i&S_SOSTANZA=&S_DITTA=&SSN=&DSNOTA_AIFA=&GRUPPO_RICETTA=&PAGE=$i"
done

echo "Ricerca lettere O"
for i in {1..230}
do
   wget "http://farmaco.agenziafarmaco.it/index.php?SEARCH=yes&S_DESCR_SPECIALITA=o&S_SOSTANZA=&S_DITTA=&SSN=&DSNOTA_AIFA=&GRUPPO_RICETTA=&PAGE=$i"
done

echo "Ricerca lettere U"
for i in {1..82}
do
   wget "http://farmaco.agenziafarmaco.it/index.php?SEARCH=yes&S_DESCR_SPECIALITA=u&S_SOSTANZA=&S_DITTA=&SSN=&DSNOTA_AIFA=&GRUPPO_RICETTA=&PAGE=$i"
done


