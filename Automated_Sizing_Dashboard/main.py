import os
import gc
import sys
import json
import time
import traceback
import logging
import datetime


def auto_install():
    print("Just installing required modules")
    print("if they do not already exist")

    os.system(" pip install boto3 ")
    os.system(" pip install flask ")
    os.system(" pip install pandas ")
    os.system(" pip install werkzeug ")
    os.system(" pip install requests ")
    os.system(" pip install flask-cognito-auth ")

    print("\nRequirements installed.\n")

auto_install()


from pandas import read_csv
from functools import wraps
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler
from flask_cognito_auth import CognitoAuthManager, login_handler, logout_handler, callback_handler
from flask import Flask, render_template, flash, url_for, redirect, request, session, jsonify
from functions.boto3_Queries import get_string_ssmps, get_user_claims, get_all_data, get_single_data, check_admin_list,\
    insert_new_instance, insert_dbrd_report, insert_resize_report, update_instance_data, remove_instance

# DynamoDB parameters used
aws_region = '<region>'

#Global Variables
BUCKET = "<bucket_name>"
TeamInstancesDB = '<dynamodb1>'
TeamInstancesReportsDB = '<dynamodb2>'
TeamInstancesResizeAttmptDB = '<dynamodb3>'
report_entry_expiry_days = "60"
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
dashboard_api_key = get_string_ssmps("<ssm_param_key>", aws_region)
TeamAWSAccounts = {"acc1": "123456789012",
                    "acc2": "098765432109"
                    }

# Initialize Flask
app = Flask(__name__)
app.secret_key = "<secret_key>"
app.permanent_session_lifetime = datetime.timedelta(minutes=60)

# Setup the flask-cognito-auth extention
app.config['COGNITO_REGION'] = '<region>'
app.config['COGNITO_USER_POOL_ID'] = '<pool_id>'
app.config['COGNITO_CLIENT_ID'] = '<client_id>'
app.config['COGNITO_CLIENT_SECRET'] = get_string_ssmps("<ssm_param_key>", aws_region)
app.config['COGNITO_DOMAIN'] = '<cognito_domain_url>'

app.config['COGNITO_REDIRECT_URI'] = get_string_ssmps("<ssm_param_key>", aws_region) + "/SizingDashboard/aws_cognito_redirect"
app.config['COGNITO_SIGNOUT_URI'] = get_string_ssmps("<ssm_param_key>", aws_region) + "/SizingDashboard"

cognito = CognitoAuthManager(app)
app.config['UPLOAD_FOLDER'] = 'uploads'


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user_claims = get_user_claims(session['access_token'], "us-east-2")
            if len(user_claims['UserAttributes']) > 0:
                try:
                    username = session.get('username')
                    check_user = check_admin_list(username, BUCKET, aws_region)
                    if check_user == "True":
                        if session.get('admin_token') is None:
                            session["admin_token"] = "<admin_token>"
                    else:
                        session.pop('admin_token', None)
                except Exception as e:
                    var = traceback.format_exc()
                    print(str(var), flush=True)
                    print(str(e), flush=True)
                    session.pop('admin_token', None)
                return f(*args, **kwargs)
            else:
                return redirect(url_for('main'))
        except Exception as e:
            var = traceback.format_exc()
            print(str(var), flush=True)
            print(str(e), flush=True)
            return redirect(url_for('main'))

    return wrap


@app.route("/SizingDashboard/api/getInstanceType", methods=['GET'])
def api_get_instance_type():
    try:
        records = request.args
        headers = request.headers

        request_api_key = headers["X-Api-Key"]
        data_primaryKey = "%s|%s|%s" % (records.get("instanceID"), records.get("machineLabel"), records.get("isProd"))

        if request_api_key == dashboard_api_key:
            get_result = get_single_data(TeamInstancesDB, data_primaryKey, aws_region)
            if int(get_result['ResponseMetadata']['HTTPStatusCode']) == 200:
                if 'Item' in get_result:
                    return jsonify({'data': "%s|%s" % (get_result['Item']["DesiredSize"]['S'], "custom")}), 200, \
                           {'ContentType': 'application/json'}
                else:
                    data_primaryKey = "%s|%s|%s" % ("i-default", records.get("machineLabel"), records.get("isProd"))
                    get_result = get_single_data(TeamInstancesDB, data_primaryKey, aws_region)
                    if int(get_result['ResponseMetadata']['HTTPStatusCode']) == 200 and 'Item' in get_result:
                        return jsonify({'data': "%s|%s" % (get_result['Item']["DesiredSize"]['S'], "default")}), 200, \
                               {'ContentType': 'application/json'}
                    else:
                        print("Failed to retrieve data (custom and default).", flush=True)
                        return jsonify({'data': "Failed to retrieve data (custom and default)."}), 400, \
                               {'ContentType': 'application/json'}
            else:
                print("Failed to retrieve data.", flush=True)
                return jsonify({'data': "Failed to retrieve data."}), 400, {'ContentType': 'application/json'}
        else:
            print("Incorrect credentials. Please check and try again.", flush=True)
            return jsonify({'data': "Incorrect credentials. Please check and try again."}), 403
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        if "conditional request failed" in str(e):
            return jsonify({'data': "Retrieve instance type failed. Instance ID not found."}), 404
        else:
            return jsonify({'data': str(e)}), 500


