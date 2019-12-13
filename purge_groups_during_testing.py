from looker_sdk import client, models
import re
import requests


sdk = client.setup('looker.ini')

#just delete all the groups that aren't the All Users and User groups
existing_groups = {group.id for group in sdk.all_groups() if group.id > 2}
print(existing_groups)
for id in existing_groups:
	sdk.delete_group(id)
existing_users = {user.id for user in sdk.all_users() if user.id > 2}
for id in existing_users:
	sdk.delete_user(id)
existing_user_attributes = {ua.id for ua in sdk.all_user_attributes() if ua.id > 13}
for id in existing_user_attributes:
	sdk.delete_user_attribute(id)