// clears flash messages in the server-side once the pop-up has been closed via ajax submission.
$(document).on("click", ".flash-clear", function () {
     $.ajax({
        type: "POST",
        url: "/SizingDashboard/index",
        data: {
            action_done: "clear_all_flashes"
        },
        contentType: 'application/x-www-form-urlencoded; charset=UTF-8'
     }).done(function(data) {
                    var returnedData = data.alert_message;
                    console.log(returnedData);
               });
});

$(document).on("click", ".open-AddInstanceDialog", function () {
    $("#incld_indv_form_instance_id").hide();
    $("#incld_indv_form_ServName").hide();
    $("#incld_indv_form_DepName").hide();
    $("#incld_indv_form_AWSRegion").hide();
    $("#incld_indv_form_IsProd").hide();
    $("#incld_indv_form_DesiredSize").hide();
    $("#incld_indv_form_Notes").hide();
    $("#incld_csv_form").hide();
});

$(document).ready(function(){

    // convert date and time in reports page to be readable and adjust according to the user's timezone.
    $("[id]").each(function(){
        if($(this).attr("id")=="report_timestamp"){
            var get_str_report_time = $(this).text();
            var converted_report_time = new Date(get_str_report_time + 'Z');

            $(this).text(converted_report_time.toLocaleString("sv-SE") + " (" + converted_report_time.toLocaleTimeString('en-US',{timeZoneName:'short'}).split(' ')[2] + ")").css({ 'font-weight': 'bold' });
        }
    });

    // to check if flashes have content so that the modal cannot be closed other than the button.
    if ($("#flashes *").length > 0){
        $("#modalId").modal({backdrop: 'static', keyboard: false});
    }

    /* Radio Buttons for adding a deployment (Options) */
    $('#Incldep_upl_rdbtn').click(function () {
        if ($(this).is(':checked')) {

            $("#incld_indv_form_instance_id").hide();
            $("#incld_indv_form_ServName").hide();
            $("#incld_indv_form_DepName").hide();
            $("#incld_indv_form_AWSRegion").hide();
            $("#incld_indv_form_IsProd").hide();
            $("#incld_indv_form_DesiredSize").hide();
            $("#incld_indv_form_Notes").hide();

            $("#incld_csv_form").show();

        }
    });

    $('#Incldep_indv_rdbtn').click(function () {
        if ($(this).is(':checked')) {

            $("#incld_indv_form_instance_id").show();
            $("#incld_indv_form_ServName").show();
            $("#incld_indv_form_DepName").show();
            $("#incld_indv_form_AWSRegion").show();
            $("#incld_indv_form_IsProd").show();
            $("#incld_indv_form_DesiredSize").show();
            $("#incld_indv_form_Notes").show();

            $("#incld_csv_form").hide();
        }
    });

    // Initialize DataTable for Homepage
    var dataTable = $('#sample_data').DataTable({
        "aaSorting": [[0,'desc']],
        buttons: [
            { extend: "copy",
              title: '',
              text: '<span class="mdi mdi-content-copy"></span> Copy to Clipboard',
              className: 'datatbl-btn-blue'
            },
            { extend: "csv",
              text: '<span class="mdi mdi-note-text"></span> Export to CSV',
              className: 'datatbl-btn-green'
            }
        ]
    });
    dataTable.buttons().container()
    .appendTo( $('#table_buttons') );

    // Initialize DataTable for Dashboard Reports tab
    var dataTable2 = $('#sample_data2').DataTable({
        "aaSorting": [[0,'desc']],
        buttons: [
            { extend: "copy",
              title: '',
              text: '<span class="mdi mdi-content-copy"></span> Copy to Clipboard',
              className: 'datatbl-btn-blue'
            },
            { extend: "csv",
              title: 'Automated Sizing Dashboard - Dashboard Reports',
              text: '<span class="mdi mdi-note-text"></span> Export to CSV',
              className: 'datatbl-btn-green'
            }
        ]
    });
    dataTable2.buttons().container()
    .appendTo( $('#table_buttons_dr') );

    // Initialize DataTable for Resize Reports tab
    var dataTable3 = $('#sample_data3').DataTable({
        "aaSorting": [[0,'desc']],
        buttons: [
            { extend: "copy",
              title: '',
              text: '<span class="mdi mdi-content-copy"></span> Copy to Clipboard',
              className: 'datatbl-btn-blue'
            },
            { extend: "csv",
              title: 'Automated Sizing Dashboard - Resize Reports',
              text: '<span class="mdi mdi-note-text"></span> Export to CSV',
              className: 'datatbl-btn-green'
            }
        ]
    });
    dataTable3.buttons().container()
    .appendTo( $('#table_buttons_rr') );

    var instanceFamily = ["c5","m5","c6a","m6a", "r5", "r6a", "t3a"]
    var instanceTypeSize = ["large", "xlarge", "2xlarge", "4xlarge",
                            "8xlarge", "12xlarge", "24xlarge", "48xlarge"]

    var instFamOpts = instanceFamily.map(function(instFam) {return '<option value="' + instFam + '">'});
    var unique_instFamOpts = [...new Set(instFamOpts)];
    var instSizeOpts = instanceTypeSize.map(function(instSize) {return '<option value="' + instSize + '">'});
    var unique_instSizeOpts = [...new Set(instSizeOpts)];

    $("#inputDesiredFamily").html(unique_instFamOpts.join(''))
    $("#inputDesiredTypeSize").html(unique_instSizeOpts.join(''))

    // allow tds to be editable by clicking the pencil icon
    $(document).on("click",".edit-cell-detail", function(){
        var td=$(this).parent("td");
        var value = td.text().trim();
        var label = td.data("label");
        if(label == "DesiredSize") {
            var input = [
                "<input class='input-data form-control instFam' list='instFamList' autocomplete='off' id='instFam' placeholder='Family' value = '" + value.split(".")[0] + "'>",
                "<datalist id='instFamList'>",
                "</datalist>",
                "<input class='input-data form-control instSize' list='instSizeList' autocomplete='off' id='instSize' placeholder='Size' value = '" + value.split(".")[1] + "'>",
                "<datalist id='instSizeList'>",
                "</datalist>",
                "<br><button type='button' class='input-data-click btn btn-warning btn-sm'>Save Changes</button>",
                "<button type='button' class='input-data-click-cancel btn btn-danger btn-sm'>Cancel</button>"
            ].join("\n");
            $(td).html(input);
            $("#instFamList").html(unique_instFamOpts.join(''))
            $("#instSizeList").html(unique_instSizeOpts.join(''))
        } else {
            var input =[
            "<input type='text' class='input-data instNotes form-control' value='"+ value +"'>",
            "<br><button type='button' class='input-data-click btn btn-warning btn-sm'>Save Changes</button>",
            "<button type='button' class='input-data-click-cancel btn btn-danger btn-sm'>Cancel</button>"
            ].join("\n");
            $(td).html(input);
        }
        $(td).removeClass("editable");
    });

    //process input field of modified td via click of button
    $(document).on("click",".input-data-click", function(e){
        var td=$(this).parent("td");
        if(td.data("label") == "DesiredSize"){
            var value = td.find('.instFam').val() + "." + td.find('.instSize').val();
        }else{
            var value = td.find('.instNotes').val()
        }
        if(value=="" || value == "."){value="N/A"}
        td.html(value);
        $(this).remove();
        td.addClass("input-spinner");

        // check in the backend the original value for comparison
        $.ajax({
            url: "/SizingDashboard/retrieveOriginalData",
            type:"POST",
            data:{'primaryKey':td.data("prikey"),'label':td.data("label")}
        })
        .done(function(response){
            if (response.data != value){
                td.addClass("editable");
                setTimeout(() => {updateInstanceDetails(td,td.data("prikey"),td.data("cxprefix"),td.data("label"),response.data,value);}, 2000);
            } else {
                td.addClass("editable");
                td.removeClass("input-spinner");
                td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
            }
        })
        .fail(function (xhr, ajaxOptions, thrownError){
            if(xhr.status==404){
                alert('Message: Error (' + xhr.status + ') ' + xhr.statusText);
            }
            else {
                msg_returned = JSON.parse(xhr.responseText)["message"];
                alert('Message: Error (' + xhr.status + ') ' + msg_returned);
            }
            td.removeClass("input-spinner");
            td.html(td.data("origval"));
            td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
        })
    });

    //cancel input field of modified td via click of button
    $(document).on("click",".input-data-click-cancel", function(e){
        var td=$(this).parent("td");
        $(this).remove();
        td.html(td.data("origval"));
        td.addClass("editable");
        td.removeClass("input-spinner");
        td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
    });

    //process input field of modified td
    $(document).on("keyup",".input-data", function(e){
        var td=$(this).parent("td");
        if(e.which == 13) { // when you press enter, process begins
            if(td.data("label") == "DesiredSize"){
                var value = td.find('.instFam').val() + "." + td.find('.instSize').val();
            }else{
                var value = td.find('.instNotes').val()
            }
            if(value=="" || value == "."){value="N/A"}
            td.html(value);
            $(this).remove();
            td.addClass("input-spinner");

            // check in the backend the original value for comparison
            $.ajax({
                url: "/SizingDashboard/retrieveOriginalData",
                type:"POST",
                data:{'primaryKey':td.data("prikey"),'label':td.data("label")}
            })
            .done(function(response){
                if (response.data != value){
                    td.addClass("editable");
                    setTimeout(() => {updateInstanceDetails(td,td.data("prikey"),td.data("cxprefix"),td.data("label"),response.data,value);}, 2000);
                } else {
                    td.addClass("editable");
                    td.removeClass("input-spinner");
                    td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
                }
            })
            .fail(function (xhr, ajaxOptions, thrownError){
                if(xhr.status==404){
                    alert('Message: Error (' + xhr.status + ') ' + xhr.statusText);
                }
                else {
                    msg_returned = JSON.parse(xhr.responseText)["message"];
                    alert('Message: Error (' + xhr.status + ') ' + msg_returned);
                }
                td.removeClass("input-spinner");
                td.html(td.data("origval"));
                td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
            })
        } else if (e.which == 27) { // while typing you press Esc, it cancels the edit.
            $(this).remove();
            td.html(td.data("origval"));
            td.addClass("editable");
            td.removeClass("input-spinner");
            td.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
        }
    });

    // send changes of tds to backend
    function updateInstanceDetails(tdCell, primary_key, cxprefix, label, oldVal, value){
        $.ajax({
            url: "/SizingDashboard/updateInstanceDetails",
            type:"POST",
            data:{'primaryKey':primary_key,'cxprefix':cxprefix,'oldValue':oldVal,'label':label,'value':value}
        })
        .done(function(response){
            console.log("Success")
            console.log(response.message);
            tdCell.removeClass("input-spinner");
            $(tdCell).attr('data-origval', value);
            tdCell.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
        })
        .fail(function (xhr, ajaxOptions, thrownError){
            if(xhr.status==404){
                alert('Message: Error (' + xhr.status + ') ' + xhr.statusText);
            }
            else {
                msg_returned = JSON.parse(xhr.responseText)["message"];
                alert('Message: Error (' + xhr.status + ') ' + msg_returned);
            }
            tdCell.removeClass("input-spinner");
            tdCell.html(oldVal);
            tdCell.append(" <a href='#' class='edit-cell-detail' style='color:#FFA500;'> <i class='mdi mdi-pencil'></i></a>")
        })
    }

    //process clicking of x to delete an instance
    $(document).on("click",".confirm-del-inst", function(e){
        var tr=$(this).closest('tr');
        var td=$(this).parent("td");
        var primary_key = td.data("prikey");
        var confirm_message = "Confirm delete on resizing record for " + primary_key.split("|")[0] + " (" +
        primary_key.split("|")[1] + "). Proceed?";
        var confirmed = confirm(confirm_message);
        if(confirmed){
            tr.addClass("input-trspinner");
            tr.find('.loading-bay').addClass("input-spinner");
            setTimeout(() => {removeInstanceEntry(tr, primary_key, td.data("cxprefix"));}, 2000);
        }
    });

    // delete instance entry send changes to backend
    function removeInstanceEntry(dtRow, primary_key, cx_prefix){
        $.ajax({
            url: "/SizingDashboard/removeInstance",
            type:"POST",
            data:{'primaryKey':primary_key,'cxprefix':cx_prefix}
        })
        .done(function(response){
            console.log("Success")
            console.log(response.message);
            dataTable.row(dtRow).remove().draw(false);
        })
        .fail(function (xhr, ajaxOptions, thrownError){
            if(xhr.status==404){
                alert('Message: Error (' + xhr.status + ') ' + xhr.statusText);
            }
            else {
                msg_returned = JSON.parse(xhr.responseText)["message"];
                alert('Message: Error (' + xhr.status + ') ' + msg_returned);
            }
            dtRow.find('.loading-bay').removeClass("input-spinner");
            dtRow.removeClass("input-trspinner");
        })
    }
});