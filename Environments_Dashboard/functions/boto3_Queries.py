import os
import json
import boto3
import requests
from botocore.exceptions import ClientError

try:
    import configparser
except:
    from backports import configparser
from boto3.dynamodb.conditions import Attr

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws\\credentials')
config.read(path)
profiles = config.sections()

#ACTION GET

def get_string_ssmps(ssm_parameter, region):
    session = boto3.Session(region_name = region)
    client = session.client('ssm')

    parameter = client.get_parameter(Name=ssm_parameter, WithDecryption=True)

    return parameter['Parameter']['Value']

def get_user_claims(access_token, region):
    session = boto3.Session(region_name = region)
    client = session.client('cognito-idp')

    response = client.get_user(
        AccessToken=access_token
        )

    return response

def listAWSInstances(alias_name, profiles, region):

    templist = []
    
    for profile in profiles:
        session = boto3.Session(region_name = region)
        client = session.resource('ec2')
        custom_filter = [{
                'Name':'tag:deployment', 
                'Values': [alias_name]}]
        instances = client.instances.filter(Filters=custom_filter)

        for instance in instances:
            if instance.tags != None:
                for tags in instance.tags:
                    if tags["Key"] == 'machineLabel':
                        instancename = tags["Value"]
            templist.append(instancename)

    return templist

def get_all_data(table_name, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data

def get_data_per_alias(table_name, alias_name, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.scan(
        FilterExpression=Attr("alias_name").eq(alias_name)
        )
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data

def get_user_settings(table_name, username, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.scan(
        FilterExpression=Attr("username").eq(username)
        )
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    return data

#ACTION CREATE/INSERT

def create_table(table_name, identifier, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': identifier,
                'KeyType': 'HASH'  # Partition key
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': identifier,
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

def insert_new_alias(table_name, alias, owner, app_env, app_version, alias_region, occupied, timeout, occupied_by, occupied_by_email, activity, remarks, occupied_date, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
       Item={
            'alias_name': alias,
            'alias_owner': owner,
            'app_env': app_env,
            'app_version': app_version,
            'alias_region': alias_region,
            'occupied': occupied,
            'timeout': timeout,
            'occupied_by': occupied_by,
            'occuipied_by_email': occupied_by_email,
            'activity': activity,
            'remarks': remarks,
            'occupied_date': occupied_date,
            'instanceList': [
            ]
        }
    )
    return response

def add_instances(table_name, alias_name, instanceName, instanceStatus, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        UpdateExpression="SET instanceList=list_append(instanceList, :vals)",
        ExpressionAttributeValues={
            ':vals': [{instanceName: instanceStatus}]
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def insert_report(table_name, date_and_time, value_ttl, user, alias, action_taken, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
       Item={
            'date_and_time': date_and_time,
            'ttl': value_ttl,
            'user': user,
            'alias_name': alias,
            'action_taken': action_taken
        }
    )
    return response

def insert_jira_key(table_name, username, jira_key, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
       Item={
            'username': username,
            'jira_api_key': jira_key
        }
    )
    return response

def insert_user(table_name, username, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
       Item={
            'username': username,
            'access_role': 'N/A',
            'jira_api_key': ''
        }
    )
    return response

#ACTION UPDATE

def update_insert_jira_key(table_name, username, jira_key, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'username': username
        },
        UpdateExpression="SET jira_api_key=:jak",
        ExpressionAttributeValues={
            ':jak': jira_key
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def check_out_alias(table_name, user_name, user_email, alias_name, jira_tickets, input_remarks, input_timeout, occupied_date, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        UpdateExpression="SET occupied=:o, occupied_by=:ob, occupied_by_email=:obe, occupied_date=:od, activity=:a, remarks=:rmk, timeout=:t",
        ExpressionAttributeValues={
            ':o': 'Yes',
            ':ob': user_name,
            ':obe': user_email,
            ':a': jira_tickets,
            ':rmk': input_remarks,
            ':t': input_timeout,
            ':od': occupied_date
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def check_in_alias(table_name, alias_name, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        UpdateExpression="SET occupied=:o, occupied_by=:ob, occupied_by_email=:obe, occupied_date=:od, activity=:a, remarks=:rmk, timeout=:t",
        ExpressionAttributeValues={
            ':o': 'No',
            ':ob': 'N/A',
            ':obe': 'N/A',
            ':a': 'N/A',
            ':rmk': 'N/A',
            ':t': 'N/A',
            ':od': 'N/A'
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def edit_alias_info(table_name, alias_name, jira_tickets, input_remarks, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        UpdateExpression="SET activity=:a, remarks=:rmk",
        ExpressionAttributeValues={
            ':a': jira_tickets,
            ':rmk': input_remarks,
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def update_alias_app_version(table_name, alias_name, app_version, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        ConditionExpression="alias_name=:alias",
        UpdateExpression="SET app_version=:app",
        ExpressionAttributeValues={
            ':app': app_version,
            ':alias': alias_name
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def update_instance_status(table_name, alias_name, instanceNum, instanceName, instanceStatus, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'alias_name': alias_name
        },
        UpdateExpression="SET instanceList[" + instanceNum + "]=:iv",
        ExpressionAttributeValues={
            ':iv': {instanceName: instanceStatus}
        },
        ReturnValues="UPDATED_NEW"
    )
    return response

def update_ttl_table(table_name, attribute_name, setting, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

        response = client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': setting,
                'AttributeName': attribute_name
            }
        )
    return response

def send_ses_email(email_recipient, subject, message, region):
    session = boto3.Session(region_name = region)
    client = session.client('ses')

    try:
        response = client.send_email(
            Destination={
                'ToAddresses': email_recipient
            },
            Message = {
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': message
                    }
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject
                }
            },
            Source = '<company_email>'
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent. Message ID: " + response['MessageId'])

#ACTION DELETE

def delete_alias(table_name, alias_name, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name = region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    try:
        response = table.delete_item(
            Key={
                'alias_name': alias_name,
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        return response

#JIRA
def add_jira_comment(jira_id, alias_name, action, jira_api_key):

    url = "https://<jira_url>/rest/api/2/issue/" + jira_id + "/comment"

    api_key = jira_api_key

    if api_key != "":
        payload = json.dumps({
            "body": action + " - *" + alias_name + "*"
             })
        headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + api_key
        }

        response = requests.request("POST", url, headers=headers, data=payload)
            
        return response.status_code
    else:
        raise Exception("JIRA Key has not been provided or it does not exist..")