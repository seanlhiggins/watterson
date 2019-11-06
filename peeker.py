import pandas as pd
import json
import sys
import numpy as np
from looker_sdk import client, models

# csvheadername = sys.argv[1]

sdk = client.setup('looker.ini')

data = pd.read_csv("examplelookerusers.csv") 
data.head()

#Testing appending names and offices together
# mailgroup = {}
# for i in range(0,data.shape[0]):
#     print(data['Name'][i],data['Office'][i])


datanonnulls = data.dropna()

def create_groups(csvheader):
	all_groups = sdk.all_groups()
	all_group_names = []
	i=0
	while i < len(all_groups):
		all_group_names.append(all_groups[i].name)
		i+=1
	unique_column_values = (datanonnulls[csvheader].unique())
	nonexistentgroups = []
	for office in unique_column_values:
		if office not in all_group_names:
			nonexistentgroups.append(office)
	print (nonexistentgroups)
	for group in nonexistentgroups:
		payload = {"name":group}
		payloadjson=json.dumps(payload)
		print (payloadjson)
		try:
			sdk.create_group(payloadjson)
			print("Created New Group " + group)
		except:
			print(group + "Already Exists")

def get_group_id_for_group_name(group_name):
	all_group_names_and_ids = {}
	all_groups = sdk.all_groups()
	i=0
	
	while i < len(all_groups):
		all_group_names_and_ids[all_groups[i].name] = all_groups[i].id
		i+=1
	newdict = dict()
	
	for (k,v) in all_group_names_and_ids.items():
		if k == group_name:
			newdict[k] = v
	return (newdict)

# create_groups(csvheadername)

def add_users_to_groups():
	users = {}
	users_group = dict()
	
	for i in range(0,data.shape[0]):
		email = data['Email Address'][i]
		office = data['Office'][i]
		users[email]=office

	for k,v in users.items():
		try:
			userid = sdk.user_for_credential('email', k)
			groupnameid = get_group_id_for_group_name(v)
			users_group[userid.id] = groupnameid[v]
			payload = {"user_id": userid.id}
			payloadjson =json.dumps(payload)
			sdk.add_group_user(groupnameid[v],payloadjson)
		except:
			"Group or User Not Found"

		# add a function that gets all the group_ids for all the groups in the csv
create_groups('Office')
add_users_to_groups()

