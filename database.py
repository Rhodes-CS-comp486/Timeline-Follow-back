import json
import os
from datetime import date

DB_PATH = "db"

# ---------- FILE HANDLING ----------
def load_table(filename):
    with open(os.path.join(DB_PATH, filename), "r") as f:
        return json.load(f)

def save_table(filename, data):
    with open(os.path.join(DB_PATH, filename), "w") as f:
        json.dump(data, f, indent=4)

def get_next_id(records, key):
    if not records:
        return 1
    return max(r[key] for r in records) + 1

# ---------- USERS ----------
def create_user(email, first_name, last_name, password, is_admin=False):
    users = load_table("users.json")

    if any(u["email"] == email for u in users):
        raise ValueError("Email already exists")

    user_id = get_next_id(users, "user_id")

    user = {
        "user_id": user_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
        "is_admin": is_admin
    }

    users.append(user)
    save_table("users.json", users)
    return user

# ---------- CALENDAR ----------
def create_calendar_entry(user_id, entry_type):
    entries = load_table("calendar_entries.json")

    entry_id = get_next_id(entries, "entry_id")

    entry = {
        "entry_id": entry_id,
        "user_id": user_id,
        "entry_date": str(date.today()),
        "entry_type": entry_type
    }

    entries.append(entry)
    save_table("calendar_entries.json", entries)
    return entry

# ---------- ALCOHOL ----------
def add_alcohol_entry(user_id, entry_id, money_spent, num_drinks, trigger):
    alcohol = load_table("alcohol.json")

    record = {
        "user_id": user_id,
        "entry_id": entry_id,
        "money_spent": money_spent,
        "num_drinks": num_drinks,
        "trigger": trigger
    }

    alcohol.append(record)
    save_table("alcohol.json", alcohol)
    return record

# ---------- GAMBLING ----------
def add_gambling_entry(user_id, entry_id, amount_spent, amount_earned,
                       time_spent, gambling_type,
                       emotion_before, emotion_during, emotion_after):

    gambling = load_table("gambling.json")

    record = {
        "user_id": user_id,
        "entry_id": entry_id,
        "amount_spent": amount_spent,
        "amount_earned": amount_earned,
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "emotion_before": emotion_before,
        "emotion_during": emotion_during,
        "emotion_after": emotion_after
    }

    gambling.append(record)
    save_table("gambling.json", gambling)
    return record
