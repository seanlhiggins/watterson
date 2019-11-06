import pandas as pd
import sys
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
i=0
while i < len(all_groups):
	print(all_groups[i].name)
	i+=1