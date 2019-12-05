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
from config import Config

from looker_sdk import client, models
import re
import requests
import urllib3
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager,UserMixin
from flask_login import current_user, login_user

from app import app, db
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app.secret_key = 'fjs9p4ajf@.w9(Fjfjw09'


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)
app.config.from_pyfile('config.py')


sdk = client.setup('looker.ini')

global datawithoutnulls

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.username)    

class User(db.Model):
    # ...

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class APILoginForm(FlaskForm):
    host = StringField('Host', validators=[DataRequired()])
    client_id = PasswordField('Client_ID', validators=[DataRequired()])
    client_secret = PasswordField('Client_Secret', validators=[DataRequired()])
    submit = SubmitField('Authenticate')
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

def create_users(email,data):
	data_without_nulls = data
	existing_users = {user.email: user.id for user in sdk.all_users()}
	print(f"existing users -{existing_users}")
	csv_users = (data_without_nulls[email].unique())
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
	print(extracted_numpy_row_values, len(extracted_numpy_row_values))
	i = 0
	while i< len(extracted_numpy_row_values):
		adjusted_column_values.append(group_header_name + " - " + extracted_numpy_row_values[i])
		i+=1
	print(adjusted_column_values)
	for group in adjusted_column_values:
		print(f'group - {group}')
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
	return '''<h2 Groups Created</h2> - {}'''.format([groups for groups in adjusted_column_values])

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
	data_without_nulls = data
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
	print(email_header,group_header)
	users = dict()
	users_group = dict()
	create_users(email_header,data)
	groups_created = create_groups(group_header,data)
	print(groups_created)
	user_emails = []
	for i in range(0,data_without_nulls.shape[0]):
		email = data_without_nulls[email_header][i]
		office = group_header + " - " + data_without_nulls[group_header][i]
		users[email]=office
	print(user_emails)
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
	return '''<h2>Groups Created</h2> - {}. 
	<h2>Users created</h2> - {}'''.format(groups_created, [x for x in user_emails])

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

@app.route('/login',methods=['GET','POST'])
def login():

	if current_user.is_authenticated:
		flash("already authenticated")
		return redirect(url_for('home'))
	apiform = APILoginForm()
	if apiform.validate_on_submit():
		flash("Validated")
		user = User.query.filter_by(username=apiform.host.data).first()
		if user is None or not user.check_password(apiform.password.data):
			flash('Invalid username or password')
			return redirect(url_for('home'))
		login_user(host, remember=apiform.client_id.data)
#	>>> u = User(username='susan', email='susan@example.com')
# 	>>> db.session.add(u)
# 	>>> db.session.commit()
		return redirect('/')
	else:	
		print(apiform)
	return render_template('login.html', title='Authenticate', form=apiform)


@app.route('/', methods=['GET', 'POST'])
def home():

	if request.method == 'POST':

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
	print(filename)
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
	print(sessiondata)

	# Need to find a nice way to figure out dynamically how many columns have been uploaded, but really how many rows exist in the form 
	csv_column_headers=len(data_without_nulls.columns)
	

	user_attributes_created =[]
	items_created = None
	r=re.compile("(?i).*email*")
	# emailheadername = list(filter(r.match,data.columns))[0]
	email_header_name = 'Email Address'
	html_table = data.to_html(max_rows=20)

	i=1
	while i<=csv_column_headers:
		if f'chkcreategroup{i}' in sessiondata:
		# Have to do this  formatting because the form length will be dynamic based on the CSV size, so the IDs and Names of the HTML elements will be dynamic also.
			fname = sessiondata[f'fieldname{i}']
			ftype = sessiondata[f'ftype{i}']
			uadefault = sessiondata[f'uadefault{i}']
			grp = sessiondata[f'chkcreategroup{i}']
			# ua = request.form.get("chkcreateuseratt{}".format(i))
			i+=1
			print(f"all fields - {fname}{ftype}{uadefault}" )
			# Create an object to store all the form values row-wise for concurrent handling
			row_i = FormRow(fname,ftype,uadefault,grp,'test1')


			# If they've checked the Add Users to Group checkbox and create as Group, create the groups and add users, otherwise just Create the Groups.
			if row_i.ftype == 'GRP' and row_i.grp == 'Y':
				items_created = add_users_to_groups(email_header_name,fname,data)
			elif row_i.ftype == 'GRP':
				print('creating group only')
				items_created = create_groups(fname,data)
			i+=1
		else:
			i+=1
	return render_template('process.html', 
							data=html_table, groups=items_created)



if __name__ == '__main__':
    app.run(debug=True)