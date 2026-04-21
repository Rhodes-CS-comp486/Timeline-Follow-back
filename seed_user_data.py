"""
Seed script: populates 3 months of daily gambling + drinking data
for the user with username m@gmail.com.

Run from the project root:
    python seed_user_data.py
"""

import random
from datetime import datetime, timedelta

from app import app
from database.db_initialization import CalendarEntry, Drinking, Gambling, User, db

# ── reproducible randomness ──────────────────────────────────────────────────
random.seed(42)

# ── date range ───────────────────────────────────────────────────────────────
END_DATE   = datetime(2026, 3, 24)          # today
START_DATE = END_DATE - timedelta(days=91)  # ~3 months back

GAMBLING_TYPES = [
    "Slot Machines",
    "Table Games",
    "Sports/Event Betting",
    "Lottery/Draw Games",
    "Online Gambling",
    "Other",
]

# ── helpers ──────────────────────────────────────────────────────────────────

def days_in_range(start, end):
    """Yield each date from start up to and including end."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def make_gambling_questions(day_index, gamble_heavily):
    """
    Return a realistic gambling_questions dict.
    ~half the sessions go over the intended amount (varied by day_index parity).
    """
    g_type   = random.choice(GAMBLING_TYPES)
    time_hrs = round(random.uniform(0.5, 4.5), 1)
    intended = round(random.uniform(50, 600), 2)

    # ~49 % of sessions: wagered MORE than intended
    if random.random() < 0.49:
        wagered = round(intended * random.uniform(1.1, 2.5), 2)
    else:
        wagered = round(intended * random.uniform(0.3, 0.99), 2)

    # win/loss: usually negative (net loss)
    earned = round(random.uniform(-wagered * 0.9, wagered * 0.3), 2)

    drinks_while = random.randint(0, 5) if gamble_heavily else random.randint(0, 2)

    return {
        "gambling_type":       g_type,
        "time_spent":          time_hrs,
        "money_intended":      intended,
        "money_spent":         wagered,
        "money_earned":        earned,
        "drinks_while_gambling": drinks_while,
    }


def make_drinking_questions(heavy_day):
    num = random.randint(4, 10) if heavy_day else random.randint(1, 4)
    return {"num_drinks": num}


# ── weekday / weekend helpers ────────────────────────────────────────────────

def is_weekend(dt):
    return dt.weekday() >= 4  # Fri, Sat, Sun


def gamble_today(dt):
    """~60 % chance on weekends, ~35 % on weekdays → ~45 days across 91."""
    return random.random() < (0.60 if is_weekend(dt) else 0.35)


def drink_today(dt):
    """~85 % chance on weekends, ~60 % on weekdays."""
    return random.random() < (0.85 if is_weekend(dt) else 0.60)


# ── main ─────────────────────────────────────────────────────────────────────

def seed():
    with app.app_context():
        user = User.query.filter_by(username="m@gmail.com").first()
        if not user:
            print("ERROR: No user found with username m@gmail.com")
            return

        print(f"Seeding data for: {user.first_name} {user.last_name} (id={user.id})")

        # Remove any existing entries in this date window so we can re-run safely
        existing = (
            CalendarEntry.query
            .filter(
                CalendarEntry.user_id == user.id,
                CalendarEntry.entry_date >= START_DATE,
                CalendarEntry.entry_date <= END_DATE,
            )
            .all()
        )
        for entry in existing:
            Drinking.query.filter_by(entry_id=entry.id).delete()
            Gambling.query.filter_by(entry_id=entry.id).delete()
            db.session.delete(entry)
        db.session.commit()
        print(f"Cleared {len(existing)} existing entries in window.")

        total_gambling = 0
        total_drinking = 0

        for day in days_in_range(START_DATE, END_DATE):
            heavy = is_weekend(day)
            will_gamble = gamble_today(day)
            will_drink  = drink_today(day)

            # Every day has at least drinking logged
            if not will_drink:
                will_drink = True

            # Determine entry_type label
            if will_gamble and will_drink:
                entry_type = "gambling"   # calendar colours by gambling if both
            elif will_gamble:
                entry_type = "gambling"
            else:
                entry_type = "drinking"

            entry = CalendarEntry(
                user_id    = user.id,
                entry_date = day.replace(hour=12, minute=0, second=0, microsecond=0),
                entry_type = entry_type,
            )
            db.session.add(entry)
            db.session.flush()  # get entry.id

            if will_gambling := will_gamble:
                g_q = make_gambling_questions(total_gambling, heavy)
                db.session.add(Gambling(
                    entry_id          = entry.id,
                    user_id           = user.id,
                    gambling_questions = g_q,
                ))
                total_gambling += 1

            if will_drink:
                d_q = make_drinking_questions(heavy)
                db.session.add(Drinking(
                    entry_id           = entry.id,
                    user_id            = user.id,
                    drinking_questions = d_q,
                ))
                total_drinking += 1

        db.session.commit()

        # ── summary ──────────────────────────────────────────────────────────
        g_entries = (
            db.session.query(Gambling)
            .join(CalendarEntry, Gambling.entry_id == CalendarEntry.id)
            .filter(
                Gambling.user_id == user.id,
                CalendarEntry.entry_date >= START_DATE,
            )
            .all()
        )
        total_intended = sum(
            float(e.gambling_questions.get("money_intended", 0) or 0)
            for e in g_entries
        )
        total_wagered = sum(
            float(e.gambling_questions.get("money_spent", 0) or 0)
            for e in g_entries
        )
        over_intent = sum(
            1 for e in g_entries
            if float(e.gambling_questions.get("money_spent", 0) or 0)
            >  float(e.gambling_questions.get("money_intended", 0) or 0)
        )

        print(f"\nDone!")
        print(f"  Drinking entries:  {total_drinking}")
        print(f"  Gambling entries:  {total_gambling}")
        print(f"  Total intended:   ${total_intended:,.2f}")
        print(f"  Total wagered:    ${total_wagered:,.2f}")
        print(f"  Over-intent days:  {over_intent} / {total_gambling}")


if __name__ == "__main__":
    seed()
