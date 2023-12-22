function OpenNewWindow(MyPath)
{
window.open(MyPath,"","toolbar=no,status=no,menubar=no,location=center,scrollbars=no,resizable=no,height=600,width=757");
}


$(document).on("click", ".open-EditDeploymentDialog", function () {
     var alias_name = $(this).data('alias');
     var alias_activity = $(this).data('activity').replace(/[\]/['"]+/g, '');
     var alias_remarks = $(this).data('remarks');
     $("#data_alias_header").text("Edit deployment details of " + alias_name);
     $("#data_alias").val(alias_name);
     $("#data_activity").val(alias_activity);
     $("#data_remarks").val(alias_remarks);
});

$(document).on("click", ".open-checkOutDeploymentDialog", function () {
     var alias_name = $(this).data('aliasco');
     $("#co_data_alias_header").text("Check Out - " + alias_name);
     $("#co-data-alias").val(alias_name);
     $("#CO_sel_cB").hide();
     $("#CO_jiratix_remarks").hide();
     $("#CO_adtl_options").hide();
});

$(document).on("click", ".open-IncludeDeploymentDialog", function () {
    $("#incld_json_form").hide();
    $("#incld_indv_form_alias").hide();
    $("#incld_indv_form_owner").hide();
    $("#incld_indv_form_region").hide();
    $("#incld_indv_form_app").hide();
    $("#incld_csv_form").hide();
});

$(document).on('click', ':not(form)[data-confirm]', function(e){
    if(!confirm($(this).data('confirm'))){
        e.stopImmediatePropagation();
        e.preventDefault();
    }
});

$(document).on('submit', 'form[data-confirm]', function(e){
    if(!confirm($(this).data('confirm'))){
        e.stopImmediatePropagation();
        e.preventDefault();
    }
});

$(document).ready(function () {

    $("[id]").each(function(){
     if($(this).attr("id")=="timer"){
        var get_str_time = $(this).text();
        var date_now = new Date();
        var converted_time = new Date(get_str_time + 'Z');
        var current_timeleft = Math.ceil((converted_time - date_now) / (1000 * 60));
        var final_value = (current_timeleft <= 0) ? 0 : current_timeleft;

        $(this).text("(" + final_value + "m left)");
     }

     else if($(this).attr("id")=="report_timestamp"){
        var get_str_report_time = $(this).text();
        var converted_report_time = new Date(get_str_report_time + 'Z');

        $(this).text(converted_report_time.toLocaleString("sv-SE") + " (" + converted_report_time.toLocaleTimeString('en-US',{timeZoneName:'short'}).split(' ')[2] + ")").css({ 'font-weight': 'bold' });
     }
     });


    /* Radio Buttons for adding a deployment (Options) */
    $('#Incldep_upl_rdbtn').click(function () {
        if ($(this).is(':checked')) {
            $("#incld_json_form").hide();

            $("#incld_indv_form_alias").hide();
            $("#incld_indv_form_owner").hide();
            $("#incld_indv_form_region").hide();
            $("#incld_indv_form_app").hide();

            $("#incld_csv_form").show();

        }
    });

    $('#Incldep_json_rdbtn').click(function () {
        if ($(this).is(':checked')) {
            $("#incld_json_form").show();

            $("#incld_indv_form_alias").hide();
            $("#incld_indv_form_owner").hide();
            $("#incld_indv_form_region").hide();
            $("#incld_indv_form_app").hide();
            
            $("#incld_csv_form").hide();
        }
    });

    $('#Incldep_indv_rdbtn').click(function () {
        if ($(this).is(':checked')) {
            $("#incld_json_form").hide();

            $("#incld_indv_form_alias").show();
            $("#incld_indv_form_owner").show();
            $("#incld_indv_form_region").show();
            $("#incld_indv_form_app").show();
            
            $("#incld_csv_form").hide();
        }
    });

    /* END */

    /* Radio buttons for checking out deployment (Options) */
    $('#CO_all_rdbtn').click(function () {
        if ($(this).is(':checked')) {
            $("#CO_sel_cB").hide();
            $("#id_input_timeout").hide();
            $("#CO_jiratix_remarks").show();
            $("#CO_adtl_options").show();
        }
    });

    $('#CO_sel_rdbtn').click(function () {
        if ($(this).is(':checked')) {
          $("#CO_sel_cB").show();
          $("#id_input_timeout").hide();
          $("#CO_jiratix_remarks").show();
          $("#CO_adtl_options").show();
          if ($("#CO_cB_machines").children().length == 1){
          $.ajax({
                    type: "POST",
                    url: "/dashboard/index",
                    data: {
                    action_done : $("input[name=CO_rd_btns]:checked").val(),
                    alias_name : $('#co-data-alias').val()
                    },
                    contentType: 'application/x-www-form-urlencoded; charset=UTF-8'
               })
               .done(function(data) {
                    var returnedData = data.alias_machines[0]["instanceList"];
                    if(returnedData){
                         var list_of_checkboxes = '';
                         for (let i = 0; i < returnedData.length; i++) {
                              list_of_checkboxes += "<input type='checkbox' name = 'CO_chbx_machines' value = '" + Object.keys(returnedData[i])[0] + "' /> <h7>" + Object.keys(returnedData[i])[0] + "</h7><br />";
                         }
                         $("#CO_cB_machines").append(list_of_checkboxes);
                         $("input[name=CO_rd_btns][value='CO_sel_rdbtn']").prop("checked",true);
                    }

               });
           } else {
               $("input[name=CO_rd_btns][value='CO_sel_rdbtn']").prop("checked",true);
           }
        }
    });

    $('#CO_set_tmt').click(function () {
        if ($(this).is(':checked')) {
            $("#id_input_timeout").show();
        } else {
          $("#id_input_timeout").hide().val("");
        }
    });

    $('#form2').submit(function () {
          var tempArray = [];
          $("input:checkbox[name=CO_chbx_machines]:checked").each(function(){
              tempArray.push($(this).val());
          });

          $('.placeholder_checkbox').val(tempArray);

    });

     $(".modal").on("hidden.bs.modal", function(){
         $(this)
         .find("input[type=text],textarea,select")
            .val('')
            .end()
         .find("input[type=checkbox], input[type=radio]")
            .prop("checked", "")
            .end();
          $('#CO_cB_machines').find('*').not('.placeholder_checkbox').remove().end();
          $("#id_input_timeout").hide().val("");
     });

     $('.white-space-is-dead').on('input change', function() {  
        $(this).val($(this).val().replace(/\s/g,""));
    });


     $(window).on('pageshow', function(e) {
          if ($("#message_alert").text().trim().length) {
             alert($("#message_alert").text());
          }
          e.preventDefault();
     });

});