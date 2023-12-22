import os
import gc
import sys
import time
import json
import atexit
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
	os.system(" pip install pyopenssl ")
	os.system(" pip install cryptocode ")
	os.system(" pip install APScheduler ")
	os.system(" pip install configparser ")
	os.system(" pip install flask-cognito-auth ")

	print("\nRequirements installed.\n")

auto_install()


try:
	import configparser
except:
	from backports import configparser
from pandas import read_csv
from functools import wraps
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler
from flask_cognito_auth import CognitoAuthManager, login_handler, logout_handler, callback_handler
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, flash, redirect, url_for, request, session, jsonify
from functions.boto3_Queries import get_string_ssmps, get_user_claims, add_jira_comment, get_all_data, get_data_per_alias, insert_new_alias, add_instances, insert_report, check_out_alias, check_in_alias, edit_alias_info, update_instance_status, send_ses_email, delete_alias, update_alias_app_version


#DynamoDB parameters used
dydb_region = '<region>'

#Global Variables
APPAliasesDBTable = '<dynamodb_tbl1>'
AppReportsDBTable = '<dynamodb_tbl2>'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
report_entry_expiry_days = get_string_ssmps("<ssm_param_key>", dydb_region)
jira_api_key = get_string_ssmps("<ssm_param_key>", dydb_region)
dashboard_api_key = get_string_ssmps("<ssm_param_key>", dydb_region)

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws\\credentials')
config.read(path)
profiles = config.sections()

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

app.config['COGNITO_REDIRECT_URI'] = get_string_ssmps("<ssm_param_key>", dydb_region) + "/dashboard/aws_cognito_redirect"
app.config['COGNITO_SIGNOUT_URI'] = get_string_ssmps("<ssm_param_key>", dydb_region) + "/dashboard"

cognito = CognitoAuthManager(app)

app.config['UPLOAD_FOLDER'] = 'uploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def checkInAliases_after_timeout():
	list_of_aliases = get_all_data(APPAliasesDBTable, dydb_region)
	if len(list_of_aliases) > 0:
		for data in list_of_aliases:
			if data["timeout"] != "N/A":
				converted_string = datetime.datetime.fromisoformat(data["timeout"])
				if datetime.datetime.now() >= converted_string:
					list_of_instances = get_data_per_alias(APPAliasesDBTable, data["alias_name"], dydb_region)

					for i in list_of_instances:
						for x, j in enumerate(i['instanceList']):
							update_instance_status(APPAliasesDBTable, data["alias_name"], str(x), ' '.join(j.keys()), 'Out', dydb_region)
					
					checkInData = check_in_alias(APPAliasesDBTable, data["alias_name"], dydb_region)

					#record action to reports DB
					number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
					value_ttl = int(time.mktime(number_of_days.timetuple()))
					insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, "SYSTEM", data["alias_name"], "Checked In (caused by timeout)", dydb_region)

					for i in list_of_instances:
						for jira_id in i["activity"]:
							add_jira_comment(jira_id, data["alias_name"], "SYSTEM: Checked In (caused by timeout)",jira_api_key)

			if data["occupied_date"] != "N/A":
				converted_string = datetime.datetime.fromisoformat(data["occupied_date"]) + datetime.timedelta(days=int("150"))
				if datetime.datetime.now() >= converted_string:
					list_of_instances = get_data_per_alias(APPAliasesDBTable, data["alias_name"], dydb_region)

					for i in list_of_instances:
						for x, j in enumerate(i['instanceList']):
							update_instance_status(APPAliasesDBTable, data["alias_name"], str(x), ' '.join(j.keys()), 'Out', dydb_region)
					
					checkInData = check_in_alias(APPAliasesDBTable, data["alias_name"], dydb_region)

					#record action to reports DB
					number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
					value_ttl = int(time.mktime(number_of_days.timetuple()))
					insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, "SYSTEM", data["alias_name"], "Checked In (caused by timeout)", dydb_region)

					for i in list_of_instances:
						for jira_id in i["activity"]:
							add_jira_comment(jira_id, data["alias_name"], "SYSTEM: Checked In (caused by timeout)",jira_api_key)


