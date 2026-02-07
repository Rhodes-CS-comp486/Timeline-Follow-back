from flask import Flask, request, jsonify, send_from_directory
from database import (
    create_user,
    create_calendar_entry,
    add_gambling_entry,
    add_alcohol_entry
)
import os

app = Flask(__name__)

# HTML pages
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/enter-information")
def enter_information():
    return send_from_directory(".", "enter-information.html")


# JS files
@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("js", filename)


# Entry Route
@app.route("/save-entry", methods=["POST"])
def save_entry():
    try:
        data = request.get_json()

        # Create user
        user_id = create_user(
            data["email"],
            data["first_name"],
            data["last_name"],
            data["password"],
            data.get("is_admin", False)
        )

        # Create calendar entry
        entry_id = create_calendar_entry(
            user_id,
            data["entry_type"],
            data["entry_date"]
        )

        # Add gambling entry (if needed)
        if data["entry_type"] in ["gambling", "both"]:
            g = data["gambling"]

            add_gambling_entry(
                user_id,
                entry_id,
                g.get("amount_spent", 0),
                g.get("amount_earned", 0),
                g.get("time_spent", ""),
                g.get("gambling_type", ""),
                g.get("emotion_before", ""),
                g.get("emotion_during", ""),
                g.get("emotion_after", "")
            )

        # Add alcohol entry (if needed)
        if data["entry_type"] in ["alcohol", "both"]:
            a = data["alcohol"]

            add_alcohol_entry(
                user_id,
                entry_id,
                a.get("money_spent", 0),
                a.get("num_drinks", 0),
                a.get("trigger", "")
            )

        return jsonify({"success": True})

    except ValueError as e:
        # Duplicate email error
        return jsonify({"success": False, "error": str(e)}), 400

    except Exception as e:
        print("Server Error:", e)
        return jsonify({"success": False, "error": "Server error"}), 500


# Run server
if __name__ == "__main__":
    app.run(debug=True, port=5001)