@app.route("/SizingDashboard/api/sendReport", methods=['POST'])
def api_send_reports():
    try:
        records = json.loads(request.data)
        headers = request.headers

        request_api_key = headers["X-Api-Key"]
        data_primaryKey = "%s|%s|%s" % (records["instanceID"], records["machineLabel"], records["isProd"])
        data_deploymentName = records["deploymentName"]
        data_awsAccount = records["awsAccount"]
        data_awsRegion = records["awsRegion"]
        data_result = records["returnedResult"]
        data_message = records["resultDetails"]
        
        try:
            if data_awsAccount.isdigit():
                data_awsAccountName = list(filter(lambda x: TeamAWSAccounts[x] == data_awsAccount, TeamAWSAccounts))[0]
            else:
                data_awsAccountName = data_awsAccount
        except Exception as e:
            data_awsAccountName = "N/A"
            var = traceback.format_exc()
            print(str(e))
            print(str(var))

        if request_api_key == dashboard_api_key:
            number_of_days = datetime.datetime.now() + datetime.timedelta(
                days=int(report_entry_expiry_days))
            value_ttl = int(time.mktime(number_of_days.timetuple()))
            insert_report = insert_resize_report(TeamInstancesResizeAttmptDB, str(datetime.datetime.now()), value_ttl,
                               data_primaryKey, data_deploymentName, data_awsAccountName, data_awsRegion, data_result,
                               data_message, aws_region)

            print(insert_report)
            if int(insert_report['ResponseMetadata']['HTTPStatusCode']) == 200:
                return jsonify({'data': "Report recorded."}), 200, {'ContentType': 'application/json'}
            else:
                return jsonify({'data': "Failed to send report."}), 400, {'ContentType': 'application/json'}
        else:
            return jsonify({'data': "Incorrect credentials. Please check and try again."}), 403
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        if "conditional request failed" in str(e):
            return jsonify({'data': "Send report failed. Please check parameters and try again."}), 404
        else:
            return jsonify({'data': str(e)}), 500


@app.route('/SizingDashboard/aws_cognito_redirect')
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
            return redirect(url_for('dashboard'))
        else:
            raise Exception("No user attributes was found for this user.")

    except Exception as e:
        print(str(e))
        return redirect(url_for('main'))


@app.route("/SizingDashboard/logout")
@login_required
@logout_handler
def logout():
    time.sleep(1)
    session.clear()
    gc.collect()


# Use @login_handler decorator on cognito login route
@app.route('/SizingDashboard/login', methods=['GET'])
@login_handler
def cognito_login():
    pass


@app.route("/SizingDashboard")
def main():
    try:
        return render_template("login.html")
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))


@app.route('/SizingDashboard/index', methods=['GET', 'POST'])
@login_required
def dashboard():
    try:
        username = session.get('username')
        if request.method == 'GET':
            list_of_instances = get_all_data(TeamInstancesDB, aws_region)
            if session.get('admin_token') is not None:
                if session["admin_token"] == "<admin_token>":
                    return render_template("index.html", list_of_instances=list_of_instances, username=username + " (Admin)")
                else:
                    return render_template("index.html", list_of_instances=list_of_instances, username=username)
            else:
                return render_template("index.html", list_of_instances=list_of_instances, username=username)
        elif request.method == 'POST':
            if 'action_done' in request.form:
                if request.form['action_done'] == 'clear_all_flashes':
                    session.pop('_flashes', None)
                    return jsonify({'alert_message': "flash messages cleared!"})
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return redirect(request.referrer)


