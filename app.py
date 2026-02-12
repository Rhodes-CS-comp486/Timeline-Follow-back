from flask import Flask, render_template

# To create and import BP use the following convention
from routes.events_handler import events_handler_bp

app = Flask(__name__)

# Register new BP
app.register_blueprint(events_handler_bp, url_prefix='/api')

# The default route is to home.html
@app.route('/')
@app.route('/home.html')

# This function just loads the home.html file
# Parameters: N/A
# Returns: The rendered home.html file
def home():
    """ Renders home view """
    return render_template('home.html')

# This function loads the gambling_instructions.html
# Parameters: N/A
# Returns: The rendered gambling_instructions.html file
@app.route('/gambling_instructions.html')
def gambling_instructions():
    """ Renders gambling instructions view """
    return render_template('gambling_instructions.html')

# This function loads the calendar.html
# Parameters: N/A
# Returns: The rendered calendar.html file
@app.route('/calendar.html')
def calendar():
    """ Renders calendar view """
    return render_template('calendar.html')

if __name__ == '__main__':
    app.run(debug=True)