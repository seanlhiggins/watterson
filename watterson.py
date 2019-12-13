#######
###		Watterson is meant to be a very basic bulk management tool for Looker to help augment workflows for those unfamiliar with using Looker's API to do so.
###		It uses the Looker Python SDK to create Groups and Users based on a CSV file uploaded by a Looker admin.
###		There are really 3 steps; upload a CSV file, see a summary page with selection options to do different things and then a process summary of what happened.
###		
#######
import pandas as pd
import json
import sys
import numpy as np
from flask import Flask, request, render_template, send_from_directory,redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from config import *
from looker_sdk.rtl import api_settings, auth_session,transport,serialize,requests_transport
from looker_sdk import client, models, error
from looker_sdk import methods
import re
import requests
import urllib3
from werkzeug.utils import secure_filename
import os
# from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config.from_pyfile('config.py')
config_file = app.config.from_pyfile('config.py')
sdk=client.setup()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app.secret_key = 'fjs9p4ajf@.w9(Fjfjw09'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv'}




# class for each row in the UI that has a form element submitted
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

def create_users(email,data):
	data_without_nulls = data
	existing_users = {user.email: user.id for user in sdk.all_users()}
	csv_users = (data_without_nulls[email].unique())
	for email in csv_users:
		if not existing_users.get(email,):
			payload = {"name": email}
			payloadjson=json.dumps(payload)
			new_user = sdk.create_user(payloadjson)
			credentialspayload = {"email":email}
			new_credentials = sdk.create_user_credentials_email(new_user.id,credentialspayload)
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



def create_groups(group_header_name, data):
	data_without_nulls = data
	existing_groups = {group.name: group.id for group in sdk.all_groups()}
	raw_column_values = (data_without_nulls[group_header_name].unique())
	extracted_numpy_row_values = [row for row in raw_column_values]
	adjusted_column_values = []

	i = 0
	while i< len(extracted_numpy_row_values):
		adjusted_column_values.append(group_header_name + " - " + extracted_numpy_row_values[i])
		i+=1

	for group in adjusted_column_values:
		if not existing_groups.get(group):
			try:
				payload = {"name": group}
				payloadjson=json.dumps(payload)
				new_group = sdk.create_group(payloadjson)
				existing_groups[new_group.name] = new_group.id
				print("Created New Group " + group)
			except:
				print("Failed to create " + group)
		else:
			print("Group " + group + " already exists")
	return [groups for groups in adjusted_column_values]

def update_group_name(groupheadername, data):
	datanonnulls = data
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

def add_users_to_groups(email_header, group_header,data):
	data_without_nulls = data

	users = dict()
	users_group = dict()
	create_users(email_header,data)
	groups_created = create_groups(group_header,data)

	user_emails = []
	for i in range(0,data_without_nulls.shape[0]):
		email = data_without_nulls[email_header][i]
		office = group_header + " - " + data_without_nulls[group_header][i]
		users[email]=office

	for k,v in users.items():
		try:
			user_emails.append(k)
			userid = sdk.user_for_credential('email', k)

			groupnameid = get_group_id_for_group_name(v)
			users_group[userid.id] = groupnameid[v]
			payload = {"user_id": userid.id}
			payloadjson =json.dumps(payload)
			sdk.add_group_user(groupnameid[v],payloadjson)
			print("Added user " + k + " to Group " + v)
		except:
			"Group or User Not Found"
	return groups_created, user_emails


##### USER ATTRIBUTE FUNCTIONS
def create_user_attribute(ua_name, default_value, data, uatype='string'):
	data_without_nulls = data
	existing_ua = {ua.name: ua.id for ua in sdk.all_user_attributes()}

	if not existing_ua.get(ua_name):
		print(f'{existing_ua}')
		print(f'uavalue = {ua_name}, default = {default_value}')
		try:
			payload = {"name": ua_name,"default_value":"","label":ua_name,"type":"string"}
			print(f'{payload}')
			payloadjson=json.dumps(payload)
			print(f'{payloadjson}')
			# new_ua = sdk.create_user_attribute(payloadjson)
			# new_ua = sdk.create_user_attribute({"name": "oneuatobindthem","default_value":"",	"label":"This Is Newest","type":"string"})
			# new_ua = sdk.create_user_attribute({"name": "twouatobindthem","default_value":"","label":"This Is Newerer","type":"string"})
			# new_ua = sdk.create_user_attribute({"name": "Team", 		  "default_value":"",	"label":"Team", 		  "type":"string"})
			print(new_ua)
			print("Created New User Attribute " + ua_name)
			return ua_name, default_value
		except:
			print("Failed to create " + ua_name)
		
	else:
		print("User Attribute " + ua_name + " already exists")



