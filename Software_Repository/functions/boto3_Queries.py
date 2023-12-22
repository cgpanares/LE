import os
import json
import re
import string
import traceback
import boto3
import requests
from bson import json_util

json_repo_file = "repo.json"
admin_users_file = "users.json"
company_jira_url = "https://<jira_url>/"


def get_string_ssmps(ssm_parameter, region):
    session = boto3.Session(region_name=region)
    client = session.client('ssm')

    parameter = client.get_parameter(Name=ssm_parameter, WithDecryption=True)

    return parameter['Parameter']['Value']


def get_user_claims(access_token, region):
    session = boto3.Session(region_name=region)
    client = session.client('cognito-idp')

    response = client.get_user(
        AccessToken=access_token
        )

    return response


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def download_item(file_name, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    return client.generate_presigned_url('get_object',
                                         Params={'Bucket': bucket, 'Key': file_name},
                                         ExpiresIn=3600)


def get_json_file(file_name, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')

    json_file = client.get_object(Bucket=bucket, Key=file_name)
    json_output = json_file["Body"].read().decode()

    return json_output


def check_admin_list(username, bucket, region):
    try:
        list_of_admin_users = json.loads(get_json_file(admin_users_file, bucket, region))

        if username in list_of_admin_users["users"]:
            return "True"
        else:
            return "Current user does not have administrator rights."
    except Exception as e:
        print(e)

def get_file_attributes(key_name, bucket, region):
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

    try:
        if json_repo[key_name][0]:
            return json_repo[key_name][0]
        else:
            return "N/A"
    except Exception as e:
        print(e)

def list_all_files_main_admin(bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    # files
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Delimiter="/")['Contents']:
            if not item1["Key"].endswith("/"):
                for item2 in json_repo[item1["Key"]]:
                    if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                        if item1["Key"] == item2["Key"]:
                            files.append([item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                          (item2["Version"] if "Version" in item2 else "-"), sizeof_fmt(item1['Size']),
                                          item1['LastModified'],
                                          ([item2["jira_ticket"],
                                            item2[
                                                "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"), item2["DownloadCount"],item2["Hidden"], item2["ISO_approved"]])
    except Exception as e:
        print(e)

    # folders
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Delimiter="/")['CommonPrefixes']:
            not_hidden_count = 0
            for item2 in json_repo:
                if item1["Prefix"] in item2:
                    if json_repo[item2][0]["Hidden"] == "No":
                        not_hidden_count += 1
            if not_hidden_count == 0:
                folders.append([item1["Prefix"], "Yes"])
            else:
                folders.append([item1["Prefix"], "No"])
    except Exception as e:
        print(e)

    return files, folders


def list_all_files_dir_admin(prefix, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    # files
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')['Contents']:
            if not item1["Key"].endswith("/"):
                for item2 in json_repo[item1["Key"]]:
                    if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                        if item1["Key"] == item2["Key"]:
                            files.append([item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                          (item2["Version"] if "Version" in item2 else "-"), sizeof_fmt(item1['Size']),
                                          item1['LastModified'],
                                          ([item2["jira_ticket"],
                                            item2[
                                                "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"), item2["DownloadCount"],item2["Hidden"], item2["ISO_approved"]])
    except Exception as e:
        print(e)

    # folders
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')['CommonPrefixes']:
            not_hidden_count = 0
            for item2 in json_repo:
                if item1["Prefix"] in item2:
                    if json_repo[item2][0]["Hidden"] == "No":
                        not_hidden_count += 1
            if not_hidden_count == 0:
                folders.append([item1["Prefix"], "Yes"])
            else:
                folders.append([item1["Prefix"], "No"])
    except Exception as e:
        print(e)

    return files, folders


def list_all_files_search_admin(keyword, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    try:
        for item1 in client.list_objects_v2(Bucket=bucket)['Contents']:
            if keyword.lower() in item1["Key"].lower():
                if not item1["Key"].endswith("/"):
                    for item2 in json_repo[item1["Key"]]:
                        if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                            if item1["Key"] == item2["Key"]:
                                files.append([item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                              (item2["Version"] if "Version" in item2 else "-"),
                                              sizeof_fmt(item1['Size']),
                                              item1['LastModified'],
                                              ([item2["jira_ticket"],
                                                item2[
                                                    "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"), item2["DownloadCount"],item2["Hidden"], item2["ISO_approved"]])
                else:
                    not_hidden_count = 0
                    for item2 in json_repo:
                        if item1["Key"] in item2:
                            if json_repo[item2][0]["Hidden"] == "No":
                                not_hidden_count += 1
                    if not_hidden_count == 0:
                        folders.append([item1["Key"], "Yes"])
                    else:
                        folders.append([item1["Key"], "No"])
    except Exception as e:
        print(e)

    return files, folders


def list_all_files_main(bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    # files
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Delimiter="/")['Contents']:
            if not item1["Key"].endswith("/"):
                for item2 in json_repo[item1["Key"]]:
                    if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                        if item1["Key"] == item2["Key"]:
                            if item2["Hidden"] == "No":
                                if item2["ISO_approved"] == "Yes":
                                    files.append([item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                                  (item2["Version"] if "Version" in item2 else "-"), sizeof_fmt(item1['Size']),
                                                  item1['LastModified'],
                                                  ([item2["jira_ticket"],
                                                    item2[
                                                        "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"), item2["DownloadCount"]])
    except Exception as e:
        print(e)

    # folders
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Delimiter="/")['CommonPrefixes']:
            not_hidden_count = 0
            for item2 in json_repo:
                if item1["Prefix"] in item2:
                    if json_repo[item2][0]["Hidden"] == "No":
                        not_hidden_count += 1
            if not_hidden_count > 0:
                folders.append(item1["Prefix"])
    except Exception as e:
        print(e)

    return files, folders


def list_all_files_dir(prefix, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    # files
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')['Contents']:
            if not item1["Key"].endswith("/"):
                for item2 in json_repo[item1["Key"]]:
                    if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                        if item1["Key"] == item2["Key"]:
                            if item2["Hidden"] == "No":
                                if item2["ISO_approved"] == "Yes":
                                    files.append(
                                        [item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                         (item2["Version"] if "Version" in item2 else "-"), sizeof_fmt(item1['Size']),
                                         item1['LastModified'],
                                         ([item2["jira_ticket"],
                                           item2[
                                               "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"),
                                         item2["DownloadCount"]])
    except Exception as e:
        print(e)

    # folders
    try:
        for item1 in client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')['CommonPrefixes']:
            not_hidden_count = 0
            for item2 in json_repo:
                if item1["Prefix"] in item2:
                    if json_repo[item2][0]["Hidden"] == "No":
                        not_hidden_count += 1
            if not_hidden_count > 0:
                folders.append(item1["Prefix"])
    except Exception as e:
        print(e)

    return files, folders


def list_all_files_search(keyword, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
    files = []
    folders = []

    try:
        for item1 in client.list_objects_v2(Bucket=bucket)['Contents']:
            if keyword.lower() in item1["Key"].lower():
                if not item1["Key"].endswith("/"):
                    for item2 in json_repo[item1["Key"]]:
                        if item1["Key"] != json_repo_file and item1["Key"] != admin_users_file:
                            if item1["Key"] == item2["Key"]:
                                if item2["Hidden"] == "No":
                                    if item2["ISO_approved"] == "Yes":
                                        files.append(
                                            [item1['Key'], (item2["Description"] if "Description" in item2 else "-"),
                                             (item2["Version"] if "Version" in item2 else "-"),
                                             sizeof_fmt(item1['Size']),
                                             item1['LastModified'],
                                             ([item2["jira_ticket"],
                                               item2[
                                                   "jira_ticket_created"]] if "jira_ticket" and "jira_ticket_created" in item2 else "-"),
                                             item2["DownloadCount"]])
                else:
                    not_hidden_count = 0
                    for item2 in json_repo:
                        if item1["Key"] in item2:
                            if json_repo[item2][0]["Hidden"] == "No":
                                not_hidden_count += 1
                    if not_hidden_count > 0:
                        folders.append(item1["Key"])
    except Exception as e:
        print(e)

    return files, folders


def upload_file_to_s3(file_name, object_name, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    response = client.upload_file(file_name, bucket, object_name)
    return response


def create_pre_signed_upload_url_to_s3(file_key_name, content_type, url_ttl, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    pattern = r'^[' + string.punctuation + ']+'
    if re.search(pattern, file_key_name) is None:
        files, folders = list_all_files_search_admin(file_key_name, bucket, region)
        if len(files) == 0:
            response = client.generate_presigned_url('put_object', Params={'Bucket': bucket, 'Key': file_key_name, 'ContentType': content_type},
                                                 ExpiresIn=url_ttl, HttpMethod='PUT')
            return response
        else:
            raise Exception("Key name already exists. Please try again.")
    else:
        raise Exception("Invalid Key name. Please try again.")


def delete_file_s3(object_name, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    response = client.delete_object(Bucket=bucket, Key=object_name)
    return response


def delete_folder_s3(object_name, bucket, region):
    session = boto3.Session(region_name=region)
    client = session.resource('s3')
    bucket = client.Bucket(bucket)
    bucket.objects.filter(Prefix=object_name).delete()


def create_json(bucket, region):
    session = boto3.Session(region_name=region)
    client = session.client('s3')
    json_data = {}
    output_file = json_repo_file
    try:
        for item in client.list_objects_v2(Bucket=bucket)['Contents']:
            if not item["Key"].endswith("/"):
                file_details = [{"Key": item["Key"]}]
                json_data[item["Key"]] = file_details
        with open(output_file, 'w') as outfile:
            json.dump(json_data, outfile, default=json_util.default, indent=4, sort_keys=True)
        upload_file_to_s3(output_file, os.path.basename(output_file), bucket, region)
        os.remove(output_file)
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def insert_report(table_name, region, date_and_time, value_ttl, user, action_taken, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
       Item={
            'date_and_time': date_and_time,
            'ttl': value_ttl,
            'user': user,
            'action_taken': action_taken
        }
    )
    return response


def get_all_reports(table_name, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data


def compare_jira_ticket(key_name, bucket, region, jira_id):
    try:
        json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

        if "jira_ticket" in json_repo[key_name][0]:
            if jira_id == json_repo[key_name][0]["jira_ticket"]:
                return True
            else:
                return False
        else:
            return False
        
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def update_key_details(key_name, bucket, region, **kwargs):
    output_file = json_repo_file
    try:
        json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

        # changes to be made
        if "description" in kwargs:
            if kwargs["description"] == "-" or kwargs["description"] == "":
                if "Description" in json_repo[key_name][0]:
                    del json_repo[key_name][0]["Description"]
            else:
                json_repo[key_name][0]["Description"] = kwargs["description"]
        if "version" in kwargs:
            if kwargs["version"] == "-" or kwargs["version"] == "":
                if "Version" in json_repo[key_name][0]:
                    del json_repo[key_name][0]["Version"]
            else:
                json_repo[key_name][0]["Version"] = kwargs["version"]
        if "jira_ticket" in kwargs:
            if kwargs["jira_ticket"] == "-" or kwargs["jira_ticket"] == "":
                if "jira_ticket" in json_repo[key_name][0]:
                    del json_repo[key_name][0]["jira_ticket"]
                    del json_repo[key_name][0]["jira_ticket_created"]
            else:
                json_repo[key_name][0]["jira_ticket"] = kwargs["jira_ticket"]
                json_repo[key_name][0]["jira_ticket_created"] = kwargs["jira_ticket_created"]
        if "download_count" in kwargs:
            if kwargs["download_count"] == "Y":
                if "DownloadCount" in json_repo[key_name][0]:
                    current_val = int(json_repo[key_name][0]["DownloadCount"])
                    json_repo[key_name][0]["DownloadCount"] = str(current_val + 1)
                else:
                    json_repo[key_name][0]["DownloadCount"] = "0"

        with open(output_file, 'w') as outfile:
            json.dump(json_repo, outfile, default=json_util.default, indent=4, sort_keys=True)
        upload_file_to_s3(output_file, os.path.basename(output_file), bucket, region)
        os.remove(output_file)
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def update_key_attributes(list_of_hidden, list_of_ISOa, bucket, region):
    output_file = json_repo_file
    json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

    list_of_hidden_changed = {}
    list_of_isoa_changed = {}

    for hkey in list_of_hidden:
        if hkey.endswith("_false"):
            hkey_false = hkey.replace("_false", "")
            if hkey_false.endswith("/"):
                for key_name in json_repo:
                    if hkey_false in key_name:
                        if json_repo[key_name][0]["Hidden"] != "No":
                            json_repo[key_name][0]["Hidden"] = "No"
                            list_of_hidden_changed[hkey_false] = "Not Hidden"
            else:
                if json_repo[hkey_false][0]["Hidden"] != "No":
                    json_repo[hkey_false][0]["Hidden"] = "No"
                    list_of_hidden_changed[hkey_false] = "Not Hidden"

        else:
            if hkey.endswith("/"):
                for key_name in json_repo:
                    if hkey in key_name:
                        if json_repo[key_name][0]["Hidden"] != "Yes":
                            json_repo[key_name][0]["Hidden"] = "Yes"
                            list_of_hidden_changed[hkey] = "Hidden"
            else:
                if json_repo[hkey][0]["Hidden"] != "Yes":
                    json_repo[hkey][0]["Hidden"] = "Yes"
                    list_of_hidden_changed[hkey] = "Hidden"

    for ikey in list_of_ISOa:
        if ikey.endswith("_false"):
            iso_no = ikey.replace("_false", "")
            if json_repo[iso_no][0]["ISO_approved"] != "No":
                json_repo[iso_no][0]["ISO_approved"] = "No"
                list_of_isoa_changed[iso_no] = "Not ISO Approved"
        else:
            if json_repo[ikey][0]["ISO_approved"] != "Yes":
                json_repo[ikey][0]["ISO_approved"] = "Yes"
                list_of_isoa_changed[ikey] = "ISO Approved"

    with open(output_file, 'w') as outfile:
        json.dump(json_repo, outfile, default=json_util.default, indent=4, sort_keys=True)
    upload_file_to_s3(output_file, os.path.basename(json_repo_file), bucket, region)
    os.remove(output_file)

    return list_of_hidden_changed, list_of_isoa_changed


def add_new_file(key_name, bucket, region, **kwargs):
    output_file = json_repo_file
    try:
        json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

        contents = [{
            "Key": key_name,
            "Hidden": "Yes",
            "ISO_approved": "No",
            "DownloadCount": "0"
        }]

        if "description" in kwargs:
            if kwargs["description"] != "-" or kwargs["description"] != "":
                contents[0]["Description"] = kwargs["description"]
        if "version" in kwargs:
            if kwargs["version"] != "-" or kwargs["version"] != "":
                contents[0]["Version"] = kwargs["version"]

        json_repo[key_name] = contents
        print("Updating " + output_file + "...")

        with open(output_file, 'w') as outfile:
            json.dump(json_repo, outfile, default=json_util.default, indent=4, sort_keys=True)
        print("Refreshing " + output_file + " in the repository...")
        upload_file_to_s3(output_file, os.path.basename(output_file), bucket, region)
        os.remove(output_file)
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def remove_file(key_name, bucket, region):
    output_file = json_repo_file
    try:
        json_repo = json.loads(get_json_file(json_repo_file, bucket, region))

        for key in list(json_repo.keys()):
            if key_name in key:
                del json_repo[key]

        with open(output_file, 'w') as outfile:
            json.dump(json_repo, outfile, default=json_util.default, indent=4, sort_keys=True)

        if key_name.endswith("/"):
            delete_folder_s3(key_name, bucket, region)
        else:
            delete_file_s3(key_name, bucket, region)
        upload_file_to_s3(output_file, os.path.basename(output_file), bucket, region)
        os.remove(output_file)
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))
        raise(Exception(e))


# JIRA REST API CALLS
def create_jira_issue(submitter_name, file_name, file_source, remarks, action, jira_api_key):
    url = company_jira_url + "rest/api/2/issue/"
    try:
        if jira_api_key != "":
            if action == "create":
                payload = json.dumps({
                    "fields": {
                       "project":
                       {
                          "key": "TEAM"
                       },
                       "summary": "Request New File - " + file_name,
                       "description": "Submitter's Name: " + submitter_name + "\nFile Name: " + file_name + "\nSource: " + file_source + "\nRemarks: " + remarks,
                       "issuetype": {
                          "name": "Story"
                       }
                   }
                })
            elif action == "update":
                payload = json.dumps({
                    "fields": {
                        "project":
                            {
                                "key": "TEAM"
                            },
                        "summary": "Request Update - " + file_name,
                        "description": "Submitter's Name: " + submitter_name + "\nFile to be updated: " + file_name + "\nNew File (Source): " + file_source + "\nRemarks: " + remarks,
                        "issuetype": {
                            "name": "Story"
                        }
                    }
                })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + jira_api_key
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            return response.text
        else:
            raise Exception("No JIRA API key found on the user currently logged on.")
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def get_jira_ticket_status(jira_id, jira_api_key):
    url = company_jira_url + "rest/api/2/issue/"
    try:
        if jira_api_key != "":
            status_query_url = url + jira_id + "?fields=status"
            payload = {}
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + jira_api_key
            }

            response = requests.request("GET", status_query_url, headers=headers, data=payload)

            return response.text
        else:
            raise Exception("No JIRA API key found on the user currently logged on.")
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))


def resolve_jira_ticket(key_name, bucket, region, jira_api_key, **kwargs):
    url = company_jira_url + "rest/api/2/issue/"
    try:
        if jira_api_key != "":
            json_repo = json.loads(get_json_file(json_repo_file, bucket, region))
            jira_id_from_repo = json_repo[key_name][0]["jira_ticket"]
            get_status = json.loads(get_jira_ticket_status(json_repo[key_name][0]["jira_ticket"], jira_api_key))
            current_status = get_status["fields"]["status"]["name"]

            if current_status != "Resolved":
                if "custom_message" in kwargs:
                    custom_message = kwargs["custom_message"]
                else:
                    custom_message = "Ticket has been marked as *Resolved* (automated message)."

                resolve_query_url = url + jira_id_from_repo + "/transitions"
                payload = json.dumps({
                    "update": {
                        "comment": [
                            {
                                "add": {
                                    "body": custom_message
                                }
                            }
                        ]
                    },
                    "fields": {
                        "resolution": {
                            "name": "Fixed"
                        }
                    },
                    "transition": {
                        "id": "5"
                    }
                })
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + jira_api_key
                }
                response = requests.request("POST", resolve_query_url, headers=headers, data=payload)

                update_key_details(key_name, bucket, region, jira_ticket="-", jira_ticket_created="-")
                return jira_id_from_repo
            else:
                update_key_details(key_name, bucket, region, jira_ticket="-", jira_ticket_created="-")
                return jira_id_from_repo
        else:
            raise Exception("No JIRA API key found on the user currently logged on.")
    except Exception as e:
        print(e)
        print(str(traceback.format_exc()))