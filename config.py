import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	# ...
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
		'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = True
	# LOOKERSDK_BASE_URL = 'https://localhost:19999'
	# LOOKERSDK_CLIENT_SECRET = '6rDd29dWCzSHXvyz4zNHSQpB'
	# LOOKERSDK_CLIENT_ID = 'JbFHRZPNcP6Ftm4wKHdT'
	# LOOKERSDK_VERIFY_SSL= False

DEBUG = True # Turns on debugging features in Flask
BCRYPT_LOG_ROUNDS = 12 # Configuration for the Flask-Bcrypt extension
MAIL_FROM_EMAIL = "shiggins@looker.com" # For use in application emails
