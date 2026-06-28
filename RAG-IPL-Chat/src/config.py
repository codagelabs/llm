"""
Configuration constants for IPL RAG project.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

# Model settings
EMBEDDING_MODEL = "text-embedding-3-large"
LLM_MODEL = "gpt-4.1-nano"

# ChromaDB settings
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "ipl_enhanced_chunks_openai"

# Dataset discovery order
DATASET_DIRS = ["ipl-2008-2026", "ipl-2008", "dataset"]

# Ingestion batch size
INGEST_BATCH_SIZE = 1000

# RAG retrieval top-k
RAG_N_RESULTS = 20

# System prompt template
SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing IPL cricket matches data.
You are chatting with a user about IPL.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""

# Query rewrite prompt template
QUERY_REWRITE_PROMPT = """
You are in a conversation with a user, answering questions about the IPL (i.e Cricket League) Season.
You are about to look up information in a Knowledge Base to answer the user's question.

This is the history of your conversation so far with the user:
{history}

And this is the user's current question:
{question}

Respond only with a single, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
Don't mention the IPL name unless it's a general question about the IPL.
IMPORTANT: Respond ONLY with the knowledgebase query, nothing else.
"""
