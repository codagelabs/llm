# Website Summarizer App

This is a Python application that fetches the content of a given website, strips away unnecessary HTML boilerplate (like scripts, images, and styles), and uses an OpenAI Large Language Model (LLM) to generate a concise summary. The result is then elegantly displayed in the terminal using Markdown parsing.

## Features
- **Web Scraping:** Uses `BeautifulSoup` and `requests` to fetch and parse HTML content.
- **AI Summary:** Interfaces with OpenAI's Chat Completion API (`gpt-3.5-turbo`) to analyze site text.
- **Terminal Rendering:** Uses the `rich` library to beautifully print the markdown-formatted summary directly to standard output.
- **Secure Credentials:** Keeps API keys secure locally via `python-dotenv`.

## Environment Setup
This project uses [uv](https://github.com/astral-sh/uv) to quickly manage Python dependencies. 

1. Create a `.env` file in the parent directory (`../.env`) if you haven't already.
2. Add your OpenAI API key:
```env
OPENAI_API_KEY="sk-proj-your-api-key..."
```

## Running the Application
Since we use `uv`, you don't need to manually create virtual environments or run `pip install`. Just run:

```bash
uv run main.py
```

`uv` will take care of automatically instantiating the environment with all packages found in `pyproject.toml` and executing the script.

## Core Libraries Used
- **`openai`**: Official Python client for OpenAI's API.
- **`beautifulsoup4`**: Extracts human-readable text from raw HTML.
- **`requests`**: For making HTTP network requests to fetch the target URL.
- **`rich`**: For rendering the LLM's Markdown output into aesthetic CLI logs.
- **`python-dotenv`**: Scans for `.env` files to prevent committing API keys.
