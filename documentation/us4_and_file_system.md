## Flask Style Organization

* **Static folder:** Used to store files that don’t change during the website’s runtime. So, files like **JS** and **CSS** (and images if we want in the future).
* **HTML:** Stored in the **templates** folder.
* **Blueprints:**
    Blueprints can be thought of as mini-programs or a series of functions related to the functionality of the website. For example, for my user story I needed to add the ability to add events to a selected date. 
    
    To do so I create a blueprint called **“events_bp”** which has functions specifically designed for storing data from the forms to our DB. To run a blueprint, simply “register” it to the main python file used to host the website which I named **“app.py”**. All blueprints are stored in the **“routes”** folder.

---

### My modification:
* Apart from the file organization changes I added code to **“app.js”** to handle behaviors related to the popup window to add events and the **“events_bp”** blueprint.