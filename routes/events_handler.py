from flask import Blueprint, request, jsonify, session
from database.db_helper import create_calendar_entry, get_calendar_entries_for_user
from database.db_initialization import CalendarEntry, Drinking, Gambling, db
from pathlib import Path
import json
from datetime import datetime, timedelta


# Create a blueprint to handle events, this will be called in app.py
events_handler_bp = Blueprint('events_handler', __name__)

# Read the questions.json
with open(Path(__file__).parent.parent / "config" / "questions.json", "r", encoding="utf-8") as f:
    qSchema = json.load(f)


def parse_iso_day(day_str: str):
    try:
        parsed = datetime.strptime(day_str, "%Y-%m-%d")
        return parsed.replace(hour=0, minute=0, second=0, microsecond=0)
    except (TypeError, ValueError):
        return None


def get_entries_for_user_day(user_id: int, day_str: str):
    start_of_day = parse_iso_day(day_str)
    if not start_of_day:
        return []
    next_day = start_of_day + timedelta(days=1)
    return CalendarEntry.query.filter_by(user_id=user_id).filter(
        CalendarEntry.entry_date >= start_of_day,
        CalendarEntry.entry_date < next_day
    ).order_by(CalendarEntry.id.desc()).all()

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

        # Keep one logical entry per user/day. Reuse latest entry if present.
        day_entries = get_entries_for_user_day(user_id, entry_date)

        if day_entries:
            primary_entry = day_entries[0]
        else:
            parsed_entry_date = parse_iso_day(entry_date)
            if not parsed_entry_date:
                raise Exception("Invalid date format. Expected YYYY-MM-DD")
            primary_entry = create_calendar_entry(user_id, parsed_entry_date)
            if not primary_entry:
                raise Exception("Failed to create CalendarEntry")

        print(f"Created calendar entry: {user_id}, {entry_date}")

        # Remove metadata fields
        activity_payload = {
            k: v for k, v in activity.items()
            if k not in ["date", "drinking_logged", "gambling_logged"]
        }

        primary_entry_id = primary_entry.id
        drinking_rows = Drinking.query.filter_by(entry_id=primary_entry_id).all()
        gambling_rows = Gambling.query.filter_by(entry_id=primary_entry_id).all()

        if drinking_logged:
            if drinking_rows:
                drinking_rows[0].drinking_questions = activity_payload
                for extra in drinking_rows[1:]:
                    db.session.delete(extra)
            else:
                db.session.add(
                    Drinking(
                        entry_id=primary_entry_id,
                        user_id=user_id,
                        drinking_questions=activity_payload
                    )
                )
        else:
            for drinking in drinking_rows:
                db.session.delete(drinking)

        if gambling_logged:
            if gambling_rows:
                gambling_rows[0].gambling_questions = activity_payload
                for extra in gambling_rows[1:]:
                    db.session.delete(extra)
            else:
                db.session.add(
                    Gambling(
                        entry_id=primary_entry_id,
                        user_id=user_id,
                        gambling_questions=activity_payload
                    )
                )
        else:
            for gambling in gambling_rows:
                db.session.delete(gambling)

        # Remove duplicate entries from same date if any already exist.
        for duplicate_entry in day_entries[1:]:
            duplicate_drinking_rows = Drinking.query.filter_by(entry_id=duplicate_entry.id).all()
            duplicate_gambling_rows = Gambling.query.filter_by(entry_id=duplicate_entry.id).all()
            for drinking in duplicate_drinking_rows:
                db.session.delete(drinking)
            for gambling in duplicate_gambling_rows:
                db.session.delete(gambling)
            db.session.flush()
            db.session.delete(duplicate_entry)

        db.session.commit()

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
        entries = get_calendar_entries_for_user(user_id)
        entries = sorted(entries, key=lambda row: (row.entry_date, row.id))

        events_by_date = {}
        for e in entries:
            iso_date = e.entry_date.isoformat().split('T')[0]
            if iso_date not in events_by_date:
                events_by_date[iso_date] = {
                    "id": e.id,
                    "date": iso_date,
                    "type": e.entry_type,
                    "has_drinking": False,
                    "has_gambling": False
                }

            event = events_by_date[iso_date]
            if e.id > event["id"]:
                event["id"] = e.id

            # Fetch drinking details if it's a drinking entry
            if not e.entry_type or e.entry_type == "drinking":
                drinking = Drinking.query.filter_by(entry_id=e.id).first()
                if drinking:
                    event["has_drinking"] = True
                if drinking and drinking.drinking_questions:
                    print(f"DEBUG - drinking_questions: {drinking.drinking_questions}")
                    extracted = extract_fields(qSchema["drinking"], drinking.drinking_questions)
                    print(f"DEBUG - extracted fields: {extracted}")
                    event.update(extracted)
                    print(f"DEBUG - final event object: {event}")


            if not e.entry_type or e.entry_type == "gambling":

                gambling = Gambling.query.filter_by(entry_id=e.id).first()
                if gambling:
                    event["has_gambling"] = True

                print(f"DEBUG - Found gambling record: {gambling}")

                print(f"DEBUG - gambling.gambling_questions: {gambling.gambling_questions if gambling else 'N/A'}")

                if gambling and gambling.gambling_questions:
                    print(f"DEBUG - gambling_questions: {gambling.gambling_questions}")
                    extracted = extract_fields(qSchema["gambling"], gambling.gambling_questions)
                    print(f"DEBUG - extracted fields: {extracted}")
                    event.update(extracted)
                    if not  e.entry_type:
                        event["type"] = "gambling"

                    print(f"DEBUG - final event object: {event}")

        events = sorted(events_by_date.values(), key=lambda item: item["date"])

        return jsonify(events), 200

    except Exception as exc:
        print(f"Error retrieving calendar events: {exc}")
        return jsonify({"status": "error", "message": "Failed to retrieve events"}), 500


