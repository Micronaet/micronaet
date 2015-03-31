<%
if not (session("isAutenticated")) then
   response.redirect(Application("WebSite") + "/index.asp")
end if
%>
