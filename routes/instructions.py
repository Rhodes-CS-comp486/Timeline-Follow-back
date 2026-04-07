from flask import Blueprint, render_template, request, redirect, url_for, session
from database.db_initialization import db, User

# Create a blueprint to handle instructions, this will be called in app.py
instructions_bp = Blueprint('instructions', __name__)

# This function loads the gambling_instructions.html
# Parameters: N/A
# Returns: The rendered gambling_instructions.html file
@instructions_bp.route('/gambling_instructions.html')
def gambling_instructions():
    """ Renders gambling instructions view """
    onboarding = request.args.get('onboarding') == '1'
    return render_template('gambling_instructions.html', onboarding=onboarding)

# This function loads the alcohol_instructions.html
# Parameters: N/A
# Returns: The rendered alcohol_instructions.html file
@instructions_bp.route('/alcohol_instructions.html')
def alcohol_instructions():
    """ Renders alcohol instructions view """
    onboarding = request.args.get('onboarding') == '1'
    return render_template('alcohol_instructions.html', onboarding=onboarding)

@instructions_bp.route('/onboarding/complete')
def complete_onboarding():
    """ Marks onboarding as done and sends the user to the calendar """
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.onboarding_complete = True
            db.session.commit()
    return redirect(url_for('calendar'))
