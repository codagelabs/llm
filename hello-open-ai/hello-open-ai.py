# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "openai",
#     "python-dotenv",
# ]
# ///

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

def main():
    api_key = os.getenv('OPENAI_API_KEY')   
    print(api_key)
    if not api_key:
        print("Error: no api key found")
        return
    elif not api_key.startswith("sk-proj-"):
        print("Error: invalid api key")
        return
    elif api_key.strip() != api_key:
        print("Error: invalid api key, might contains whitespace")
        return
    else:
        print("API key is valid")
        

    client = OpenAI(api_key=api_key)

    print("Sending request to OpenAI (model: gpt-3.5-turbo)...")
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, Open AI its Rahul"}
            ]
        )
        print("\nResponse from OpenAI:")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()