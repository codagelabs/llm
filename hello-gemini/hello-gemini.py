from openai import OpenAI
import os
from dotenv import load_dotenv



load_dotenv(override=True)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: no api key found")
elif api_key.strip() != api_key:
    print("Error: invalid api key, might contains whitespace")
else:
    print("API key is valid")


gemini = OpenAI(base_url="https://generativelanguage.googleapis.com/v1beta/openai", api_key=api_key)

response = gemini.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, Gemini its Rahul"}
    ]
)

print(response.choices[0].message.content)
