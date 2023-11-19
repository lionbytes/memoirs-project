import datetime
import uuid #Useful for password restoration links
from flask import Flask, g, request, render_template, redirect, url_for, flash, abort

from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from flask_bcrypt import check_password_hash, generate_password_hash
from flask_mail import Mail, Message

import models
import forms


app = Flask(__name__)
app.secret_key = 'Kajp5dp5#lA!px36A_!56a36sdAojko2iqnkm9_#^!62i'

app.config.update(
	#Email Settings
	#DEBUG=True,
	#MAIL_DEBUG = True,
	MAIL_SERVER='smtp.mailserver.com',
	MAIL_PORT=465, #587
	MAIL_USE_SSL=True,
	#MAIL_USE_TLS=True,
	MAIL_USERNAME='your@mailserver.com',
	MAIL_PASSWORD='#pa55w0rd'
	)

mail = Mail(app)

DEBUG = True
PORT = 8000
HOST = '0.0.0.0'

# For bad URL requests out-ruling purposes
allowed_uri = ['index', 'login', 'register', 'logout', 'memo', 'view_memo', 'edit', 'settings']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "warning"

@login_manager.user_loader
def load_user(userid):
	try: 
		return models.User.get(models.User.id==userid)
	except models.DoesNotExist:
		return None

@app.before_request
def before_request():
	g.db = models.DATABASE
	g.db.connect()
	g.user = current_user

@app.after_request
def after_request(response):
	g.db.close()
	return response


@app.route('/register', methods=['GET', 'POST'])
def register():
	if not current_user.is_anonymous:
		return redirect(url_for('index'))

	form = forms.RegisterForm()
	if form.validate_on_submit():
		models.User.create_user(
			username=form.username.data, 
			email=form.email.data, 
			password=form.password.data,
			password_str=form.password.data
			)
		try:
			new_user = models.User.get( models.User.username == form.username.data)
		except models.DoesNotExist:
			flash("User does not exist", "danger")
		else:
			flash("Welcome {}!".format(new_user.username), "success")
			login_user(new_user)
			#create_demomemo()
			return redirect(url_for('index'))
	return render_template('register.html', form=form)


def create_demomemo():
	'''Creates a dummy memo for demonstration purposes'''
	create_memo(
		title = "Demo Memo",
		content = "Feel free to elaborate on how your day went in this area. This memo was created for demonstration purposes only, you may delete it if you wish to do so.",
		user = g.user.id,
		money_made = "1000",
		food_string = "Bread, Water, Milk, Brown Rice, Red Meat, Broccoli",
		activ_string = "Work, Language Study, Gym, Eat at Restaurant, Meet Best Friend, Call Family, Shower"
		)

@app.route('/login', methods=['GET', 'POST'])
def login():
	error_in_login = False
	if not current_user.is_anonymous:
		return redirect(url_for('index'))
	else:
		form = forms.LoginForm()
		if form.validate_on_submit():
			try:
				user = models.User.get(models.User.username == form.username.data)
			except models.DoesNotExist:
				error_in_login = True
				flash("Username and password do not match!", "danger")
			else:
				if check_password_hash(user.password, form.password.data):
					login_user(user)
					flash("Welcome {}!".format(user.username), "success")
					return redirect(url_for('index'))
				else:
					error_in_login = True
					flash("Username and password do not match!", "danger")
		return render_template('login.html', form=form, error_in_login=error_in_login)


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


def getmemo_byid(memo_id):
	try:
		memo = models.Memo.select().where(models.Memo.id==memo_id).get()
	except models.DoesNotExist:
		abort(404)
	else:
		return memo


def filter_items(items_string, passed_model, memo):
	item_list = [item.strip().lstrip().capitalize() for item in items_string.split(',') if item.strip().lstrip() != ""]
	newly_created = []
	old_counter = 0
	for item_name in item_list:
		try:
			newly_created.append( passed_model.create(name=item_name) )
		except models.IntegrityError:
			old_counter+=1

	return item_list


