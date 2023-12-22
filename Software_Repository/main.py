import json
import os
import gc
import sys
import logging
import time
import traceback
import datetime
import tempfile              


def auto_install():
    print("Just installing required modules")
    print("if they do not already exist")

    os.system(" pip install boto3 ")
    os.system(" pip install flask==2.3.3 ")
    os.system(" pip install pymongo ")
    os.system(" pip install requests ")
    os.system(" pip install flask-cognito-auth ")

    print("\nRequirements installed.\n")


auto_install()

from functools import wraps
# from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler
from flask_cognito_auth import CognitoAuthManager, login_handler, logout_handler, callback_handler
from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify, Markup, send_file
from functions.boto3_Queries import list_all_files_main_admin, list_all_files_dir_admin, list_all_files_search_admin, \
    list_all_files_main, list_all_files_dir, list_all_files_search, download_item, \
    create_jira_issue, update_key_details, get_file_attributes, get_string_ssmps, get_user_claims, compare_jira_ticket, remove_file, \
    resolve_jira_ticket, add_new_file, create_pre_signed_upload_url_to_s3, insert_report, get_all_reports, \
    update_key_attributes, check_admin_list

#global variables
BUCKET = "<s3_bucket_name>"
aws_region = "<region>"
S3RepoReportsDBTable = "<dynamodb_report_name>"
report_entry_expiry_days = "90"
json_repo_file = "repo.json"
jira_api_key = get_string_ssmps("<ssm_param_key>", aws_region)
dashboard_api_key = get_string_ssmps("<ssm_param_key>", aws_region)

#Initialize Flask
app = Flask(__name__)
app.secret_key = "<secret_key>"
app.permanent_session_lifetime = datetime.timedelta(minutes=60)

# Setup the flask-cognito-auth extention
app.config['COGNITO_REGION'] = '<region>'
app.config['COGNITO_USER_POOL_ID'] = '<pool_id>'
app.config['COGNITO_CLIENT_ID'] = '<client_id>'
app.config['COGNITO_CLIENT_SECRET'] = get_string_ssmps("<ssm_param_key>", aws_region)
app.config['COGNITO_DOMAIN'] = '<cognito_domain_url>'

app.config['COGNITO_REDIRECT_URI'] = get_string_ssmps("<ssm_param_key>", aws_region) + "/repo/aws_cognito_redirect"
app.config['COGNITO_SIGNOUT_URI'] =  get_string_ssmps("<ssm_param_key>", aws_region) + "/repo"

cognito = CognitoAuthManager(app)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user_claims = get_user_claims(session['access_token'], "us-east-2")
            if len(user_claims['UserAttributes']) > 0:
                return f(*args, **kwargs)
            else:
                return redirect(url_for('buffer', _scheme='https', _external=True))
        except Exception as e:
            print(str(e), flush=True)
            return redirect(url_for('buffer', _scheme='https', _external=True))

    return wrap


def admin_login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_token' in session and session['admin_token'] == "<admin_token>":
            return f(*args, **kwargs)
        else:
            return redirect(url_for('main', _scheme='https', _external=True))

    return wrap


@app.route("/repo/api/getFileInfo", methods=['GET'])
def get_file_info_api():
    try:
        records = request.args
        headers = request.headers

        request_api_key = headers["x-api-key"]
        data_filePath = records.get("Path")

        if request_api_key == dashboard_api_key:
            output = get_file_attributes(data_filePath, BUCKET, aws_region)
            return jsonify({'data': output}), 200
        else:
            print("Incorrect credentials. Please check and try again.", flush=True)
            return jsonify({'data': "Incorrect credentials. Please check and try again."}), 403
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return jsonify({'data': str(e)}), 500


@app.route("/repo/api/download", methods=['GET'])
def download_file_api():
    try:
        records = request.args
        headers = request.headers
        
        request_api_key = headers["x-api-key"]
        data_filePath = records.get("Path")

        if request_api_key == dashboard_api_key:
            output = download_item(data_filePath, BUCKET, aws_region)
            return jsonify({'data': output}), 200
        else:
            print("Incorrect credentials. Please check and try again.", flush=True)
            return jsonify({'data': "Incorrect credentials. Please check and try again."}), 403
    except Exception as e:
        var = traceback.format_exc()
        print(str(var))
        print(str(e))
        return jsonify({'data': str(e)}), 500


