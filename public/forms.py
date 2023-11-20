import re
from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, NumberRange, ValidationError

from models import User


def name_exists(form, field):
	if User.select().where(User.username==field.data).exists():
		raise ValidationError("Username has already been taken.")

def email_exists(form, field):
	if User.select().where(User.email==field.data).exists():
		raise ValidationError("Email has already been registered.")


def name_change_check(form, field):
	if field.data and User.select().where( (User.username==field.data) & (User.id != current_user.id)	).exists():
		raise ValidationError("Username taken.")

def email_change_check(form, field):
	if field.data and User.select().where( (User.email==field.data) & (User.id != current_user.id)	).exists():
		raise ValidationError("Email already registered.")

# Password Strength not used.
def password_strength_check(form, field):
    """
    A password is considered strong if it has:
        1 digit or more
        1 symbol or more
        1 uppercase letter or more
        1 lowercase letter or more
    """
    digit_error = re.search(r"\d", field.data) is None
    uppercase_error = re.search(r"[A-Z]", field.data) is None
    lowercase_error = re.search(r"[a-z]", field.data) is None
    symbol_error = re.search(r"\W", field.data) is None

    if digit_error or uppercase_error or lowercase_error or symbol_error:
    	raise ValidationError("Password must contain uppercases, lowercases, digits and symbols")

class RegisterForm(FlaskForm):
	username = StringField(
		'Username',
		validators=[
			DataRequired(), 
			Regexp(
				r'^[a-zA-Z0-9_]+$', 
				message="Username can only contain letters, numbers and underscores."
				),
				name_exists
		])

	email = StringField(
		'Email',
		validators=[ DataRequired(), Email(), email_exists ]
		)

	password = PasswordField(
		'Password',
		validators=[
			DataRequired(),
			Length(min=6, max=50, message="Password must be at least 6 characters long!"),
			EqualTo('password2', message="Passwords do not match!"), 
		])

	password2 = PasswordField(
		'Confirm',
		validators=[DataRequired()]
		)


class LoginForm(FlaskForm):
	username = StringField( 'Username', validators=[DataRequired()] )
	password = PasswordField( 'Password', validators=[DataRequired()] )


class MemoForm(FlaskForm):
	title = StringField('Day Title')
	content = TextAreaField('How did it go?')
	money_made = StringField( 'Income', validators=[Regexp(r'^[0-9]*$', message="Must be a number.")])
	foods = StringField( 'Foods', validators=[
									Regexp(
											r'^([a-zA-Z0-9 ]+[,]?)*$',
											message="Foods should be separated by a comma, containing letters and numbers only."
											)
						])
	activities = StringField( 'Activities', validators=[
									Regexp(
											r'^([a-zA-Z0-9 ]+[,]?)*$',
											message="Activities should be separated by a comma, containing letters and numbers only."
											)
						])


class SettingsForm(FlaskForm):
	username = StringField(
		'Username',
		validators=[
			Regexp(
				r'^[a-zA-Z0-9_]*$',
				message="Username can only contain letters, numbers and underscores."
				),
				name_change_check
		])

	email = StringField(
		'Email',
		validators=[ Email(), email_change_check ]
		)
	
	password = PasswordField(
		'Old Password', 
		validators=[ 
			DataRequired()
		])

	new_password = PasswordField(
		'New Password',
		validators=[ 
			Length(min=6, max=50, message="Password must be at least 6 characters long!"),
			EqualTo('confirm_password', message="Passwords do not match!") 
		])

	confirm_password = PasswordField(
		'Confirm Password'
		)

class NewPwdForm(FlaskForm):
	email = StringField(
		'Email Address',
		validators = [ DataRequired(), Email()  ]
		)