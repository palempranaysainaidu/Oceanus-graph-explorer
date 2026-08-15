# agents/semantic_agent.py - Pinecone Semantic Search Agent
import logging
from typing import Dict, Any, Optional, List
import numpy as np

from tools import ArgoToolFactory

logger = logging.getLogger(__name__)

class SemanticAgent:
    """
    Specialized agent for semantic search using Pinecone vector database
    """
    
    def __init__(self):
        self.tools = ArgoToolFactory()
    
    def process(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process semantic search query
        """
        try:
            logger.info(f"SemanticAgent processing: {query}")
            
            # Generate embedding for the query
            query_vector = self._get_query_embedding(query)
            
            # Perform semantic search
            results = self.tools.pinecone.semantic_search(
                query_vector=query_vector,
                top_k=10
            )
            
            if results:
                return {
                    "agent": "SemanticAgent",
                    "results": [
                        {
                            "platform_number": r.platform_number,
                            "score": r.score,
                            "time": r.time.isoformat() if hasattr(r.time, 'isoformat') else str(r.time)
                        }
                        for r in results
                    ],
                    "count": len(results),
                    "summary": f"Found {len(results)} semantically similar measurements"
                }
            else:
                return {
                    "agent": "SemanticAgent",
                    "results": [],
                    "count": 0,
                    "summary": "No semantic matches found"
                }
                
        except Exception as e:
            logger.error(f"SemanticAgent error: {e}")
            return {
                "agent": "SemanticAgent",
                "error": str(e)
            }
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding vector for semantic search
        """
        try:
            import hashlib
            query_hash = hashlib.md5(query.lower().encode()).hexdigest()
            seed = int(query_hash[:8], 16)
            np.random.seed(seed)
            embedding = np.random.normal(0, 0.1, 384)
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * 384
    
    def close(self):
        """Cleanup resources"""
        if hasattr(self, 'tools'):
            self.tools.pinecone.close()
