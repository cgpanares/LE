import os
import sys
import json
import boto3
import datetime
import configparser
import pandas as pd

#Functions
def listAWSInstances(alias_name, profiles, region):

    templist = []
    
    for profile in profiles:
        try:
            session = boto3.Session(profile_name= profile, region_name = region)
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
        except Exception as e:
            print(e)

    return templist

#Get inputs
json_file = sys.argv[1]
set_column = ["alias_name", "alias_owner", "alias_region", "alias_app", "alias_instances"]

#Set Initialization
nan_value = float("NaN")
f = open(json_file)
data = json.load(f)
processedData = []
empty_alias_data = []

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws\\credentials')
config.read(path)
list_of_profiles = config.sections()

for i in data['data']:
    list_instances_from_AWS = listAWSInstances(i["alias_name"], list_of_profiles, i["alias_region"])

    if len(list_instances_from_AWS) > 0:
        processedData.append([i["alias_name"], i["alias_owner"], i["alias_region"], i["alias_app"], "\n".join(str(x) for x in list_instances_from_AWS)])
    else:
        empty_alias_data.append(i["alias_name"])

if len(processedData) > 0:
    #create DataFrame and csv
    new_df = pd.DataFrame(processedData, columns=set_column)
    new_df.to_csv("alias_data-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".csv", index=False)

    if len(empty_alias_data) > 0:
        print("Please check if you have specified the correct region for the alias: " + ", ".join(str(x) for x in empty_alias_data))

    print("CSV created successfully!")
else:
    print("The json file specified contains aliases that may not exist. Please check and try again.")

exit(1)