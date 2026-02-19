from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for
from database.db_initialization import db
import os

# helper function to load questions from JSON
from config.config_helper import load_questions

# To create and import BP use the following convention
from routes.events_handler import events_handler_bp
from routes.instructions import instructions_bp
from routes.auth import auth_bp

app = Flask(__name__)

# Register new BP
app.register_blueprint(events_handler_bp, url_prefix='/api')
app.register_blueprint(instructions_bp)
app.register_blueprint(auth_bp)


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
    '''
    print(f"--- CONNECTION CHECK ---")
    print(f"Database: {db.engine.url.database}")
    print(f"Host: {db.engine.url.host}")
    print(f"Username: {db.engine.url.username}")
    print("Create new database columns and rows")
    '''
    db.create_all()
    '''
    # This reflects the database schema and prints table names
    inspector = inspect(db.engine)
    print(f"Tables found: {inspector.get_table_names()}")
    print("Database synced! Models now match the Postgres schema.")
    '''




# The default route is to home.html
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

if __name__ == '__main__':
    app.run(debug=True)