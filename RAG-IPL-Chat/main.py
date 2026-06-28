#!/usr/bin/env python3
"""
IPL RAG Chat — interactive command-line interface.

Usage
-----
    python main.py                  # chat (assumes ChromaDB is already populated)
    python main.py --ingest         # ingest data first, then start chat
    python main.py --ingest --dir ipl-2008-2026   # specify data directory
    python main.py --verbose        # show retrieved chunks during chat
"""

import argparse
import os
import sys

from dotenv import load_dotenv

# Load env vars early
load_dotenv("../.env")
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()


def _run_chat(verbose: bool = False) -> None:
    from src.rag import IPLRagEngine

    print("\n" + "=" * 60)
    print("  🏏  IPL RAG Chat  🏏")
    print("=" * 60)
    print("Ask anything about IPL matches (2008–2026).")
    print("Type 'exit' or 'quit' to stop.\n")

    try:
        engine = IPLRagEngine()
    except Exception as exc:
        print(f"\n❌  Could not connect to ChromaDB: {exc}")
        print("Tip: Run  `python main.py --ingest`  to populate the database first.")
        sys.exit(1)

    history: list[dict] = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! 🏏")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye! 🏏")
            break
        if user_input.lower() in ("clear", "reset"):
            history = []
            print("[Conversation history cleared]\n")
            continue

        try:
            answer = engine.answer_question(user_input, history=history, verbose=verbose)
        except Exception as exc:
            print(f"[ERROR] {exc}\n")
            continue

        print(f"\nAssistant: {answer}\n")

        # Update conversation history
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": answer})

        # Keep history window to last 10 messages to avoid token overflow
        if len(history) > 10:
            history = history[-10:]


def _run_ingest(dataset_dir: str | None = None) -> None:
    from src.ingest import ingest

    ingest(dataset_dir=dataset_dir, clear=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="IPL RAG Chat — query IPL cricket data using RAG.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest IPL JSON data into ChromaDB before starting chat.",
    )
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Only ingest data (do not start chat).",
    )
    parser.add_argument(
        "--dir",
        metavar="PATH",
        default=None,
        help="Path to the IPL JSON dataset directory (default: auto-detect).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print retrieved chunks and rewritten query during chat.",
    )
    args = parser.parse_args()

    if args.ingest or args.ingest_only:
        _run_ingest(dataset_dir=args.dir)

    if not args.ingest_only:
        _run_chat(verbose=args.verbose)


if __name__ == "__main__":
    main()
