from flask import Blueprint, request, jsonify
from database import (
    create_calendar_entry,
    add_gambling_entry,
    add_alcohol_entry,
    get_calendar_entries,
    get_latest_calendar_entry,
    get_alcohol_entry,
    get_gambling_entry,
    update_alcohol_entry,
    update_gambling_entry,
    delete_calendar_entry
)

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


# This function returns calendar entries for a user to render indicators
# Parameters: user_id (optional)
# Returns: JSON list of entry_date and entry_type
@events_handler_bp.route('/calendar-entries', methods=['GET'])
def calendar_entries():
    user_id = request.args.get("user_id") or "default"
    entries = get_calendar_entries(user_id)
    payload = []
    for entry in entries:
        payload.append({
            "entry_date": entry.get("entry_date"),
            "entry_type": entry.get("entry_type")
        })
    return jsonify({
        "status": "success",
        "entries": payload
    }), 200


# This function returns entry details for a specific date
# Parameters: date (required), user_id (optional)
# Returns: JSON object containing drinking and gambling data if present
@events_handler_bp.route('/entry', methods=['GET'])
def get_entry():
    user_id = request.args.get("user_id") or "default"
    entry_date = request.args.get("date")
    if not entry_date:
        return jsonify({"status": "error", "message": "date is required"}), 400

    drinking_entry = get_latest_calendar_entry(user_id, entry_date, "drinking")
    gambling_entry = get_latest_calendar_entry(user_id, entry_date, "gambling")

    response = {
        "status": "success",
        "date": entry_date,
        "drinking": None,
        "gambling": None
    }

    if drinking_entry:
        details = get_alcohol_entry(drinking_entry.get("entry_id"))
        if details:
            response["drinking"] = {
                "entry_id": drinking_entry.get("entry_id"),
                "drinks": details.get("num_drinks"),
                "drinks_cost": details.get("money_spent"),
                "drink_trigger": details.get("trigger")
            }

    if gambling_entry:
        details = get_gambling_entry(gambling_entry.get("entry_id"))
        if details:
            response["gambling"] = {
                "entry_id": gambling_entry.get("entry_id"),
                "gambling_type": details.get("gambling_type"),
                "time_spent": details.get("time_spent"),
                "money_intended": details.get("money_intended"),
                "money_spent": details.get("amount_spent"),
                "money_earned": details.get("amount_earned"),
                "drinks_while_gambling": details.get("drinks_while_gambling")
            }

    return jsonify(response), 200

# This function saves the data from log_activity() to the db
# Parameters: JSON format
# Returns: True on success and False on failure
def save_activity(activity: dict):
    """
        Saves the data from log_activity() to the db
        Parameters: JSON format (dict)
        Returns: True on success and False on failure
        """
    try:
        # Get important entries needed to create calendar entry
        user_id = activity.get("user_id")
        entry_date = activity.get("date")
        drinking = activity.get("drinking")
        gambling = activity.get("gambling")

        # Set this to default user if there's no user
        if not user_id:
            user_id = "default"

        # Debug here
        #print(activity)
        #print("Debug:", user_id, entry_date, entry_type)

        if not entry_date:
            return False

        if drinking:
            existing = get_latest_calendar_entry(user_id, entry_date, "drinking")
            if existing:
                update_alcohol_entry(
                    entry_id=existing.get("entry_id"),
                    num_drinks=drinking.get("drinks"),
                    money_spent=drinking.get("drinks_cost"),
                    trigger=drinking.get("drink_trigger")
                )
            else:
                entry_id = create_calendar_entry(user_id, "drinking", entry_date)
                add_alcohol_entry(
                    user_id = user_id,
                    entry_id = entry_id,
                    money_spent = drinking.get("drinks_cost"),
                    num_drinks = drinking.get("drinks"),
                    trigger = drinking.get("drink_trigger")
                )

        if gambling:
            existing = get_latest_calendar_entry(user_id, entry_date, "gambling")
            if existing:
                update_gambling_entry(
                    entry_id=existing.get("entry_id"),
                    amount_spent=gambling.get("money_spent"),
                    amount_earned=gambling.get("money_earned"),
                    time_spent=gambling.get("time_spent"),
                    gambling_type=gambling.get("gambling_type"),
                    money_intended=gambling.get("money_intended"),
                    drinks_while_gambling=gambling.get("drinks_while_gambling")
                )
            else:
                entry_id = create_calendar_entry(user_id, "gambling", entry_date)
                add_gambling_entry(
                    user_id = user_id,
                    entry_id = entry_id,
                    amount_spent = gambling.get("money_spent"),
                    amount_earned = gambling.get("money_earned"),
                    time_spent = gambling.get("time_spent"),
                    gambling_type = gambling.get("gambling_type"),
                    money_intended = gambling.get("money_intended"),
                    drinks_while_gambling = gambling.get("drinks_while_gambling")
                )

        # If we reached here, everything inserted correctly
        return True

    except Exception as e:
        print(f"Database Save Error: {e}")
        return False


# This function deletes an entry for a specific date and type
# Parameters: JSON with date, entry_type, user_id (optional)
# Returns: JSON status
@events_handler_bp.route('/delete-entry', methods=['POST'])
def delete_entry():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    user_id = data.get("user_id") or "default"
    entry_date = data.get("date")
    entry_type = data.get("entry_type")

    if not entry_date or entry_type not in ["drinking", "gambling"]:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    existing = get_latest_calendar_entry(user_id, entry_date, entry_type)
    if not existing:
        return jsonify({"status": "error", "message": "Entry not found"}), 404

    delete_calendar_entry(existing.get("entry_id"), entry_type)
    return jsonify({"status": "success"}), 200
