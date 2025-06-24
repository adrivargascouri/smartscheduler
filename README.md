# SmartScheduler

![ChatGPT Image Jun 20, 2025, 04_53_17 PM](https://github.com/user-attachments/assets/ed07b35f-fa3f-409f-a3ff-76cc7e5922d6)


WELCOME TO **SmartScheduler**!  
An intelligent, AI-powered appointment scheduling application with a modern graphical interface and seamless database integration for businesses and organizations.

---

## FEATURES

- **AI-Powered Appointment Scheduling:**  
  Instantly schedule appointments via a smart assistant. The AI engine validates and finds the best available slot—no manual forms needed!
- **Easy Appointment Cancellation:**  
  Cancel appointments at any time just by asking the AI Assistant in natural language.
- **Appointment List & Status Tracking:**  
  View all appointments, track their status (Scheduled, Completed, Cancelled), and mark them as completed or cancelled.
- **Employee Availability Calendar:**  
  Real-time view of all employees’ schedules and available slots.
- **Google Calendar Export:**  
  Export selected appointments as `.ics` files for easy import into Google Calendar or Outlook.
- **Database Integration:**  
  All information is securely managed using a local SQLite database, created automatically on first run.
- **Business-Oriented Dashboard:**  
  Summary widgets for employee count, client count, appointments today, and available employees.
- **Modern GUI:**  
  Beautiful, responsive interface built with [ttkbootstrap](https://ttkbootstrap.readthedocs.io/) (Tkinter theme engine). Includes theme switching.
- **Welcome Animation:**  
  Engaging animated welcome screen for an enhanced user experience.

---

## REQUIREMENTS

- Python 3.8+
- SQLite (bundled with Python)
- pip (Python package manager)

**Python Libraries:**  
All dependencies are listed in `requirements.txt`. Main ones include:
- [`ttkbootstrap`](https://pypi.org/project/ttkbootstrap/) (GUI)
- [`ics`](https://pypi.org/project/ics/) (Calendar file export)
- [`pillow`](https://pypi.org/project/Pillow/) (Image support)
- [`tkinter`](https://docs.python.org/3/library/tkinter.html) (Standard GUI, included with Python)

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## SETUP AND INSTALLATION

1. **Clone this repository:**
   ```bash
   git clone https://github.com/adrivargascouri/smartscheduler.git
   cd smartscheduler
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

   - On first run, the database (`smartscheduler.db`) is created automatically, and sample employees are seeded if none exist.

---

## HOW TO USE

1. **Welcome & Dashboard:**  
   The app starts with a visually engaging welcome screen. Click “Enter” to access the dashboard.
   
   ![Screenshot 2025-06-20 144144](https://github.com/user-attachments/assets/31a43fb3-0235-4054-8277-7d94daa2016a)

3. **View Appointments:**  
   Browse, refresh, complete, cancel, and export appointments from the main table.
   
   ![Screenshot 2025-06-20 144304](https://github.com/user-attachments/assets/0a532cdb-6b39-4135-9a44-408993508a49)

5. **Schedule Appointments (AI Assistant):**  
   Go to the **AI Assistant** tab and follow the on-screen instructions to schedule new appointments using natural language.  
   > **Note:** Appointment scheduling is only available through the AI Assistant; there is no manual form.
   >
   > ![Screenshot 2025-06-20 170220](https://github.com/user-attachments/assets/24601916-94b8-44dd-b752-a61d20a45ee8)



   #### Example commands you can use in the AI Assistant tab:
   - `I want to schedule an appointment with Laura on Friday at 10 am.`
   - `Book a meeting with Carlos next Tuesday at 3 pm.`
   - `Show all my appointments for this month.`

   Just type your request in natural language and let the AI Assistant handle the rest!

6. **Cancel Appointments (AI Assistant):**  
   To cancel an appointment, simply ask the AI Assistant using natural language.  
   For example, you can type:
   - `I want to cancel an appointment.`
   - `Cancel my meeting with Laura next week.`
   - `Please remove my appointment with Carlos.`

   The AI will handle the cancellation for you—no need to search or select manually.

7. **Employee Calendar:**  
   Visualize employee schedules and free slots for better planning.

   ![Screenshot 2025-06-20 170431](https://github.com/user-attachments/assets/422be497-c5da-43ac-9a9a-7abb0210c6c0)

9. **Export to Calendar:**  
   Select one or more appointments and export them as `.ics` files to import into Google Calendar or Outlook.
10. **Switch Theme:**  
   Instantly toggle between visual themes using the theme switch button in the header.

  ![Screenshot 2025-06-20 170638](https://github.com/user-attachments/assets/40129f10-80cd-49d3-80ec-3c6328570f5c)


---

## DATABASE STRUCTURE

- **Engine:** SQLite (no setup needed)
- **Schema:** Automatically managed by the app (`create_tables()` on startup)
- **File:** Typically `smartscheduler.db` in the root/working directory
- **Seeding:** On first launch, adds sample employees if the DB is empty

---

## CONTRIBUTING

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-branch
   ```
3. Make your changes and commit them:
   ```bash
   git commit -am "Add new feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-branch
   ```
5. Create a new pull request.

---

## ACKNOWLEDGMENTS

- Thanks to all contributors!
- Built with Python, ttkbootstrap, ics, pillow, and SQLite.
- Logo and calendar images are optional; use your own for branding.

---

## LICENSE

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Explore the [project files here](https://github.com/adrivargascouri/smartscheduler/tree/master/)**  
_Note: For latest updates and full file listing, visit the [GitHub repository](https://github.com/adrivargascouri/smartscheduler/tree/master/)._
