import json
import boto3
from botocore.exceptions import ClientError

admin_users_file = "users.json"


# ACTION GET
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


def get_all_data(table_name, region, dynamodb=None):
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


def get_single_data(table_name, primary_key, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.client('dynamodb')

    response = client.get_item(
        TableName=table_name,
        Key={
            'instanceIDName': {'S': primary_key}
        }
    )
    return response


# ACTION CREATE/INSERT


def update_ttl_table(table_name, attribute_name, setting, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.client('dynamodb')

        response = client.update_time_to_live(
            TableName=table_name,
            TimeToLiveSpecification={
                'Enabled': setting,
                'AttributeName': attribute_name
            }
        )
    return response


def create_table(table_name, identifier, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
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


def insert_new_instance(table_name, instanceIDName, deployment_name, desired_size, notes, region,
                        dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
        Item={
            'instanceIDName': instanceIDName,
            'DeploymentName': deployment_name,
            'DesiredSize': desired_size,
            'Notes': notes
        }
    )
    return response


def insert_dbrd_report(table_name, date_and_time, ttl, instanceIDName, deployment_name, action_by, action_taken, additional_details,
                       region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
        Item={
            'date_and_time': date_and_time,
            'ttl': ttl,
            'instanceIDName': instanceIDName,
            'DeploymentName': deployment_name,
            'ActionBy': action_by,
            'ActionTaken': action_taken,
            'AdditionalDetails': additional_details
        }
    )
    return response


def insert_resize_report(table_name, date_and_time, ttl, instanceIDName, deployment_name, aws_account, aws_region,
                         result, details, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)
    response = table.put_item(
        Item={
            'date_and_time': date_and_time,
            'ttl': ttl,
            'instanceIDName': instanceIDName,
            'DeploymentName': deployment_name,
            'awsAccount': aws_account,
            'awsRegion': aws_region,
            'Result': result,
            'Details': details
        }
    )
    return response


def update_instance_data(table_name, primary_key, label, value, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    response = table.update_item(
        Key={
            'instanceIDName': primary_key
        },
        UpdateExpression="SET " + label + "=:lbl",
        ExpressionAttributeValues={
            ':lbl': value
        },
        ReturnValues="UPDATED_NEW"
    )
    return response['ResponseMetadata']['HTTPStatusCode']


# ACTION DELETE
def remove_instance(table_name, key, region, dynamodb=None):
    if not dynamodb:
        session = boto3.Session(region_name=region)
        client = session.resource('dynamodb')

    table = client.Table(table_name)

    try:
        response = table.delete_item(
            Key={
                'instanceIDName': key,
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise
    else:
        return response['ResponseMetadata']['HTTPStatusCode']