from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from collections import deque

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

data = {
  "kind": "calendar#freeBusy",
  "timeMin": "2025-11-07T09:00:00Z",
  "timeMax": "2025-11-07T18:00:00Z",
  "calendars": {
    "primary": {
      "busy": [
        {
          "start": "2025-11-07T10:00:00Z",
          "end": "2025-11-07T11:30:00Z"
        },
        {
          "start": "2025-11-07T13:00:00Z",
          "end": "2025-11-07T14:00:00Z"
        },
        {
          "start": "2025-11-07T15:30:00Z",
          "end": "2025-11-07T16:00:00Z"
        }
      ]
    }
  },
  "groups": {},
  "errors": []
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

def get_current_availability(day: str) -> str:
    return f"My availability on {day} is from"
    
def setup_meeting(day:str, start_time: str, end_time: str) -> str:
    print(f"Setting up meeting on {day} from {start_time} to {end_time}...")
    return f"Meeting scheduled on {day} from {start_time} to {end_time}."

AVAILABLE_TOOLS = [get_current_availability, setup_meeting]
config = types.GenerateContentConfig(tools=AVAILABLE_TOOLS)

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