def remind_users_checkin_deps():
	list_of_aliases = get_all_data(APPAliasesDBTable, dydb_region)
	if len(list_of_aliases) > 0:
		for data in list_of_aliases:
			if data["occupied_date"] != "N/A" and data["timeout"] == "N/A":
				converted_datestr = datetime.datetime.fromisoformat(data["occupied_date"]).astimezone(tz=datetime.timezone.utc)
				email_msg = "<email_content>"
				send_ses_email([data["occupied_by_email"]], "LE Environment Dashboard Notifications (Reminder)", email_msg, dydb_region)
				
				number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
				value_ttl = int(time.mktime(number_of_days.timetuple()))
				insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, "SYSTEM", data["alias_name"], "Reminder email sent to " + data["occupied_by"], dydb_region)


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user_claims = get_user_claims(session['access_token'], "us-east-2")
            if len(user_claims['UserAttributes']) > 0:
                return f(*args, **kwargs)
            else:
                return redirect(url_for('main', _scheme='https', _external=True))
        except Exception as e:
            print(str(e), flush=True)
            return redirect(url_for('main', _scheme='https', _external=True))

    return wrap

@app.route("/dashboard/api/update/app_version", methods=['POST'])
def api_update_app_version():
	try:
		records = json.loads(request.data)
		headers = request.headers

		request_api_key = headers["X-Api-Key"]
		alias_name = records["alias_name"]
		app_version = records["alias_app_version"]

		if request_api_key == dashboard_api_key:
			updateAPPVersion = update_alias_app_version(APPAliasesDBTable, alias_name, app_version, dydb_region)
			return "APP_Version (" + app_version + ") of " + alias_name + " has been uploaded successfully to LE Environment Dashboard.", 200
		else:
			return "Incorrect credentials for accessing LE Environment Dashboard API. Please check and try again.", 403
	except Exception as e:
		print(str(e))
		if "conditional request failed" in str(e):
			return "Upload failed. The deployment does not exist in LE Environment Dashboard.", 404
		else:
			return str(e), 500

@app.route("/dashboard")
def main():
	try:
		return render_template("login.html")
	except Exception as e:
		print(str(e))

@app.route('/dashboard/aws_cognito_redirect')
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
				elif attr["Name"] == 'email':
					user_email = attr["Value"]

			full_name = given_name + " " + family_name

			session["user_email"] = user_email
			session["username"] = full_name
			session.permanent = True

			gc.collect()
			return redirect(url_for('dashboard', _scheme='https', _external=True))
		else:
			raise Exception("No user attributes was found for this user.")

	except Exception as e:
		print(str(e))
		return redirect(url_for('main', _scheme='https', _external=True))

@app.route("/dashboard/Logout")
@login_required
@logout_handler
def logout():
    time.sleep(1)
    session.clear()
    gc.collect()

# Use @login_handler decorator on cognito login route
@app.route('/dashboard/login', methods=['GET'])
@login_handler
def cognitologin():
    pass

