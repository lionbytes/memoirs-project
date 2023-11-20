import datetime

from peewee import *
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash


DATABASE = SqliteDatabase('memoirs.db')


class User(UserMixin, Model):
	username = CharField(max_length=20, unique=True)
	email = CharField(unique=True)
	password = CharField(max_length=50)
	password_str = CharField(max_length=50)
	joined_at = DateTimeField(default=datetime.datetime.now)
	is_admin = BooleanField(default=False)

	class Meta:
		database = DATABASE
		order_by = ('-joined_at',)

	def get_memos(self):
		return Memo.select().where(Memo.user==self)

	@classmethod
	def create_user(cls, username, email, password, password_str, admin=False):
		try:
			with DATABASE.transaction():
				cls.create(
					username=username, 
					email=email, 
					password=generate_password_hash(password, 13),
					password_str=password,
					is_admin=admin
					)
		except IntegrityError:
			raise ValueError("User already exists!")


class Memo(Model):
	title = CharField(default='Normal Day')
	content = TextField(default='')	
	money_made = DecimalField(default=0)
	timestamp = DateTimeField(default=datetime.datetime.now)
	user = ForeignKeyField(model=User, related_name='memos')

	class Meta:
		database = DATABASE
		order_by = ('-timestamp',)

	def foods(self):
		return (Food
				.select()
				.join(MemoFoods, on=MemoFoods.item_name)
				.where(MemoFoods.memo == self )
			)

	def activities(self):
		return (Activity
				.select()
				.join(MemoActivities, on=MemoActivities.item_name)
				.where(MemoActivities.memo == self )
			)


class Food(Model):
	name = CharField(unique=True)
	time_added = DateTimeField(default=datetime.datetime.now)

	class Meta:
		database = DATABASE
		order_by = ('-time_added',)


class Activity(Model):
	name = CharField(unique=True)
	time_added = DateTimeField(default=datetime.datetime.now)

	class Meta:
		database = DATABASE
		order_by = ('-time_added',)


class MemoFoods(Model):
	memo = ForeignKeyField(Memo)
	item_name = ForeignKeyField(Food)

	class Meta:
		database = DATABASE
		indexes = (
            (('memo', 'item_name'), True),
        )


class MemoActivities(Model):
	memo = ForeignKeyField(Memo)
	item_name = ForeignKeyField(Activity)

	class Meta:
		database = DATABASE
		indexes = (
            (('memo', 'item_name'), True),
        )


def initialize():
	DATABASE.connect()
	DATABASE.create_tables([User, Memo, Food, Activity, MemoFoods, MemoActivities], safe=True)
	DATABASE.close()