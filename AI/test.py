synthetic_data = {
    "busy": [
        {
            "start": "2025-11-08T08:00:00Z",
            "end": "2025-11-08T09:30:00Z"
        },
        {
            "start": "2025-11-08T12:00:00Z",
            "end": "2025-11-08T13:00:00Z"
        },
        {
            "start": "2025-11-08T15:30:00Z",
            "end": "2025-11-08T16:00:00Z"
        }
    ],
    "free": [
        {
            "start": "2025-11-08T05:40:24Z",
            "end": "2025-11-08T08:00:00Z"
        },
        {
            "start": "2025-11-08T09:30:00Z",
            "end": "2025-11-08T12:00:00Z"
        },
        {
            "start": "2025-11-08T13:00:00Z",
            "end": "2025-11-08T15:30:00Z"
        },
        {
            "start": "2025-11-08T16:00:00Z",
            "end": "2025-11-09T05:40:24Z"
        }
    ]
}



def parse_freebusy_data(freebusy_data):
    free = freebusy_data["calendars"]["primary"]["free"]
    busy = freebusy_data["calendars"]["primary"]["busy"]

    data = "Free times:\n"
    for slot in free:
        data += f"- From {slot['start']} to {slot['end']}\n"
    data += "Busy times:\n"
    for slot in busy:
        data += f"- From {slot['start']} to {slot['end']}\n"
    return data

print(parse_freebusy_data(data))