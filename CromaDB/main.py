import os
import glob
from pathlib import Path
import chromadb

def main():
    knowledge_base_path = "knowledge-base/**/*.md"
    files = glob.glob(knowledge_base_path, recursive=True)
    print(f"Found {len(files)} files in the knowledge base")

    # Set up persistent ChromaDB client
    db_path = "./chroma_db"
    print(f"Initializing ChromaDB client at {db_path}...")
    client = chromadb.PersistentClient(path=db_path)
    collection_name = "knowledge_base"

    # Reset collection if it already exists to ensure fresh ingestion
    if collection_name in [c.name for c in client.list_collections()]:
        print(f"Collection '{collection_name}' already exists. Re-creating...")
        client.delete_collection(collection_name)
    
    collection = client.create_collection(name=collection_name)

    documents = []
    metadatas = []
    ids = []

    for file_path in files:
        path = Path(file_path)
        if not path.is_file():
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract category from subdirectory (e.g. knowledge-base/contracts/abc.md -> contracts)
        parts = path.parts
        category = parts[1] if len(parts) >= 3 else "general"

        documents.append(content)
        metadatas.append({
            "source": str(path),
            "filename": path.name,
            "category": category
        })
        ids.append(str(path))

    print(f"Preparing to ingest {len(documents)} documents...")

    # Ingest in batches of 40 to avoid sqlite limits or large payload issues
    batch_size = 40
    for i in range(0, len(documents), batch_size):
        batch_ids = ids[i : i + batch_size]
        batch_docs = documents[i : i + batch_size]
        batch_metas = metadatas[i : i + batch_size]
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas
        )
        print(f"Ingested batch {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1}")

    print(f"\nSuccessfully loaded {collection.count()} documents into Chroma collection '{collection_name}'")

    # Run a test query to verify embeddings & retrieval
    test_query = "What is the payment term for Advantage Medical Coverage?"
    print(f"\nRunning test query: '{test_query}'")
    results = collection.query(
        query_texts=[test_query],
        n_results=2
    )

    for idx, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        print(f"\nResult {idx + 1} (Distance: {dist:.4f}):")
        print(f"Source: {meta['source']} (Category: {meta['category']})")
        preview = doc[:300].replace('\n', ' ').strip()
        print(f"Preview: {preview}...")

if __name__ == "__main__":
    main()
