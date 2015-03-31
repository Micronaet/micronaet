<%
function getDate()
  ' non funziona in vb 
  dim d
  set d = new Date()
  
  getDate = d.getDate() + "/" + (d.getMonth()+1)  + "/" + d.getYear()
end function

%>