# Hello Gemini

A minimal Python script that demonstrates how to call **Google Gemini** using the **OpenAI-compatible API** — no separate Gemini SDK required.

## How It Works

Google's Generative Language API exposes an OpenAI-compatible endpoint, which means you can reuse the standard `openai` Python client by simply pointing it to Google's base URL:

```
https://generativelanguage.googleapis.com/v1beta/openai
```

The script sends a simple chat message to `gemini-2.0-flash` and prints the model's response to the terminal.

## Prerequisites

### Get a Google API Key
1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create an API key for the Generative Language API.

### Set Up the `.env` File
Create a `.env` file in the parent directory (`../.env`) and add your key:

```env
GOOGLE_API_KEY="your-google-api-key-here"
```

## Environment Setup

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
uv sync
```

## Running the Script

```bash
uv run hello-gemini.py
```

Expected output:
```
API key is valid
Hello Rahul! How can I assist you today?
```

## Core Libraries Used
- **`openai`**: Used as the HTTP client, pointed at Google's OpenAI-compatible Gemini endpoint.
- **`python-dotenv`**: Loads the `GOOGLE_API_KEY` from a `.env` file securely.
