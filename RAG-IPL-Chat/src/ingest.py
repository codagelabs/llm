"""
ChromaDB ingestion pipeline.

Usage (as a script):
    python -m src.ingest            # uses auto-detected dataset dir
    python -m src.ingest --dir ipl-2008-2026
"""

import os
import time
import argparse

import chromadb
import tqdm
from chromadb.utils import embedding_functions

from src.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    INGEST_BATCH_SIZE,
)
from src.data_loader import discover_dataset_dir, load_all_matches, build_match_id_map
from src.chunker import generate_match_chunks


# ---------------------------------------------------------------------------
# ChromaDB helpers
# ---------------------------------------------------------------------------

def get_chroma_collection(chroma_path: str = CHROMA_DB_PATH) -> tuple:
    """Initialise (or re-open) a ChromaDB persistent client and collection."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not set.")

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=EMBEDDING_MODEL,
    )
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=openai_ef,
        get_or_create=True,
    )
    return client, collection, openai_ef


def clear_collection(collection, collection_name: str) -> int:
    """Delete all documents from *collection* and return the count deleted."""
    try:
        existing_ids = collection.get(include=[])["ids"]
        if existing_ids:
            batch_size = 1000
            for i in range(0, len(existing_ids), batch_size):
                collection.delete(ids=existing_ids[i : i + batch_size])
            print(f"Cleared {len(existing_ids)} existing documents from '{collection_name}'.")
            return len(existing_ids)
        print(f"Collection '{collection_name}' is already empty.")
        return 0
    except Exception as exc:
        print(f"Warning while clearing collection: {exc}")
        return 0


def _safe_add(
    collection,
    client,
    openai_ef,
    docs: list,
    metas: list,
    ids: list,
    retries: int = 5,
    delay: int = 5,
):
    """Add a batch to ChromaDB with retry / re-connect logic."""
    last_err = None
    for attempt in range(retries):
        try:
            collection.add(documents=docs, metadatas=metas, ids=ids)
            return collection, client
        except Exception as exc:
            last_err = exc
            print(f"\n[WARN] Ingestion error (attempt {attempt + 1}/{retries}): {exc}")
            if attempt < retries - 1:
                time.sleep(delay)
                try:
                    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
                    collection = client.get_collection(
                        name=COLLECTION_NAME, embedding_function=openai_ef
                    )
                except Exception as re_err:
                    print(f"  Failed to re-initialise client: {re_err}")
            else:
                raise last_err
    return collection, client


# ---------------------------------------------------------------------------
# Main ingestion function
# ---------------------------------------------------------------------------

def ingest(dataset_dir: str | None = None, clear: bool = True) -> None:
    """
    Full pipeline: discover data → generate chunks → ingest into ChromaDB.

    Parameters
    ----------
    dataset_dir : str | None
        Path to the directory containing IPL JSON files.  If ``None``, the
        directory is auto-detected from the candidates in ``config.DATASET_DIRS``.
    clear : bool
        Whether to delete existing documents before ingesting.
    """
    # 1. Discover dataset
    if dataset_dir is None:
        dataset_dir = discover_dataset_dir()
    print(f"Using dataset directory: {dataset_dir}")

    # 2. Load & sort matches
    all_matches = load_all_matches(dataset_dir)
    print(f"Loaded {len(all_matches)} match files.")

    filepath_to_id = build_match_id_map(all_matches)
    seasons = {v.split("_")[1] for v in filepath_to_id.values()}
    print(f"Grouped {len(filepath_to_id)} matches across {len(seasons)} seasons.")

    # 3. Generate chunks
    all_chunks: list[dict] = []
    for filepath, match_id in tqdm.tqdm(filepath_to_id.items(), desc="Generating chunks"):
        match_chunks = generate_match_chunks(filepath, match_id)
        all_chunks.extend(match_chunks)

    print(f"\nTotal chunks generated: {len(all_chunks)}")
    chunk_counts: dict[str, int] = {}
    for chunk in all_chunks:
        ctype = chunk["metadata"]["chunk_type"]
        chunk_counts[ctype] = chunk_counts.get(ctype, 0) + 1
    print("Chunk breakdown:")
    for ctype, cnt in chunk_counts.items():
        print(f"  {ctype}: {cnt}")

    # 4. Connect to ChromaDB
    client, collection, openai_ef = get_chroma_collection()

    if clear:
        clear_collection(collection, COLLECTION_NAME)

    # 5. Ingest in batches
    total = len(all_chunks)
    for i in range(0, total, INGEST_BATCH_SIZE):
        batch = all_chunks[i : i + INGEST_BATCH_SIZE]
        collection, client = _safe_add(
            collection=collection,
            client=client,
            openai_ef=openai_ef,
            docs=[c["document"] for c in batch],
            metas=[c["metadata"] for c in batch],
            ids=[c["id"] for c in batch],
        )
        print(f"Ingested chunks {i + 1} – {min(i + INGEST_BATCH_SIZE, total)} of {total}…")

    print(f"\n✅  Successfully loaded {total} chunks into ChromaDB collection '{COLLECTION_NAME}'!")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest IPL match data into ChromaDB.")
    parser.add_argument("--dir", metavar="PATH", help="Path to IPL JSON dataset directory.")
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Skip clearing existing documents before ingestion.",
    )
    args = parser.parse_args()
    ingest(dataset_dir=args.dir, clear=not args.no_clear)