@app.route('/SizingDashboard/retrieveOriginalData', methods=['POST'])
@login_required
def get_item_label():
    try:
        data_primaryKey = request.values.get('primaryKey')
        data_label = request.values.get('label')

        get_result = get_single_data(TeamInstancesDB, data_primaryKey, aws_region)

        if int(get_result['ResponseMetadata']['HTTPStatusCode']) == 200:
            return jsonify({'data': get_result['Item'][data_label]['S']})
        else:
            return jsonify({'message': "Failed to retrieve data."}), 400, {'ContentType': 'application/json'}
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return jsonify({'message': str(e)}), 400, {'ContentType': 'application/json'}


@app.route('/SizingDashboard/addInstance', methods=['POST'])
@login_required
def add_item():
    try:
        username = session.get('username')
        if request.form['Incldep_rdbtns'] == 'Incldep_upl_rdbtn':
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.referrer)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.referrer)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                df = read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                df_clean = df.drop_duplicates(subset=['InstanceID'])
                failed_IDs = []

                for data in df_clean.to_records(index=False):
                    if ((not isinstance(data["InstanceID"], float)) and (not isinstance(data["machineLabel"], float))
                            and (not isinstance(data["deploymentName"], float))
                            and (not isinstance(data["isProduction"], float))
                            and (not isinstance(data["DesiredFamily"], float))
                            and (not isinstance(data["DesiredSize"], float))):
                        data_primaryKey = "%s|%s|%s" % (str(data["InstanceID"]), str(data["machineLabel"]), str(data["isProduction"]))
                        data_desiredSize = "%s.%s" % (str(data["DesiredFamily"]), str(data["DesiredSize"]))
                        if data["InstanceID"] == "i-default" and session.get('admin_token') is None:
                            failed_IDs.append(str(data["InstanceID"]))
                        else:
                            insert_data = insert_new_instance(TeamInstancesDB, data_primaryKey,
                                    str(data["deploymentName"]), data_desiredSize,
                                    'N/A' if isinstance(data["Notes"], float) else data["Notes"],
                                    aws_region)

                            if int(insert_data['ResponseMetadata']['HTTPStatusCode']) == 200:
                                additional_details = "%s,%s,%s,%s" % (str(data["machineLabel"]),
                                                    str(data["deploymentName"]), str(data["isProduction"]),
                                                    data_desiredSize)
                                number_of_days = datetime.datetime.now() + datetime.timedelta(
                                    days=int(report_entry_expiry_days))
                                value_ttl = int(time.mktime(number_of_days.timetuple()))
                                insert_dbrd_report(TeamInstancesReportsDB, str(datetime.datetime.now()), value_ttl,
                                                   data_primaryKey, str(data["deploymentName"]), username, "Add Instance", additional_details,
                                                   aws_region)
                            else:
                                failed_IDs.append(str(data["InstanceID"]))
                    else:
                        failed_IDs.append(str(data["InstanceID"]))
                if len(failed_IDs) > 0:
                    flash(
                        "The following instance IDs were not added successfully:"
                        " (" + ", ".join(str(x) for x in failed_IDs) + ")")
                    print(
                        "The following instance IDs were not added successfully:"
                        " (" + ", ".join(str(x) for x in failed_IDs) + ")")

                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            else:
                flash("You may have uploaded a csv file with incorrect details or a non-csv file. Please check again.")
        elif request.form['Incldep_rdbtns'] == 'Incldep_indv_rdbtn':
            data_isProd = str(request.form['add_is_prod'])
            data_primaryKey = "%s|%s|%s" % (str(request.form['add_instance_id']), str(request.form['add_server_name']), data_isProd)
            data_depName = str(request.form['add_cust_prefix'])
            data_desiredSize = "%s.%s" % (str(request.form['add_desired_family']), str(request.form['add_desired_size']))
            data_addNotes = str(request.form['add_notes']) if str(request.form['add_notes']) != "" else "N/A"

            insert_data = insert_new_instance(TeamInstancesDB, data_primaryKey, data_depName,
                                              data_desiredSize, data_addNotes, aws_region)

            if int(insert_data['ResponseMetadata']['HTTPStatusCode']) == 200:
                additional_details = "%s,%s,%s,%s" % (data_primaryKey.split("|")[1], data_depName, data_isProd,
                                                      data_desiredSize)
                number_of_days = datetime.datetime.now() + datetime.timedelta(
                    days=int(report_entry_expiry_days))
                value_ttl = int(time.mktime(number_of_days.timetuple()))
                insert_dbrd_report(TeamInstancesReportsDB, str(datetime.datetime.now()), value_ttl, data_primaryKey, data_depName,
                                   username, "Add Instance", additional_details, aws_region)
            else:
                flash(data_primaryKey.split("|")[0] + " was not added successfully.")
                print(flash(data_primaryKey.split("|")[0] + " was not added successfully."))
        return redirect(request.referrer)
    except Exception as e:
        var = traceback.format_exc()
        flash(str(e))
        print(str(e))
        print(str(var))
        return redirect(request.referrer)


