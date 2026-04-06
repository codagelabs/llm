from typing import override
import os
from dotenv import load_dotenv
from scraper import fetch_website_contents, fetch_website_links
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

console = Console()

system_prompt = "You are an assistant that analyzes the text contents of a website and provides a short summary."
user_prompt_prefix = "Please provide a concise summary of the following website contents:\n\n"

def messages_for(website):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_prefix + website}
    ]

def summarize(url):
    website = fetch_website_contents(url)
    response = client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = messages_for(website)
    )
    return response.choices[0].message.content


def display_summary(url):
    summary = summarize(url)
    console.print(Markdown(summary))

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

client = OpenAI(api_key=api_key)

display_summary("https://github.com/codagelabs")
