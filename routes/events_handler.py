from flask import Blueprint, request, jsonify, session
from database.db_helper import create_calendar_entry, add_gambling_entry, add_alcohol_entry
from pathlib import Path
import json


# Create a blueprint to handle events, this will be called in app.py
events_handler_bp = Blueprint('events_handler', __name__)

# Read the questions.json
with open(Path("config\questions.json"), "r", encoding="utf-8") as f:
    qSchema = json.load(f)

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

def extract_fields(schema_section, answers_dict):
    """
    schema_section: list of question definitions
    answers_dict: stored answers (from DB)
    """
    result = {}
    for q in schema_section:
        qid = q["id"]
        if answers_dict and qid in answers_dict:
            result[qid] = answers_dict[qid]
    return result


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
                if drinking:
                    event.update(extract_fields(qSchema["drinking"], drinking.drinking_questions))

            # Fetch gambling details if it's a gambling entry
            elif e.entry_type == "gambling":
                gambling = Gambling.query.filter_by(entry_id=e.id).first()
                if gambling:
                    event.update(
                        extract_fields(
                            qSchema["gambling"],
                            gambling.gambling_questions
                        )
                    )

            events.append(event)

        return jsonify(events), 200

    except Exception as exc:
        print(f"Error retrieving calendar events: {exc}")
        return jsonify({"status": "error", "message": "Failed to retrieve events"}), 500