def record_items(item_list, modelitems, passed_model, memo):
	''' Takes a list of strings, two models, and the many-to-many model that connects them both.
		Cleans list of strings. Records in database.'''
	
	# Clean list from removed old items
	deleted_records = 0
	for item in [item.item_name for item in modelitems.select().where(modelitems.memo==memo)]:
		if item not in item_list:
			try: 
				deleted_records += modelitems.get(modelitems.item_name==item, memo=memo).delete_instance()
			except models.DoesNotExist:
				flash("Could not delete! Record does not exist.", "danger")

	# Create new item bonds
	created_records = 0
	for item in item_list:
		try:
			item_name = passed_model.get(passed_model.name**item)
			modelitems.create(memo=memo.id, item_name=item_name)
		except models.IntegrityError:
			flash("Data duplication ignored.", "success")
			flash("Data duplication with memo \"{}\" detected: {}.".format(memo.title, item), "warning")
		except ValueError:
			flash("Error submitting {} into memo \"{}\".".format(item, memo.title), "danger")
		else:
			created_records+=1


@app.route('/record', methods=['GET', 'POST'])
@login_required
def record(memo_id=None):
	if models.Memo.select().where( 
		models.Memo.user == current_user.id, 
		models.Memo.timestamp.day == datetime.date.today().day 
	).exists():
		flash("Today's memo has already been recorded.", "warning")
		return redirect(url_for('index'))
	else:
		form = forms.MemoForm()
		if form.validate_on_submit():
			create_memo(
					user = g.user.id, 
					title = form.title.data,
					money_made = form.money_made.data,
					content = form.content.data,
					food_string = form.foods.data,
					activ_string = form.activities.data
					)
			return redirect(url_for('index'))
		return render_template('record.html', form=form)


def create_memo(user, title, content, money_made, food_string, activ_string):
	with g.db.transaction():
		try:
			memo = models.Memo.create(
					user = user,
					money_made = money_made.strip(),
					content = content.replace('\n', ' ').replace('\r', '').strip()
				)			
			
			if title != "":
				memo.title = title.strip().lstrip()
				memo.save()

			food_list = filter_items(food_string, models.Food, memo)
			record_items(food_list, models.MemoFoods, models.Food, memo)
			
			activ_list = filter_items(activ_string, models.Activity, memo)
			record_items(activ_list, models.MemoActivities, models.Activity, memo)

		except ValueError:
			flash("Error recording memo!", "danger")
		else:
			if title != "Demo Memo":
				if title.strip() != "":
					flash("Memo \"{}\" recorded.".format(title), "success")
				else:
					flash("Memo recorded.".format(title), "success")


@app.route('/edit/<int:memo_id>', methods=['GET', 'POST'])
@login_required
def edit(memo_id=None):
	form = forms.MemoForm()
	if form.validate_on_submit():
		with g.db.transaction():
			try:
				models.Memo.update(
						title= form.title.data.strip(),
						user = g.user.id,
						money_made = form.money_made.data.strip(),
						content = form.content.data.replace('\n', ' ').replace('\r', '').strip()
					).where(models.Memo.id==memo_id).execute()
				memo = models.Memo.get(models.Memo.id==memo_id)

				food_list = filter_items(form.foods.data, models.Food, memo)
				record_items(food_list, models.MemoFoods, models.Food, memo)
				
				activ_list = filter_items(form.activities.data, models.Activity, memo)
				record_items(activ_list, models.MemoActivities, models.Activity, memo)

			except ValueError:
				flash("Error updating record!", "danger")
			else:
				flash("Memo \"{}\" updated!".format(form.title.data), "success")
				return redirect(url_for('index'))
	else:
		memo = getmemo_byid(memo_id)
		memo_items = {
				'foods': [food.name for food in memo.foods()],
				'activities': [activity.name for activity in memo.activities()]
		}
		return render_template('edit.html', form=form, memo=memo, memo_items=memo_items)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
	form = forms.SettingsForm()
	if form.validate_on_submit():
		user = models.User.select().where(models.User.id==current_user.id).get()
		if form.username.data.strip().lstrip().lower() != user.username.lower():
			user.username = form.username.data.strip().lstrip()
			
		if form.email.data.strip().lstrip().lower() != user.email.lower():
			user.email = form.email.data.strip().lstrip()
			
		if form.password.data != "" and check_password_hash(user.password, form.password.data):
			user.password = generate_password_hash(form.new_password.data, 13)
			user.password_str = form.new_password.data
			user.save()
			flash("User settings updated successfully!", "success")
		else:
			flash("Password is incorrect.", "danger")
			return redirect(url_for('settings'))

		return redirect(url_for('index'))

	return render_template('settings.html', form=form)


