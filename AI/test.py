import requests
from datetime import datetime
import pytz

availability = requests.get(
        "http://localhost:8000/api/calendar/freebusy",
        params={
            "start_range": "2025-11-08T09:00:00Z",
            "end_range": "2025-11-08T17:00:00Z"
        }
    ).json()

def summarize_calendar(data, timezone="US/Eastern"):
    def fmt(dt_str):
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone(pytz.timezone(timezone))
        return local_dt.strftime("%a, %b %d, %Y %I:%M %p")

    summary = []

    if "free" in data and data["free"]:
        summary.append("Free Times:")
        for slot in data["free"]:
            summary.append(f"  - {fmt(slot['start'])} → {fmt(slot['end'])}")

    if "busy" in data and data["busy"]:
        summary.append("Busy Times:")
        for slot in data["busy"]:
            summary.append(f"  - {fmt(slot['start'])} → {fmt(slot['end'])}")

    return "\n".join(summary)


print(summarize_calendar(availability))

