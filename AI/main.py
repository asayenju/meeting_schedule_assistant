from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def get_current_weather(city: str) -> str:
    if "boston" in city.lower():
        return "The weather in Boston is currently 5°C and cloudy with a chance of light snow."
    elif "tokyo" in city.lower():
        return "The weather in Tokyo is currently 12°C and sunny."
    else:
        return f"Weather data for {city} is not available."
    
def say_hello(name: str) -> str:
    return f"Hello, {name}! How can I assist you today?"

AVAILABLE_TOOLS = [get_current_weather, say_hello]

config = types.GenerateContentConfig(
    tools=AVAILABLE_TOOLS
)

def generate_response(prompt: str):
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt,
        config=config
    )
    
    if response.function_calls:
        function_responses = []
        
        for func_call in response.function_calls:
            function_name = func_call.name
            args = dict(func_call.args)
            
            tool_function = globals().get(function_name)
            
            if tool_function:
                function_output = tool_function(**args)
                
                function_responses.append(
                    {"function_name": function_name, "response": function_output}
                )
            else:
                print(f"   - Error: Tool {function_name} not found.")

        contents = [response.candidates[0].content]

        for f_response in function_responses:
            contents.append(
                types.Part.from_function_response(
                    name=f_response["function_name"], 
                    response=f_response["response"]
                )
            )

        final_response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=contents
        )

        return final_response.text
        
    else:
        return response.text

if __name__ == "__main__":
    prompt = "What is the weather like in Boston? also say hello to minh"

    print("="*60)
    result1 = generate_response(prompt)
    print(f"\nResponse: {result1}")