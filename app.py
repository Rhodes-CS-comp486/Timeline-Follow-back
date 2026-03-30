from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, session
from database.db_initialization import db
import os
from database.db_initialization import User
from sqlalchemy import inspect

# helper function to load questions from JSON
from config.config_helper import load_questions

# To create and import BP use the following convention
from routes.events_handler import events_handler_bp
from routes.instructions import instructions_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.user_report import user_report_bp
from routes.personal_expense import personal_expense_bp
from routes.insights import insights_bp

app = Flask(__name__)

# Register new BP
app.register_blueprint(events_handler_bp, url_prefix='/api')
app.register_blueprint(instructions_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin/api')
app.register_blueprint(user_report_bp, url_prefix='/user')
app.register_blueprint(personal_expense_bp, url_prefix='/user')
app.register_blueprint(insights_bp, url_prefix='/user')


# ------------- This part is for DB initialization and connection ----------------
load_dotenv()
# load the DATABASE_URL from .env
db_url = os.getenv("DATABASE_URL")
secret_session_key = os.getenv("SECRET_KEY")

# make sure it actually exists in .env
if not db_url or not secret_session_key:
    raise ValueError("No DATABASE_URL or SECRET_KEY found in environment variables!")

# connect to our flask app with config
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_session_key

db.init_app(app)

# create database contents if not already
with app.app_context():
    #db.drop_all() # uncomment this to reset the db
    print(f"--- CONNECTION CHECK ---")
    print(f"Database: {db.engine.url.database}")
    print(f"Host: {db.engine.url.host}")
    print(f"Username: {db.engine.url.username}")
    print("Create new database columns and rows")

    db.create_all()

    # Add any missing columns that weren't present when the table was first created
    with db.engine.connect() as conn:
        from sqlalchemy import text
        existing_columns = [col['name'] for col in inspect(db.engine).get_columns('user')]
        migrations = {
            'username':   'ALTER TABLE "user" ADD COLUMN username VARCHAR UNIQUE',
            'first_name': 'ALTER TABLE "user" ADD COLUMN first_name VARCHAR',
            'last_name':  'ALTER TABLE "user" ADD COLUMN last_name VARCHAR',
            'is_admin':   'ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN',
            'email':      'ALTER TABLE "user" ADD COLUMN email VARCHAR',
        }
        for col, sql in migrations.items():
            if col not in existing_columns:
                conn.execute(text(sql))
                print(f"Migrated: added '{col}' column to user table.")
        conn.commit()

    # This reflects the database schema and prints table names
    inspector = inspect(db.engine)
    print(f"Tables found: {inspector.get_table_names()}")
    print("Database synced! Models now match the Postgres schema.")


# The default route is to auth.html
@app.route('/')
def index():
    """ Redirects to login page """
    return redirect(url_for('auth.login'))

@app.route('/home.html')
# This function just loads the home.html file
# Parameters: N/A
# Returns: The rendered home.html file
def home():
    """ Renders home view """
    return render_template('home.html')

# This function loads the calendar.html
# Parameters: N/A
# Returns: The rendered calendar.html file
@app.route('/calendar.html')
def calendar():
    questions = load_questions()
    return render_template('calendar.html', questions=questions)

@app.route('/settings.html')
def user_settings():
    return render_template('user_settings.html')

# This function defines current_user=user in the context of our flask app
# Parameters: N/A
# Returns: current_user as a User object\
@app.context_processor
def inject_user():
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = User.query.get(user_id)
    return dict(current_user=user)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
