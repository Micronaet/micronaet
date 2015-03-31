<%
function GetImmagine(Estensione, Puntatore)
   dim Finale

   if Puntatore then Finale="p.gif" else Finale=".gif" 
  
   Estensione=lcase(Estensione)
   select case Estensione
      Case "msg" , "xls", "doc", "cad", "bmp", "tif", "jpg", "zip", "rtf", "pdf", "cdr", "txt", "vsd"
	       GetImmagine= Application("WebSite") + "/immagini/sistema/logo/documenti/"+Estensione+finale
	  Case Else
	       GetImmagine =Application("WebSite") + "/immagini/sistema/logo/documenti/std"+finale	    	   
   end select
end function   
%>