from flask import Blueprint, request, jsonify, session
from database.db_helper import create_calendar_entry, add_gambling_entry, add_alcohol_entry


# Create a blueprint to handle events, this will be called in app.py
events_handler_bp = Blueprint('events_handler', __name__)

# This function retrieves data from the frontend to backend under a JSON format
# Parameters: N/A
# Returns: A JSON file containing all answers to the input fields
@events_handler_bp.route('/log-activity', methods=['POST'])
def log_activity():
    data = request.get_json()
    # Error handling
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # save entry to database
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

# This function saves the data from log_activity() to the database
# Parameters: JSON format
# Returns: True on success and False on failure
def save_activity(activity: dict):
    try:
        # Get important entries needed to create calendar entry
        user_id = session.get('user_id')
        entry_date = activity.get("date")
        entry_type = activity.get("type")

        # Set this to default user if there's no user
        if not user_id:
            user_id = 1

        # create calendar entry
        entry_id = create_calendar_entry(user_id, entry_type, entry_date)

        print(f"Check calendar entry info: {user_id}, {entry_date}, {entry_type}")

        if not entry_id:
            raise Exception("Failed to create CalendarEntry")

        # Extract all the information from our form
        if entry_type == "gambling":
            add_gambling_entry(
                user_id = user_id,
                entry_id = entry_id,
                amount_spent = activity.get("money_spent"),
                amount_earned = activity.get("money_earned"),
                time_spent = activity.get("time_spent"),
                gambling_type = activity.get("gambling_type"),
                amount_intended_spent= activity.get("money_intended"),
                num_drinks = activity.get("drinks_while_gambling"),
            )

        elif entry_type == "drinking":
            add_alcohol_entry(
                user_id = user_id,
                entry_id = entry_id,
                num_drinks = activity.get("drinks"),
            )

        return True

    except Exception as e:
        print(f"Save Error: {e}")
        return False