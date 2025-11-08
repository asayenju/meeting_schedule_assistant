import requests
from datetime import datetime
import pytz
import requests

url = "http://127.0.0.1:8000/api/calendar/create"
params = {"google_id": "112274170123197936875"}
data = {
    "summary": "Test Meeting",
    "description": "Test description",
    "start_time": "2025-11-08T10:00:00Z",
    "end_time": "2025-11-08T11:00:00Z",
    "timezone": "UTC"
}

response = requests.post(url, params=params, json=data)
print(response.json())

# availability = requests.get(
#     "http://localhost:8000/api/calendar/freebusy",
#     params={
#         "google_id": 108790826938109809514,  # Add this - REQUIRED
#         "start_range": "2025-11-15T00:00:00Z",
#         "end_range": "2025-11-15T23:59:59Z"
#     }
# ).json()

# print(availability)

# def summarize_calendar(data, timezone="US/Eastern"):
#     def fmt(dt_str):
#         dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
#         local_dt = dt.astimezone(pytz.timezone(timezone))
#         return local_dt.strftime("%a, %b %d, %Y %I:%M %p")

#     summary = []

#     if "free" in data and data["free"]:
#         summary.append("Free Times:")
#         for slot in data["free"]:
#             summary.append(f"  - {fmt(slot['start'])} → {fmt(slot['end'])}")

#     if "busy" in data and data["busy"]:
#         summary.append("Busy Times:")
#         for slot in data["busy"]:
#             summary.append(f"  - {fmt(slot['start'])} → {fmt(slot['end'])}")

#     return "\n".join(summary)


# print(summarize_calendar(availability))

