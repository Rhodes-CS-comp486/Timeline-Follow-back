from database import *

# Create user
user = create_user("megan@email.com", "Megan", "Bass", "1234")

# Create calendar entry
entry = create_calendar_entry(user["user_id"], "both")

# Add gambling data
add_gambling_entry(
    user["user_id"], entry["entry_id"],
    100, 20, "3 hours", "slots",
    "stressed", "excited", "guilty"
)

# Add alcohol data
add_alcohol_entry(
    user["user_id"], entry["entry_id"],
    25, 4, "friends"
)
