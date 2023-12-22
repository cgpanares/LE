$(document).ready(function() {

    // to check if flashes have content so that the modal cannot be closed other than the button.
    if ($("#flashes *").length > 0){
        $("#modalId").modal({backdrop: 'static', keyboard: false});
    }

    // unhides the Save Changes button if there would be changes to be detected in the checkboxes.
    $("input[id^='status_chkbox']").change(function() {
        $('#checkbox_save_changes').removeAttr('hidden');
    });

    // detects changes on the checkboxes of the files if it is going to be ISO approved or not.
    $("input[id^='status_chkbox_iso']").change(function() {
        var isChecked= $(this).is(':checked');
        var name = "#" + $(this).attr('id') + "_1";
        if(!isChecked){
            $(name).prop('checked', true);
       } else {
            $(name).prop('checked', false);
       }
    });

    // detects changes on the checkboxes of the files if it is going to be hidden or not.
    $("input[id^='status_chkbox_file_hidden']").change(function() {
        var isChecked= $(this).is(':checked');
        var name = "#" + $(this).attr('id') + "_1";
        if(!isChecked){
            $(name).prop('checked', true);
       } else {
            $(name).prop('checked', false);
       }
    });

    // detects changes on the checkboxes of the folders if it is going to be hidden or not.
    $("input[id^='status_chkbox_folder_hidden']").change(function() {
        var isChecked= $(this).is(':checked');
        var name = "#" + $(this).attr('id') + "_1";
        if(!isChecked){
            $(name).prop('checked', true);
       } else {
            $(name).prop('checked', false);
       }
    });

    // disables the element recent-purchases-listing_length to prevent from being submitted as data as this is not needed.
    // This element's purpose is for the DataTable to have pagination.
    $("form").submit(function() {
       $('[name=recent-purchases-listing_length]').attr('disabled','disabled');
    });

    // removes values provided in the elements found in a modal when closed/did not make a submission.
    $(".modal").on("hidden.bs.modal", function(){
         $(this).find("input[type=text],textarea").val('').end();
     });

    $(".modal").on("hidden.bs.modal", function(){
         $(this)
         .find("input[type=text],input[type=file],textarea,select")
            .val('')
            .end()
         .find("input[type=checkbox], input[type=radio]")
            .prop("checked", "")
            .end();
     });


    // converts timestamps in the application to a readable format and based on the timezone of the user's browser.
    $("[id]").each(function(){
        if($(this).attr("id")=="jira_timestamp"){
        var get_str_report_time = $(this).text();
        var converted_report_time = new Date(get_str_report_time + 'Z');

        $(this).text("(" + converted_report_time.toLocaleDateString() + " " + converted_report_time.toLocaleTimeString() + ")").css({ 'font-weight': 'bold' });
        }
        else if($(this).attr("id")=="file_last_modified"){
        var get_str_report_time = $(this).text();
        var converted_report_time = new Date(get_str_report_time + 'Z');

        $(this).text(converted_report_time.toLocaleDateString() + " " + converted_report_time.toLocaleTimeString());
        }

        else if($(this).attr("id")=="report_datetime"){
        var get_str_report_time = $(this).text();
        var converted_report_time = new Date(get_str_report_time + 'Z');

        $(this).text(converted_report_time.toLocaleString("sv-SE") + " (" + converted_report_time.toLocaleTimeString('en-US',{timeZoneName:'short'}).split(' ')[2] + ")").css({ 'font-weight': 'bold' });
        }

    });

    // ajax submission for the checkboxes that have been changed. Triggered by clicking the Save Changes button.
    $('#checkbox_save_changes').on("click", function(e){
        var confirmed = confirm("Are you sure you want to save changes on the checkboxes?");
        if (confirmed) {
            var table = $('#recent-purchases-listing').DataTable();
            var checkbox_data = table.$('input[type="checkbox"]').serializeArray();
            checkbox_data.push({name: $('#checkbox_save_changes').attr("name"), value: $('#checkbox_save_changes').val()});

            $("#checkbox_save_changes").html("Please wait...");

            $.ajax({
              url: '/repo/admin',
              type: 'POST',
              data: checkbox_data,
              success: function(data){
                alert(data.message);
                location.reload();
              },
              error: function (request, status, error) {
                alert("Failed to process data. Please try again.");
                location.reload();
              }
            });
        }
    });

    // ajax submission which runs when the Upload New File has been invoked. (In the Admin Page)
    $('#form_modal_upl').submit(function(e){
        if($('#upld_new_file').val()){
            e.preventDefault();

            var formData = new FormData(this);
            formData.append($('#btn_submit_upl_file').attr("name"), $('#btn_submit_upl_file').val());
            var upld_file = $('#upld_new_file').get()[0].files[0];

            // global variable for storing the pre-signed url after generating it.
            var presigned_s3_ajax;
            var upload_file_ajax;
            var update_repo_ajax;
            var pre_signed_url_data = "";

            var progress_bar_html = [
                '<div class="text-center">',
                '<p class = "text-center" id = "upload_message"></p>',
                '</div>',
                '<div class="progress">',
                '<div class="progress-bar progress-bar-striped bg-success" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">0%</div>',
                '</div>'
            ].join('\n');

            // Change the content of the modal for uploading new file to a progress bar.
            $('#upload_content').html(progress_bar_html);
            $('#btn_submit_upl_file').hide();
            $('#upload_small_close_button').hide();
            $('#btn_close_upl_window').hide();
            $('#btn_cancel_upl_window').removeAttr('hidden');

            // disabling the capability of the user to close the modal via clicking on other part of the page or by keyboard.
            $("#newUplFile").data('bs.modal')._config.backdrop = 'static';
            $("#newUplFile").data('bs.modal')._config.keyboard = 'false';

            $('#upload_message').text("Creating Pre-Signed URL...");

            // function for creating the pre-signed s3 url for uploading files.
            async function presigned_s3_url_ajax(){
                 presigned_s3_ajax = $.ajax({
                    type: "POST",
                    url: "/repo/sign_s3",
                    data: formData,
                    processData: false,
                    contentType: false,
                    error:function(resp) {
                        var returnedData = resp.data;
                        return returnedData
                    }
                });
                return presigned_s3_ajax
            }

            // function for uploading the file to the pre-signed s3 url.
            function upload_file_to_s3_ajax() {
                upload_file_ajax = $.ajax({
                    xhr: function() {
                        var xhr = new window.XMLHttpRequest();
                        xhr.upload.addEventListener("progress", function(evt) {
                            if (evt.lengthComputable) {
                                var percentComplete = Math.round((evt.loaded / evt.total) * 100) + 10;
                                if(percentComplete <= 100) {
                                    $('.progress-bar').attr('aria-valuenow', percentComplete).css('width', percentComplete + '%').text(percentComplete + '%');
                                }
                                if (percentComplete >= 100){
                                    $('#upload_message').text("Upload done. Please wait...");
                                }
                            }
                        }, false);
                        return xhr;
                    },
                    type: 'PUT',
                    url:pre_signed_url_data.pre_signed_url,
                    processData: false,
                    contentType: 'multipart/form-data',
                    data: upld_file,
                    error:function(resp) {
                        $('#upload_message').text(pre_signed_url_data.data);
                        $('#btn_close_upl_window').attr('onclick', 'window.location.reload();');
                        $('#btn_close_upl_window').show();
                        $('#btn_cancel_upl_window').hide();
                    }
                });
                return upload_file_ajax;
            }

            // to update the repo.json file in the s3 repo.
            function update_s3_repo_json_ajax() {
                update_repo_ajax = $.ajax({
                    type: "POST",
                    url: "/repo/admin",
                    data: formData,
                    processData: false,
                    contentType: false,
                    error:function (data) {
                        var returnedData = data.alert_message;
                        $('#upload_message').text(returnedData);
                        $('#btn_close_upl_window').attr('onclick', 'window.location.reload();');
                        $('#btn_close_upl_window').show();
                        $('#btn_cancel_upl_window').hide();
                    },
                    success:function(data){
                        var returnedData = data.alert_message;
                        $('#upload_message').text(returnedData);
                        $('#btn_close_upl_window').attr('onclick', 'window.location.reload();');
                        $('#btn_close_upl_window').show();
                    },
                    resetForm: true
                });
            }

           var upload_process = $.when(presigned_s3_url_ajax()).done(function(resp){
                $('.progress-bar').attr('aria-valuenow', 10).css('width', 10 + '%').text(10 + '%');
                $('#upload_message').text("Uploading file to S3...");
                var data_resp = resp;
                pre_signed_url_data = data_resp;

                $.when(upload_file_to_s3_ajax()).done(function(file,response){
                    console.log("response=>",response);
                    update_s3_repo_json_ajax()
                    $('.progress-bar').attr('aria-valuenow', 100).css('width', 100 + '%').text(100 + '%');
                    $('#btn_cancel_upl_window').hide();
                });
            });

           $(document).on('click','#btn_cancel_upl_window', function(e){
                if(presigned_s3_ajax){presigned_s3_ajax.abort();}
                if(upload_file_ajax){upload_file_ajax.abort();}
                if(update_repo_ajax){update_repo_ajax.abort();}
                console.log("Cancelled");
           });
        }
        return false;
    });

});

