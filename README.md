# 🍊 Orangetheory Fitness (OTF) Email Tracker

A Python Web App (built with Streamlit) that securely reads your Orangetheory Fitness workout summary emails straight from your Gmail, parses the data, and builds interactive trend charts. 

## 🔒 Privacy & Cost (Important!)
* **100% Free:** This uses the Google Gmail API. Google provides a massive free tier (1 Billion requests per month). You **do not** need to enter a credit card or set up a billing account to use this for your personal emails.
* **Read-Only Access:** This app requests `gmail.readonly` access. It can only *view* your emails. It literally does not have the permissions required to send, modify, or delete any of your emails.
* **Local Processing:** Your email data never leaves your computer. The app downloads the data directly from Google to your machine and displays it on a local web server.

---

## 🛠️ Setup Instructions

### Step 1: Clone the repository
Download this code to your local machine:
```bash
git clone https://github.com/DataGeek-Harsh/otf-workout-tracker.git
cd otf-workout-tracker

```
### Step 2: Set up Virtual Environment
###For Windows
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

###For Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

```

### Step 3: Get your Google Credentials
Because this app reads your private emails, you must create your own private "key" to access them.

Go to theGoogle Cloud Console. Log in with your Google account.

At the top left, click Select a Project -> New Project. Name it "OTF Tracker" and click Create.

In the search bar at the top, type Gmail API and select it. Click the blue Enable button.

On the left sidebar, click OAuth consent screen.
Choose External and click Create.

App Name: "OTF Tracker" (or whatever you want).
User Support Email: Select your email from the dropdown.
Developer Contact Info: Enter your email again.
Click Save and Continue until you reach the Test Users step.
CRITICAL: Click + Add Users and type in the exact Gmail address you use for Orangetheory. Click Save.
On the left sidebar, click Credentials.
Click + Create Credentials at the top -> OAuth client ID.
Application Type: Select Desktop App.
Name: "OTF Scraper Desktop" (or leave as default).
Click Create.
A box will pop up with your Client ID. Click the Download JSON button.
Rename that downloaded file to exactly credentials.json and move it into the main folder of this project (the exact same folder where app.py is located).

###Step 4: Run the Application!
```bash
streamlit run app.py
```
⚠️ The "First Login" Warning
When you click "Fetch Latest Workouts" in the app for the first time, a browser window will open asking you to log into Google.
Because you created this app in "Test Mode" for yourself (and didn't pay Google to formally verify it), Google will show a scary warning screen saying "Google hasn't verified this app."
This is completely normal because you are the developer!
Click Advanced at the bottom of the warning.
Click Go to OTF Tracker (unsafe).
Click Continue to grant the app read-only access to your Gmail.
The app will securely save a token.json file on your computer so you don't have to repeat this login step every time you want to see your updated stats.
Enjoy your workout trends! 🏃‍♂️🚣‍♀️🏋️‍♀️