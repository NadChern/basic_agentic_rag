import requests
import chromadb

OLLAMA_API_BASE = "http://localhost:11434"
EMBEDDING_MODEL = "granite-embedding:30m"
CHROMA_DB_PATH = "./chromadb_storage"


def search_documents(query: str, n_results: int = 3) -> dict:
    """Search the vector database for relevant document chunks.

    Args:
        query (str): The search query to find relevant documents.
        n_results (int): Number of results to return. Defaults to 3.

    Returns:
        dict: Contains 'status' and 'chunks' (list of relevant text).
    """
    try:
        # Get embedding for the query
        response = requests.post(
            f"{OLLAMA_API_BASE}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": query}
        )
        response.raise_for_status()
        query_embedding = response.json()["embedding"]

        # Search ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        collection = client.get_or_create_collection(name="documents")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        if results and results['documents']:
            return {
                "status": "success",
                "chunks": results['documents'][0]
            }
        return {"status": "success", "chunks": []}
    except Exception as e:
        return {"status": "error", "message": str(e)}