@events_handler_bp.route('/activity/<int:entry_id>', methods=['PUT'])
def update_activity(entry_id):
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    user_id = session.get('user_id')
    if not user_id:
        user_id = 1

    drinking_logged = data.get("drinking_logged")
    gambling_logged = data.get("gambling_logged")
    if not drinking_logged and not gambling_logged:
        return jsonify({"status": "error", "message": "No activity selected"}), 400

    entry = CalendarEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if not entry:
        return jsonify({"status": "error", "message": "Entry not found"}), 404

    day_iso = entry.entry_date.isoformat().split('T')[0]
    same_day_entries = get_entries_for_user_day(user_id, day_iso)

    activity_payload = {
        k: v for k, v in data.items()
        if k not in ["date", "drinking_logged", "gambling_logged"]
    }

    try:
        drinking_rows = Drinking.query.filter_by(entry_id=entry_id).all()
        gambling_rows = Gambling.query.filter_by(entry_id=entry_id).all()

        if drinking_logged:
            if drinking_rows:
                drinking_rows[0].drinking_questions = activity_payload
                for extra in drinking_rows[1:]:
                    db.session.delete(extra)
            else:
                db.session.add(
                    Drinking(
                        entry_id=entry_id,
                        user_id=user_id,
                        drinking_questions=activity_payload
                    )
                )
        else:
            for drinking in drinking_rows:
                db.session.delete(drinking)

        if gambling_logged:
            if gambling_rows:
                gambling_rows[0].gambling_questions = activity_payload
                for extra in gambling_rows[1:]:
                    db.session.delete(extra)
            else:
                db.session.add(
                    Gambling(
                        entry_id=entry_id,
                        user_id=user_id,
                        gambling_questions=activity_payload
                    )
                )
        else:
            for gambling in gambling_rows:
                db.session.delete(gambling)

        # Keep only the edited entry for that day.
        for day_entry in same_day_entries:
            if day_entry.id == entry_id:
                continue

            duplicate_drinking_rows = Drinking.query.filter_by(entry_id=day_entry.id).all()
            duplicate_gambling_rows = Gambling.query.filter_by(entry_id=day_entry.id).all()

            for drinking in duplicate_drinking_rows:
                db.session.delete(drinking)
            for gambling in duplicate_gambling_rows:
                db.session.delete(gambling)
            db.session.flush()
            db.session.delete(day_entry)

        db.session.commit()
        return jsonify({"status": "success", "message": "Activity updated successfully"}), 200

    except Exception as exc:
        db.session.rollback()
        print(f"Update Error: {exc}")
        return jsonify({"status": "error", "message": "Failed to update activity"}), 500


@events_handler_bp.route('/activity/<int:entry_id>', methods=['DELETE'])
def delete_activity(entry_id):
    user_id = session.get('user_id')
    if not user_id:
        user_id = 1

    entry = CalendarEntry.query.filter_by(id=entry_id, user_id=user_id).first()
    if not entry:
        return jsonify({"status": "error", "message": "Entry not found"}), 404

    day_iso = entry.entry_date.isoformat().split('T')[0]
    same_day_entries = get_entries_for_user_day(user_id, day_iso)

    try:
        # Delete all entries for the same date so duplicates are removed too.
        for day_entry in same_day_entries:
            drinking_rows = Drinking.query.filter_by(entry_id=day_entry.id).all()
            gambling_rows = Gambling.query.filter_by(entry_id=day_entry.id).all()

            for drinking in drinking_rows:
                db.session.delete(drinking)
            for gambling in gambling_rows:
                db.session.delete(gambling)
            db.session.flush()
            db.session.delete(day_entry)

        db.session.commit()
        return jsonify({"status": "success", "message": "Entry deleted successfully"}), 200

    except Exception as exc:
        db.session.rollback()
        print(f"Delete Error: {exc}")
        return jsonify({"status": "error", "message": "Failed to delete entry"}), 500
