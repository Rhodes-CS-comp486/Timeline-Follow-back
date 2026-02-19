const mountApp = () => {
    // grab elements from HTML
    const app = document.getElementById('app');
    const baseTemplate = document.getElementById('base-layout');
    const pageTemplate = document.getElementById('calendar-page');

    // just a safety check to make sure nothing is missing
    if (!app || !baseTemplate) {
        return;
    }

    // clone template contents
    const baseFragment = baseTemplate.content.cloneNode(true);
    const pageFragment = pageTemplate ? pageTemplate.content.cloneNode(true) : null;

    // this is the slot replacement logic for the calendar
    if (pageFragment) {
        const pageSlots = new Map();
        pageFragment.querySelectorAll('[data-slot]').forEach((slot) => {
            pageSlots.set(slot.dataset.slot, slot);
        });

        baseFragment.querySelectorAll('[data-slot]').forEach((target) => {
            const name = target.dataset.slot;
            const source = pageSlots.get(name);
            if (source) {
                target.replaceChildren(...Array.from(source.childNodes));
            }
        });
    }

    app.replaceChildren(baseFragment);
};
// Returns a Map of ISO date strings to holiday names for a given year
const getUSHolidays = (year) => {
    const holidays = new Map();

    // Helper: get the Nth weekday of a month (weekday: 0=Sun, 1=Mon, ...)
    const nthWeekday = (y, month, weekday, n) => {
        const first = new Date(y, month, 1);
        let day = 1 + ((weekday - first.getDay() + 7) % 7);
        day += (n - 1) * 7;
        return new Date(y, month, day);
    };

    // Helper: get the last weekday of a month
    const lastWeekday = (y, month, weekday) => {
        const last = new Date(y, month + 1, 0); // last day of month
        let day = last.getDate() - ((last.getDay() - weekday + 7) % 7);
        return new Date(y, month, day);
    };

    const toISO = (d) => {
        const yy = d.getFullYear();
        const mm = String(d.getMonth() + 1).padStart(2, '0');
        const dd = String(d.getDate()).padStart(2, '0');
        return `${yy}-${mm}-${dd}`;
    };

    // Fixed-date holidays
    holidays.set(`${year}-01-01`, "New Year's Day");
    holidays.set(`${year}-06-19`, 'Juneteenth');
    holidays.set(`${year}-07-04`, 'Independence Day');
    holidays.set(`${year}-11-11`, "Veterans Day");
    holidays.set(`${year}-12-25`, 'Christmas Day');

    // Floating holidays
    holidays.set(toISO(nthWeekday(year, 0, 1, 3)), 'MLK Day');
    holidays.set(toISO(nthWeekday(year, 1, 1, 3)), "Presidents' Day");
    holidays.set(toISO(lastWeekday(year, 4, 1)), 'Memorial Day');
    holidays.set(toISO(nthWeekday(year, 8, 1, 1)), 'Labor Day');
    holidays.set(toISO(nthWeekday(year, 9, 1, 2)), 'Columbus Day');
    holidays.set(toISO(nthWeekday(year, 10, 4, 4)), 'Thanksgiving');

    return holidays;
};

