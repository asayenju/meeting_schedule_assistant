from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from collections import deque
from datetime import datetime
import pytz
import requests

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
google_id = os.getenv("GOOGLE_ID")
client = genai.Client(api_key=api_key)

# -------- Start Tools Functions ----------- #

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

def get_current_availability(start_range: str, end_range: str) -> str:
    print(start_range, end_range)
    availability = requests.get(
        "http://localhost:8000/api/calendar/freebusy",
            params={
                "google_id": google_id,
                "start_range": start_range,
                "end_range": end_range
            }
        ).json()
    print(availability)
    return summarize_calendar(availability)

def send_email(recipient: str, subject: str, body: str) -> str:
    url = "http://localhost:8000/api/gmail/send"

    params = {
        "google_id": str(google_id)
    }
    payload = {
        "to": recipient,
        "subject": subject,
        "body": body
    }

    response = requests.post(url, params=params, json=payload)
    return f"Email sent to {recipient} with subject '{subject}'." if response.status_code == 200 else "Failed to send email."
    
def setup_meeting(summary: str, description: str, start_time: str, end_time: str) -> str:
    params = {"google_id": str(google_id)}
    data = {
        "summary": summary,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": "UTC"
    }
    print(data)

    response = requests.post("http://127.0.0.1:8000/api/calendar/create", params=params, json=data)
    print(response)
    return f"Meeting scheduled successfully from {start_time} to {end_time}." if response.status_code == 200 else "Failed to schedule meeting."

def format_emails(data):
    emails = data.get('emails', [])
    result = []

    for i, email in enumerate(emails, start=1):
        email_str = (
            f"Email {i}\n"
            f"From: {email.get('from')}, Date: {email.get('date')}\n"
            f"Subject: {email.get('subject')}\n"
            f"Snippet: {email.get('snippet')}\n"
        )
        result.append(email_str)

    return "\n".join(result)

def retrieve_email() -> str:
    url = "http://localhost:8000/api/gmail/unread"

    params = {
        "google_id": str(google_id),
        "max_results": 5,
        "mark_as_read": False
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return format_emails(response.json())
    else:
        return "Failed to retrieve emails."

get_availability_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_current_availability",
            description="Get the user's current availability during start_range to end_range.",
            parameters={
                "type": "object",
                "properties": {
                    "start_range": {
                        "type": "string",
                        "description": "The beginning of the range to check availability. Format: 'YYYY-MM-DDTHH:MM:SSZ'."
                    },
                    "end_range": {
                        "type": "string",
                        "description": "The beginning of the range to check availability. Format: 'YYYY-MM-DDTHH:MM:SSZ'."
                    }
                },
                "required": ["start_range", "end_range"]
            }
        )
    ]
)

setup_meeting_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="setup_meeting",
            description="Schedule a meeting by create a calendar event on a given day and time range. Generate a short meeting agenda based on the context of the meeting scheduled.",
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Summary or title of the meeting."},
                    "description": {"type": "string", "description": "Description or agenda of the meeting."},
                    "start_time": {"type": "string", "description": "Start time in 'YYYY-MM-DDTHH:MM:SSZ' format."},
                    "end_time": {"type": "string", "description": "End time in 'YYYY-MM-DDTHH:MM:SSZ' format."}
                },
                "required": ["summary", "description", "start_time", "end_time"]
            }
        )
    ]
)

send_email_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="send_email",
            description="Send an email to a specified recipient. make sure to include recipient, subject, and body based on the context of the meeting scheduled.",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Email address of the recipient."},
                    "subject": {"type": "string", "description": "Subject of the email."},
                    "body": {"type": "string", "description": "Body content of the email."}
                },
                "required": ["recipient", "subject", "body"]
            }
        )
    ]
)

retrieve_email_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="retrieve_email",
            description="Retrieve new emails from the inbox.",
            parameters={
                "type": "object",
                "properties": {
                },
                "required": []
            }
        )
    ]
)

config = types.GenerateContentConfig(
    tools=[get_availability_tool, setup_meeting_tool, send_email_tool, retrieve_email_tool]
)

# -------- End Tools Functions ----------- #

MAX_HISTORY = 10
conversation_history = deque(maxlen=MAX_HISTORY)

curr_datetime = datetime.now()

system_instruction = """
You are a virtual scheduling assistant. You can perform two types of tasks: sending emails and scheduling meetings.

Rules:

1. **Sending emails**:
   - If the user asks you to send an email, do so using the `send_email` function.
   - After sending an email, confirm to the user that the email has been sent.
   - Do **not** suggest or ask about setting up a meeting unless explicitly instructed.

2. **Scheduling meetings**:
   - Only if the user explicitly asks to schedule a meeting, check the user's availability using the `get_current_availability` function before proposing any times.
   - Only after confirming an available time should you schedule the meeting using the `setup_meeting` function.
   - If the proposed time conflicts with the user's availability, suggest alternative times based on their availability and confirm with the user before scheduling.
3. The current date and time is: """ + curr_datetime.strftime("%Y-%m-%d %H:%M:%S") + """. Imply user's query word like today, tomorrow, next week based on this current date.
4. Always respond politely to the user.  
5. Never reference yourself as an AI or mention limitations.  
6. Only take actions necessary for the user's request; do not provide unrelated commentary.

"""


def generate_response(user_input: str):
    conversation_history.append(f"User: {user_input}")

    contents = [system_instruction] + list(conversation_history)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )

    if response.function_calls:
        for func_call in response.function_calls:
            function_name = func_call.name
            args = dict(func_call.args)
            
            tool_function = globals().get(function_name)
            if tool_function:
                function_output = tool_function(**args)
                conversation_history.append(f"Function {function_name} output: {function_output}")
            else:
                print(f"Tool {function_name} not found.")

        contents = [system_instruction] + list(conversation_history)
        final_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents
        )
        conversation_history.append(f"Assistant: {final_response.text}")
        return final_response.text
    else:
        conversation_history.append(f"Assistant: {response.text}")
        return response.text

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        result = generate_response(user_input)
        print(f"Assistant: {result}")
    # print(generate_response("do we have any meeting tomorrow?"))
