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
	unique_column_values = (datanonnulls[csvheader].unique())
	nonexistentgroups = set(unique_column_values) - set(all_group_names)

	for group in nonexistentgroups:
		payload = {"name":group}
		payloadjson=json.dumps(payload)
		print (payloadjson)
		sdk.create_group(payloadjson)
		print("Created New Group " + group)

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

	for i in range(0,data.shape[0]):
		email = data['Email Address'][i]
		office = data['Office'][i]
		users[email]=office

	for k,v in users.items():
		users_group = newDict()
		userid = sdk.user_for_credential('Email Address', x).id
		users_group = get_group_id_for_group_name(v)
		users_group[users_group] = userid
		# add a function that gets all the group_ids for all the groups in the csv

add_users_to_groups()



