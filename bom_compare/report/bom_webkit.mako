<html>
<head>
    <style type="text/css">
        ${css}

        /*Colori utilizzati:
          #b7bec8 blu celeste
          #f6cf3b giallo
          #7c7bad violetto
          #444242 grigio scuro
        */

        p {
           margin:2px;
        }
        h2 {
            font-size:13px;
        }

        .red {
            color:#A70010;
            font-weight:bold;
        }
        .blu {
            color:#363AA7;
            font-weight:bold;
        }
        .green {
            color:#004E00;
            font-weight:bold;
        }

        .right {
            text-align:right;
        }
        .center {
            text-align:center;
        }
        .left {
            text-align:left;
        }
        .even {
            background-color: #efeff8;
        }
        .odd {
            background-color: #FFFFFF;
        }

        .total {
            font-size:11px;
            font-weight:bold;
            padding:4px;
            background-color: #f6cf3b;
        }

        .center_line {
            text-align:center;
            border:1px solid #000;
            padding:3px;
        }

        table.list_table {
            border:1px solid #000;
            padding:0px;
            margin:0px;
            cellspacing:0px;
            cellpadding:0px;
            border-collapse:collapse;

            /*Non funziona il paginate*/
            -fs-table-paginate: paginate;
        }

        table.list_table tr, table.list_table tr td {
            page-break-inside:avoid;
        }

        thead tr th{
            text-align:center;
            font-size:10px;
            border:1px solid #000;
            background:#7c7bad;
        }
        thead {
            display: table-header-group;
            }

        tbody tr td{
            text-align:center;
            font-size:10px;
            border:1px solid #000;
        }
        .description{
              width:250px;
              text-align:left;
        }
        .data{
              width:80px;
              /*color: #000000;*/
        }
        .nopb {
            page-break-inside: avoid;
           }
    </style>
</head>
<body>
   <% setLang('it_IT') %>
   %for parent in object_list(data):
         <!-- ################## BOM BLOCK ################################# -->
         <p><h2>Distinta base primaria: [${parent|entity}] ${get_mp_name(parent)}</h2></p>
         %if create_current_bom(parent):
             <table class="list_table">
                 <!-- ################## HEADER ############################ -->
                   <thead>
                       <tr>
                          <th>Componenti</th>
                          %for col in get_cols():
                              <th>${col|entity}<br/>${get_internal_note(col)}</th>
                          %endfor
                       </tr>
                   </thead>

                 <!-- ################## BODY ############################## -->
                  <tbody>
                      <%i=0%>
                      <%rows = get_rows()%>
                      %for row in rows:
                          %if (i % 2) == 0:
                              <% c = "even" %>
                          %else:
                              <% c = "odd" %>
                          %endif

                          <tr>
                            <td class="description ${c|entity}">${row} ${get_mp_name(row)}</td>
                            <%cols=get_cols()%>
                            %for col in cols:
                               <%sign=test_bom_model(row,col)%>
                               <%q=get_current_bom(row, col)%>
                               %if q == "-":
                                   <td class="data ${c|entity}">${q|entity}</font></td>
                               %else:
                                   %if sign == ">":
                                       <td class="data blu ${c|entity}">${q|entity}</td>
                                   %elif sign == "+":
                                       <td class="data green ${c|entity}">${q|entity}</td>
                                   %elif sign == "-":
                                       <td class="data red ${c|entity}">${q|entity}</td>
                                   %else: # ("=","<"):
                                       <td class="data ${c|entity}">${q|entity}</td>
                                   %endif
                               %endif
                        %endfor
                      </tr>
                   <%i+=1%>
                   %endfor
                 <!-- ################## TOTALS ############################ -->
                       <tr>
                          <td class="total right">Totali</td>
                          %for col in get_cols():
                              <%tot_col=get_total_cols(col)%>
                              %if tot_col!="1.00000":
                                  <td class="total center red">${tot_col|entity}</td>
                              %else:
                                  <td class="total center">${tot_col|entity}</td>
                              %endif

                          %endfor
                       </tr>

                  </tbody>

             </table>
         %endif
   %endfor
</body>
</html>
