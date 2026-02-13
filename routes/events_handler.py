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

    # save entry to db
    success = save_activity(data)

    # Printing in JSON style to verify
    print(f"JSON Data: {data}")

    # checking success
    if success:
        return jsonify({
            "status": "success",
            "message": "Activity logged successfully"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to save activity. Check server logs for details."
        }), 500

# This function saves the data from log_activity() to the db
# Parameters: JSON format
# Returns: True on success and False on failure
def save_activity(activity: dict):
    """
        Saves the data from log_activity() to the db.
        TODO: Implement Postgres storage.
        Parameters: JSON format (dict)
        Returns: True on success and False on failure
        """
    try:
        print(f"Activity received (Postgres save not yet implemented): {activity}")
        return True
    except Exception as e:
        print(f"Save Error: {e}")
        return False