# 🤖 Chat Boat

A conversational AI chatbot built with **OpenAI** and **Gradio**, featuring streaming responses and full multi-turn conversation history support.

---

## ✨ Features

- 💬 **Multi-turn conversations** — remembers the full chat history so context carries across messages
- ⚡ **Streaming responses** — replies appear token-by-token in real time
- 🧠 **Custom system prompt** — persona can be tailored (currently set up as Rahul Shinde's personal assistant)
- 🌐 **Web UI** — clean browser-based interface powered by Gradio
- 🔐 **Secure API key loading** — uses `.env` file via `python-dotenv`

---

## 🗂 Project Structure

```
chat-boat/
├── main.py          # Core app — OpenAI client, chat function, Gradio UI
├── .env             # Your API keys (not committed to git)
├── pyproject.toml   # uv project config & dependencies
└── README.md
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) package manager

### 2. Install dependencies

```bash
uv add openai gradio python-dotenv
```

### 3. Set up your API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...your-key-here...
```

### 4. Run the app

```bash
uv run main.py
```

The app will start and print a local URL like:

```
* Running on local URL: http://127.0.0.1:7860
```

Open it in your browser to start chatting.

---

## ⚙️ How It Works

```
User message
     │
     ▼
Build messages list:
  [system prompt] + [full conversation history] + [new user message]
     │
     ▼
OpenAI Chat Completions API (streaming)
     │
     ▼
Stream tokens back → Gradio UI renders in real time
```

The `history` parameter passed by Gradio is a list of `{"role": "user"/"assistant", "content": "..."}` dicts that gets injected directly into the OpenAI messages array, giving the model full context of the conversation.

---

## 🛠 Configuration

| Variable | Location | Description |
|---|---|---|
| `OPENAI_API_KEY` | `.env` | Your OpenAI secret key |
| `model_name` | `main.py` | OpenAI model to use (default: `gpt-5-mini`) |
| `system_prompt` | `main.py` | System instructions / persona for the assistant |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `openai` | OpenAI Python SDK |
| `gradio` | Web-based chat UI |
| `python-dotenv` | Load secrets from `.env` |

---

## 🔒 Security Note

Never commit your `.env` file. Add it to `.gitignore`:

```bash
echo ".env" >> .gitignore
```
