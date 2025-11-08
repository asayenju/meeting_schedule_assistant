from datetime import datetime, timedelta
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = FastAPI()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Get absolute paths for credentials and token
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

@app.get("/freebusy")
def get_freebusy():
    service = get_calendar_service()

    now = datetime.utcnow().isoformat() + 'Z'
    end_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'

    body = {
        "timeMin": now,
        "timeMax": end_time,
        "items": [{"id": "primary"}]
    }

    freebusy_result = service.freebusy().query(body=body).execute()
    busy_times = freebusy_result['calendars']['primary']['busy']

    # Calculate free slots
    last_end = datetime.fromisoformat(now[:-1])
    free_slots = []
    for period in busy_times:
        start = datetime.fromisoformat(period['start'][:-1])
        if start > last_end:
            free_slots.append({"start": last_end.isoformat(), "end": start.isoformat()})
        last_end = datetime.fromisoformat(period['end'][:-1])

    end_dt = datetime.fromisoformat(end_time[:-1])
    if last_end < end_dt:
        free_slots.append({"start": last_end.isoformat(), "end": end_dt.isoformat()})

    response = {
        "busy": busy_times,
        "free": free_slots
    }

    return JSONResponse(content=response)
