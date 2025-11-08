from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from service.google_service import get_calendar_service
from pydantic import BaseModel

class EventRequest(BaseModel):
    summary: str
    description: str | None = None
    start_time: str     # ISO datetime string
    end_time: str       # ISO datetime string
    timezone: str = "UTC"


router = APIRouter(prefix="/calendar", tags=["Calendar"])

@router.get("/freebusy")
def get_freebusy(start_range: str = None, end_range: str = None):
    """Get free/busy calendar information"""
    try:
        service = get_calendar_service()

        now = start_range
        end_time = end_range

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/create")
async def create_event(event: EventRequest):
    """Create an event in Google Calendar."""
    try:
        service = get_calendar_service()

        event_body = {
            "summary": event.summary,
            "description": event.description,
            "start": {
                "dateTime": event.start_time,
                "timeZone": event.timezone
            },
            "end": {
                "dateTime": event.end_time,
                "timeZone": event.timezone
            }
        }

        created_event = (
            service.events()
            .insert(calendarId="primary", body=event_body)
            .execute()
        )

        return JSONResponse(content=created_event)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))