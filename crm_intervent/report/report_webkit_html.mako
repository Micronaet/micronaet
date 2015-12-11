<html>
<head>
    <style type="text/css">
        ${css}        
    </style>
</head>
<body>
    <% setLang("it_IT") %>
    %for appointment in objects :
        %if appointment.relation_needed :                     
            <table class="simple_border_pb w100 font_14">
               <tr>
                  <td class="font_big centered" height="25px" colspan="2">RELAZIONE APPUNTAMENTO</td>
               </tr>               
               <tr>
                  <td class="font_big sx" height="25px" colspan="2">VISITA DEL ${appointment.date or "" |entity}</td>
               </tr>               
               <tr>
                  <td class="simple_no_bottom_border font_10" width="50%" height="25px"><i>Società: </i>${appointment.partner_ids and appointment.partner_ids[0].name or "" |entity}</td>
                  <td class="simple_no_bottom_border font_10" width="50%" height="25px"><i>Visita del periodo:</i></td>          
               </tr>
               <tr>
                  <td class="simple_no_top_border font_10" width="50%" height="25px"><i>${_("Referent")}: </i>${appointment.relation_ref or "" |entity}</td>
                  <td class="simple_no_top_border font_big" width="50%" height="25px"><i>${appointment.date and appointment.date[5:7] or "" |entity} - ${appointment.date and appointment.date[:4] or "" |entity}</i></td>          
               </tr>

               <tr>
                  <td class="simple_no_bottom_border font_10" width="50%" height="25px"><i>${_("Supervisor")}: </i>${appointment.relation_supervisor or "" |entity}</td>          
                  <td class="simple_no_bottom_border font_10" width="50%" height="25px"><i>${_("Department")}:</i></td>
               </tr>
               <tr>
                  <td class="simple_no_top_border font_10" width="50%" height="25px"><i>${_("uperv. position")}: </i>${appointment.relation_supervisor_position or "" |entity}</td>          
                  <td class="simple_no_top_border font_10" width="50%" height="25px"><i>${appointment.relation_department or "" |entity}</i></td>
               </tr>

               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">OBIETTIVI DURANTE IL PERIODO DI VALUTAZIONE</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_goal or "" |entity}</td>
               </tr>
               
               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">CONSEGUIMENTI, RISULTATI E RESPONSABILITA' (parte al dipendente)</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_result or "" |entity}</td>
               </tr>

               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">VALUTAZIONE (parte riservata al supervisore)</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_evaluation or "" |entity}</td>
               </tr>

               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">PUNTI DI FORZA E AREE DI POTENZIAMENTO</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_strength or "" |entity}</td>
               </tr>

               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">PIANO DI SVILUPPO</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_plan or "" |entity}</td>
               </tr>

               <tr>
                  <td colspan="2" class="simple_no_bottom_border font_12 bg_yellow sx">OBIETTIVI PER IL PERIODO DI VALUTAZIONE SUCCESSIVO</td>
               </tr>
               <tr>
                  <td colspan="2" class="simple_no_top_border font_10" height="70px">${appointment.relation_goal_future or "" |entity}</td>
               </tr>

               <tr>
                  <td class="simple_no_bottom_border font_12 bg_yellow sx">FIRMA</td>
                  <td class="simple_no_bottom_border font_12 bg_yellow sx">FIRMA SUPERVISORE</td>
               </tr>
               <tr>
                  <td class="simple_no_top_border font_10" height="50px"><p>Nome: ${appointment.user_id.name or "" |entity}</p><p>Data: ${appointment.date[:10] or "" |entity}</p></td>
                  <td class="simple_no_top_border font_10" height="50px"><p>Nome: ${appointment.user_id.name or "" |entity}</p><p>Data: ${appointment.date[:10] or "" |entity}</p></td>
               </tr>
            </table>
            <!--<div class="page-break">&nbsp;</div>-->
        %endif
    %endfor
</body>
</html>
