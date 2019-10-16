"""
To Run:
	Unix Bash (Linux, Mac, etc.):
	$ export FLASK_APP=catering
	$ flask run
	$ flask initdb

	Windows CMD:
	> set FLASK_APP=catering
	> flask run
	> flask initdb
"""

from werkzeug import check_password_hash, generate_password_hash
from flask import Flask, request, session, url_for, redirect, flash, \
						render_template, abort, g

from datetime import datetime, date, timedelta
import os
from hashlib import md5

from models import db, User, Event

app = Flask(__name__)

##################### Config ####################
DEBUG = True
SECRET_KEY = 'development_key'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'catering.db')
SQLALCHEMY_TRACK_MODIFICATIONS = True

app.config.from_object(__name__)
app.config.from_envvar('CATERING_SETTINGS', silent=True)

db.init_app(app)


@app.cli.command('initdb')
def initdb_command():
	""" Creates the database tables """
	db.create_all()
	
	# hard-code owner account
	owner_account = User(username='owner', email='owner@gmail.com', name='Owner',
					  pw_hash = generate_password_hash('pass'), user_type = 'Owner')
	db.session.add(owner_account)
	db.session.commit()

	################################ for testing #####################################
	#cust_account = User(username='customer', email='cust@gmail.com', name='Customer One',
	#				  pw_hash = generate_password_hash('pass'), user_type = 'Customer')
	#staff_account = User(username='staff', email='staff@gmail.com', name='Staff One',
	#				  pw_hash = generate_password_hash('pass'), user_type = 'Staff')
	#event1 = Event(date = datetime.today(), name = 'Wedding', requestor = cust_account, staff1=staff_account)
	#event2 = Event(date = date(2019, 10, 30), name = 'Graduation', requestor = cust_account)
	#event3 = Event(date = date(2019, 10, 18), name = 'Birthday', requestor = cust_account)
	#event4 = Event(date = date(2019, 10, 2), name = 'Birthday', requestor = cust_account)

	#db.session.add(cust_account)
	#db.session.add(staff_account)
	#db.session.add(event1)
	#db.session.add(event2)
	#db.session.add(event3)
	#db.session.add(event4)
	#db.session.commit()
	#################################################################################


	print('Initialized the database.')

@app.before_request
def before_request():
	""" Run before each request """
	g.user = None
	if 'user_id' in session:
		g.user = User.query.filter_by(user_id=session['user_id']).first()

@app.context_processor
def inject_var():
	""" inject variables into template """
	return {'year': datetime.now().year}


##################### Functions ####################
def get_user_id(username):
	""" Look up the id for a given username """
	u = User.query.filter_by(username=username).first()
	return u.user_id if u else None

def get_event_by_date(event_date):
	""" Look up the event for a given date """
	e = Event.query.filter_by(date = event_date).first()
	return e if e else None

def convert_to_datetime(event_date):
	""" convert HTML date input to python datetime object """
	d = event_date.split('-')
	return date(int(d[0]), int(d[1]), int(d[2]))


