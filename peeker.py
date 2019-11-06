import pandas as pd
import json
import sys
import numpy as np

csvheadername = sys.argv[1]

from looker_sdk import client, models

sdk = client.setup('looker.ini')

data = pd.read_csv("examplelookerusers.csv") 
data.head()

#Testing appending names and offices together
# mailgroup = {}
# for i in range(0,data.shape[0]):
#     print(data['Name'][i],data['Office'][i])

all_groups = sdk.all_groups()
all_group_names = []
i=0
while i < len(all_groups):
	all_group_names.append(all_groups[i].name)
	i+=1

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

create_groups(csvheadername)