@app.route('/repo/aws_cognito_redirect')
@callback_handler
def callback():
    try:
        access_token = session["access_token"]
        user_claims = get_user_claims(access_token, "us-east-2")

        if len(user_claims['UserAttributes']) > 0:
            for attr in user_claims['UserAttributes']:
                if attr["Name"] == 'given_name':
                    given_name = attr["Value"]
                elif attr["Name"] == 'family_name':
                    family_name = attr["Value"]

            full_name = given_name + " " + family_name

            session["username"] = full_name
            session.permanent = True

            gc.collect()
            return redirect(url_for('main', _scheme='https', _external=True))
        else:
            gc.collect()
            print("User not found in the list of allowed users.")
            return redirect(url_for('buffer', _scheme='https', _external=True))

    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(url_for('main', _scheme='https', _external=True))


@app.route("/repo/logout")
@login_required
@logout_handler
def logout():
    time.sleep(1)
    session.clear()
    gc.collect()


@app.route("/repo/adminLogout")
@admin_login_required
@login_required
def admin_logout():
    time.sleep(1)
    session.pop('admin_token', None)
    gc.collect()
    return redirect(url_for('main', _scheme='https', _external=True))


@app.route("/repo")
def buffer():
    try:
        return render_template("login.html")
    except Exception as e:
        print(str(e))


# Use @login_handler decorator on cognito login route
@app.route('/repo/login', methods=['GET'])
@login_handler
def cognitologin():
    pass


@app.route("/repo/adminLogin")
@login_required
def buffer_admin():
    try:
        username = session.get('username')
        check_user = check_admin_list(username, BUCKET, aws_region)
        if check_user == "True":
            session["admin_token"] = "@dM1n z3Sz!0n"
            return redirect(url_for('main_admin', _scheme='https', _external=True))
        else:
            flash(str(check_user))
            return redirect(url_for('main', _scheme='https', _external=True))
    except Exception as e:
        print(str(e))


@app.route('/repo/sign_s3', methods=['GET', 'POST'])
@login_required
def sign_s3():
    if request.method == 'POST':
        try:
            new_file_keyname = request.form["new_file_name"]
            pre_signed_url = create_pre_signed_upload_url_to_s3(new_file_keyname,'multipart/form-data', 3600, BUCKET, aws_region)
            return jsonify({"pre_signed_url": pre_signed_url})
        except Exception as e:
            print(str(e))
            print(str(traceback.format_exc()))
            return jsonify({"data": str(e.args[0])})