##################### Pages ####################
@app.route('/')
def homepage():
	""" Main Page """
	if not g.user:
		return render_template('homepage.html')

	# if User is "Owner"
	if g.user.user_type == 'Owner':
		events = Event.query.filter(Event.date > date.today() - \
							timedelta(days=1)).order_by(Event.date).all()
		no_staff_warning = Event.query.filter(Event.staff1 == None, 
				Event.staff2 == None, Event.staff3 == None,
				Event.date > date.today() - timedelta(days=1)).order_by(Event.date).all()
		return render_template('owner.html', events = events, no_staff_warning = no_staff_warning)

	# if User is "Staff"
	if g.user.user_type == 'Staff':
		events = Event.query.filter(Event.date > date.today() - timedelta(days=1)).filter((Event.staff1 == g.user) | (Event.staff2 == g.user) | (Event.staff3 == g.user)).order_by(Event.date).all()
		avail_events = Event.query.filter(Event.date > date.today() - timedelta(days=1)).filter(Event.staff3 == None).filter((Event.staff1 != g.user) & (Event.staff2 != g.user) & (Event.staff3 != g.user)).order_by(Event.date).all()
		return render_template('staff.html', events = events, avail_events = avail_events)
	

	# if User is "Customer"
	if g.user.user_type == 'Customer':
		events = Event.query.filter(Event.date > date.today() - timedelta(days=1)).filter(Event.requestor == g.user).order_by(Event.date).all()
		return render_template('customer.html', events = events)

	return render_template('homepage.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
	""" Logs the user in """
	if g.user:
		return redirect(url_for('homepage'))

	error = None
	if request.method == 'POST':
		user = User.query.filter_by(username=request.form['username']).first()
		if user is None:
			error = 'Invalid username'
		elif not check_password_hash(user.pw_hash, request.form['password']):
			error = 'Invalid password'
		else:
			flash('You were logged in.')
			session['user_id'] = user.user_id
			return redirect(url_for('homepage'))
	return render_template('login.html', error = error)



@app.route('/register', methods=['GET', 'POST'])
def register():
	""" Registers users """
	curr_user = None
	if g.user:
		if g.user.user_type == 'Staff' or g.user.user_type == 'Customer':
			return redirect(url_for('homepage'))
		else:
			curr_user = 'Owner'

	error = None
	if request.method == 'POST':
		if not request.form['name']:
			error = 'You have to enter a name.'
		elif not request.form['username']:
			error = 'You have to enter a username.'
		elif not request.form['email'] or '@' not in request.form['email']:
			error = 'You have to enter a valid email address.'
		elif not request.form['password']:
			error = 'You have to enter a password.'
		elif request.form['password'] != request.form['password2']:
			error = 'The passwords do not match.'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken.'

		# every entry has a valid entry -> register the user
		else:
			if not g.user:		# new customer is signing up
				new_user_type = 'Customer'
				message = 'You were successfully registered and can login now.'
				redirect_to = 'login'
			elif g.user.user_type == 'Owner':	# if Owner is registering staff:
				new_user_type = 'Staff'
				message = 'You successfully registered a staff.'
				redirect_to = 'homepage'
			
			db.session.add(User(username = request.form['username'], 
							email = request.form['email'], name = request.form['name'], 
							pw_hash = generate_password_hash(request.form['password']), 
							user_type = new_user_type))
			db.session.commit()
			flash(message)
			return redirect(url_for(redirect_to))
	return render_template('register.html', error=error, curr_user = curr_user)


@app.route('/logout')
def logout():
	""" Logs the user out """
	flash('You were logged out.')
	session.pop('user_id', None)
	return redirect(url_for('homepage'))


@app.route('/edit/<int:id>', methods=['POST', 'GET'])
def staff_sign_up_for_event(id):
	""" Signs up the staff for the selected event """
	if g.user.user_type == 'Staff':
		event = Event.query.get(id)
		if not event.staff1:
			event.staff1 = g.user
		elif not event.staff2:
			event.staff2 = g.user
		else:
			event.staff3 = g.user
		db.session.commit()
		flash('You have signed up for %s on %s.'%(event.name, event.date))

	return redirect(url_for('homepage'))


@app.route('/request_event', methods=['POST', 'GET'])
def request_event():
	""" Customer can request a new event """
	if not g.user:
		return redirect(url_for('homepage'))

	if g.user.user_type == 'Staff' or g.user.user_type == 'Owner':
		return redirect(url_for('homepage'))

	error = None
	if request.method == 'POST':
		if not request.form['name']:
			error = 'You have to enter an event name.'
		elif get_event_by_date(request.form['date']) is not None:
			error = 'The chosen date is not available.'

		# every entry has a valid entry -> successfully request an event
		else:
			date_object = convert_to_datetime(request.form['date'])
			db.session.add(Event(name = request.form['name'], 
								date = date_object,
								requestor = g.user))
			db.session.commit()
			flash('Event %s on %s was successfully created.' %(request.form['name'], request.form['date']))
			return redirect(url_for('homepage'))
	
	return render_template('request.html', error=error, today = date.today())


@app.route('/cancel/<int:id>', methods=['POST', 'GET'])
def customer_cancel_event(id):
	""" Customer cancels the selected event """
	if g.user.user_type == 'Customer':
		event = Event.query.get(id)
		if event.requestor == g.user:
			db.session.delete(event)
			db.session.commit()
			flash('You have canceled the event %s on %s.'%(event.name, event.date))

	return redirect(url_for('homepage'))