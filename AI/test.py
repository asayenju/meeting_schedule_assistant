# import requests
# from datetime import datetime
# import pytz
# import requests

# import time

# import requests
# from pprint import pprint

# url = "http://localhost:8000/api/gmail/unread"

# # Define the query parameters
# params = {
#     "google_id": "112274170123197936875",
#     "max_results": 5,
#     "mark_as_read": False
# }

# # Make the GET request
# response = requests.get(url, params=params)

# def format_emails(data):
#     emails = data.get('emails', [])
#     result = []

#     for i, email in enumerate(emails, start=1):
#         email_str = (
#             f"Email {i}\n"
#             f"From: {email.get('from')}, Date: {email.get('date')}\n"
#             f"Subject: {email.get('subject')}\n"
#             f"Snippet: {email.get('snippet')}\n"
#         )
#         result.append(email_str)

#     return "\n".join(result)

# # Check the response
# if response.status_code == 200:
#     print(format_emails(response.json()))
# else:
#     print("Error:", response.status_code, response.text)

# Define the API URL
# url = "http://localhost:8001/get-response"

# # Define the input data
# data = {
#     "input": "do I have any meeting tomorrow"
# }

# # Make the POST request
# response = requests.post(url, json=data)

# # Check the response
# if response.status_code == 200:
#     print("Response:", response.json())
# else:
#     print("Error:", response.status_code, response.text)

# # Name of the time zone
# timezone_name = time.tzname[0]
# print("Time zone:", timezone_name)

# curr_datetime = datetime.now()
# print(str(curr_datetime))

# def send_email(recipient: str, subject: str, body: str) -> str:
#     # The API endpoint URL
#     url = "http://localhost:8000/api/gmail/send"

#     # The google_id is sent as a query parameter
#     params = {
#         "google_id": "112274170123197936875"
#     }

#     # The email details are sent in the JSON body
#     payload = {
#         "to": recipient,
#         "subject": subject,
#         "body": body
#     }

#     # Make the POST request with params and json
#     response = requests.post(url, params=params, json=payload)
#     print(response)

# send_email("teerat.nahm@gmail.com", "Test Subject", "This is a test email body.")

# url = "http://127.0.0.1:8000/api/calendar/create"
# params = {"google_id": "112274170123197936875"}
# data = {'summary': 'Gym Session', 'description': 'Meeting to discuss and plan gym activities.', 'start_time': '2025-11-09T15:00:00Z', 'end_time': '2025-11-09T17:00:00Z', 'timezone': timezone_name}

# response = requests.post(url, params=params, json=data)
# print(response.json())

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

