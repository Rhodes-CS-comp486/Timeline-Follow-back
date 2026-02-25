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

    // Popup Window Elements
    const modal = document.getElementById('eventModal');
    const modalTitle = document.getElementById('modalDateTitle');
    const closeModalBtn = document.getElementById('closeModal');
    const activityForm = document.getElementById('activityForm');
    const saveEntryBtn = document.getElementById('saveEntryBtn');
    const deleteEntryBtn = document.getElementById('deleteEntryBtn');
    const modalModeText = document.getElementById('modalModeText');

    // Toggling Elements
    const chkDrinking = document.getElementById('chkDrinking');
    const chkGambling = document.getElementById('chkGambling');
    const drinkingSection = document.getElementById('drinkingSection');
    const gamblingSection = document.getElementById('gamblingSection');
    let activeEntryId = null;

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

    const hasValue = (value) => (
        value !== null &&
        value !== undefined &&
        String(value).trim() !== ''
    );

    const gamblingFieldNames = [
        'gambling_type',
        'time_spent',
        'money_intended',
        'money_spent',
        'money_earned',
        'drinks_while_gambling',
    ];

    const entryHasDrinking = (entry) => Boolean(entry?.has_drinking) || hasValue(entry?.num_drinks);
    const entryHasGambling = (entry) => (
        Boolean(entry?.has_gambling) ||
        gamblingFieldNames.some((field) => hasValue(entry?.[field]))
    );

    const setModalMode = (mode, iso) => {
        if (mode === 'edit') {
            if (saveEntryBtn) saveEntryBtn.textContent = 'Update Entry';
            if (deleteEntryBtn) deleteEntryBtn.style.display = 'inline-flex';
            if (modalTitle) modalTitle.textContent = `Edit Activity for ${iso}`;
            if (modalModeText) modalModeText.textContent = 'Existing entry loaded. You can update or delete it.';
            return;
        }

        activeEntryId = null;
        if (saveEntryBtn) saveEntryBtn.textContent = 'Save Entry';
        if (deleteEntryBtn) deleteEntryBtn.style.display = 'none';
        if (modalTitle) modalTitle.textContent = `Log Activity for ${iso}`;
        if (modalModeText) modalModeText.textContent = 'No existing entry for this date yet.';
    };

    const getEditableEntryForDate = (iso) => {
        const dayEntries = entries[iso];
        if (!Array.isArray(dayEntries) || dayEntries.length === 0) {
            return null;
        }

        return dayEntries.reduce((latest, current) => {
            if (!latest) return current;
            return (current.id || 0) > (latest.id || 0) ? current : latest;
        }, null);
    };

    const fillInput = (name, value) => {
        if (!activityForm) return;
        const input = activityForm.querySelector(`[name="${name}"]`);
        if (input) input.value = hasValue(value) ? value : '';
    };

    const populateFormFromEntry = (entry) => {
        resetFormState();
        if (!entry) return;

        if (chkDrinking) chkDrinking.checked = entryHasDrinking(entry);
        if (chkGambling) chkGambling.checked = entryHasGambling(entry);

        fillInput('num_drinks', entry.num_drinks);
        fillInput('gambling_type', entry.gambling_type);
        fillInput('time_spent', entry.time_spent);
        fillInput('money_intended', entry.money_intended);
        fillInput('money_spent', entry.money_spent);
        fillInput('money_earned', entry.money_earned);
        fillInput('drinks_while_gambling', entry.drinks_while_gambling);

        toggleSection(chkDrinking, drinkingSection);
        toggleSection(chkGambling, gamblingSection);
    };

    const closeModal = () => {
        if (modal) modal.style.display = 'none';
        activeEntryId = null;
        resetFormState();
        if (saveEntryBtn) saveEntryBtn.textContent = 'Save Entry';
        if (deleteEntryBtn) deleteEntryBtn.style.display = 'none';
        if (modalModeText) modalModeText.textContent = '';
    };

    const openModalForDate = (iso) => {
        const editableEntry = getEditableEntryForDate(iso);

        if (editableEntry && editableEntry.id) {
            activeEntryId = editableEntry.id;
            setModalMode('edit', iso);
            populateFormFromEntry(editableEntry);
        } else {
            setModalMode('create', iso);
            resetFormState();
        }

        if (modal) {
            modal.style.display = 'flex';
            modal.scrollTop = 0;
            const content = modal.querySelector('.modal-content');
            if (content) content.scrollTop = 0;
        }
    };

    const loadEvents = async () => {
        try {
            const response = await fetch(`/api/calendar-events?ts=${Date.now()}`, {
                cache: 'no-store'
            });
            const events = await response.json();

            if (!Array.isArray(events)) {
                console.error('calendar-events failed:', events);
                render();
                return;
            }

            Object.keys(entries).forEach((key) => delete entries[key]);

            events.forEach((event) => {
                const dateKey = event.date;
                if (!entries[dateKey]) {
                    entries[dateKey] = [event];
                    return;
                }

                const merged = entries[dateKey][0];
                merged.id = Math.max(merged.id || 0, event.id || 0);
                merged.has_drinking = Boolean(merged.has_drinking) || Boolean(event.has_drinking);
                merged.has_gambling = Boolean(merged.has_gambling) || Boolean(event.has_gambling);

                [
                    'num_drinks',
                    'gambling_type',
                    'time_spent',
                    'money_intended',
                    'money_spent',
                    'money_earned',
                    'drinks_while_gambling',
                ].forEach((field) => {
                    if (hasValue(event[field])) merged[field] = event[field];
                });
            });

            render();
        } catch (error) {
            console.error('Error fetching calendar events:', error);
            render();
        }
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

        if (!state.selectedISO) {
            entrySummary.innerHTML = '<p class="entry-empty">Select a date to view its entry.</p>';
            return;
        }

        const dayEntries = entries[state.selectedISO];
        if (!Array.isArray(dayEntries) || dayEntries.length === 0) {
            entrySummary.innerHTML = '<p class="entry-empty">No activity logged for this date.</p>';
            return;
        }

        let html = '';
        dayEntries.forEach(entry => {
            if (hasValue(entry.num_drinks)) {
                html += `<div class="entry-section">`;
                html += `<div class="entry-section-title" style="color: var(--primary);">Drinking</div>`;
                html += `<div class="entry-row"><span class="entry-label">Drinks:</span> ${entry.num_drinks}</div>`;
                html += `</div>`;
            }
            if (entryHasGambling(entry)) {
                html += `<div class="entry-section">`;
                html += `<div class="entry-section-title">Gambling</div>`;
                if (hasValue(entry.gambling_type)) html += `<div class="entry-row"><span class="entry-label">Type:</span> ${entry.gambling_type}</div>`;
                if (hasValue(entry.time_spent)) html += `<div class="entry-row"><span class="entry-label">Time Spent:</span> ${entry.time_spent}</div>`;
                if (hasValue(entry.money_intended)) html += `<div class="entry-row"><span class="entry-label">Intended:</span> $${entry.money_intended}</div>`;
                if (hasValue(entry.money_spent)) html += `<div class="entry-row"><span class="entry-label">Wagered:</span> $${entry.money_spent}</div>`;
                if (hasValue(entry.money_earned)) html += `<div class="entry-row"><span class="entry-label">Won/Lost:</span> $${entry.money_earned}</div>`;
                if (hasValue(entry.drinks_while_gambling)) html += `<div class="entry-row"><span class="entry-label">Drinks While Gambling:</span> ${entry.drinks_while_gambling}</div>`;
                html += `</div>`;
            }
        });

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

            // Show two activity markers for days with saved entries
            const dayEntries = entries[iso];

            if (Array.isArray(dayEntries) && dayEntries.length > 0) {
                const hasDrinkingMarker = dayEntries.some((entry) => entryHasDrinking(entry));
                const hasGamblingMarker = dayEntries.some((entry) => entryHasGambling(entry));

                if (hasDrinkingMarker || hasGamblingMarker) {
                    button.classList.add('day--has-markers');
                    const markerWrap = document.createElement('div');
                    markerWrap.className = 'activity-markers';

                    if (hasDrinkingMarker) {
                        const drinkingMarker = document.createElement('span');
                        drinkingMarker.className = 'activity-marker marker-drinking';
                        drinkingMarker.title = 'Drinking entry';
                        markerWrap.appendChild(drinkingMarker);
                    }

                    if (hasGamblingMarker) {
                        const gamblingMarker = document.createElement('span');
                        gamblingMarker.className = 'activity-marker marker-gambling';
                        gamblingMarker.title = 'Gambling entry';
                        markerWrap.appendChild(gamblingMarker);
                    }

                    button.appendChild(markerWrap);
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

                    // Open the modal when a valid day is clicked
                    openModalForDate(iso);

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
            closeModal();
        });
    }

    // Close modal when clicking outside the form
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
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

        // Validate numeric fields before submitting
        const nonNegativeFields = {
            num_drinks: 'Number of drinks',
            time_spent: 'Time spent gambling',
            money_intended: 'Money intended to gamble',
            money_spent: 'Money wagered',
            drinks_while_gambling: 'Drinks while gambling',
        };
        const anyNumberFields = {
            money_earned: 'Money won/lost',
        };

        for (const [field, label] of Object.entries(nonNegativeFields)) {
            const val = payload[field];
            if (val === undefined || val === null || String(val).trim() === '') continue;
            if (isNaN(Number(val))) {
                alert(`${label} must be a number.`);
                return;
            }
            if (Number(val) < 0) {
                alert(`${label} cannot be negative.`);
                return;
            }
            const dotIndex = String(val).indexOf('.');
            if (dotIndex !== -1 && String(val).length - dotIndex - 1 > 2) {
                alert(`${label} can have at most 2 decimal places.`);
                return;
            }
        }
        for (const [field, label] of Object.entries(anyNumberFields)) {
            const val = payload[field];
            if (val === undefined || val === null || String(val).trim() === '') continue;
            if (isNaN(Number(val))) {
                alert(`${label} must be a number.`);
                return;
            }
            const dotIndex = String(val).indexOf('.');
            if (dotIndex !== -1 && String(val).length - dotIndex - 1 > 2) {
                alert(`${label} can have at most 2 decimal places.`);
                return;
            }
        }

        try {
            const endpoint = activeEntryId ? `/api/activity/${activeEntryId}` : '/api/log-activity';
            const method = activeEntryId ? 'PUT' : 'POST';

            const response = await fetch(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                console.warn('Server did not save the entry.', errorData);
                alert(errorData.message || 'Unable to save changes. Check console/server logs.');
                return;
            }

            closeModal();
            await loadEvents();
        } catch (error) {
            console.error('Error saving data:', error);
        }
    });
}

    if (deleteEntryBtn) {
        deleteEntryBtn.addEventListener('click', async () => {
            if (!activeEntryId) return;

            const confirmed = window.confirm('Delete this entry for the selected date?');
            if (!confirmed) return;

            try {
                const response = await fetch(`/api/activity/${activeEntryId}`, {
                    method: 'DELETE'
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    console.warn('Server did not delete the entry.', errorData);
                    alert(errorData.message || 'Unable to delete this entry. Check console/server logs.');
                    return;
                }

                closeModal();
                await loadEvents();
            } catch (error) {
                console.error('Error deleting data:', error);
            }
        });
    }


    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    resetFormState();
    render();
    loadEvents();
};

mountApp();
initCalendar();
