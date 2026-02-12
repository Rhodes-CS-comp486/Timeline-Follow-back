from database.db_initialization import User, Gambling, Drinking, db, CalendarEntry


def create_user(email, first_name, last_name, password, username, is_admin=False):
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

def create_calendar_entry(user_id, entry_type, entry_date):
    new_entry = CalendarEntry(
        user_id=user_id,
        entry_type=entry_type,
        entry_date=entry_date
    )
    return commit_to_db(new_entry)

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
    # Ensure entry_id is an int, not an object
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    # Create a dictionary "aka JSON"
    gambling_json_content = {
        "user_id": user_id,  # Redundant consider removing
        "entry_id": entry_id,
        "amount_spent": float(amount_spent),
        "amount_earned": float(amount_earned),
        "time_spent": time_spent,
        "gambling_type": gambling_type,
        "emotion_before": emotion_before,
        "emotion_during": emotion_during,
        "emotion_after": emotion_after
    }

    new_gambling_entry = Gambling(
        user_id=user_id,
        entry_id=entry_id,
        id=entry_id,
        gambling_questions=gambling_json_content
    )

    return commit_to_db(new_gambling_entry)

def add_alcohol_entry(
    user_id,
    entry_id,
    money_spent,
    num_drinks,
    trigger
):
    # Ensure entry_id is an int, not an object
    if hasattr(entry_id, 'id'):
        entry_id = entry_id.id

    drinking_json_content = {
        "user_id": user_id,
        "entry_id": entry_id,
        "money_spent": float(money_spent),
        "num_drinks": int(num_drinks),
        "trigger": trigger
    }

    new_alcohol_entry = Drinking(user_id=user_id,
                                 id=entry_id,
                                 entry_id=entry_id,
                                 drinking_questions=drinking_json_content)

    return commit_to_db(new_alcohol_entry)


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