@app.route("/repo/admin", methods=['GET', 'POST'])
@admin_login_required
@login_required
def main_admin():
    try:
        username = session.get('username')
        if request.method == 'GET':
            files, folders = list_all_files_main_admin(BUCKET, aws_region)
            go_back = "hidden"
            return render_template('index.html', files=files, folders=folders, go_back=go_back, username=username)
        elif request.method == 'POST':
            if 'btn_submit' in request.form:
                # Edit Details
                if request.form['btn_submit'] == 'modify_file_btn':
                    existing_key_name = request.form["existing_key_name"]
                    existing_key_desc = request.form["modify_file_desc"] if not request.form['modify_file_desc'].isspace() else "-"
                    existing_key_version = request.form["modify_file_version"] if not request.form['modify_file_version'].isspace() else "-"
                    existing_key_jiraid = request.form["modify_jira_ticket"] if not request.form['modify_jira_ticket'].isspace() else "-"

                    if compare_jira_ticket(existing_key_name, BUCKET, aws_region, existing_key_jiraid):
                        update_key_details(existing_key_name, BUCKET, aws_region, description=existing_key_desc,
                                           version=existing_key_version)

                        # record action to reports DB
                        timestamp = datetime.datetime.utcnow()
                        number_of_days = timestamp + datetime.timedelta(days=int(report_entry_expiry_days))
                        value_ttl = int(time.mktime(number_of_days.timetuple()))
                        action_taken = "Edit Details: " + existing_key_name

                        insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                                      value_ttl, username, action_taken)
                    else:
                        timestamp = datetime.datetime.utcnow()
                        update_key_details(existing_key_name, BUCKET, aws_region, description=existing_key_desc,
                                           version=existing_key_version, jira_ticket=existing_key_jiraid, jira_ticket_created=str(timestamp))

                        # record action to reports DB
                        number_of_days = timestamp + datetime.timedelta(
                            days=int(report_entry_expiry_days))
                        value_ttl = int(time.mktime(number_of_days.timetuple()))
                        action_taken = "Edit Details: " + existing_key_name

                        insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                                      value_ttl, username, action_taken)
                    return redirect(request.referrer)
                # Update the repo and add the newly uploaded file
                elif request.form['btn_submit'] == 'new_upl_file_btn':
                    try:
                        new_file_keyname = request.form["new_file_name"]
                        new_file_desc = request.form["new_file_desc"] if request.form[
                                                                             'new_file_desc'] != "" else "-"
                        new_file_version = request.form["new_file_version"] if request.form[
                                                                                   'new_file_version'] != "" else "-"
                        if new_file_keyname:
                            add_new_file(new_file_keyname, BUCKET,
                                         aws_region, description=new_file_desc,
                                         version=new_file_version)
                            msg = new_file_keyname.split("/")[-1] + " has been successfully uploaded!"

                            # record action to reports DB
                            timestamp = datetime.datetime.utcnow()
                            number_of_days = timestamp + datetime.timedelta(
                                days=int(report_entry_expiry_days))
                            value_ttl = int(time.mktime(number_of_days.timetuple()))
                            action_taken = "Add New File: " + new_file_keyname

                            insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                                          value_ttl, username, action_taken)
                        else:
                            msg = "Failed to update the repo file. Please try again."
                        return jsonify({'alert_message': msg})
                    except Exception as e:
                        print(str(e))
                        print(str(traceback.format_exc()))
                        return jsonify({'alert_message': e})
                elif request.form['btn_submit'] == 'checkbox_save_changes':
                    try:
                        list_of_chkbx_hidden = request.form.getlist('HiddenKeyName', type=str)
                        list_of_chkbx_ISOA = request.form.getlist('ISOKeyName', type=str)

                        hidden_result, iso_result = update_key_attributes(list_of_chkbx_hidden, list_of_chkbx_ISOA, BUCKET, aws_region)

                        # record action to reports DB

                        if hidden_result:
                            timestamp = datetime.datetime.utcnow()
                            number_of_days = timestamp + datetime.timedelta(
                                days=int(report_entry_expiry_days))
                            value_ttl = int(time.mktime(number_of_days.timetuple()))
                            action_taken = "Edited Hidden Attributes: " + json.dumps(hidden_result)
                            insert_report(S3RepoReportsDBTable, aws_region, str(timestamp), value_ttl,
                                          username, str(action_taken))

                        if iso_result:
                            timestamp = datetime.datetime.utcnow()
                            number_of_days = timestamp + datetime.timedelta(
                                days=int(report_entry_expiry_days))
                            value_ttl = int(time.mktime(number_of_days.timetuple()))
                            action_taken = "Edited ISO Attributes: " + json.dumps(iso_result)
                            insert_report(S3RepoReportsDBTable, aws_region, str(timestamp), value_ttl,
                                          username, str(action_taken))

                        output = "Successfully updated the attributes of the files and folders affected!"
                        return jsonify(message=output)
                    except Exception as e:
                        print(str(e))
                        print(str(traceback.format_exc()))
                        return jsonify(message=str(e))

            # Resolved JIRA ticket
            elif 'btn_submit_jira' in request.form:
                jira_key_name = request.form['btn_submit_jira']
                jira_id = resolve_jira_ticket(jira_key_name, BUCKET, aws_region, jira_api_key)
                message_to_flash = "Successfully marked the ticket " + jira_id + " as resolved."
                flash(Markup(message_to_flash))

                # record action to reports DB
                timestamp = datetime.datetime.utcnow()
                number_of_days = timestamp + datetime.timedelta(
                    days=int(report_entry_expiry_days))
                value_ttl = int(time.mktime(number_of_days.timetuple()))
                action_taken = "Resolve Ticket: " + jira_key_name

                insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                              value_ttl, username, action_taken)
                return redirect(request.referrer)
            # Delete file from repo and json
            elif 'btn_submit_del' in request.form:
                del_key_name = request.form['btn_submit_del']
                remove_file(del_key_name, BUCKET, aws_region)
                if del_key_name.endswith("/"):
                    message_to_flash = "Successfully deleted the folder <strong>" + del_key_name.rsplit('/', 1)[0].split("/")[
                        -1] + "</strong> from the repository."
                else:
                    message_to_flash = "Successfully deleted <strong>" + del_key_name.split("/")[-1] + "</strong> from the repository."
                flash(Markup(message_to_flash))

                # record action to reports DB
                timestamp = datetime.datetime.utcnow()
                number_of_days = timestamp + datetime.timedelta(
                    days=int(report_entry_expiry_days))
                value_ttl = int(time.mktime(number_of_days.timetuple()))
                action_taken = "Delete File: " + del_key_name

                insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                              value_ttl, username, action_taken)
                return redirect(request.referrer)
            elif 'btn_submit_create_url' in request.form:
                download_key_name = request.form['btn_submit_create_url']
                output = download_item(download_key_name, BUCKET, aws_region)

                # record action to reports DB
                timestamp = datetime.datetime.utcnow()
                number_of_days = timestamp + datetime.timedelta(
                    days=int(report_entry_expiry_days))
                value_ttl = int(time.mktime(number_of_days.timetuple()))
                action_taken = "Generated Pre-signed Download URL: " + download_key_name
                
                message_to_store = """LE Software Repository

File name: """ + download_key_name + """
Link Expiration: 1 hour
URL: """ + output

                tmp = tempfile.TemporaryFile()
                tmp.write(bytes(message_to_store, encoding='utf-8'))
                tmp.seek(0)

                text_file_name = download_key_name + "_pre-signed-URL_" + str(
                    timestamp.replace(microsecond=0).isoformat(' ')) + ".txt"
                    
                update_key_details(download_key_name, BUCKET, aws_region, download_count="Y")
                insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                              value_ttl, username, action_taken)
                return send_file(tmp, download_name=text_file_name, as_attachment=True)

    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/adminSearch", methods=['GET', 'POST'])