// initialise the calendar to create and control the dates
const initCalendar = () => {
    // define today at midnight
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // for current date/month/year
    const state = {
        viewYear: today.getFullYear(),
        viewMonth: today.getMonth(),
        selectedISO: null,
    };

    const monthLabel = document.getElementById('monthLabel');
    const grid = document.getElementById('calendarGrid');
    const prevBtn = document.getElementById('prevMonth');
    const nextBtn = document.getElementById('nextMonth');
    const selectedLabel = document.getElementById('selectedDateLabel');
    const entrySummary = document.getElementById('entrySummary');

    // In-memory store for saved entries (keyed by ISO date)
    const entries = {};

    // Fetch calendar events from the backend and populate entries
    // Fetch calendar events from the backend and populate entries
fetch('/api/calendar-events')
    .then(response => response.json())
    .then(events => {
        events.forEach(event => {
            const dateKey = event.date; // already YYYY-MM-DD

            if (!entries[dateKey]) {
                entries[dateKey] = [];
            }

            entries[dateKey].push(event);
        });

        console.log("Events loaded from database:", entries);
        console.log("Total events:", Object.keys(entries).length);
    })
    .catch(error => {
        console.error("Error fetching calendar events:", error);
    });


    // Popup Window Elements
    const modal = document.getElementById('eventModal');
    const modalTitle = document.getElementById('modalDateTitle');
    const closeModalBtn = document.getElementById('closeModal');
    const activityForm = document.getElementById('activityForm');

    // Toggling Elements
    const chkDrinking = document.getElementById('chkDrinking');
    const chkGambling = document.getElementById('chkGambling');
    const drinkingSection = document.getElementById('drinkingSection');
    const gamblingSection = document.getElementById('gamblingSection');

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel) {
        return;
    }

    const toggleSection = (checkbox, section) => {
        if (!checkbox || !section) return;

        // Find every input inside this specific div
        const inputs = section.querySelectorAll('input, select, textarea');

        if (checkbox.checked) {
            section.classList.remove('section-disabled'); // Removes the grey-out CSS
            inputs.forEach(input => input.disabled = false); // Allows typing
        }
        else {
            section.classList.add('section-disabled');    // Adds the grey-out CSS
            inputs.forEach(input => input.disabled = true);  // Prevents typing
        }
    };
    const resetFormState = () => {
        if (activityForm) activityForm.reset();
        // Force the sections back to their "locked" state
        toggleSection(chkDrinking, drinkingSection);
        toggleSection(chkGambling, gamblingSection);
    };

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ];

    const toISO = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const formatReadable = (date) => date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    const setView = (year, month) => {
        const target = new Date(year, month, 1);
        state.viewYear = target.getFullYear();
        state.viewMonth = target.getMonth();
        render();
    };

    const changeMonth = (delta) => {
        setView(state.viewYear, state.viewMonth + delta);
    };

    const renderSidebar = () => {
        if (!entrySummary) return;

        if (!state.selectedISO || !entries[state.selectedISO]) {
            entrySummary.innerHTML = '<p class="entry-empty">Select a date to view its entry.</p>';
            return;
        }

        const entry = entries[state.selectedISO];
        let html = '';

        if (entry.drinks) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Drinking</div>';
            html += `<div class="entry-row"><span class="entry-label">Drinks:</span> ${entry.drinks}</div>`;
            if (entry.drinks_cost) html += `<div class="entry-row"><span class="entry-label">Cost:</span> ${entry.drinks_cost}</div>`;
            if (entry.drink_trigger) html += `<div class="entry-row"><span class="entry-label">Trigger:</span> ${entry.drink_trigger}</div>`;
            html += '</div>';
        }

        if (entry.gambling_type) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Gambling</div>';
            html += `<div class="entry-row"><span class="entry-label">Type:</span> ${entry.gambling_type}</div>`;
            if (entry.time_spent) html += `<div class="entry-row"><span class="entry-label">Time Spent:</span> ${entry.time_spent}</div>`;
            if (entry.money_intended) html += `<div class="entry-row"><span class="entry-label">Intended to Wager:</span> ${entry.money_intended}</div>`;
            if (entry.money_spent) html += `<div class="entry-row"><span class="entry-label">Actually Wagered:</span> ${entry.money_spent}</div>`;
            if (entry.money_earned) html += `<div class="entry-row"><span class="entry-label">Won/Lost:</span> ${entry.money_earned}</div>`;
            if (entry.drinks_while_gambling) html += `<div class="entry-row"><span class="entry-label">Drinks While Gambling:</span> ${entry.drinks_while_gambling}</div>`;
            html += '</div>';
        }

        if (!html) {
            entrySummary.innerHTML = '<p class="entry-empty">No activity logged for this date.</p>';
        } else {
            entrySummary.innerHTML = html;
        }
    };

    const renderGrid = () => {
        grid.innerHTML = '';

        const firstOfMonth = new Date(state.viewYear, state.viewMonth, 1);
        const startDay = firstOfMonth.getDay();
        const daysInMonth = new Date(state.viewYear, state.viewMonth + 1, 0).getDate();
        const holidays = getUSHolidays(state.viewYear);

        // Add empty placeholders for days before the 1st
        for (let i = 0; i < startDay; i += 1) {
            const placeholder = document.createElement('div');
            placeholder.className = 'day day--empty';
            grid.appendChild(placeholder);
        }

        // Only render days that belong to this month
        for (let day = 1; day <= daysInMonth; day += 1) {
            const cellDate = new Date(state.viewYear, state.viewMonth, day);
            cellDate.setHours(0, 0, 0, 0);

            const iso = toISO(cellDate);
            const isToday = cellDate.getTime() === today.getTime();
            const isFuture = cellDate.getTime() > today.getTime();
            const isSelected = state.selectedISO === iso;
            const holidayName = holidays.get(iso);

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'day';
            button.dataset.iso = iso;
            button.setAttribute('aria-label', formatReadable(cellDate));

            // Day number
            const dayNumber = document.createElement('span');
            dayNumber.className = 'day-number';
            dayNumber.textContent = day;
            button.appendChild(dayNumber);

            // Holiday label
            if (holidayName) {
                button.classList.add('day--holiday');
                const label = document.createElement('span');
                label.className = 'holiday-label';
                label.textContent = holidayName;
                button.appendChild(label);
            }

            // Show X indicators for no-drinking / no-gambling entries
            const entry = entries[iso];
            if (entry) {
                button.classList.add('day--holiday');
                if (entry.no_drinking) {
                    const redX = document.createElement('span');
                    redX.className = 'no-drink-x';
                    redX.textContent = 'X';
                    button.appendChild(redX);
                }
                if (entry.no_gambling) {
                    const blueX = document.createElement('span');
                    blueX.className = 'no-gamble-x';
                    blueX.textContent = 'X';
                    button.appendChild(blueX);
                }
            }

            if (isToday) button.classList.add('day--today');
            if (isFuture) {
                button.classList.add('day--future');
                button.disabled = true;
            }
            if (isSelected) button.classList.add('day--selected');

            if (!isFuture) {
                button.addEventListener('click', () => {
                    // Toggle selection: clicking the same date unselects it
                    if (state.selectedISO === iso) {
                        state.selectedISO = null;
                        selectedLabel.textContent = 'Pick a day';
                        renderSidebar();
                        renderGrid();
                        return;
                    }

                    state.selectedISO = iso;
                    selectedLabel.textContent = formatReadable(cellDate);
                    renderSidebar();

                    // Added: Open the Modal when a valid day is clicked
                    if (modal && modalTitle) {
                        modalTitle.textContent = `Log Activity for ${iso}`;
                        resetFormState()
                        modal.style.display = 'flex';
                        modal.scrollTop = 0;
                        const content = modal.querySelector('.modal-content');
                        if (content) content.scrollTop = 0;
                    }

                    renderGrid();
                });
            }

            grid.appendChild(button);
        }
    };

    const render = () => {
        monthLabel.textContent = `${monthNames[state.viewMonth]} ${state.viewYear}`;
        const isCurrentMonth = state.viewYear === today.getFullYear() &&
            state.viewMonth === today.getMonth();
        nextBtn.disabled = isCurrentMonth;
        nextBtn.classList.toggle('is-disabled', isCurrentMonth);
        renderGrid();
        renderSidebar();
    };

    /*
        Everything related to event listeners
     */

    // Added: Event listener to close the popup window
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    // Close modal when clicking outside the form
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
    }

    // Listen for clicks on the Drinking checkbox
    if (chkDrinking) {
        chkDrinking.addEventListener('change', () => toggleSection(chkDrinking, drinkingSection));
    }
    // Listen for clicks on the Gambling checkbox
    if (chkGambling) {
        chkGambling.addEventListener('change', () => toggleSection(chkGambling, gamblingSection));
    }
    // Added: Event listener for the Activity Form submission
    // Handle saving the event
    if (activityForm) {
    activityForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!state.selectedISO) return;

        const payload = {
            date: state.selectedISO
        };


        if (!chkDrinking.checked && !chkGambling.checked) {
            alert("Please select drinking and/or gambling.");
            return;
        }

        // Store flags instead of forcing single type
        payload.drinking_logged = chkDrinking.checked;
        payload.gambling_logged = chkGambling.checked;


        // Collect ALL enabled inputs dynamically
        const enabledInputs = activityForm.querySelectorAll(
            'input:not([disabled]), select:not([disabled]), textarea:not([disabled])'
        );

        enabledInputs.forEach(input => {
            if (!input.name) return; // Skip inputs without name attribute
            payload[input.name] = input.value;
        });

        // Store locally for sidebar display
        if (!entries[state.selectedISO]) {
            entries[state.selectedISO] = {};
        }

        Object.assign(entries[state.selectedISO], payload);

        if (modal) modal.style.display = 'none';

        resetFormState();
        renderSidebar();
        renderGrid();

        try {
            const response = await fetch('/api/log-activity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                console.warn('Server did not save the entry.');
            }
        } catch (error) {
            console.error('Error saving data:', error);
        }
    });
}


    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    render();
    resetFormState()
};

mountApp();
initCalendar();