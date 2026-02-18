import datetime

from database.db_initialization import User, Gambling, Drinking, db, CalendarEntry
"""
    NOTE USING THESE HELPER FUNCTIONS COMMITS THE ENTRIES TO THE DB !!!
    If we want, we can commit later using the commit_to_db() function but this may cause sync issues
"""

# This function creates a user in the db and commits it
# Parameters: email, first_name, last_name, username (maybe), password (maybe) -> str
#             is_admin -> bool
# Returns: entry if valid, error if failure
def create_user(email : str, first_name : str, last_name : str, password, username, is_admin=False):
    # Create a user
    new_user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password,
        username=username,
        is_admin=is_admin
    )

    # Add and Commit to Postgres
    return commit_to_db(new_user)

# This function creates a calendar entry in the database and returns the entry object (or its ID)
# Parameters: user_id    -> int (Foreign Key from the User table)
#             entry_type -> str (e.g., 'drinking' or 'gambling')
#             entry_date -> datetime/str (The date of the activity)
# Returns: The entry object if commit is successful, False or None if it fails
def create_calendar_entry(user_id : int, entry_type : str, entry_date):
    new_entry = CalendarEntry(
        user_id=user_id,
        entry_type=entry_type,
        entry_date=entry_date
    )
    return commit_to_db(new_entry)

# This function creates a gambling entry in the database and commits it
# Parameters: user_id         -> int (Foreign Key from User table)
#             entry_id        -> int/obj (Foreign Key from CalendarEntry)
#             amount_spent    -> float
#             amount_earned   -> float
#             time_spent      -> str
#             gambling_type   -> str
#             num_drinks      -> int
#             amount_intended_spent -> float
# Returns: The entry object if valid, None if failure
def add_gambling_entry(
    user_id : int,
    entry_id :int,
    amount_intended_spent: float,
    amount_spent : float,
    amount_earned : float,
    time_spent :str,
    gambling_type : str,
    num_drinks : int
):
    # Ensure entry_id is an int, not an object
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    # Create a dictionary aka JSON file
    gambling_json_content = {
        "user_id": user_id,  # Redundant consider removing
        "entry_id": entry_id,
        "amount_spent": float(amount_spent),
        "amount_earned": float(amount_earned),
        "amount_intended_spent": float(amount_intended_spent),
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "num_drinks": int(num_drinks),
    }

    new_gambling_entry = Gambling(
        user_id=user_id,
        entry_id=entry_id,
        gambling_questions=gambling_json_content
    )

    return commit_to_db(new_gambling_entry)

# This function creates a drinking entry in the database and commits it
# Parameters: user_id     -> int (Foreign Key from User table)
#             entry_id    -> int/obj (Foreign Key from CalendarEntry)
#             num_drinks  -> int
# Returns: The entry object if valid, None if failure
def add_alcohol_entry(
    user_id : int,
    entry_id: int,
    num_drinks : int,
):
    # Ensure entry_id is an int, not an object
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    drinking_json_content = {
        "user_id": user_id,
        "entry_id": entry_id,
        "num_drinks": int(num_drinks),
    }

    new_alcohol_entry = Drinking(user_id=user_id,
                                 entry_id=entry_id,
                                 drinking_questions=drinking_json_content)

    return commit_to_db(new_alcohol_entry)

# This function retrieves all calendar entries for a specific user from the database
# Parameters: user_id -> int (Foreign Key from User table)
# Returns: List of CalendarEntry objects ordered by date, or empty list if none found
# Used by: events_handler.py's get_calendar_events() to fetch entries for display on calendar
def get_calendar_entries_for_user(user_id: int):
    return CalendarEntry.query.filter_by(user_id=user_id).order_by(
        CalendarEntry.entry_date
    ).all()

# This function adds any object to the session and commits it to Postgres
# Parameters: new_entry -> db.Model object (User, CalendarEntry, Gambling, etc.)
# Returns: The committed object if successful, None if failure
def commit_to_db(new_entry):
    # Add and Commit to Postgres
    try:
        db.session.add(new_entry)
        db.session.commit()
        print(f"Successfully commited {new_entry} to database")
        return new_entry
    # This super cool rollback makes sure nothing is commited if this goes wrong
    except Exception as e:
        db.session.rollback()
        print(f"Error creating user: {e}")
        return None
