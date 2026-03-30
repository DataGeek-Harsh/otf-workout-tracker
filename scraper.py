import os
import base64
import re
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES =['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_email_body(payload):
    """Recursively search for the email body."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif 'parts' in part:
                return get_email_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return ""

def parse_otf_data(html_body, date_str):
    """Parse the HTML body of the OTF email to extract metrics."""
    soup = BeautifulSoup(html_body, 'html.parser')
    text = soup.get_text(separator=' ') # Flatten HTML to plain text

    # Helper function to safely turn extracted text into numbers (removes commas)
    def parse_number(val, default=0):
        try:
            return float(val.replace(',', ''))
        except:
            return default

    # Helper function to find the FIRST match of a pattern
    def extract_metric(pattern, text, default=0):
        match = re.search(pattern, text, re.IGNORECASE)
        return parse_number(match.group(1)) if match else default

    # Updated Regex to match OTF's specific email formatting
    calories = extract_metric(r'([\d,]+)\s+CALORIES BURNED', text)
    splats = extract_metric(r'([\d,]+)\s+SPLAT POINTS', text)
    steps = extract_metric(r'([\d,]+)\s+STEPS', text)
    
    # Speed is formatted as "AVG. SPEED [lots of space] 4.8 mph"
    avg_speed = extract_metric(r'AVG\. SPEED\s+([\d.]+)\s+mph', text)
    # Max speed is formatted just below Avg speed
    max_speed = extract_metric(r'AVG\. SPEED[\s\S]*?Max:\s+([\d.]+)', text)

    # Zones are 5 consecutive numbers followed by "MINUTES / ZONE"
    zones_match = re.search(r'(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+MINUTES / ZONE', text, re.IGNORECASE)
    if zones_match:
        zone1 = parse_number(zones_match.group(1)) # Grey
        zone2 = parse_number(zones_match.group(2)) # Blue
        zone3 = parse_number(zones_match.group(3)) # Green
        zone4 = parse_number(zones_match.group(4)) # Orange
        zone5 = parse_number(zones_match.group(5)) # Red
    else:
        zone1 = zone2 = zone3 = zone4 = zone5 = 0

    data = {
        "Date": datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z").date(),
        "Calories": calories,
        "Splat Points": splats,
        "Steps": steps,
        "Avg Speed": avg_speed,
        "Max Speed": max_speed,
        "Zone 1 (Grey)": zone1,
        "Zone 2 (Blue)": zone2,
        "Zone 3 (Green)": zone3,
        "Zone 4 (Orange)": zone4,
        "Zone 5 (Red)": zone5
    }
    return data

def fetch_otf_workouts(max_results=50, after_date=None): 
    service = authenticate_gmail()
    
    # Query for OTF emails
    query = "from:OTbeatReport@orangetheoryfitness.com"
    
    # Add the date filter to the Gmail query if the user provided one
    if after_date:
        query += f" after:{after_date}"
        
    results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
    messages = results.get('messages',[])

    workouts =[]
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        
        # Get Date
        headers = msg_data['payload']['headers']
        date_str = next(h['value'] for h in headers if h['name'] == 'Date')
        
        # Get Body & Parse
        html_body = get_email_body(msg_data['payload'])
        workout_data = parse_otf_data(html_body, date_str)
        workouts.append(workout_data)

    return pd.DataFrame(workouts)