// includes the keyname of the selected file for update request in one of the form submission elements.
$(document).on("click", ".open-UpdateFileDialog", function () {
     var key_name = $(this).data('keyname');
     $("#data_key_name").val(key_name);
});

// gets the current value of the elements and place them in their corresponding entities in the modal for modification.
$(document).on("click", ".open-EditFileDialog", function () {
     var key_name = $(this).data('keyname');
     var key_description = $(this).data('description');
     var key_version = $(this).data('version');
     var key_jiraid = $(this).data('jiraid');
     $("#dataedit_key_name").val(key_name);
     $("#dataedit_file_desc").val(key_description);
     $("#dataedit_file_version").val(key_version);
     $("#dataedit_jira_ticket").val(key_jiraid);
     var file_name = key_name.split("/");
     $("#edit_detail_title").text("Edit details of " + file_name[file_name.length - 1]);
});

// function that allows the user to go back from the previous page.
function goBack() {
  window.history.back();
}

// clears flash messages in the server-side once the pop-up has been closed via ajax submission.
$(document).on("click", ".flash-clear", function () {
     $.ajax({
        type: "POST",
        url: "/repo/search",
        data: {
            action_done: "clear_all_flashes"
        },
        contentType: 'application/x-www-form-urlencoded; charset=UTF-8'
     }).done(function(data) {
                    var returnedData = data.alert_message;
                    console.log(returnedData);
               });
});

// For enabling data-confirm in some buttons that require confirmation before doing the action.
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