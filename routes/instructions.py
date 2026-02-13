from flask import Blueprint, render_template

# Create a blueprint to handle instructions, this will be called in app.py
instructions_bp = Blueprint('instructions', __name__)

# This function loads the gambling_instructions.html
# Parameters: N/A
# Returns: The rendered gambling_instructions.html file
@instructions_bp.route('/gambling_instructions.html')
def gambling_instructions():
    """ Renders gambling instructions view """
    return render_template('gambling_instructions.html')

# This function loads the alcohol_instructions.html
# Parameters: N/A
# Returns: The rendered alcohol_instructions.html file
@instructions_bp.route('/alcohol_instructions.html')
def alcohol_instructions():
    """ Renders alcohol instructions view """
    return render_template('alcohol_instructions.html')
