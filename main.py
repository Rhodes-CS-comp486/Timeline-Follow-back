from database import *

# Create user
user_id = create_user("megan@email.com", "Megan", "Bass", "1234")

# Create entry
entry_id = create_calendar_entry(user_id, "both")

# Add gambling details
add_gambling_entry(user_id, entry_id, 100, 20, "2 hours", "slots",
                   "stressed", "excited", "regret")

# Add alcohol details
add_alcohol_entry(user_id, entry_id, 30, 4, "friends")
