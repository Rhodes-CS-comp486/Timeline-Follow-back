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
        const day = last.getDate() - ((last.getDay() - weekday + 7) % 7);
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
    holidays.set(`${year}-11-11`, 'Veterans Day');
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

const initCalendar = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

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

    const modal = document.getElementById('eventModal');
    const modalTitle = document.getElementById('modalDateTitle');
    const closeModalBtn = document.getElementById('closeModal');
    const activityForm = document.getElementById('activityForm');
    const activityDrinkingToggle = document.getElementById('activityDrinkingToggle');
    const activityGamblingToggle = document.getElementById('activityGamblingToggle');
    const drinkingSection = document.getElementById('drinkingSection');
    const gamblingSection = document.getElementById('gamblingSection');
    const deleteDrinkingBtn = document.getElementById('deleteDrinkingBtn');
    const deleteGamblingBtn = document.getElementById('deleteGamblingBtn');

    const drinksInput = document.getElementById('drinksInput');
    const gamblingTypeInput = document.getElementById('gamblingType');
    const timeSpentInput = document.getElementById('timeSpent');
    const moneyIntendedInput = document.getElementById('moneyIntended');
    const moneySpentInput = document.getElementById('moneyInputSpent');
    const moneyEarnedInput = document.getElementById('moneyInputEarned');
    const drinksWhileGamblingInput = document.getElementById('drinksWhileGambling');

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel || !entrySummary || !modal || !activityForm || !activityDrinkingToggle || !activityGamblingToggle) {
        return;
    }

    const entries = {};

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

    const escapeHtml = (value) => String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');

    const makeEmptyDateEntry = (isoDate) => ({
        date: isoDate,
        drinking: null,
        gambling: null,
    });

    const getDateEntry = (isoDate) => entries[isoDate] || makeEmptyDateEntry(isoDate);

    const hasAnyActivity = (entry) => Boolean(entry && (entry.drinking || entry.gambling));

    const setActivitySelection = ({ drinking, gambling }) => {
        activityDrinkingToggle.checked = Boolean(drinking);
        activityGamblingToggle.checked = Boolean(gambling);
    };

    const setSectionState = (section, isVisible) => {
        if (!section) return;
        section.classList.toggle('section-hidden', !isVisible);
        section.classList.toggle('section-disabled', !isVisible);
        section.querySelectorAll('input, select, textarea').forEach((input) => {
            input.disabled = !isVisible;
        });
    };

    const updateSectionsFromSelection = () => {
        const isDrinkingSelected = activityDrinkingToggle.checked;
        const isGamblingSelected = activityGamblingToggle.checked;
        setSectionState(drinkingSection, isDrinkingSelected);
        setSectionState(gamblingSection, isGamblingSelected);
    };

    const clearForm = () => {
        activityForm.reset();
        setActivitySelection({ drinking: false, gambling: false });
        updateSectionsFromSelection();
    };

    const updateDeleteButtons = (entry) => {
        if (!deleteDrinkingBtn || !deleteGamblingBtn) return;
        deleteDrinkingBtn.disabled = !(entry && entry.drinking);
        deleteGamblingBtn.disabled = !(entry && entry.gambling);
    };

    const fillFormFromEntry = (entry) => {
        clearForm();
        setActivitySelection({
            drinking: Boolean(entry.drinking),
            gambling: Boolean(entry.gambling),
        });
        updateSectionsFromSelection();

        if (entry.drinking && drinksInput) {
            drinksInput.value = entry.drinking.drinks ?? '';
        }

        if (entry.gambling) {
            if (gamblingTypeInput) gamblingTypeInput.value = entry.gambling.gambling_type ?? '';
            if (timeSpentInput) timeSpentInput.value = entry.gambling.time_spent ?? '';
            if (moneyIntendedInput) moneyIntendedInput.value = entry.gambling.money_intended ?? '';
            if (moneySpentInput) moneySpentInput.value = entry.gambling.money_spent ?? '';
            if (moneyEarnedInput) moneyEarnedInput.value = entry.gambling.money_earned ?? '';
            if (drinksWhileGamblingInput) drinksWhileGamblingInput.value = entry.gambling.drinks_while_gambling ?? '';
        }

        updateDeleteButtons(entry);
    };

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
        if (!state.selectedISO) {
            entrySummary.innerHTML = '<p class="entry-empty">Select a date to view its entry.</p>';
            return;
        }

        const entry = getDateEntry(state.selectedISO);
        if (!hasAnyActivity(entry)) {
            entrySummary.innerHTML = '<p class="entry-empty">No activity logged for this date. Click a date on the calendar to add one.</p>';
            return;
        }

        let html = '';

        if (entry.drinking) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Drinking</div>';
            html += `<div class="entry-row"><span class="entry-label">Drinks:</span> ${escapeHtml(entry.drinking.drinks ?? 'Not provided')}</div>`;
            html += '</div>';
        }

        if (entry.gambling) {
            html += '<div class="entry-section">';
            html += '<div class="entry-section-title">Gambling</div>';
            html += `<div class="entry-row"><span class="entry-label">Type:</span> ${escapeHtml(entry.gambling.gambling_type ?? 'Not provided')}</div>`;
            html += `<div class="entry-row"><span class="entry-label">Time Spent:</span> ${escapeHtml(entry.gambling.time_spent ?? 'Not provided')}</div>`;
            html += `<div class="entry-row"><span class="entry-label">Intended to Wager:</span> ${escapeHtml(entry.gambling.money_intended ?? 'Not provided')}</div>`;
            html += `<div class="entry-row"><span class="entry-label">Actually Wagered:</span> ${escapeHtml(entry.gambling.money_spent ?? 'Not provided')}</div>`;
            html += `<div class="entry-row"><span class="entry-label">Won/Lost:</span> ${escapeHtml(entry.gambling.money_earned ?? 'Not provided')}</div>`;
            html += `<div class="entry-row"><span class="entry-label">Drinks While Gambling:</span> ${escapeHtml(entry.gambling.drinks_while_gambling ?? 'Not provided')}</div>`;
            html += '</div>';
        }

        entrySummary.innerHTML = html;
    };

    const renderGrid = () => {
        grid.innerHTML = '';

        const firstOfMonth = new Date(state.viewYear, state.viewMonth, 1);
        const startDay = firstOfMonth.getDay();
        const daysInMonth = new Date(state.viewYear, state.viewMonth + 1, 0).getDate();
        const holidays = getUSHolidays(state.viewYear);

        for (let i = 0; i < startDay; i += 1) {
            const placeholder = document.createElement('div');
            placeholder.className = 'day day--empty';
            grid.appendChild(placeholder);
        }

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

            const dayNumber = document.createElement('span');
            dayNumber.className = 'day-number';
            dayNumber.textContent = day;
            button.appendChild(dayNumber);

            if (holidayName) {
                button.classList.add('day--holiday');
                const label = document.createElement('span');
                label.className = 'holiday-label';
                label.textContent = holidayName;
                button.appendChild(label);
            }

            const entry = getDateEntry(iso);
            if (hasAnyActivity(entry)) {
                const markerRow = document.createElement('span');
                markerRow.className = 'day-marker-row';

                if (entry.drinking) {
                    const drinkingMarker = document.createElement('span');
                    drinkingMarker.className = 'calendar-marker marker-drinking';
                    drinkingMarker.title = 'Drinking logged';
                    markerRow.appendChild(drinkingMarker);
                }

                if (entry.gambling) {
                    const gamblingMarker = document.createElement('span');
                    gamblingMarker.className = 'calendar-marker marker-gambling';
                    gamblingMarker.title = 'Gambling logged';
                    markerRow.appendChild(gamblingMarker);
                }

                button.appendChild(markerRow);
            }

            if (isToday) button.classList.add('day--today');
            if (isFuture) {
                button.classList.add('day--future');
                button.disabled = true;
            }
            if (isSelected) button.classList.add('day--selected');

            if (!isFuture) {
                button.addEventListener('click', () => {
                    state.selectedISO = iso;
                    selectedLabel.textContent = formatReadable(cellDate);
                    renderSidebar();
                    renderGrid();
                    openEditorForSelectedDate();
                });
            }

            grid.appendChild(button);
        }
    };

    const render = () => {
        monthLabel.textContent = `${monthNames[state.viewMonth]} ${state.viewYear}`;
        const isCurrentMonth = state.viewYear === today.getFullYear() && state.viewMonth === today.getMonth();
        nextBtn.disabled = isCurrentMonth;
        nextBtn.classList.toggle('is-disabled', isCurrentMonth);
        renderGrid();
        renderSidebar();
    };

    const normalizeEvent = (event) => {
        const dateKey = (event.date || '').split('T')[0];
        const normalized = {
            ...makeEmptyDateEntry(dateKey),
            partial: false,
        };

        if (!dateKey) {
            return null;
        }

        if (event.drinking || event.gambling) {
            normalized.drinking = event.drinking || null;
            normalized.gambling = event.gambling || null;
            return normalized;
        }

        if (event.type === 'drinking') {
            normalized.partial = true;
            normalized.drinking = {
                id: event.id,
                drinks: event.drinks ?? null,
            };
        }

        if (event.type === 'gambling') {
            normalized.partial = true;
            normalized.gambling = {
                id: event.id,
                gambling_type: event.gambling_type ?? null,
                time_spent: event.time_spent ?? null,
                money_intended: event.money_intended ?? null,
                money_spent: event.money_spent ?? null,
                money_earned: event.money_earned ?? null,
                drinks_while_gambling: event.drinks_while_gambling ?? null,
            };
        }

        return normalized;
    };

    const updateEntryForDate = (isoDate, entry) => {
        if (entry && hasAnyActivity(entry)) {
            entries[isoDate] = {
                date: isoDate,
                drinking: entry.drinking || null,
                gambling: entry.gambling || null,
            };
        } else {
            delete entries[isoDate];
        }
    };

    const loadEntries = async () => {
        try {
            const response = await fetch('/api/calendar-events');
            if (!response.ok) {
                throw new Error('Unable to load saved events');
            }

            const events = await response.json();
            events.forEach((event) => {
                const normalized = normalizeEvent(event);
                if (!normalized) return;
                if (normalized.partial) {
                    const existing = getDateEntry(normalized.date);
                    updateEntryForDate(normalized.date, {
                        date: normalized.date,
                        drinking: normalized.drinking || existing.drinking,
                        gambling: normalized.gambling || existing.gambling,
                    });
                } else {
                    updateEntryForDate(normalized.date, normalized);
                }
            });

            render();
        } catch (error) {
            console.error('Error fetching calendar events:', error);
        }
    };

    const closeModal = () => {
        modal.style.display = 'none';
    };

    const openEditorForSelectedDate = () => {
        if (!state.selectedISO) {
            return;
        }

        const existing = getDateEntry(state.selectedISO);
        modalTitle.textContent = `Edit Activity for ${state.selectedISO}`;
        fillFormFromEntry(existing);
        modal.style.display = 'flex';
        modal.scrollTop = 0;

        const content = modal.querySelector('.modal-content');
        if (content) {
            content.scrollTop = 0;
        }
    };

    const saveSelectedDate = async () => {
        if (!state.selectedISO) {
            return;
        }

        const isDrinkingSelected = activityDrinkingToggle.checked;
        const isGamblingSelected = activityGamblingToggle.checked;
        if (!isDrinkingSelected && !isGamblingSelected) {
            alert('Please select Drinking, Gambling, or both before saving.');
            return;
        }

        const payload = {
            date: state.selectedISO,
            activities: {},
        };

        if (isDrinkingSelected) {
            payload.activities.drinking = {
                drinks: drinksInput ? drinksInput.value.trim() : null,
            };
        }

        if (isGamblingSelected) {
            payload.activities.gambling = {
                gambling_type: gamblingTypeInput ? gamblingTypeInput.value.trim() : null,
                time_spent: timeSpentInput ? timeSpentInput.value.trim() : null,
                money_intended: moneyIntendedInput ? moneyIntendedInput.value.trim() : null,
                money_spent: moneySpentInput ? moneySpentInput.value.trim() : null,
                money_earned: moneyEarnedInput ? moneyEarnedInput.value.trim() : null,
                drinks_while_gambling: drinksWhileGamblingInput ? drinksWhileGamblingInput.value.trim() : null,
            };
        }

        try {
            const response = await fetch('/api/log-activity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || 'Failed to save entry');
            }

            const normalized = normalizeEvent(result.entry || {});
            updateEntryForDate(state.selectedISO, normalized);
            closeModal();
            renderSidebar();
            renderGrid();
        } catch (error) {
            alert(error.message || 'Error saving data. Please try again.');
            console.error('Error saving data:', error);
        }
    };

    const deleteActivityType = async (entryType) => {
        if (!state.selectedISO) {
            return;
        }

        const selectedEntry = getDateEntry(state.selectedISO);
        if (!selectedEntry[entryType]) {
            return;
        }

        const confirmed = window.confirm(`Delete the ${entryType} entry for ${state.selectedISO}?`);
        if (!confirmed) {
            return;
        }

        try {
            const response = await fetch('/api/delete-activity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ date: state.selectedISO, type: entryType }),
            });

            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || `Failed to delete ${entryType} entry`);
            }

            const normalized = normalizeEvent(result.entry || {});
            updateEntryForDate(state.selectedISO, normalized);
            fillFormFromEntry(getDateEntry(state.selectedISO));
            renderSidebar();
            renderGrid();
        } catch (error) {
            alert(error.message || `Error deleting ${entryType} entry.`);
            console.error(`Error deleting ${entryType} entry:`, error);
        }
    };

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    activityDrinkingToggle.addEventListener('change', updateSectionsFromSelection);
    activityGamblingToggle.addEventListener('change', updateSectionsFromSelection);

    activityForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        await saveSelectedDate();
    });

    if (deleteDrinkingBtn) {
        deleteDrinkingBtn.addEventListener('click', async () => {
            await deleteActivityType('drinking');
        });
    }

    if (deleteGamblingBtn) {
        deleteGamblingBtn.addEventListener('click', async () => {
            await deleteActivityType('gambling');
        });
    }

    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    clearForm();
    render();
    loadEntries();
};

mountApp();
initCalendar();
