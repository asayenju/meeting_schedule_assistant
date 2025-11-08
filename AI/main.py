from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from collections import deque
import datetime as datetime
import pytz

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

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
    return """ my availablity between {start_range} and {end_range} is as follows:
    🟢 Free Times:
        - Sat, Nov 08, 2025 12:40 AM → Sat, Nov 08, 2025 03:00 AM
        - Sat, Nov 08, 2025 04:30 AM → Sat, Nov 08, 2025 07:00 AM
        - Sat, Nov 08, 2025 08:00 AM → Sat, Nov 08, 2025 10:30 AM
        - Sat, Nov 08, 2025 11:00 AM → Sun, Nov 09, 2025 12:40 AM
        🔴 Busy Times:
        - Sat, Nov 08, 2025 03:00 AM → Sat, Nov 08, 2025 04:30 AM
        - Sat, Nov 08, 2025 07:00 AM → Sat, Nov 08, 2025 08:00 AM
        - Sat, Nov 08, 2025 10:30 AM → Sat, Nov 08, 2025 11:00 AM
        """
    # availability = None #call ashwin function
    # return summarize_calendar(availability)
    
def setup_meeting(day:str, start_time: str, end_time: str) -> str:
    print(f"Setting up meeting on {day} from {start_time} to {end_time}...")
    return f"Meeting scheduled on {day} from {start_time} to {end_time}."

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
            description="Schedule a meeting on a given day and time range.",
            parameters={
                "type": "object",
                "properties": {
                    "day": {"type": "string", "description": "The day of the meeting, e.g., 'Monday'."},
                    "start_time": {"type": "string", "description": "Start time in HH:MM format or ISO 8601."},
                    "end_time": {"type": "string", "description": "End time in HH:MM format or ISO 8601."}
                },
                "required": ["day", "start_time", "end_time"]
            }
        )
    ]
)

config = types.GenerateContentConfig(
    tools=[get_availability_tool, setup_meeting_tool]
)

MAX_HISTORY = 8
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
