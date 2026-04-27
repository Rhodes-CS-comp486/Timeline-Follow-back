import datetime

from database.db_initialization import User, Gambling, Drinking, db, CalendarEntry
"""
    NOTE USING THESE HELPER FUNCTIONS COMMITS THE ENTRIES TO THE DB !!!
    If we want, we can commit later using the commit_to_db() function but this may cause sync issues
"""

# This function creates a user in the db and commits it
# Parameters: username, first_name, last_name, password (maybe) -> str
#             is_admin -> bool
# Returns: entry if valid, error if failure
def create_user(username: str, password, is_admin=False, study_group_code=None):
    # Create a user
    new_user = User(
        username=username,
        password=password,
        is_admin=is_admin,
        study_group_code=study_group_code,
    )

    # Add and Commit to Postgres
    return commit_to_db(new_user)

# This function creates a calendar entry in the database and returns the entry object (or its ID)
# Parameters: user_id    -> int (Foreign Key from the User table)
#             entry_date -> datetime/str (The date of the activity)
# Returns: The entry object if commit is successful, False or None if it fails
def create_calendar_entry(user_id : int, entry_date):
    new_entry = CalendarEntry(
        user_id=user_id,
        entry_date=entry_date
    )
    return commit_to_db(new_entry)

# This function creates a gambling entry in the database and commits it
# Parameters: user_id         -> int (Foreign Key from User table)
#             entry_id        -> int/obj (Foreign Key from CalendarEntry)
#             activity_data   -> JSON file
# Returns: The entry object if valid, None if failure
def add_gambling_entry(
    user_id: int,
    entry_id: int,
    activity_data: dict
):
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    new_gambling_entry = Gambling(
        user_id=user_id,
        entry_id=entry_id,
        gambling_questions=activity_data
    )

    return commit_to_db(new_gambling_entry)

# This function creates a personal expense in the database and commits it
# Parameters: user_id     -> int (Foreign Key from User table)
#             activity_data  -> JSON
# Returns: The entry object if valid, None if failure
def add_personal_expense_entry(
    user_id: int,
    activity_data: dict
):

    new_personal_expense_entry = PersonalExpense(
        user_id=user_id,
        drinking_questions=activity_data
    )

    return commit_to_db(new_personal_expense_entry)

# This function creates a drinking entry in the database and commits it
# Parameters: user_id     -> int (Foreign Key from User table)
#             entry_id    -> int/obj (Foreign Key from CalendarEntry)
#             activity_data  -> JSON
# Returns: The entry object if valid, None if failure
def add_alcohol_entry(
    user_id: int,
    entry_id: int,
    activity_data: dict
):
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    new_alcohol_entry = Drinking(
        user_id=user_id,
        entry_id=entry_id,
        drinking_questions=activity_data
    )

    return commit_to_db(new_alcohol_entry)

# This function retrieves all calendar entries for a specific user from the database
# Parameters: user_id -> int (Foreign Key from User table)
# Returns: List of CalendarEntry objects ordered by date, or empty list if none found
# Used by: events_handler.py's get_calendar_events() to fetch entries for display on calendar
def get_calendar_entries_for_user(user_id: int):
    return CalendarEntry.query.filter_by(user_id=user_id).order_by(
        CalendarEntry.entry_date
    ).all()

# This function aggregates gambling data across users for the admin report
# Parameters: start_date -> str (optional), end_date -> str (optional), user_id -> int (optional)
# Returns: dict of aggregated values
def get_gambling_aggregates(start_date=None, end_date=None, user_id=None, user_ids=None, schema=None):
    from database.db_initialization import Gambling, Drinking, CalendarEntry
    from datetime import datetime
    from config.config_helper import field_map_from_schema
    fm = field_map_from_schema(schema)

    # --- Gambling aggregates ---
    gambling_query = db.session.query(Gambling, CalendarEntry).join(
        CalendarEntry, Gambling.entry_id == CalendarEntry.id
    )

    if user_id:
        gambling_query = gambling_query.filter(Gambling.user_id == user_id)
    elif user_ids is not None:
        gambling_query = gambling_query.filter(Gambling.user_id.in_(user_ids))
    if start_date:
        gambling_query = gambling_query.filter(CalendarEntry.entry_date >= datetime.fromisoformat(start_date).date())
    if end_date:
        gambling_query = gambling_query.filter(CalendarEntry.entry_date <= datetime.fromisoformat(end_date).date())

    gambling_results = gambling_query.all()

    day_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = {day: 0.0 for day in day_labels}

    total_intended = 0.0
    total_spent = 0.0
    total_hours = 0.0
    gambling_user_ids = set()

    for gambling, calendar_entry in gambling_results:
        questions = gambling.gambling_questions or {}
        gambling_user_ids.add(gambling.user_id)

        try:
            total_intended += float(questions.get(fm['money_intended']) or 0)
        except (ValueError, TypeError):
            pass

        try:
            total_spent += float(questions.get(fm['money_spent']) or 0)
        except (ValueError, TypeError):
            pass

        try:
            total_hours += float(questions.get(fm['time_spent']) or 0)
        except (ValueError, TypeError):
            pass

        try:
            day_name = calendar_entry.entry_date.strftime("%A")
            by_day[day_name] += float(questions.get(fm['money_spent']) or 0)
        except (ValueError, TypeError):
            pass

    # --- Drinking aggregates ---
    drinking_query = db.session.query(Drinking, CalendarEntry).join(
        CalendarEntry, Drinking.entry_id == CalendarEntry.id
    )

    if user_id:
        drinking_query = drinking_query.filter(Drinking.user_id == user_id)
    elif user_ids is not None:
        drinking_query = drinking_query.filter(Drinking.user_id.in_(user_ids))
    if start_date:
        drinking_query = drinking_query.filter(CalendarEntry.entry_date >= datetime.fromisoformat(start_date).date())
    if end_date:
        drinking_query = drinking_query.filter(CalendarEntry.entry_date <= datetime.fromisoformat(end_date).date())

    drinking_results = drinking_query.all()

    total_drinks = 0.0
    drinking_user_ids = set()

    for drinking, calendar_entry in drinking_results:
        questions = drinking.drinking_questions or {}
        drinking_user_ids.add(drinking.user_id)

        try:
            total_drinks += float(questions.get(fm['num_drinks']) or 0)
        except (ValueError, TypeError):
            pass

    all_user_ids = gambling_user_ids | drinking_user_ids

    return {
        "user_count": len(all_user_ids),
        "total_intended": round(total_intended, 2),
        "total_spent": round(total_spent, 2),
        "total_hours": round(total_hours, 2),
        "by_day": {day: round(by_day[day], 2) for day in day_labels},
        "total_drinks": round(total_drinks, 2),
    }

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
