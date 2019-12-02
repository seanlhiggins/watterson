import pandas as pd
import json
import sys
import numpy as np
from flask import Flask, request, render_template, send_from_directory,redirect, url_for
from looker_sdk import client, models
import re
import requests
import urllib3
from werkzeug.utils import secure_filename
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object('config')
app.config.from_pyfile('config.py')


sdk = client.setup('looker.ini')

global datawithoutnulls

# This object is for linking all the form elements into a row-wise, linked reference so they can be handled concurrently later
class FormRow():

    def __init__(self, fname, ftype, uadefault, grp, ua):
        """Constructor"""
        self.fname = fname
        self.ftype = ftype
        self.uadefault = uadefault
        self.grp = grp
        self.ua = ua

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# TODO: preliminary checks - 
## - Check if the users exist already, if not, create them - DONE

def create_users(email):
	global datawithoutnulls
	existing_users = {user.email: user.id for user in sdk.all_users()}
	print(f"existing users -{existing_users}")
	csv_users = (datawithoutnulls[email].unique())
	for email in csv_users:
		print(f"email - {email}")
		if not existing_users.get(email,):
			print(f"nonexistingemail {existing_users.get(email)}")
			payload = {"name": email}
			print(f"payload - {payload}")
			payloadjson=json.dumps(payload)
			new_user = sdk.create_user(payloadjson)
			credentialspayload = {"email":email}
			print(f"creds - {credentialspayload}")
			print(f"newuser - {new_user}")
			new_credentials = sdk.create_user_credentials_email(new_user['id'],credentialspayload)
			existing_users[new_user.email] = new_user.id
			print("Created New User " + email)
		else :
			print("User " + email + " already exists.")
	return csv_users

## - Import the User Attributes functions. A lot of columns will be used for UAs not Groups

## - Find more efficient ways to check if the groups and users already exist that doesn't involve
##   looping through every group and comparing against the all_groups() call 

## - Set what the expected Column Headers are so we don't need to explicitly set them in the script - PARTIALLY DONE (see column headers at top)

## - Raise errors for bad formats, header names etc. Just establish a codified .csv format
## - Marry up the functions so that a user can just supply the path to a .csv and the script will take care of the rest
## - Nice to have would be if you wanted to rename a Group. It could be helpful to have regex for the column headers so if there's collision
# we prompt a rename of the existing group instead of a new one.

## Create the groups that are needed to add users to.  
## Check if they exist and only create the ones that don't already. 
## We'll use the column header as a prefix for that group e.g. "Market - France, Market - Germany, Office - Berlin, Office - Paris"



def create_groups(groupheadername):
	global datawithoutnulls
	existing_groups = {group.name: group.id for group in sdk.all_groups()}
	raw_column_values = (datawithoutnulls[groupheadername].unique())
	adjusted_column_values = []
	for row in raw_column_values:
		adjusted_column_values.append(groupheadername + " - " + row)

	for group in adjusted_column_values:
		if not existing_groups.get(group):
			try:
				payload = {"name":groupheadername + " - " + group}
				payloadjson=json.dumps(payload)
				new_group = sdk.create_group(payloadjson)
				existing_groups[new_group.name] = new_group.id
				print("Created New Group " + group)
			except:
				print("Failed to create " + group)
		else:
			print("Group " + group + " already exists")
	return adjusted_column_values

def update_group_name(groupheadername):
	unique_column_values = (datanonnulls[groupheadername].unique())
	for group in unique_column_values:
		lookergroup = get_group_id_for_group_name(group)
		for k,v in lookergroup.items():
			try:
				newgroupname = groupheadername + " - " + k 
				payload = {"name": newgroupname}
				payloadjson =json.dumps(payload)
				update_group = sdk.update_group(v, payloadjson)
				print("Updated " + k + " to " + newgroupname)
			except:
				print("Failed to update" + k)

## Helper function to get the group_id for a supplied group_name.
## Output in a dictionary so it can at least reference the right name/id pair.

def get_group_id_for_group_name(group_name):
	global datawithoutnulls
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

