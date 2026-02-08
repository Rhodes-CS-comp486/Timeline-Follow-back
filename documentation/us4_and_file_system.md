## Flask Style Organization

* **Static folder:** Used to store files that don’t change during the website’s runtime. So, files like **JS** and **CSS** (and images if we want in the future).
* **HTML:** Stored in the **templates** folder.
* **Blueprints:**
    Blueprints can be thought of as mini-programs or a series of functions related to the functionality of the website. For example, for my user story I needed to add the ability to add events to a selected date. 
    
    To do so I create a blueprint called **“events_bp”** which has functions specifically designed for storing data from the forms to our DB. To run a blueprint, simply “register” it to the main python file used to host the website which I named **“app.py”**. All blueprints are stored in the **“routes”** folder.

---

### My modification:
* Apart from the file organization changes I added code to **“app.js”** to handle behaviors related to the popup window to add events and the **“events_bp”** blueprint.


---

### Flask routes and functions:

* func: index() is usually the name of the function used to render the main website's html.
* routes: To connect your backend flask function to your frontend JS and HTML indicate the route that the JS is fetching data to.
```python
# the fetch function indicate the route "/api/log-activity" (this is in the JS code)
 await fetch('/api/log-activity', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    // sending the payload
                    body: JSON.stringify(payload)
                });
                
# now in our blueprint python file if we want to fetch that data indicate the same (relative is okay) path:
@events_handler_bp.route('/log-activity', methods=['POST'])
def log_activity():
    pass