@admin_login_required
@login_required
def search_key_admin():
    try:
        username = session.get('username')
        if request.method == 'GET':
            keyword = request.args.get('searchKey')
            files, folders = list_all_files_search_admin(keyword, BUCKET, aws_region)
            return render_template('index.html', files=files, folders=folders, username=username)
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/reports", methods=['GET', 'POST'])
@admin_login_required
@login_required
def reports():
    try:
        username = session.get('username')
        if request.method == 'GET':
            list_of_reports = get_all_reports(S3RepoReportsDBTable, aws_region)
            return render_template('reports.html', list_of_reports=list_of_reports, username=username)
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/admin", strict_slashes=False)
@app.route("/repo/admin/<path:path>", methods=['GET'])
@admin_login_required
@login_required
def inside_dir_admin(path=None):
    if request.method == 'GET':
        try:
            username = session.get('username')
            files, folders = list_all_files_dir_admin(path, BUCKET, aws_region)
            return render_template('index.html', files=files, folders=folders, username=username)
        except Exception as e:
            print(str(e))
            print(str(traceback.format_exc()))
            return redirect(request.referrer)


@app.route("/repo/index", methods=['GET', 'POST'])
@login_required
def main():
    try:
        files, folders = list_all_files_main(BUCKET, aws_region)
        go_back = "hidden"
        return render_template('index.html', files=files, folders=folders, go_back=go_back)
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/search", methods=['GET', 'POST'])
@login_required
def search_key():
    try:
        if request.method == 'GET':
            keyword = request.args.get('searchKey')
            files, folders = list_all_files_search(keyword, BUCKET, aws_region)
            return render_template('index.html', files=files, folders=folders)
        elif request.method == 'POST':
            if 'action_done' in request.form:
                if request.form['action_done'] == 'clear_all_flashes':
                    session.pop('_flashes', None)
                    return jsonify({'alert_message': "flash messages cleared!"})
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/index", strict_slashes=False)
@app.route("/repo/index/<path:path>", methods=['GET'])
@login_required
def inside_dir(path=None):
    if request.method == 'GET':
        try:
            files, folders = list_all_files_dir(path, BUCKET, aws_region)
            return render_template('index.html', files=files, folders=folders)
        except Exception as e:
            print(str(e))
            print(str(traceback.format_exc()))
            return redirect(request.referrer)