def add_users_to_groups(emailheader, groupheader):
	global datawithoutnulls
	users = dict()
	users_group = dict()
	create_users(emailheader)
	groups_created = create_groups(groupheader)
	useremails = []
	for i in range(0,datawithoutnulls.shape[0]):
		email = datawithoutnulls[emailheader][i]
		office = groupheader + " - " + datawithoutnulls[groupheader][i]
		users[email]=office

	for k,v in users.items():
		try:
			useremails.append(k)
			userid = sdk.user_for_credential('email', k)
			groupnameid = get_group_id_for_group_name(v)
			users_group[userid.id] = groupnameid[v]
			payload = {"user_id": userid.id}
			payloadjson =json.dumps(payload)
			sdk.add_group_user(groupnameid[v],payloadjson)
			print("Added user " + k + " to Group " + v)
		except:
			"Group or User Not Found"
	return "Groups Created - {}. Users created - {}".format(groups_created, [x for x in useremails])




@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
	if request.method == 'POST':

		# First read a static CSV. Later we'll have a UI that will have a user provide a CSV 
		file = request.files.get('file')
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return redirect(url_for('process',
                                    filename=filename))
		data = pd.read_csv(request.files.get('file'))

		# Get all the column names. Later we'll use these to create an array in the UI with checkboxes for each - DONE
		csvcolumnheaders = []
		for col in data.columns:
			csvcolumnheaders.append(col)

		# Get just the email address header name so we can just quickly use it for creating users - DONE
		r=re.compile("(?i).*email*")
		emailheadername = list(filter(r.match,data.columns))[0]


		# Remove any rows that have nulls. A bit too intense but works fine for now.
		global datawithoutnulls
		datawithoutnulls = data.dropna()
		html = datawithoutnulls.to_html(max_rows=20,border=10)
		return render_template('upload.html', shape=datawithoutnulls.shape, columns=csvcolumnheaders, table=html)
	return render_template('upload.html')

@app.route('/process/<filename>', methods=['GET', 'POST'])
def process(filename):
	global datawithoutnulls

	data = pd.read_csv('{}/{}'.format(app.config['UPLOAD_FOLDER'],filename))


	# Get everything a user sends in the form

	formelements = []
	formelements.append(request.form.items())

	# Need to find a nice way to figure out dynamically how many columns have been uploaded, but really how many rows exist in the form - DONE with a global variable. Yuck.

	csvcolumnheaders=8
	# len(datawithoutnulls.columns)
	
	# With everything the user's given us, tie all the form rows together in objects so they can be handled discretely e.g. if not checked do X, if checked do Y etc.
	listofentries = []
	groups_created = []
	users_created = []
	user_attributes_created =[]
	usergroupscreated = None
	r=re.compile("(?i).*email*")
	emailheadername = list(filter(r.match,data.columns))[0]

	emailheadername='email'
	for element in formelements:
		i=0
		while i<=csvcolumnheaders:

			# Have to do this weird formatting because the form length will be dynamic based on the CSV size, so the IDs and Names of the HTML elements will be dynamic also.
			fname = request.form.get("fieldname{}".format(i))
			ftype = request.form.get("ftype{}".format(i))
			uadefault = request.form.get("uadefault{}".format(i))
			grp = request.form.get("chkcreategroup{}".format(i))
			ua = request.form.get("chkcreateuseratt{}".format(i))
			i+=1

			row_i = FormRow(fname,ftype,uadefault,grp,ua)
			listofentries.append(row_i)	

			# If they've checked the Add Users to Group checkbox, create the groups and add users, otherwise just Create the Groups.
			if row_i.grp == 'Y':
				usergroupscreated = add_users_to_groups(emailheadername,fname)
				# groups_created.append(create_groups(fname))
				# users_created.append(create_users(emailheadername))



	return render_template('process.html', groups=usergroupscreated)
	# return send_from_directory(app.config['UPLOAD_FOLDER'],
                               # filename)

if __name__ == '__main__':
    app.run(debug=True)