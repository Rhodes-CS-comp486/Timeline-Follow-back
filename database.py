from tinydb import TinyDB, Query
import os

# Create db folder if missing
os.makedirs("db", exist_ok=True)

db = TinyDB("db/db.json")

# Tables
users_table = db.table("users")
calendar_table = db.table("calendar_entries")
gambling_table = db.table("gambling")
alcohol_table = db.table("alcohol")


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# Create User
def create_user(email, first_name, last_name, password, is_admin=False):
    User = Query()

    # Prevent duplicate email
    existing_user = users_table.search(User.email == email)
    if existing_user:
        raise ValueError("Email already exists")

    user_id = len(users_table) + 1

    users_table.insert({
        "user_id": user_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "is_admin": is_admin
    })

    return user_id


# Create Calendar Entry
def create_calendar_entry(user_id, entry_type, entry_date):
    entry_id = len(calendar_table) + 1

    calendar_table.insert({
        "entry_id": entry_id,
        "user_id": user_id,
        "entry_date": entry_date,
        "entry_type": entry_type
    })

    return entry_id


# Add Gambling Entry
def add_gambling_entry(
    user_id,
    entry_id,
    amount_spent,
    amount_earned,
    time_spent,
    gambling_type,
    money_intended,
    drinks_while_gambling
):

    gambling_table.insert({
        "user_id": user_id,
        "entry_id": entry_id,
        "amount_spent": _to_float(amount_spent),
        "amount_earned": _to_float(amount_earned),
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "money_intended": money_intended,
        "drinks_while_gambling": drinks_while_gambling
    })


# Add Alcohol Entry
def add_alcohol_entry(
    user_id,
    entry_id,
    money_spent,
    num_drinks,
    trigger
):

    alcohol_table.insert({
        "user_id": user_id,
        "entry_id": entry_id,
        "money_spent": _to_float(money_spent),
        "num_drinks": _to_int(num_drinks),
        "trigger": trigger
    })


# Retrieve calendar entries for a user (or all if not provided)
def get_calendar_entries(user_id=None):
    if user_id:
        return calendar_table.search(Query().user_id == user_id)
    return calendar_table.all()


# Retrieve the most recent calendar entry for a user/date/type
def get_latest_calendar_entry(user_id, entry_date, entry_type):
    Entry = Query()
    matches = calendar_table.search(
        (Entry.user_id == user_id) &
        (Entry.entry_date == entry_date) &
        (Entry.entry_type == entry_type)
    )
    if not matches:
        return None
    return max(matches, key=lambda item: item.get("entry_id", 0))


def get_alcohol_entry(entry_id):
    Entry = Query()
    return alcohol_table.get(Entry.entry_id == entry_id)


def get_gambling_entry(entry_id):
    Entry = Query()
    return gambling_table.get(Entry.entry_id == entry_id)


def update_alcohol_entry(entry_id, num_drinks, money_spent=None, trigger=None):
    Entry = Query()
    alcohol_table.update({
        "num_drinks": _to_int(num_drinks),
        "money_spent": _to_float(money_spent),
        "trigger": trigger
    }, Entry.entry_id == entry_id)


def update_gambling_entry(
    entry_id,
    amount_spent,
    amount_earned,
    time_spent,
    gambling_type,
    money_intended,
    drinks_while_gambling
):
    Entry = Query()
    gambling_table.update({
        "amount_spent": _to_float(amount_spent),
        "amount_earned": _to_float(amount_earned),
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "money_intended": money_intended,
        "drinks_while_gambling": drinks_while_gambling
    }, Entry.entry_id == entry_id)


def delete_calendar_entry(entry_id, entry_type):
    Entry = Query()
    if entry_type == "drinking":
        alcohol_table.remove(Entry.entry_id == entry_id)
    elif entry_type == "gambling":
        gambling_table.remove(Entry.entry_id == entry_id)
    calendar_table.remove(Entry.entry_id == entry_id)
