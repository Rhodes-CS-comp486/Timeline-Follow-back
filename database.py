from tinydb import TinyDB, Query
from datetime import date
import os

os.makedirs("db", exist_ok=True)

db = TinyDB("db/db.json")

users_table = db.table("users")
calendar_table = db.table("calendar_entries")
gambling_table = db.table("gambling")
alcohol_table = db.table("alcohol")

def create_user(email, first_name, last_name, password, is_admin=False):
    User = Query()

    if users_table.search(User.email == email):
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

def create_calendar_entry(user_id, entry_type):
    entry_id = len(calendar_table) + 1

    calendar_table.insert({
        "entry_id": entry_id,
        "user_id": user_id,
        "entry_date": str(date.today()),
        "entry_type": entry_type
    })

    return entry_id

def add_gambling_entry(user_id, entry_id, amount_spent, amount_earned,
                       time_spent, gambling_type,
                       emotion_before, emotion_during, emotion_after):

    gambling_table.insert({
        "user_id": user_id,
        "entry_id": entry_id,
        "amount_spent": amount_spent,
        "amount_earned": amount_earned,
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "emotion_before": emotion_before,
        "emotion_during": emotion_during,
        "emotion_after": emotion_after
    })

def add_alcohol_entry(user_id, entry_id, money_spent, num_drinks, trigger):
    alcohol_table.insert({
        "user_id": user_id,
        "entry_id": entry_id,
        "money_spent": money_spent,
        "num_drinks": num_drinks,
        "trigger": trigger
    })
