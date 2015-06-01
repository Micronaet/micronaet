#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import lxml.html
t = lxml.html.fromstring('''<b>TRANDIUR</b>&nbsp;</td><td class="sc4bis" >
"200 MG + 20 MG COMPRESSE RIVESTITE CON FILM" 30 COMPRESSE&nbsp;</td><td class="sc4bis" >
TEOFARMA Srl&nbsp;</td><td class="sc4bis" ><a href="index.php?&amp;SEARCH=yes&amp;SOSTANZA=LABETALOLO/CLORTALIDONE" >
LABETALOLO/CLORTALIDONE&nbsp;</a></td><td class="sc4bis" >
Ricetta ripetibile, validità 6mesi, ripetibile 10 volte&nbsp;</td><td class="sc4bis"  align="right">
C&nbsp;</td><td class="sc4bis"  align="right">
&nbsp;</td><td class="sc4bis"  align="right">
       11.47&nbsp;</td><td class="sc4bis"  align="right">
14/02/2011&nbsp;</td></tr>''')
print t.text_content()

