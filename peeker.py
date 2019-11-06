import pandas as pd
import json
import sys
import itertools

sys.path.insert(1, '../looker_sdk')

from looker_sdk import client, models

sdk = client.setup('looker.ini')

data = pd.read_csv("examplelookerusers.csv") 
data.head()
# Preview the first 5 lines of the loaded data 

mailgroup = {}
for i in range(0,data.shape[0]):
    print(data['Name'][i],data['Office'][i])

all_groups = sdk.all_groups()
all_group_names = []
i=0
while i < len(all_groups):
	all_group_names.append(all_groups[i].name)
	i+=1



uniquemarkets = (data['Market'].unique())
for market in uniquemarkets:
	payload = {"name":market}
	payloadjson=json.dumps(payload)
	sdk.create_group(payloadjson)

