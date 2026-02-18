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
        user_id = session.get('user_id')
        entry_date = activity.get("date")

        drinking_logged = activity.get("drinking_logged")
        gambling_logged = activity.get("gambling_logged")

        if not user_id:
            user_id = 1

        if not entry_date:
            raise Exception("Missing date")

        if not drinking_logged and not gambling_logged:
            raise Exception("No activity selected")

        # Changed this so calendar entry no longer needs submission type (eg gambling or drinking)
        entry_id = create_calendar_entry(user_id, entry_date)

        if not entry_id:
            raise Exception("Failed to create CalendarEntry")

        print(f"Created calendar entry: {user_id}, {entry_date}")

        # Remove metadata fields
        activity_payload = {
            k: v for k, v in activity.items()
            if k not in ["date", "drinking_logged", "gambling_logged"]
        }

        # Add gambling if selected
        if gambling_logged:
            add_gambling_entry(
                user_id=user_id,
                entry_id=entry_id,
                activity_data=activity_payload
            )

        # Add drinking if selected
        if drinking_logged:
            add_alcohol_entry(
                user_id=user_id,
                entry_id=entry_id,
                activity_data=activity_payload
            )

        return True

    except Exception as e:
        print(f"Save Error: {e}")
        return False
