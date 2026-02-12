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
    // In-memory store for activity indicators (keyed by ISO date)
    const indicators = {};

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
    const deleteDrinkingBtn = document.getElementById('deleteDrinking');
    const deleteGamblingBtn = document.getElementById('deleteGambling');
    const dropdownSummary = document.querySelector('.type-dropdown summary');

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel) {
        return;
    }

    const toggleSection = (checkbox, section) => {
        if (!checkbox || !section) return;

        // Find every input inside this specific div
        const inputs = section.querySelectorAll('input, select, textarea');

        if (checkbox.checked) {
            section.classList.remove('section-disabled'); // Removes the grey-out CSS
            section.classList.remove('section-hidden');
            inputs.forEach(input => input.disabled = false); // Allows typing
        }
        else {
            section.classList.add('section-disabled');    // Adds the grey-out CSS
            section.classList.add('section-hidden');
            inputs.forEach(input => input.disabled = true);  // Prevents typing
        }
    };
    const updateDropdownLabel = () => {
        if (!dropdownSummary) return;
        const labels = [];
        if (chkDrinking && chkDrinking.checked) labels.push('Drinking');
        if (chkGambling && chkGambling.checked) labels.push('Gambling');
        dropdownSummary.textContent = labels.length ? `Activities: ${labels.join(', ')}` : 'Select activities';
    };

    const resetFormState = () => {
        if (activityForm) activityForm.reset();
        // Force the sections back to their "locked" state
        toggleSection(chkDrinking, drinkingSection);
        toggleSection(chkGambling, gamblingSection);
        if (deleteDrinkingBtn) deleteDrinkingBtn.disabled = true;
        if (deleteGamblingBtn) deleteGamblingBtn.disabled = true;
        updateDropdownLabel();
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

        if (entry.drinking) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Drinking</div>';
            html += `<div class="entry-row"><span class="entry-label">Drinks:</span> ${entry.drinking.drinks ?? ''}</div>`;
            html += '</div>';
        }

        if (entry.gambling) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Gambling</div>';
            html += `<div class="entry-row"><span class="entry-label">Type:</span> ${entry.gambling.gambling_type ?? ''}</div>`;
            if (entry.gambling.time_spent) html += `<div class="entry-row"><span class="entry-label">Time Spent:</span> ${entry.gambling.time_spent}</div>`;
            if (entry.gambling.money_intended) html += `<div class="entry-row"><span class="entry-label">Intended to Wager:</span> ${entry.gambling.money_intended}</div>`;
            if (entry.gambling.money_spent !== undefined) html += `<div class="entry-row"><span class="entry-label">Actually Wagered:</span> ${entry.gambling.money_spent}</div>`;
            if (entry.gambling.money_earned !== undefined) html += `<div class="entry-row"><span class="entry-label">Won/Lost:</span> ${entry.gambling.money_earned}</div>`;
            if (entry.gambling.drinks_while_gambling) html += `<div class="entry-row"><span class="entry-label">Drinks While Gambling:</span> ${entry.gambling.drinks_while_gambling}</div>`;
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
            if (entry && (entry.no_drinking || entry.no_gambling)) {
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

            // Show activity markers for logged entries
            const indicator = indicators[iso];
            if (indicator && (indicator.drinking || indicator.gambling)) {
                const markerWrap = document.createElement('div');
                markerWrap.className = 'activity-markers';
                if (indicator.drinking) {
                    const marker = document.createElement('span');
                    marker.className = 'activity-marker marker--drinking';
                    marker.setAttribute('aria-hidden', 'true');
                    markerWrap.appendChild(marker);
                }
                if (indicator.gambling) {
                    const marker = document.createElement('span');
                    marker.className = 'activity-marker marker--gambling';
                    marker.setAttribute('aria-hidden', 'true');
                    markerWrap.appendChild(marker);
                }
                button.appendChild(markerWrap);
            }

            if (isToday) button.classList.add('day--today');
            if (isFuture) {
                button.classList.add('day--future');
                button.disabled = true;
            }
            if (isSelected) button.classList.add('day--selected');

            if (!isFuture) {
                button.addEventListener('click', async () => {
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
                    await loadEntryForDate(iso);
                    renderSidebar();

                    // Added: Open the Modal when a valid day is clicked
                    if (modal && modalTitle) {
                        modalTitle.textContent = `Log Activity for ${iso}`;
                        setFormFromEntry(entries[iso]);
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

    const setFormFromEntry = (entry) => {
        if (!activityForm) return;
        activityForm.reset();

        const drinking = entry && entry.drinking ? entry.drinking : null;
        const gambling = entry && entry.gambling ? entry.gambling : null;

        if (chkDrinking) chkDrinking.checked = !!drinking;
        if (chkGambling) chkGambling.checked = !!gambling;

        toggleSection(chkDrinking, drinkingSection);
        toggleSection(chkGambling, gamblingSection);
        updateDropdownLabel();

        if (drinking) {
            const drinksInput = document.getElementById('drinksInput');
            if (drinksInput) drinksInput.value = drinking.drinks ?? '';
        }

        if (gambling) {
            const gamblingType = document.getElementById('gamblingType');
            const timeSpent = document.getElementById('timeSpent');
            const moneyIntended = document.getElementById('moneyIntended');
            const moneyInputSpent = document.getElementById('moneyInputSpent');
            const moneyInputEarned = document.getElementById('moneyInputEarned');
            const drinksWhileGambling = document.getElementById('drinksWhileGambling');

            if (gamblingType) gamblingType.value = gambling.gambling_type ?? '';
            if (timeSpent) timeSpent.value = gambling.time_spent ?? '';
            if (moneyIntended) moneyIntended.value = gambling.money_intended ?? '';
            if (moneyInputSpent) moneyInputSpent.value = gambling.money_spent ?? '';
            if (moneyInputEarned) moneyInputEarned.value = gambling.money_earned ?? '';
            if (drinksWhileGambling) drinksWhileGambling.value = gambling.drinks_while_gambling ?? '';
        }

        if (deleteDrinkingBtn) deleteDrinkingBtn.disabled = !drinking;
        if (deleteGamblingBtn) deleteGamblingBtn.disabled = !gambling;
    };

    const loadEntryForDate = async (iso) => {
        if (!iso) return;
        try {
            const response = await fetch(`/api/entry?date=${iso}`);
            if (!response.ok) {
                entries[iso] = { drinking: null, gambling: null };
                return;
            }
            const data = await response.json();
            entries[iso] = {
                drinking: data.drinking || null,
                gambling: data.gambling || null,
                no_drinking: false,
                no_gambling: false
            };
            indicators[iso] = {
                drinking: !!data.drinking,
                gambling: !!data.gambling
            };
        } catch (error) {
            console.warn('Unable to load entry details.', error);
        }
    };

    const loadIndicators = async () => {
        try {
            const response = await fetch('/api/calendar-entries');
            if (!response.ok) {
                return;
            }
            const data = await response.json();
            if (!data || !Array.isArray(data.entries)) {
                return;
            }
            data.entries.forEach((entry) => {
                if (!entry || !entry.entry_date) {
                    return;
                }
                const iso = entry.entry_date;
                if (!indicators[iso]) {
                    indicators[iso] = { drinking: false, gambling: false };
                }
                if (entry.entry_type === 'drinking') {
                    indicators[iso].drinking = true;
                } else if (entry.entry_type === 'gambling') {
                    indicators[iso].gambling = true;
                }
            });
        } catch (error) {
            console.warn('Unable to load calendar indicators.', error);
        }
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
        chkDrinking.addEventListener('change', () => {
            toggleSection(chkDrinking, drinkingSection);
            updateDropdownLabel();
        });
    }
    // Listen for clicks on the Gambling checkbox
    if (chkGambling) {
        chkGambling.addEventListener('change', () => {
            toggleSection(chkGambling, gamblingSection);
            updateDropdownLabel();
        });
    }
    // Added: Event listener for the Activity Form submission
    // Handle saving the event
    if (activityForm) {
        activityForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Base payload is the date, else this payload does not exist
            const payload = {
                date: state.selectedISO
            };

            // Is drinking checked? If true then save data related to it
            if (chkDrinking.checked) {
                payload.drinking = {
                    drinks: document.getElementById('drinksInput').value
                };
            }

            // Same for gambling
            if (chkGambling.checked) {
                payload.gambling = {
                    gambling_type: document.getElementById('gamblingType').value,
                    time_spent: document.getElementById('timeSpent').value,
                    money_intended: document.getElementById('moneyIntended').value,
                    money_spent: document.getElementById('moneyInputSpent').value,
                    money_earned: document.getElementById('moneyInputEarned').value,
                    drinks_while_gambling: document.getElementById('drinksWhileGambling').value
                };
            }

            // Track whether the user did NOT drink or gamble
            payload.no_drinking = !chkDrinking.checked;
            payload.no_gambling = !chkGambling.checked;

            // Store the entry locally so the sidebar can display it
            entries[state.selectedISO] = {
                drinking: payload.drinking || null,
                gambling: payload.gambling || null,
                no_drinking: payload.no_drinking,
                no_gambling: payload.no_gambling
            };
            indicators[state.selectedISO] = {
                drinking: !!payload.drinking,
                gambling: !!payload.gambling
            };
            indicators[state.selectedISO] = {
                drinking: chkDrinking.checked,
                gambling: chkGambling.checked
            };

            if (modal) {
                modal.style.display = 'none';
            }

            resetFormState()
            renderSidebar();
            renderGrid();

            // Send data to backend in the background => route: log-activity
            try {
                const response = await fetch('/api/log-activity', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    // sending the payload
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    console.log(`Saved entry for ${state.selectedISO}!`);
                } else {
                    console.warn('Server did not save the entry.');
                }
            } catch (error) {
                console.error('Error saving data:', error);
            }
        });
    }

    const handleDelete = async (entryType) => {
        if (!state.selectedISO) return;
        const confirmed = window.confirm(`Delete ${entryType} entry for ${state.selectedISO}?`);
        if (!confirmed) return;

        try {
            const response = await fetch('/api/delete-entry', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: state.selectedISO,
                    entry_type: entryType
                })
            });

            if (!response.ok) {
                console.warn('Unable to delete entry.');
                return;
            }

            const current = entries[state.selectedISO] || {};
            if (entryType === 'drinking') {
                current.drinking = null;
                if (deleteDrinkingBtn) deleteDrinkingBtn.disabled = true;
            } else if (entryType === 'gambling') {
                current.gambling = null;
                if (deleteGamblingBtn) deleteGamblingBtn.disabled = true;
            }

            entries[state.selectedISO] = current;
            indicators[state.selectedISO] = {
                drinking: !!current.drinking,
                gambling: !!current.gambling
            };

            renderSidebar();
            renderGrid();
        } catch (error) {
            console.warn('Error deleting entry.', error);
        }
    };

    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    loadIndicators().then(() => {
        render();
        resetFormState();
    });

    if (deleteDrinkingBtn) {
        deleteDrinkingBtn.addEventListener('click', () => handleDelete('drinking'));
    }
    if (deleteGamblingBtn) {
        deleteGamblingBtn.addEventListener('click', () => handleDelete('gambling'));
    }
};

mountApp();
initCalendar();
