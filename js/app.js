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
