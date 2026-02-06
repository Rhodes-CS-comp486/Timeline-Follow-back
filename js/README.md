# app.js Overview

This file wires the calendar page UI together and handles the month grid behavior.

## What it does

- Mounts the base calendar template into the `#app` container.
- Builds a month grid (6 rows x 7 columns = 42 cells) so weeks always align.
- Shows the current month by default.
- Enables navigation with previous/next month arrows.
- Disables future dates and prevents clicking them.
- Highlights today and the currently selected day.
- Updates the “Selected Day” label when a day is clicked.
- Renders the “Quick Jump” list for the past 3 months.

## Main functions

- `mountApp()`
  - Clones the `template#base-layout` in `calendar.html` and injects it into `#app`.
  - If `template#calendar-page` contains slot content, it inserts it into matching `data-slot` areas.

- `initCalendar()`
  - Sets up calendar state (month/year/selected date).
  - Finds required DOM elements (`#monthLabel`, `#calendarGrid`, navigation buttons).
  - Defines helper functions (`toISO`, `formatReadable`).
  - Renders the calendar and wires up click handlers.

- `render()` (inside `initCalendar`)
  - Updates the month label.
  - Enables/disables the “next” button when the view reaches the current month.
  - Calls `renderGrid()` and `renderQuickJump()`.

- `renderGrid()` (inside `initCalendar`)
  - Builds the 42-day grid for the current view.
  - Marks days as muted (outside the month), today, selected, or future.
  - Adds click handlers for selectable days.

- `renderQuickJump()` (inside `initCalendar`)
  - Creates buttons for the current month and the previous 2 months.
  - Clicking a month button jumps the view.

## Where it is used

- Loaded by `calendar.html` using `<script src="js/app.js"></script>`.
- Only applies on the calendar page. The home page (`index.html`) does not use it.
