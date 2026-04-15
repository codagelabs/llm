import os
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

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
You are a helpful assistant of rahul shinde to provide information about rahul shinde
here is linkedin profile you can visit and find information about rahul 
 

if someone asked baout rahul you can read this information and answer the question

if you are not sure about the answer then say i am not sure
"""

def chat_with_openai(message, history):
    # Build messages: system prompt + prior history + current user message
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=messages,
            stream=True,
        )
        response_message = ""
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta is not None:
                response_message += delta
                yield response_message
    except Exception as e:
        yield f"Error: {str(e)}"


def main():
    gr.ChatInterface(
        fn=chat_with_openai,
        title="Chat Boat",
        description="Ask me anything",
    ).launch()


if __name__ == "__main__":
    main()
