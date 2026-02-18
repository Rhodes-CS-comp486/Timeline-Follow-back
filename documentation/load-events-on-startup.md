# Load Events on Startup Documentation

*Documentation generated with assistance from Claude AI*

---

## What This Does

When you load the calendar page, it automatically fetches all your saved entries from the database and displays them. Basically, your data persists now - refreshing the page won't make your entries disappear.

## What I Added

### 1. Database Helper (`db_helper.py`)

Added `get_calendar_entries_for_user(user_id)` - grabs all calendar entries for a user, ordered by date.

### 2. API Endpoint (`events_handler.py`)

**Route:** `GET /api/calendar-events`

Returns a JSON array with full entry details:
- Basic info: `id`, `date`, `type`
- Drinking entries include: `drinks`
- Gambling entries include: `gambling_type`, `time_spent`, `money_intended`, `money_spent`, `money_earned`, `drinks_while_gambling`

It queries the CalendarEntry table, then fetches the related Drinking or Gambling data and merges it all together.

### 3. Frontend Fetch (`app.js`)

Added a fetch call right after `const entries = {}` in `initCalendar()`:

```javascript
fetch('/api/calendar-events')
  .then(response => response.json())
  .then(events => {
    events.forEach(event => {
      const dateKey = event.date.split('T')[0];
      entries[dateKey] = event;
    });
    console.log("Events loaded from database:", entries);
  })
```

This populates the `entries` object with database data on page load. The rest of the existing code uses this data automatically.

## Testing

1. Open DevTools Console (F12)
2. Load the calendar page
3. You should see "Events loaded from database: {object}"
4. Click a date with an entry - sidebar should show the details
5. Refresh - entries still there

## Bonus Fix

Also fixed the gambling save bug - it was choking on dollar signs in the money fields. Added `.replace('$', '')` to strip them out before converting to floats.

## What This Doesn't Do

- No visual markers on the calendar yet (that's a different user story)
- Only loads on page refresh, not in real-time
- Falls back to user_id=1 if no session (for dev purposes)
