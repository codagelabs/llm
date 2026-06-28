import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Load env
load_dotenv('../.env')
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv()

def test_query(collection, query_text, ctype_filter=None, n=3):
    print(f"\nQuery: '{query_text}'" + (f" (Filter: {ctype_filter})" if ctype_filter else ""))
    
    kwargs = {"query_texts": [query_text], "n_results": n}
    if ctype_filter:
        kwargs["where"] = {"chunk_type": ctype_filter}
        
    results = collection.query(**kwargs)
    
    for idx in range(len(results['ids'][0])):
        print(f"  [{idx+1}] ID: {results['ids'][0][idx]} (Distance: {results['distances'][0][idx]:.4f})")
        doc_preview = "\n".join(results['documents'][0][idx].split('\n')[:8])
        print(f"  Document Preview:\n{doc_preview}\n")
        print("-" * 50)

def main():
    client = chromadb.PersistentClient(path="./chroma_db")
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-large"
    )
    
    collection = client.get_collection(
        name="ipl_enhanced_chunks_openai",
        embedding_function=openai_ef
    )
    
    # Run test queries
    # 1. KKR won in Bangalore
    test_query(collection, "KKR won in Bangalore", ctype_filter="match_summary")
    
    # 2. How was Ganguly dismissed in the first IPL match
    test_query(collection, "Ganguly dismissal in first IPL match 2008", ctype_filter="wicket_event")
    
    # 3. Brendon McCullum 158 runs
    test_query(collection, "Brendon McCullum 158 runs opening match", ctype_filter="player_batting")

if __name__ == "__main__":
    main()
