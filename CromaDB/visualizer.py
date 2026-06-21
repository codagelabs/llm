import os
import glob
from pathlib import Path
import numpy as np
import chromadb
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="ChromaDB Vector Store Visualizer")

# Global variables for PCA projection
mean_vec = None
W = None  # Projection matrix (D, 2)
documents_data = {}  # Store loaded document info

DB_PATH = "./chroma_db"
COLLECTION_NAME = "knowledge_base"

# Ensure directories exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

def compute_pca_projection():
    """Retrieves embeddings from ChromaDB and computes PCA projection parameters."""
    global mean_vec, W, documents_data
    
    print("Connecting to ChromaDB...")
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Check if collection exists
    if COLLECTION_NAME not in [c.name for c in client.list_collections()]:
        raise RuntimeError(f"Chroma collection '{COLLECTION_NAME}' does not exist. Please run ingestion first.")
        
    collection = client.get_collection(COLLECTION_NAME)
    
    # Get all embeddings, documents, and metadatas
    data = collection.get(include=["embeddings", "documents", "metadatas"])
    embeddings = data.get("embeddings")
    docs = data.get("documents")
    metadatas = data.get("metadatas")
    ids = data.get("ids")
    
    if embeddings is None or len(embeddings) == 0:
        raise ValueError("No embeddings found in the collection.")
        
    X = np.array(embeddings)
    N, D = X.shape
    print(f"Loaded {N} embeddings of dimension {D}")
    
    if N < 2:
        # Cannot project with less than 2 points
        mean_vec = np.zeros((D,))
        W = np.zeros((D, 2))
        projected = np.zeros((N, 2))
    else:
        # Compute PCA in pure NumPy
        mean_vec = np.mean(X, axis=0)
        centered = X - mean_vec
        
        # Calculate covariance matrix
        cov_matrix = np.cov(centered, rowvar=False)
        
        # Solve eigenvalues and eigenvectors
        eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
        
        # Sort in descending order of eigenvalues
        idx = np.argsort(eigenvalues)[::-1]
        eigenvectors = eigenvectors[:, idx]
        
        # Take the top 2 components
        W = eigenvectors[:, :2]
        
        # Project original points
        projected = np.dot(centered, W)
        
    # Populate the global documents lookup
    documents_data = {}
    for i in range(N):
        doc_id = ids[i]
        documents_data[doc_id] = {
            "id": doc_id,
            "x": float(projected[i, 0]),
            "y": float(projected[i, 1]),
            "content": docs[i],
            "filename": metadatas[i].get("filename", ""),
            "category": metadatas[i].get("category", "general"),
            "source": metadatas[i].get("source", "")
        }
    
    print("PCA Projection computed successfully.")

# Setup endpoint to serve index.html
@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = Path("templates/index.html")
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/documents")
def get_documents():
    """Returns all documents with their projected coordinates."""
    try:
        # Re-compute to ensure we have the latest
        compute_pca_projection()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
        
    return list(documents_data.values())

class SearchQuery(BaseModel):
    query: str
    limit: int = 5

@app.post("/api/search")
def search_documents(payload: SearchQuery):
    """Searches documents, projects query into PCA space, and returns coordinates."""
    global mean_vec, W, documents_data
    
    if mean_vec is None or W is None:
        try:
            compute_pca_projection()
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})
            
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    
    # Query Chroma
    results = collection.query(
        query_texts=[payload.query],
        n_results=payload.limit,
        include=["documents", "metadatas", "distances"]
    )
    
    # Project the query embedding into 2D PCA space
    emb_fn = collection._embedding_function
    query_embedding = np.array(emb_fn([payload.query])[0])
    
    query_centered = query_embedding - mean_vec
    query_projected = np.dot(query_centered, W)
    query_x = float(query_projected[0])
    query_y = float(query_projected[1])
    
    # Format matches
    matches = []
    matched_ids = results["ids"][0]
    matched_distances = results["distances"][0]
    
    for doc_id, distance in zip(matched_ids, matched_distances):
        if doc_id in documents_data:
            doc_info = documents_data[doc_id].copy()
            doc_info["distance"] = float(distance)
            matches.append(doc_info)
            
    return {
        "query": payload.query,
        "query_x": query_x,
        "query_y": query_y,
        "matches": matches
    }

if __name__ == "__main__":
    import uvicorn
    # Initialize PCA on start
    try:
        compute_pca_projection()
    except Exception as e:
        print(f"Warning on startup PCA computation: {e}")
        
    print("Starting visualizer server on http://127.0.0.1:8000...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