##### ROUTES {

@app.route('/', methods=['GET', 'POST'])
def home():

	if request.method == 'POST':
		base_url = os.environ['LOOKERSDK_BASE_URL'] = request.form['host']
		os.environ['LOOKERSDK_CLIENT_ID'] = request.form['clientid']
		os.environ['LOOKERSDK_CLIENT_SECRET'] = request.form['clientsecret']
		sdk = client.setup()

		#just check the SDK is initiated
		me = sdk.me()
		print(me)
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit an empty part without filename
		if file.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			
			return redirect(url_for('process',
										filename=filename))
	return render_template('upload.html')

@app.route('/upload/<filename>', methods=['GET', 'POST'])
def process(filename):
	data = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'],filename))
	# Get all the column names. Later we'll use these to create an array in the UI with checkboxes for each - DONE
	csv_column_headers = [col for col in data.columns]
	html_table = data.to_html(max_rows=20)
	# Get just the email address header name so we can just quickly use it for creating users - DONE
	r=re.compile("(?i).*email*")

	emailheadername = list(filter(r.match,data.columns))[0]

	if request.method == 'POST':
		
			session['formdata'] = request.form
			return redirect(url_for('uploaded_file', filename=filename))
	return render_template('uploaded_file.html', table=html_table,columns=csv_column_headers)


@app.route('/process/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
	data_from_file = None
	f = open(os.path.join(app.config['UPLOAD_FOLDER'],filename))
	dataraw = f.read()
	data = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'],filename))

	data_without_nulls = data.dropna()
	# Get everything a user sends in the form
	sessiondata=(session['formdata'])

	# Need to find a nice way to figure out dynamically how many columns have been uploaded, but really how many rows exist in the form 
	csv_column_headers=len(data_without_nulls.columns)
	

	user_attributes_created =[]
	items_created = None
	r=re.compile("(?i).*email*")
	# emailheadername = list(filter(r.match,data.columns))[0]
	email_header_name = 'Email Address'
	html_table = data.to_html(max_rows=20)
	print(sessiondata)
	i=1
	while i<=csv_column_headers:
		print(f'checkcreategroup{i} + chkcreateua{i}')
		if f'chkcreategroup{i}' in sessiondata:
			print(f'chkcreategroup{i}')
		# Have to do this  formatting because the form length will be dynamic based on the CSV size, so the IDs and Names of the HTML elements will be dynamic also.
			fname = sessiondata[f'fieldname{i}']
			ftype = sessiondata[f'ftype{i}']
			uadefault = sessiondata[f'uadefault{i}']
			grp = sessiondata[f'chkcreategroup{i}']
			ua = None

			# Create an object to store all the form values row-wise for concurrent handling
			row_i = FormRow(fname,ftype,uadefault,grp,ua)


			# If they've checked the Add Users to Group checkbox and create as Group, create the groups and add users, otherwise just Create the Groups.
			if row_i.grp =='Y' and not row_i.ftype:
				alert('Choose the data type')

			elif row_i.ftype == 'GRP' and row_i.grp == 'Y':
				print('creating groups and adding users to groups')
				items_created = add_users_to_groups(email_header_name,fname,data)
				return render_template('process.html', 
								data=html_table, groups=items_created[0], users=items_created[1])

			elif row_i.ftype == 'GRP':
				print('creating group only')
				items_created = create_groups(fname,data)
				return render_template('process.html', 
							data=html_table, groups=items_created[0])
		
		elif sessiondata[f'ftype{i}'] == 'UA':
			print('got here')
			fname = sessiondata[f'fieldname{i}']
			ftype = sessiondata[f'ftype{i}']
			uadefault = sessiondata[f'uadefault{i}']
			grp = None
			if f'chkcreateua{i}' in sessiondata:
				ua = sessiondata[f'chkcreateua{i}']
			else:
				ua = ''
			row_i = FormRow(fname,ftype,uadefault,grp,ua)

			if row_i.ua == 'Y':
				print('creating user attributes')
				# items_created = add_user_attribute_to_users(email_header_name,fname,data) -- function to be created still

			else:
				print('creating new user attribute')
				items_created = create_user_attribute(fname,uadefault, data, uatype='string')
				print(items_created)
			i+=1
		else:
			print(sessiondata[f'ftype{i}'])
			i+=1
	return render_template('process.html', ua=items_created)


#### END ROUTES }


if __name__ == '__main__':
    app.run(debug=True)