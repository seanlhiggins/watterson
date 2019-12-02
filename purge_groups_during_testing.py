from looker_sdk import client, models
import re
import requests


sdk = client.setup('looker.ini')

#just delete all the groups that aren't the All Users and User groups
existing_groups = {group.id for group in sdk.all_groups() if group.id > 2}
print(existing_groups)
for id in existing_groups:
	sdk.delete_group(id)
