# Website Summarizer (Ollama — Local LLM)

This is a Python application that fetches the content of a given website, strips away unnecessary HTML boilerplate (like scripts, images, and styles), and uses a **locally running LLM via [Ollama](https://ollama.com)** to generate a concise summary. The result is then elegantly displayed in the terminal using Markdown rendering — all without sending data to any external cloud API.

## Features
- **Web Scraping:** Uses `BeautifulSoup` and `requests` to fetch and parse HTML content.
- **Local AI Summary:** Interfaces with a locally running Ollama instance using the OpenAI-compatible API (`llama3.2` model).
- **No API Key Required:** Runs entirely on your machine — no OpenAI account or billing needed.
- **Terminal Rendering:** Uses the `rich` library to beautifully print the markdown-formatted summary directly to standard output.

## Prerequisites

### Install Ollama
Download and install Ollama from [https://ollama.com](https://ollama.com), then pull the required model:

```bash
ollama pull llama3.2
```

Make sure the Ollama server is running before executing the script:

```bash
ollama serve
```

> By default, Ollama exposes an OpenAI-compatible API at `http://localhost:11434/v1`.

## Environment Setup
This project uses [uv](https://github.com/astral-sh/uv) to manage Python dependencies.

Install dependencies with:

```bash
uv sync
```

## Running the Application

```bash
uv run main.py
```

`uv` will automatically set up the virtual environment from `pyproject.toml` and run the script. No manual `pip install` needed.

## How It Works

1. The script connects to the locally running Ollama server at `http://localhost:11434/v1`.
2. It uses the `openai` Python client pointing to that local endpoint (with `api_key="ollama"` as a placeholder — no real key needed).
3. It fetches and parses the target website's text content.
4. It sends the content to the `llama3.2` model for summarization.
5. The response is rendered as Markdown in the terminal via `rich`.

## Core Libraries Used
- **`openai`**: Used as an HTTP client pointing to the Ollama local API endpoint.
- **`beautifulsoup4`**: Extracts human-readable text from raw HTML.
- **`requests`**: For making HTTP network requests to fetch the target URL.
- **`rich`**: For rendering the LLM's Markdown output into aesthetic CLI output.
