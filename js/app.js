document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("entry-form");

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const entryType = document.getElementById("entry-type").value;

        const data = {
            email: document.getElementById("email").value,
            first_name: document.getElementById("first-name").value,
            last_name: document.getElementById("last-name").value,
            password: document.getElementById("password").value,
            is_admin: document.getElementById("is-admin").checked,
            entry_date: document.getElementById("entry-date").value,
            entry_type: entryType,
            gambling: {},
            alcohol: {}
        };

        // Gambling data
        if (entryType === "gambling" || entryType === "both") {
            data.gambling = {
                amount_spent: parseFloat(document.getElementById("amount-spent").value) || 0,
                amount_earned: parseFloat(document.getElementById("amount-earned").value) || 0,
                time_spent: document.getElementById("time-spent").value,
                gambling_type: document.getElementById("gambling-type").value,
                emotion_before: document.getElementById("emotion-before").value,
                emotion_during: document.getElementById("emotion-during").value,
                emotion_after: document.getElementById("emotion-after").value
            };
        }

        // Alcohol data
        if (entryType === "alcohol" || entryType === "both") {
            data.alcohol = {
                money_spent: parseFloat(document.getElementById("money-spent").value) || 0,
                num_drinks: parseInt(document.getElementById("num-drinks").value) || 0,
                trigger: document.getElementById("trigger").value
            };
        }

        try {
            const response = await fetch("/save-entry", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                alert("Entry saved successfully!");
                form.reset();
            } else {
                alert("Something went wrong.");
            }

        } catch (error) {
            console.error("Error:", error);
            alert("Server error. Check Flask terminal.");
        }
    });

});

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

        // replace base layout with page slots
        // as the calendar page is empty right now this logic is doing nothing
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
// initialise the calendar  to create and control the dates
const initCalendar = () => {
    // define today at midnight
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    // for current date/month/ year
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

    if (!monthLabel || !grid || !prevBtn || !nextBtn || !selectedLabel || !quickJump) {
        return;
    }

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ];

    // helper function to convert js dates
    const toISO = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    // format the date into readable UI
    const formatReadable = (date) => date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
    });

    // changing which month you're viewing
    const setView = (year, month) => {
        const target = new Date(year, month, 1);
        state.viewYear = target.getFullYear();
        state.viewMonth = target.getMonth();
        render();
    };

    // change month +1= next month -1 = last month
    const changeMonth = (delta) => {
        setView(state.viewYear, state.viewMonth + delta);
    };

    // to show calendar just for last 3 months
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

    // render the calendar on the grid
    const renderGrid = () => {
        grid.innerHTML = '';

        const firstOfMonth = new Date(state.viewYear, state.viewMonth, 1);
        const startDay = firstOfMonth.getDay();
        const totalCells = 42;

        for (let i = 0; i < totalCells; i += 1) {
            const cellDate = new Date(state.viewYear, state.viewMonth, i - startDay + 1);
            cellDate.setHours(0, 0, 0, 0);

            // show today's date
            // disable future date selection
            // add highlight for selected date
            const iso = toISO(cellDate);
            const isCurrentMonth = cellDate.getMonth() === state.viewMonth &&
                cellDate.getFullYear() === state.viewYear;
            const isToday = cellDate.getTime() === today.getTime();
            const isFuture = cellDate.getTime() > today.getTime();
            const isSelected = state.selectedISO === iso;

            // add button to click and select the date
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'day';
            button.textContent = cellDate.getDate();
            button.dataset.iso = iso;
            button.setAttribute('aria-label', formatReadable(cellDate));

            // apply css based on condition
            if (!isCurrentMonth) {
                button.classList.add('day--muted');
            }
            if (isToday) {
                button.classList.add('day--today');
            }
            if (isFuture) {
                button.classList.add('day--future');
                button.disabled = true;
            }
            if (isSelected) {
                button.classList.add('day--selected');
            }

            if (!isFuture) {
                button.addEventListener('click', () => {
                    state.selectedISO = iso;
                    selectedLabel.textContent = formatReadable(cellDate);
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

    prevBtn.addEventListener('click', () => changeMonth(-1));
    nextBtn.addEventListener('click', () => changeMonth(1));

    render();
};

mountApp();
initCalendar();
