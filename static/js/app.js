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

    // New Modal Elements
    const modal = document.getElementById('eventModal');
    const modalTitle = document.getElementById('modalDateTitle');
    const closeModalBtn = document.getElementById('closeModal');
    const activityForm = document.getElementById('activityForm');

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel || !quickJump) {
        return;
    }

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

    // Added: Event listener to close the popup window
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }

    // Added: Event listener for the Activity Form submission
    // Handle saving the event
    if (activityForm) {
        activityForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // 1. Grab the data
            const payload = {
                date: state.selectedISO,
                drinks: document.getElementById('drinksInput').value,
                money_spent: document.getElementById('moneyInput').value
            };

            // 2. Close the modal IMMEDIATELY for instant feedback
            if (modal) {
                modal.style.display = 'none';
            }

            // 3. Reset the form for next time
            activityForm.reset();

            // 4. Send data to backend in the background
            try {
                const response = await fetch('/api/log-activity', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
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
};

mountApp();
initCalendar();