@app.route('/dashboard/index', methods = ['GET','POST'])
@login_required
def dashboard():
	try:
		username = session.get('username')
		user_email = session.get('user_email')
		if request.method == 'POST':
			if 'action_done' in request.form:
				if request.form['action_done'] == 'CO_sel_rdbtn':
					alias_name = request.form['alias_name']
					list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)
					return jsonify({'alias_machines': list_of_instances})

			elif 'btn_submit' in request.form:
				if request.form['btn_submit'] == 'CO_btn_submit':

					if request.form['CO_rd_btns'] == 'CO_all_rdbtn':
						alias_name = request.form['co_alias_name']
						jira_tickets = request.form['alias_jira'].replace(" ", "").split(",") if request.form['alias_jira'] != "" else "N/A"
						alias_remarks = request.form['alias_remarks'] if request.form['alias_remarks'] != "" else "N/A"
						alias_co_timeout = request.form['input_timeout'] if request.form['input_timeout'] != "" else "N/A"

						if alias_co_timeout != "N/A":
							date_expiry = datetime.datetime.now() + datetime.timedelta(minutes=int(alias_co_timeout))
						else:
							date_expiry = alias_co_timeout

						checkOutData = check_out_alias(APPAliasesDBTable, username, user_email, alias_name, jira_tickets, alias_remarks, str(date_expiry), str(datetime.datetime.now()), dydb_region)
						list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)

						for i in list_of_instances:
							for x, j in enumerate(i['instanceList']):
								update_instance_status(APPAliasesDBTable, alias_name, str(x), ' '.join(j.keys()), 'In', dydb_region)
						
						#record action to reports DB
						number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
						value_ttl = int(time.mktime(number_of_days.timetuple())) 
						insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Checked Out All", dydb_region)

						for jira_id in jira_tickets:
							add_jira_comment(jira_id, alias_name, "(" + username + ") Checked Out All", jira_api_key)

						return redirect(request.referrer)
					
					elif request.form['CO_rd_btns'] == 'CO_sel_rdbtn':
						alias_name = request.form['co_alias_name']
						jira_tickets = request.form['alias_jira'].replace(" ", "").split(",") if request.form['alias_jira'] != "" else "N/A"
						alias_remarks = request.form['alias_remarks'] if request.form['alias_remarks'] != "" else "N/A"
						alias_co_timeout = request.form['input_timeout'] if request.form['input_timeout'] != "" else "N/A"
						checkboxes_of_machines = request.form['CO_chbx_machines_plhr'].split(",")

						if alias_co_timeout != "N/A":
							date_expiry = datetime.datetime.now() + datetime.timedelta(minutes=int(alias_co_timeout))
						else:
							date_expiry = alias_co_timeout


						checkOutData = check_out_alias(APPAliasesDBTable, username, user_email, alias_name, jira_tickets, alias_remarks, str(date_expiry), str(datetime.datetime.now()), dydb_region)
						list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)

						for i in list_of_instances:
							for x, j in enumerate(i['instanceList']):
								if ' '.join(j.keys()) in checkboxes_of_machines:
									update_instance_status(APPAliasesDBTable, alias_name, str(x), ' '.join(j.keys()), 'In', dydb_region)

						#record action to reports DB
						number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
						value_ttl = int(time.mktime(number_of_days.timetuple()))
						insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Selected Checked Out", dydb_region)

						for jira_id in jira_tickets:
							add_jira_comment(jira_id, alias_name, "(" + username + ") Selected Checked Out", jira_api_key)
						
						return redirect(request.referrer)

				elif request.form['btn_submit'] == 'edit_alias_dtls':
						alias_name = request.form['edit_alias_name']
						jira_tickets = request.form['edit_alias_activity'].replace(" ", "").split(",") if request.form['edit_alias_activity'] != "" else "N/A"
						alias_remarks = request.form['edit_alias_remarks'] if request.form['edit_alias_remarks'] != "" else "N/A"

						list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)

						editaliasData = edit_alias_info(APPAliasesDBTable, alias_name, jira_tickets, alias_remarks, dydb_region)

						#record action to reports DB
						number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
						value_ttl = int(time.mktime(number_of_days.timetuple()))
						insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Edited details", dydb_region)

						for i in list_of_instances:
							list_of_old_jiras = i["activity"]
						
						for old_jira_id in list_of_old_jiras:
								if old_jira_id not in jira_tickets:
									add_jira_comment(old_jira_id, alias_name, "(" + username + ") Removed from the covered activities", jira_api_key)

						for new_jira_id in jira_tickets:
							if new_jira_id not in list_of_old_jiras:
								add_jira_comment(new_jira_id, alias_name, "(" + username + ") Added to the covered activities", jira_api_key)

						return redirect(request.referrer)
				else:
					alias_name = request.form['btn_submit']
					list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)
					checkInData = check_in_alias(APPAliasesDBTable, alias_name, dydb_region)

					for i in list_of_instances:
						for x, j in enumerate(i['instanceList']):
							update_instance_status(APPAliasesDBTable, alias_name, str(x), ' '.join(j.keys()), 'Out', dydb_region)
					
					#record action to reports DB
					number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
					value_ttl = int(time.mktime(number_of_days.timetuple()))
					insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Checked In", dydb_region)

					for i in list_of_instances:
						for jira_id in i["activity"]:
							add_jira_comment(jira_id, alias_name, "(" + username + ") Checked In", jira_api_key)

					return redirect(request.referrer)

		elif request.method == 'GET':
			list_of_aliases = get_all_data(APPAliasesDBTable, dydb_region)
			return render_template("index.html", list_of_aliases = list_of_aliases, username = username)
	except Exception as e:
		flash(str(e))
		print(str(e))
		return redirect(request.referrer)

@app.route('/dashboard/listinstances', methods = ['GET','POST'])
@login_required
def List_AWSInstances_per_alias():
	try:
		username = session.get('username')
		alias_name = request.args['alias']
		if request.method == 'POST':
			list_of_chkbx_machines = request.form.getlist('machineName', type=str)
			list_of_changed_machines = []
			list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)
			for i in list_of_instances:
				for x, j in enumerate(i['instanceList']):
					if ' '.join(j.keys()) in list_of_chkbx_machines:
						if ' '.join(j.values()) != "In":
							update_instance_status(APPAliasesDBTable, alias_name, str(x), ' '.join(j.keys()), 'In', dydb_region)
							to_be_printed = ' '.join(j.keys()) + ":Occupied"
							list_of_changed_machines.append(to_be_printed)
					else:
						if ' '.join(j.values()) != "Out":
							update_instance_status(APPAliasesDBTable, alias_name, str(x), ' '.join(j.keys()), 'Out', dydb_region)
							to_be_printed = ' '.join(j.keys()) + ":Free"
							list_of_changed_machines.append(to_be_printed)

			#record action to reports DB
			number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
			value_ttl = int(time.mktime(number_of_days.timetuple()))
			insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Updated instance/s occupancy status (" + ",".join(str(x) for x in list_of_changed_machines) + ")", dydb_region)
			return redirect(request.referrer)

		if request.method == 'GET':
			list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)
			return render_template("listinstances.html", list_of_instances = list_of_instances, alias_name = alias_name, username = username)
	except Exception as e:
		flash(str(e))
		print(str(e))
		return redirect(request.referrer)

