import os
import requests
from dotenv import load_dotenv


load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("Error: no api key found")
elif not api_key.startswith("sk-proj-"):
    print("Error: invalid api key")
elif api_key.strip() != api_key:
    print("Error: invalid api key, might contains whitespace")
else:
    print("API key is valid")

header={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
payload={
    "model": "gpt-4.1-nano",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, Open AI its Rahul"}
    ]

}

response = requests.post(
    "https://api.openai.com/v1/chat/completions", 
    headers=header,
    json=payload
)

print(response.json()["choices"][0]["message"]["content"])