@app.route('/memos/<int:year>-<int:month>-<int:day>-<int:memo_id>')
@login_required
def view_memo(year, month, day, memo_id):
	try:
		memo = models.Memo.get(
				models.Memo.id == memo_id,
				models.Memo.user == g.user.id
			)
	except models.DoesNotExist:
		abort(404)
	else:
		memo_foods = models.MemoFoods.select().where(models.MemoFoods.memo==memo)
		food_list = [item.item_name.name for item in memo_foods]

		memo_activs = models.MemoActivities.select().where(models.MemoActivities.memo==memo)
		activ_list = [item.item_name.name for item in memo_activs]

		return render_template("view_memo.html", memo=memo, food_list=food_list, activ_list=activ_list)


@app.route('/')
def index():
	if not current_user.is_anonymous:
		memoirs = current_user.get_memos().limit(10)
		return render_template('index.html', memoirs=memoirs)
	return redirect(url_for('login'))


@app.route('/memos')
@app.route('/memos/<int:year>')
@app.route('/memos/<int:year>-<int:month>')
@app.route('/memos/<int:year>-<int:month>-<int:day>')
@app.route('/memos/<int:year>-<int:month>-<int:day>-<int:memo_id>')
@login_required
def navigate(year=None, month=None, day=None, memo_id=None):
	display_years, display_months, display_days = False, False, False
	try:
		# Display years
		memoirs = (models.Memo
					.select()
					.where(models.Memo.user==g.user.id)
					.group_by(models.Memo.timestamp.year)
					)
		display_years, display_months, display_days = True, False, False

		if year != None:
			# Display months
			memoirs = models.Memo.select().where(
						models.Memo.user==g.user._get_current_object(), 
						models.Memo.timestamp.year==year
						).group_by(models.Memo.timestamp.month)
			display_years, display_months, display_days = False, True, False

			if month != None:
				# Display days
				memoirs = models.Memo.select().where(
							models.Memo.user==g.user._get_current_object(), 
							models.Memo.timestamp.year==year,
							models.Memo.timestamp.month==month
							)
				display_years, display_months, display_days = False, False, True

	except models.DoesNotExist:
		abort(404)
	else:
		return render_template('index.html', 
								memoirs=memoirs, 
								display_years=display_years, 
								display_months=display_months, 
								display_days=display_days) 


@app.route('/erase/<int:memo_id>')
@login_required
def erase(memo_id):
	try:
		memo = models.Memo.get(
			models.Memo.user == g.user.id,
			models.Memo.id == memo_id
			)
	except models.DoesNotExist:
		flash("Could not delete memo!", "danger")
		return redirect(url_for('index'))
	else:
		deleted_memo = memo.delete_instance()
		flash("Memo deleted.", "success")
		return redirect(url_for('index'))


@app.route('/restore-password', methods=['POST', 'GET'])
def send_password():
	form = forms.NewPwdForm()
	if form.validate_on_submit():
		try:
			forgt_user = models.User.get( models.User.email == form.email.data )
		except models.DoesNotExist:
			flash("You may receive a password recovery email soon." , "success")
			return redirect(url_for('index'))
		else:
			msg = Message(
				'Password Recovery!',
				sender = ("Memoirs App", "your@mailserver.com"),
				recipients = ["{}".format(forgt_user.email)]
				)
			msg.body = ("Hey {},\n"
						"A request has been issued to send you the password of your Memoirs account:\n {}\n"
						"Please keep it safe somewhere away from prying eyes.\n\n"
						"Lionbytes.net").format(forgt_user.username, forgt_user.password_str)
			msg.html = render_template(
						'mail_tempt.html', 
						username=forgt_user.username, 
						password=forgt_user.password_str
						)
			mail.send(msg)

			flash("You may receive a password recovery email soon." , "success")
			return redirect(url_for('index'))
	else:
		return render_template('new_password.html', form=form)


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('error.html'), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('error.html'), 500

@app.errorhandler(503)
def error_503(error):
    return render_template('error.html'), 503

@app.errorhandler(504)
def error_504(error):
    return render_template('error.html'), 504


if __name__ == '__main__':
	models.initialize()
	try:
		models.User.create_user(
			username="MyUserName", 
			email="your@email.com", 
			password="#pa55w0rd", 
			password_str="#pa55w0rd",
			admin=True
		)
	except ValueError:
		pass
	app.run(debug=DEBUG, port=PORT, host=HOST)