@app.route("/repo/download", strict_slashes=False)
@app.route("/repo/download/<path:path>", methods=['GET'])
@login_required
def download_files(path=None):
    if request.method == 'GET':
        output = download_item(path, BUCKET, aws_region)
        update_key_details(path, BUCKET, aws_region, download_count="Y")
        return redirect(output)


@app.route("/repo/requestFile", methods=['GET', 'POST'])
@login_required
def request_new_file():
    try:
        if request.method == 'POST':
            if 'btn_submit' in request.form:
                if request.form['btn_submit'] == 'new_file_sub_btn':
                    new_subm_name = request.form["new_subm_name"]
                    new_file_name = request.form["new_file_name"]
                    new_file_source = request.form["new_file_source"] if request.form['new_file_source'] != "" else "N/A"
                    new_file_remarks = request.form["new_file_remarks"] if request.form['new_file_remarks'] != "" else "N/A"
                    action = "create"

                    create_jira = create_jira_issue(new_subm_name, new_file_name, new_file_source, new_file_remarks, action, jira_api_key)
                    jira_to_json = json.loads(create_jira)
                    message_to_flash = "<a href = 'https://<jira_url>/browse/" + jira_to_json["key"] + "' target = '_blank'>" + jira_to_json["key"] + "</a> has been successfully created!"
                    flash(Markup(message_to_flash))

                    # record action to reports DB
                    timestamp = datetime.datetime.utcnow()
                    number_of_days = timestamp + datetime.timedelta(
                        days=int(report_entry_expiry_days))
                    value_ttl = int(time.mktime(number_of_days.timetuple()))
                    action_taken = "Request New File: " + new_file_name + " and " + jira_to_json["key"] + " has been created."

                    insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                                  value_ttl, new_subm_name + "(Submitter)", action_taken)
                    return redirect(request.referrer)

    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


@app.route("/repo/updateFile", methods=['GET', 'POST'])
@login_required
def request_update_file():
    try:
        if request.method == 'POST':
            if 'btn_submit' in request.form:
                if request.form['btn_submit'] == 'upd_file_sub_btn':
                    new_subm_name = request.form["new_subm_name"]
                    update_key_name = request.form["update_key_name"]
                    update_file_remarks = request.form["update_file_remarks"] if request.form['update_file_remarks'] != "" else "N/A"
                    action = "update"

                    create_jira = create_jira_issue(new_subm_name, update_key_name, "", update_file_remarks, action, jira_api_key)
                    jira_to_json = json.loads(create_jira)
                    message_to_flash = "<a href = 'https://<jira_url>/browse/" + jira_to_json["key"] + "' target = '_blank'>" + jira_to_json["key"] + "</a> has been successfully created!"

                    timestamp = datetime.datetime.utcnow()
                    update_key_details(update_key_name, BUCKET, aws_region, jira_ticket=jira_to_json["key"], jira_ticket_created=str(timestamp))
                    flash(Markup(message_to_flash))

                    # record action to reports DB
                    number_of_days = timestamp + datetime.timedelta(
                        days=int(report_entry_expiry_days))
                    value_ttl = int(time.mktime(number_of_days.timetuple()))
                    action_taken = "Request Update: " + update_key_name + " and " + jira_to_json["key"] + " has been created."

                    insert_report(S3RepoReportsDBTable, aws_region, str(timestamp),
                                  value_ttl, new_subm_name + "(Submitter)", action_taken)
                    return redirect(request.referrer)
    except Exception as e:
        print(str(e))
        print(str(traceback.format_exc()))
        return redirect(request.referrer)


if __name__ == '__main__':
    try:
        try:
            os.mkdir("logs")
        except OSError:
            list_of_files = os.listdir('logs')
            full_path = ["logs/{0}".format(x) for x in list_of_files]
            if len(list_of_files) == 10:
                oldest_file = min(full_path, key=os.path.getctime)
                os.remove(oldest_file)

        log = logging.getLogger('')
        handler = RotatingFileHandler('logs/access.log', maxBytes=10240000, backupCount=5)
        stream = logging.StreamHandler(sys.stdout)
        log.addHandler(stream)
        log.addHandler(handler)

        app.run(host='0.0.0.0', port=80)
    except KeyboardInterrupt:
        gc.collect()
        sys.exit(0)