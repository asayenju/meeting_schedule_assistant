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
        "google_id": 103748791506482361674,
        "start_range": "2025-11-08T09:00:00Z",
        "end_range": "2025-11-08T17:00:00Z"
    }).json()
    print(availability)
    return summarize_calendar(availability)

def send_email(recipient: str, subject: str, body: str) -> str:
    payload = {
        "to": recipient,
        "subject": subject,
        "body": body
    }

    response = requests.post("http://localhost:8000/gmail/send", json=payload)
    return f"Email sent to {recipient} with subject '{subject}'." if response.text == "Success" else "Failed to send email."
    
def setup_meeting(summary: str, description: str, start_time: str, end_time: str) -> str:
    event_data = {
        "summary": summary,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": "UTC"
    }
    print(event_data)

    response = requests.post("http://localhost:8000/calendar/create", json=event_data)
    print(response)
    return f"Meeting scheduled successfully from {start_time} to {end_time}." if response.status_code == 200 else "Failed to schedule meeting."

def retrieve_email() -> str:
    print("Retrieving new emails...")
    return "Email 1: Hi Nahm, would you be available to meet at 8 pm on november 8 Email 2: I want to meet for project discussion, what time are you available?"

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

MAX_HISTORY = 5
conversation_history = deque(maxlen=MAX_HISTORY)

system_instruction = """
You are a virtual scheduling assistant. Your goal is to schedule meetings accurately based on the user's availability.

Rules:
1. You **must always check the user's availability** using the `get_current_availability` function before proposing or scheduling any meeting. Do not assume availability.
2. Only after confirming an available time can you schedule the meeting using the `setup_meeting` function.
3. If the proposed time conflicts with the user's availability, suggest alternative times based on their availability. Confirm with the user before scheduling.
4. Respond politely to the user, but never reference yourself as an AI or mention limitations.
5. Only take actions necessary to schedule meetings; do not provide unrelated commentary.
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
