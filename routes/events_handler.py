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
                amount_spent = float(activity.get("money_spent", "0").replace('$', '').replace(',', '')),
                amount_earned = float(activity.get("money_earned", "0").replace('$', '').replace(',', '')),
                time_spent = activity.get("time_spent"),
                gambling_type = activity.get("gambling_type"),
                amount_intended_spent= float(activity.get("money_intended", "0").replace('$', '').replace(',', '')),
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

# This function retrieves all saved calendar entries for a user with full details and returns them as JSON
# Called by: Frontend (app.js) on page load to populate the calendar with existing entries
# Parameters: user_id from session (or query param as fallback)
# Returns: JSON array of events with:
#   - id, date (YYYY-MM-DD format), type (drinking/gambling)
#   - For drinking entries: drinks (number of drinks consumed)
#   - For gambling entries: gambling_type, time_spent, money_intended, money_spent, money_earned, drinks_while_gambling
# This enables the "load events on startup" functionality and populates the sidebar with entry details
# Queries both CalendarEntry table and related Drinking/Gambling tables to get complete entry information
@events_handler_bp.route('/calendar-events', methods=['GET'])
def get_calendar_events():
    user_id = session.get('user_id')

    if not user_id:
        user_id = request.args.get('user_id', default=1, type=int)

    try:
        from database.db_helper import get_calendar_entries_for_user
        from database.db_initialization import Drinking, Gambling

        entries = get_calendar_entries_for_user(user_id)

        events = []
        for e in entries:
            event = {
                "id": e.id,
                "date": e.entry_date.isoformat().split('T')[0],  # Just YYYY-MM-DD
                "type": e.entry_type
            }

            # Fetch drinking details if it's a drinking entry
            if e.entry_type == "drinking":
                drinking = Drinking.query.filter_by(entry_id=e.id).first()
                if drinking and drinking.drinking_questions:
                    event["drinks"] = drinking.drinking_questions.get("num_drinks")

            # Fetch gambling details if it's a gambling entry
            elif e.entry_type == "gambling":
                gambling = Gambling.query.filter_by(entry_id=e.id).first()
                if gambling and gambling.gambling_questions:
                    gq = gambling.gambling_questions
                    event["gambling_type"] = gq.get("gambling_type")
                    event["time_spent"] = gq.get("time_spent")
                    event["money_intended"] = gq.get("amount_intended_spent")
                    event["money_spent"] = gq.get("amount_spent")
                    event["money_earned"] = gq.get("amount_earned")
                    event["drinks_while_gambling"] = gq.get("num_drinks")

            events.append(event)

        return jsonify(events), 200

    except Exception as exc:
        print(f"Error retrieving calendar events: {exc}")
        return jsonify({"status": "error", "message": "Failed to retrieve events"}), 500