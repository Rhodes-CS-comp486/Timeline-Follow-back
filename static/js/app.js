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
    const quickJump = document.getElementById('monthQuickJump');

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

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel || !quickJump) {
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

    const renderQuickJump = () => {
        const months = [];
        for (let i = 2; i >= 0; i -= 1) {
            months.push(new Date(today.getFullYear(), today.getMonth() - i, 1));
        }

        quickJump.innerHTML = '';
        months.forEach((date) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'month-pill';
            if (date.getFullYear() === state.viewYear && date.getMonth() === state.viewMonth) {
                button.classList.add('is-active');
            }
            button.textContent = `${monthNames[date.getMonth()]} ${date.getFullYear()}`;
            button.addEventListener('click', () => setView(date.getFullYear(), date.getMonth()));
            quickJump.appendChild(button);
        });
    };

    const renderGrid = () => {
        grid.innerHTML = '';

        const firstOfMonth = new Date(state.viewYear, state.viewMonth, 1);
        const startDay = firstOfMonth.getDay();
        const totalCells = 42;

        for (let i = 0; i < totalCells; i += 1) {
            const cellDate = new Date(state.viewYear, state.viewMonth, i - startDay + 1);
            cellDate.setHours(0, 0, 0, 0);

            const iso = toISO(cellDate);
            const isCurrentMonth = cellDate.getMonth() === state.viewMonth &&
                cellDate.getFullYear() === state.viewYear;
            const isToday = cellDate.getTime() === today.getTime();
            const isFuture = cellDate.getTime() > today.getTime();
            const isSelected = state.selectedISO === iso;

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'day';
            button.textContent = cellDate.getDate();
            button.dataset.iso = iso;
            button.setAttribute('aria-label', formatReadable(cellDate));

            if (!isCurrentMonth) button.classList.add('day--muted');
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

                    // Added: Open the Modal when a valid day is clicked
                    if (modal && modalTitle) {
                        modalTitle.textContent = `Log Activity for ${iso}`;
                        resetFormState()
                        modal.style.display = 'flex';
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
        renderQuickJump();
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

            // Base payload is the date, else this payload does not exist
            const payload = {
                date: state.selectedISO
            };

            // Is drinking checked? If true then save data related to it
            if (chkDrinking.checked) {
                payload.type = "drinking";
                payload.drinks = document.getElementById('drinksInput').value;
                payload.drinks_cost = document.getElementById('drinksCost').value;
                payload.drink_trigger = document.getElementById('drinkTrigger').value;
            }

            // Same for gambling
            if (chkGambling.checked) {
                payload.type = "gambling";
                payload.gambling_type = document.getElementById('gamblingType').value;
                payload.money_spent = document.getElementById('moneyInputSpent').value;
                payload.money_earned = document.getElementById('moneyInputEarned').value;
                payload.time_spent = document.getElementById('timeSpent').value;
                payload.emotion_before = document.getElementById('emotionBefore').value;
                payload.emotion_during = document.getElementById('emotionDuring').value;
                payload.emotion_after = document.getElementById('emotionAfter').value;
            }

            if (modal) {
                modal.style.display = 'none';
            }

            resetFormState()

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

    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    render();
    resetFormState()
};

mountApp();
initCalendar();