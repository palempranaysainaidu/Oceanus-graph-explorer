from langchain.tools import tool
import chromadb
import json
import os

CHROMA_PATH = "database/chroma_db"

@tool
def vector_search_tool(query: str, n_results: int = 5) -> str:
    """
    Performs semantic search on Argo profile summaries using ChromaDB.
    Use this to find profiles based on semantic similarity to natural language queries.
    For example: "unusual temperature patterns", "deep water profiles", "Arctic measurements".
    Returns a JSON string with the most relevant profile summaries and their metadata.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(CHROMA_PATH, exist_ok=True)
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(name="argo_summaries")
        
        # Perform semantic search
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'document': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return json.dumps(formatted_results, default=str)
        
    except Exception as e:
        return f"Error performing vector search: {e}"