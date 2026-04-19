from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# creating user table that stores ID, password, items, date borrowed and date due
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String)
    is_admin = db.Column(db.Boolean)
    email = db.Column(db.String)
    onboarding_complete = db.Column(db.Boolean, default=False)
    study_group_code = db.Column(db.VARCHAR(50)) # study group being a mix of char and int stored as str

class CalendarEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow)
    entry_type = db.Column(db.String(50))

# create a gambling table that stores all gambling information
class Gambling(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('calendar_entry.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gambling_questions = db.Column(db.JSON)

# create a drinking table that stores all drinking information
class Drinking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('calendar_entry.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    drinking_questions = db.Column(db.JSON)

# create a personal expense table that stores all personal expense information
class PersonalExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    personal_expense_questions = db.Column(db.JSON)

class StudyCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(8), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    researcher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    questions = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