@app.route('/SizingDashboard/updateInstanceDetails', methods=['POST'])
@login_required
def update_item():
    try:
        username = session.get('username')
        data_primaryKey = request.values.get('primaryKey')
        data_cxprefix = request.values.get('cxprefix')
        data_label = request.values.get('label')
        data_oldValue = request.values.get('oldValue')
        data_value = request.values.get('value') if request.values.get('value') != "" else "N/A"

        if data_label == "DesiredSize":
            action_taken = "Changed Size"
            additional_details = data_oldValue + " to " + data_value
        elif data_label == "Notes":
            action_taken = "Edit Notes"
            additional_details = data_value
        else:
            return jsonify({'message': "Action forbidden."}), 403, {'ContentType':'application/json'}

        update_result = update_instance_data(TeamInstancesDB, data_primaryKey, data_label, data_value,
                                             aws_region)

        if int(update_result) == 200:
            number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
            value_ttl = int(time.mktime(number_of_days.timetuple()))
            insert_dbrd_report(TeamInstancesReportsDB, str(datetime.datetime.now()), value_ttl, data_primaryKey, data_cxprefix,
                               username, action_taken, additional_details, aws_region)
            return jsonify({'message': "Update successful!"})
        else:
            return jsonify({"message": "Update failed. Status code: " + str(update_result)})
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return jsonify({'message': str(e)}), 400, {'ContentType':'application/json'}


@app.route('/SizingDashboard/removeInstance', methods=['POST'])
@login_required
def delete_item():
    try:
        username = session.get('username')
        data_primaryKey = request.values.get('primaryKey')
        data_cxprefix = request.values.get('cxprefix')

        if data_primaryKey.split("|")[0] != "i-default":
            action_taken = "Remove Instance"
            additional_details = "N/A"
        else:
            return jsonify({'message': "Action forbidden."}), 403, {'ContentType':'application/json'}

        remove_result = remove_instance(TeamInstancesDB, data_primaryKey, aws_region)

        if int(remove_result) == 200:
            number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
            value_ttl = int(time.mktime(number_of_days.timetuple()))
            insert_dbrd_report(TeamInstancesReportsDB, str(datetime.datetime.now()), value_ttl, data_primaryKey, data_cxprefix, username,
                               action_taken, additional_details, aws_region)
            return jsonify({'message': "Remove successful!"})
        else:
            return jsonify({"message": "Remove failed. Status code: " + str(remove_result)})
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return jsonify({'message': str(e)}), 400, {'ContentType':'application/json'}


@app.route('/SizingDashboard/reports', methods=['GET'])
@login_required
def reports():
    try:
        username = session.get('username')
        list_of_reports = get_all_data(TeamInstancesReportsDB, aws_region)
        list_of_resize_reports = get_all_data(TeamInstancesResizeAttmptDB, aws_region)
        if session.get('admin_token') is not None:
            if session["admin_token"] == "<admin_token>":
                return render_template("reports.html", list_of_reports=list_of_reports,
                                   list_of_resize_reports=list_of_resize_reports, username=username + " (Admin)")
            else:
                return render_template("reports.html", list_of_reports=list_of_reports,
                                       list_of_resize_reports=list_of_resize_reports, username=username)
        else:
            return render_template("reports.html", list_of_reports=list_of_reports,
                                   list_of_resize_reports=list_of_resize_reports, username=username)
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return redirect(request.referrer)


@app.route('/SizingDashboard/help', methods=['GET'])
@login_required
def help_page():
    try:
        username = session.get('username')
        if session.get('admin_token') is not None:
            if session["admin_token"] == "<admin_token>":
                return render_template("help.html", username=username + " (Admin)")
            else:
                return render_template("help.html", username=username)
        else:
            return render_template("help.html", username=username)
    except Exception as e:
        var = traceback.format_exc()
        print(str(e))
        print(str(var))
        return redirect(request.referrer)


if __name__ == '__main__':
    try:
        try:
            os.mkdir("logs")
            os.mkdir("uploads")
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