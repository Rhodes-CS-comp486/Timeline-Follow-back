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
    emotion_before,
    emotion_during,
    emotion_after
):

    gambling_table.insert({
        "user_id": user_id,
        "entry_id": entry_id,
        "amount_spent": float(amount_spent),
        "amount_earned": float(amount_earned),
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "emotion_before": emotion_before,
        "emotion_during": emotion_during,
        "emotion_after": emotion_after
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
        "money_spent": float(money_spent),
        "num_drinks": int(num_drinks),
        "trigger": trigger
    })
