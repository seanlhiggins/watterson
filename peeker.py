import pandas as pd
import json
import sys
import numpy as np
from looker_sdk import client, models

# csvheadername = sys.argv[1]

sdk = client.setup('looker.ini')

data = pd.read_csv("examplelookerusers.csv") 
data.head()

# Remove any rows that have nulls. A bit too intense but works fine for now.
datanonnulls = data.dropna()

# TODO: preliminary checks - 
## - Check if the users exist already, if not, create them

def create_users(email):
	existing_users = {user.name: user.id for user in sdk.all_users()}
	csv_users = (datanotnulls[email].unique())
	for email in csv_users:
		if not existing_users.get(email):
			payload = {"name": email}
			payloadjson=json.dumps(payload)
			new_user = sdk.create_user(payloadjson)
			existing_groups[new_user.name] = new_user.id
			print("Created New User " + email)
		print("User " + email + " already exists.")
## - Import the User Attributes functions. A lot of columns will be used for UAs not Groups
## - Find more efficient ways to check if the groups and users already exist that doesn't involve
##   looping through every group and comparing against the all_groups() call - DONE

## - Set what the expected Column Headers are so we don't need to explicitly set them in the script
## - Raise errors for bad formats, header names etc. Just establish a codified .csv format
## - Marry up the functions so that a user can just supply the path to a .csv and the script will take care of the rest
##

## Create the groups that are needed to add users to. 
## Check if they exist and only create the ones that don't already




def create_groups(csvheader):
	existing_groups = {group.name: group.id for group in sdk.all_groups()}
	unique_column_values = (datanonnulls[csvheader].unique())
	for group in unique_column_values:
		if not existing_groups.get(group):
			payload = {"name":group}
			payloadjson=json.dumps(payload)
			new_group = sdk.create_group(payloadjson)
			existing_groups[new_group.name] = new_group.id
			print("Created New Group " + group)


## Helper function to get the group_id for a supplied group_name.
## Output in a dictionary so it can at least reference the right name/id pair.

def get_group_id_for_group_name(group_name):
	existing_groups = {group.name: group.id for group in sdk.all_groups()}
	newdict = dict()
	
	for (k,v) in existing_groups.items():
		if k == group_name:
			newdict[k] = v
	return (newdict)

# create_groups(csvheadername)

## Main function that adds users found in the CSV to groups created by the create_groups() function
## Needs to go get all the preexisting users (later I'll make a function that checks the users exist first)
## Then with the list of Emails and Offices found in the CSV as a dict, pair them with the Groups and IDs
## in the get_group_id_for_group_name() created dictionary and add them to the group. 

def add_users_to_groups():
	users = dict()
	users_group = dict()

	for i in range(0,data.shape[0]):
		email = data['Email Address'][i]
		office = data['Office'][i]
		users[email]=office

	for k,v in users.items():
		create_users(k)
		try:
			userid = sdk.user_for_credential('email', k)
			groupnameid = get_group_id_for_group_name(v)
			users_group[userid.id] = groupnameid[v]
			payload = {"user_id": userid.id}
			payloadjson =json.dumps(payload)
			sdk.add_group_user(groupnameid[v],payloadjson)
		except:
			"Group or User Not Found"

create_groups('Office')
add_users_to_groups()

