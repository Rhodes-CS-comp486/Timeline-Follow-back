from flask import Blueprint, request, jsonify

# Create a blueprint to handle events, this will be called in app.py
events_handler_bp = Blueprint('events_handler', __name__)

# This function retrieves data from the frontend to backend under a JSON format
# Parameters: N/A
# Returns: A JSON file containing all answers to the input fields
@events_handler_bp.route('/log-activity', methods=['POST'])
def log_activity():
    """
    Receives JSON data
    """
    data = request.get_json()

    # Error handling
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # Printing in JSON style to verify
    print(f"JSON Data: {data}")
    return jsonify({
        "status": "success",
        "message": "Event logged successfully",
        "data": data
    }), 200

# This function saves the data from log_activity() to the db
# Parameters: JSON format
# Returns: True on success and False on failure
def save_activity(activity: dict):
    pass