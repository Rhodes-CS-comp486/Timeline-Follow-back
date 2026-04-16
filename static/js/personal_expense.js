function formatCurrency(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(value);
}

function buildLegendRow(item) {
    const row = document.createElement("div");
    row.className = "expense-legend-row";

    const identity = document.createElement("div");
    identity.className = "expense-legend-identity";

    const swatch = document.createElement("span");
    swatch.className = "expense-legend-swatch";
    swatch.style.background = item.color;

    const label = document.createElement("span");
    label.className = "expense-legend-label";
    label.textContent = item.label;

    identity.append(swatch, label);

    const value = document.createElement("span");
    value.className = "expense-legend-value";
    value.textContent = `${formatCurrency(item.value)} (${item.percent.toFixed(1)}%)`;

    row.append(identity, value);
    return row;
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("[data-expense-form]");
    if (!form) {
        return;
    }

    const allInputs = Array.from(form.querySelectorAll("[data-expense-field]"));
    const incomeInput = allInputs.find((input) => input.dataset.fieldKey === "income");
    const expenseInputs = allInputs.filter((input) => input.dataset.fieldKey !== "income");

    const summaryTargets = {
        income: document.querySelector('[data-summary="income"]'),
        expenseTotal: document.querySelector('[data-summary="expense_total"]'),
        remaining: document.querySelector('[data-summary="remaining"]'),
        allocationTotal: document.querySelector('[data-summary="allocation_total"]'),
    };

    const pieChart = document.getElementById("expensePieChart");
    const legend = document.getElementById("expenseChartLegend");

    const getNumericValue = (input) => {
        const parsed = Number.parseFloat(input.value);
        return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
    };

    const renderChart = () => {
        const income = incomeInput ? getNumericValue(incomeInput) : 0;
        const items = expenseInputs
            .map((input) => ({
                key: input.dataset.fieldKey,
                label: input.dataset.fieldLabel,
                color: input.dataset.fieldColor,
                value: getNumericValue(input),
            }))
            .filter((item) => item.value > 0);

        const expenseTotal = items.reduce((sum, item) => sum + item.value, 0);
        const remaining = income - expenseTotal;

        if (summaryTargets.income) {
            summaryTargets.income.textContent = formatCurrency(income);
        }
        if (summaryTargets.expenseTotal) {
            summaryTargets.expenseTotal.textContent = formatCurrency(expenseTotal);
        }
        if (summaryTargets.remaining) {
            summaryTargets.remaining.textContent = formatCurrency(remaining);
        }
        if (summaryTargets.allocationTotal) {
            summaryTargets.allocationTotal.textContent = formatCurrency(expenseTotal);
        }

        if (!pieChart || !legend) {
            return;
        }

        if (!items.length || allocationTotal === 0) {
            pieChart.style.background = "linear-gradient(135deg, #eef3f1, #dce8e2)";
            legend.innerHTML = '<p class="entry-empty">Enter values to see the breakdown.</p>';
            return;
        }

        let start = 0;
        const segments = items.map((item) => {
            const percent = (item.value / allocationTotal) * 100;
            const segment = `${item.color} ${start.toFixed(2)}% ${(start + percent).toFixed(2)}%`;
            start += percent;
            return segment;
        });
        pieChart.style.background = `conic-gradient(${segments.join(", ")})`;

        legend.innerHTML = "";
        items.forEach((item) => {
            const percent = allocationTotal ? (item.value / allocationTotal) * 100 : 0;
            legend.appendChild(buildLegendRow({ ...item, percent }));
        });
    };

    allInputs.forEach((input) => {
        input.addEventListener("input", renderChart);
    });

    renderChart();
});
