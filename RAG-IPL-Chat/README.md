# 🏏 IPL RAG Chat

A **Retrieval-Augmented Generation (RAG)** system for querying ball-by-ball IPL match data, powered by **ChromaDB** vector search and **OpenAI** embeddings + LLM.

## Features

- **7 specialized chunk types** per match for fine-grained retrieval:
  - `match_summary` — result, venue, toss, player of the match
  - `innings_summary` — team score, overs, top scorers
  - `player_batting` — individual batting stats
  - `player_bowling` — individual bowling stats
  - `partnership` — partnership runs per wicket
  - `wicket_event` — over, dismissal type, fielder
  - `milestone` — centuries, half-centuries, 5-wicket hauls
  - `match_narrative` — natural-language match story
- **Query rewriting** — LLM refines user questions before KB lookup
- **Persistent ChromaDB** store — embed once, query many times
- **Conversation memory** — multi-turn chat with rolling history window

---

## Project Structure

```
RAG-IPL-Chat/
├── main.py               # CLI entry-point (chat + ingest)
├── src/
│   ├── __init__.py
│   ├── config.py         # Models, paths, prompt templates
│   ├── utils.py          # Team abbreviations, season helpers
│   ├── chunker.py        # 8-type chunk generator per match
│   ├── data_loader.py    # Dataset discovery & match ID assignment
│   ├── ingest.py         # Chunk generation → ChromaDB pipeline
│   └── rag.py            # IPLRagEngine (retrieval + LLM answer)
├── ipl-2008-2026/        # IPL JSON files (place your data here)
├── chroma_db/            # Persisted ChromaDB (auto-created)
├── pyproject.toml
└── .env                  # OPENAI_API_KEY=sk-...
```

---

## Setup

### 1. Prerequisites

- Python 3.12+
- An [OpenAI API key](https://platform.openai.com/)
- IPL match JSON files (Cricsheet format) in `ipl-2008-2026/`

### 2. Install dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Configure environment

Create a `.env` file in the project root (or the parent directory):

```
OPENAI_API_KEY=sk-your-key-here
```

---

## Usage

### Ingest data into ChromaDB

Run **once** (or when your dataset changes):

```bash
python main.py --ingest
# or specify a custom data directory:
python main.py --ingest --dir ipl-2008-2026
```

This will:
1. Auto-detect the dataset directory
2. Parse all match JSON files into 8 chunk types
3. Embed and store them in `./chroma_db`

### Start chat

```bash
python main.py
```

### Ingest + chat in one command

```bash
python main.py --ingest
```

### Verbose mode (shows KB queries & retrieved chunks)

```bash
python main.py --verbose
```

### Ingest only (no chat)

```bash
python main.py --ingest-only
```

---

## Example Questions

```
You: Who won the first IPL match in 2008?
You: What were the top 5 highest partnerships in IPL 2008?
You: How many wickets did AB Dinda take against RCB?
You: Who scored a century in IPL 2008 and in which over?
You: Tell me about BB McCullum's performance in the first match
```

---

## Programmatic Usage

```python
from src.rag import IPLRagEngine

engine = IPLRagEngine()
answer = engine.answer_question("Who won the 2008 IPL final?")
print(answer)

# Multi-turn conversation
history = []
q1 = "Which team scored the most in IPL 2008?"
a1 = engine.answer_question(q1, history=history)
history += [{"role": "user", "content": q1}, {"role": "assistant", "content": a1}]

q2 = "Who was their top scorer?"
a2 = engine.answer_question(q2, history=history)
print(a2)
```

---

## Configuration

All tuneable parameters live in [`src/config.py`](src/config.py):

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL` | `text-embedding-3-large` | OpenAI embedding model |
| `LLM_MODEL` | `gpt-4.1-nano` | LLM for query rewriting & answering |
| `CHROMA_DB_PATH` | `./chroma_db` | ChromaDB persistence path |
| `COLLECTION_NAME` | `ipl_enhanced_chunks_openai` | ChromaDB collection name |
| `RAG_N_RESULTS` | `20` | Number of chunks retrieved per query |
| `INGEST_BATCH_SIZE` | `1000` | Chunks per ChromaDB upsert batch |
