import json
from collections import deque
from datetime import datetime
import pytz
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

# --- Setup ---
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

MAX_HISTORY = 8
conversation_history = deque(maxlen=MAX_HISTORY)

system_instruction = """
You are a virtual scheduling assistant. Your goal is to schedule meetings accurately based on the user's availability.

Rules:
1. You **must always check the user's availability** using `get_current_availability` before proposing or scheduling any meeting. Do not assume availability.
2. Only after confirming an available time can you schedule a meeting using `setup_meeting`.
3. If the proposed time conflicts with the user's availability, suggest alternative times based on their availability. Confirm with the user before scheduling.
4. Respond politely and concisely.
5. Never mention being an AI.
"""

# --- Utility: Format and summarize availability ---
def summarize_calendar(data, timezone="US/Eastern"):
    def fmt(dt_str):
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        local_dt = dt.astimezone(pytz.timezone(timezone))
        return local_dt.strftime("%a, %b %d, %Y %I:%M %p")

    free = data.get("free", [])
    busy = data.get("busy", [])
    return {
        "free": [{"start": fmt(slot["start"]), "end": fmt(slot["end"])} for slot in free],
        "busy": [{"start": fmt(slot["start"]), "end": fmt(slot["end"])} for slot in busy],
    }

# --- Fixed function ---
def get_current_availability(start_range: str, end_range: str) -> str:
    """Check calendar availability using the local FastAPI backend."""
    try:
        print(f"Checking availability from {start_range} to {end_range}...")
        resp = requests.get(
            "http://localhost:8000/api/calendar/freebusy",
            params={"start_range": start_range, "end_range": end_range},
            timeout=10,
        )
        resp.raise_for_status()
        availability = resp.json()
        summary = summarize_calendar(availability)
        # Return structured JSON so Gemini can parse it
        return json.dumps(summary)
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- Your other tools (simplified for clarity) ---
def setup_meeting(summary: str, description: str, start_time: str, end_time: str) -> str:
    try:
        event_data = {
            "summary": summary,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": "UTC",
        }
        resp = requests.post("http://localhost:8000/calendar/create", json=event_data, timeout=10)
        resp.raise_for_status()
        return f"Meeting scheduled successfully: {summary} from {start_time} to {end_time}."
    except Exception as e:
        return f"Failed to schedule meeting: {e}"

# --- Gemini tool definitions ---
get_availability_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_current_availability",
            description="Get the user's calendar availability for a date range.",
            parameters={
                "type": "object",
                "properties": {
                    "start_range": {"type": "string"},
                    "end_range": {"type": "string"},
                },
                "required": ["start_range", "end_range"],
            },
        )
    ]
)

setup_meeting_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="setup_meeting",
            description="Create a Google Calendar meeting event.",
            parameters={
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"},
                },
                "required": ["summary", "description", "start_time", "end_time"],
            },
        )
    ]
)

config = types.GenerateContentConfig(
    tools=[get_availability_tool, setup_meeting_tool]
)

# --- 🧠 Main conversation loop ---
def generate_response(user_input: str):
    conversation_history.append(f"User: {user_input}")
    contents = [system_instruction] + list(conversation_history)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config,
    )

    if response.function_calls:
        for func_call in response.function_calls:
            fn_name = func_call.name
            args = dict(func_call.args)
            fn = globals().get(fn_name)

            if fn:
                print(f"Calling {fn_name} with args: {args}")
                try:
                    result = fn(**args)
                    # 🔑 Always tell Gemini what the function returned
                    conversation_history.append(f"Tool {fn_name} output:\n{result}")
                except Exception as e:
                    conversation_history.append(f"Tool {fn_name} error: {e}")
            else:
                conversation_history.append(f"Tool {fn_name} not found")

        # 🔁 Second call — now Gemini continues based on tool result
        contents = [system_instruction] + list(conversation_history)
        final = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
        conversation_history.append(f"Assistant: {final.text}")
        return final.text

    else:
        conversation_history.append(f"Assistant: {response.text}")
        return response.text

# --- Run loop ---
if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        answer = generate_response(user_input)
        print(f"Assistant: {answer}")