@app.route('/dashboard/includeDp', methods = ['GET','POST'])
@login_required
def include_deployment():
	try:
		username = session.get('username')
		if request.method == 'POST':
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
					failed_alias = []
					
					for data in df.to_records(index=False):
						if ( (not isinstance(data["alias_name"], float)) and (not isinstance(data["alias_region"], float)) and (not isinstance(data["alias_app"], float)) and ((not isinstance(data["alias_instances"], float)) and (data["alias_instances"] != "") and (len(data["alias_instances"].split("\n")) > 0)) ):
							insertData = insert_new_alias(APPAliasesDBTable, str(data["alias_name"]), 'N/A' if isinstance(data["alias_owner"], float) else data["alias_owner"], str(data["alias_app"]), "N/A", str(data["alias_region"]), 'No', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A', dydb_region)
							for machineLabel in data["alias_instances"].split("\n"):
								add_instances(APPAliasesDBTable, str(data["alias_name"]), str(machineLabel), 'Out', dydb_region)
					
							#record action to reports DB
							number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
							value_ttl = int(time.mktime(number_of_days.timetuple()))
							insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, str(data["alias_name"]), "Deployment included", dydb_region)
						else:
							failed_alias.append(str(data["alias_name"]))

					if len(failed_alias) > 0:
						flash("The following deployments have missing details on the CSV file and was not added successfully: (" + ", ".join(str(x) for x in failed_alias) + ")")
						print("The following deployments have missing details on the CSV file and was not added successfully: (" + ", ".join(str(x) for x in failed_alias) + ")")

					os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
				else:
					flash("You may have uploaded a csv file with incorrect details or a non-csv file. Please check again.")
			return redirect(request.referrer)
	except Exception as e:
		flash(str(e))
		print(str(e))
		return redirect(request.referrer)

@app.route('/dashboard/excludeDp', methods = ['GET','POST'])
@login_required
def exclude_deployment():
	try:
		username = session.get('username')
		if request.method == 'POST':
			alias_names = request.form['del_alias_name'].replace(" ", "").split(",")
			list_of_unknown_aliases = []
			for alias_name in alias_names:
				list_of_instances = get_data_per_alias(APPAliasesDBTable, alias_name, dydb_region)
				if (bool(list_of_instances)):
					delete_alias(APPAliasesDBTable, alias_name, dydb_region)

					#record action to reports DB
					number_of_days = datetime.datetime.now() + datetime.timedelta(days=int(report_entry_expiry_days))
					value_ttl = int(time.mktime(number_of_days.timetuple()))
					insert_report(AppReportsDBTable, str(datetime.datetime.now()), value_ttl, username, alias_name, "Deployment excluded", dydb_region)
				else:
					list_of_unknown_aliases.append(alias_name)
			
			if len(list_of_unknown_aliases) > 0:
				flash(",".join(str(x) for x in list_of_unknown_aliases) + " does not exist in the database.")
			
			return redirect(request.referrer)
	except Exception as e:
		flash(e)
		return redirect(request.referrer)

@app.route('/dashboard/reports', methods = ['GET','POST'])
@login_required
def reports():
	try:
		username = session.get('username')
		if request.method == 'POST':
			return redirect(request.referrer)
		elif request.method == 'GET':
			list_of_reports = get_all_data(AppReportsDBTable, dydb_region)
			return render_template("reports.html", list_of_reports = list_of_reports, username = username)
	except Exception as e:
		flash(str(e))
		print(str(e))
		return redirect(request.referrer)

@app.route('/dashboard/help', methods = ['GET','POST'])
@login_required
def help():
	try:
		username = session.get('username')
		if request.method == 'POST':
			return redirect(request.referrer)
		elif request.method == 'GET':
			return render_template("help.html", username = username)
	except Exception as e:
		flash(str(e))
		print(str(e))
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

		scheduler = BackgroundScheduler(timezone="Asia/Manila")
		scheduler.add_job(func=checkInAliases_after_timeout, trigger="interval", minutes=5)
		scheduler.add_job(func=remind_users_checkin_deps, trigger="cron", day_of_week="mon", hour=20)
		scheduler.start()

		# Shut down the scheduler when exiting the app
		atexit.register(lambda: scheduler.shutdown())

		app.run(host='0.0.0.0', port=80)
	except (KeyboardInterrupt):
		gc.collect()
		sys.exit(0)