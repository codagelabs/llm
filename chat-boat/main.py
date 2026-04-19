import os
import json
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from scraper import fetch_website_contents

# Load env and set up globals once at startup
load_dotenv(override=True)
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print("API Key loaded successfully")
else:
    print("API Key not found")

openai_client = OpenAI(api_key=api_key)
model_name = "gpt-5-mini"
system_prompt = """
You are a helpful assistant of Rahul to provide information about Rahul 
provide an one line response
"""

website_content = ""

def get_profile_details(arguments):
    global website_content
    if not website_content=="":
        return website_content
    
    url = "https://www.linkedin.com/in/rahul-shinde-72b605142/" 
    content = fetch_website_contents(url)
    print(f"content {content}")

    response = openai_client.chat.completions.create(
        model=model_name,
            messages=[
                {"role": "system", "content": "Extract every meaningful information from the content"},
                {"role": "user", "content": content},
            ],
        )

    website_content = response.choices[0].message.content
    return website_content
    

    

price_function = {
        "name": "get_profile_details",
        "description": "Get the profile details of rahul shinde",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the person",
                },
            },
            "required": ["name"],
            "additionalProperties": False
        }
    }

tools = [{"type": "function", "function": price_function}]

def handle_tool_call(message):
    print("handle_tool_call:", json.dumps(message.model_dump(), indent=2))
    tool_calls = message.tool_calls
    print(f"tool_calls {tool_calls}")
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments
        if function_name == "get_profile_details":
            response = {
            "role": "tool",
            "content": get_profile_details(json.loads(function_args)),
            "tool_call_id": tool_call.id
            }

            return response
            
    


def chat_with_openai(message, history):
    # Build messages: system prompt + prior history + current user message
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    print(messages)

    
    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools, 
        )

        print(response)
        
        if response.choices[0].finish_reason=="tool_calls":
            message = response.choices[0].message
            print(f"message {message}")
            response = handle_tool_call(message)
            messages.append(message)
            messages.append(response)
            response = openai_client.chat.completions.create(model=model_name, messages=messages)
    
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def main():
    gr.ChatInterface(
        fn=chat_with_openai,
        type="messages",
        title="Rahul's chat Boat",
    ).launch()


if __name__ == "__main__":
    main()
