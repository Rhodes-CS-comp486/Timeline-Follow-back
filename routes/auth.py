import re

from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db_initialization import User
from database.db_helper import create_user

from functools import wraps
auth_bp = Blueprint('auth', __name__)


def validate_password(password):
    """Returns (is_valid: bool, error_message: str)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*()\-_=+\[\]{};:\'",.<>?/\\|`~]', password):
        return False, "Password must contain at least one special character."
    return True, ""


@auth_bp.route('/create-account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        # All fields required
        if not all([first_name, last_name, email, username, password, confirm_password]):
            errors.append("All fields are required.")

        # Passwords must match
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Password strength
        if password:
            valid, pw_error = validate_password(password)
            if not valid:
                errors.append(pw_error)

        # Email uniqueness
        if email and User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists.")

        # Username uniqueness
        if username and User.query.filter_by(username=username).first():
            errors.append("This username is already taken.")

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'username': username,
        }

        if errors:
            return render_template('create_account.html', errors=errors, form_data=form_data)

        hashed_password = generate_password_hash(password)

        user = create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=hashed_password,
            username=username,
            is_admin=False,
        )

        if user is None:
            return render_template('create_account.html',
                                   errors=["An unexpected error occurred. Please try again."],
                                   form_data=form_data)

        return redirect(url_for('auth.login'))

    return render_template('create_account.html', errors=[], form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        error = None

        if not email or not password:
            error = "Email and password are required."
        else:
            user = User.query.filter_by(email=email).first()
            if user is None or not check_password_hash(user.password, password):
                error = "Invalid email or password."

        if error:
            return render_template('login.html', error=error)

        session['user_id'] = user.id

        return redirect(url_for('home'))

    return render_template('login.html', error=None)


@auth_bp.route('/logout')
def logout():
    # Clear all session data so the user is fully signed out.
    session.clear()
    # Send the user back to the login screen after logout.
    return redirect(url_for('auth.login'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')

        if not user_id:
            return redirect(url_for('auth.login'))

        user = User.query.get(user_id)

        if not user or not user.is_admin:
            return abort(403)  # Forbidden

        return f(*args, **kwargs)

    return decorated_function
