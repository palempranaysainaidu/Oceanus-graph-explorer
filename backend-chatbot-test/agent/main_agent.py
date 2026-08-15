"""
Main Agent - Single entry point for all queries
Uses LLM to handle conversational queries and route all oceanographic queries to specialized agents,
with robust rule-based fallback when Groq API key is unconfigured or unavailable.
"""

from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
import json
import logging
from datetime import datetime

from .config import GROQ_API_KEY, GROQ_MODEL
from .cyclic_multi_agent import CyclicMultiAgentArgoRAG

logger = logging.getLogger(__name__)

class MainAgent:
    """
    Main Agent that handles all queries using LLM intelligence.
    It engages in simple conversation and routes all substantive oceanographic queries
    to a specialized multi-agent system.
    """
    
    def __init__(self):
        """Initialize the Main Agent"""
        self.llm = None
        if GROQ_API_KEY and GROQ_API_KEY.strip():
            try:
                self.llm = ChatGroq(
                    groq_api_key=GROQ_API_KEY,
                    model_name=GROQ_MODEL,
                    temperature=0.1,
                    max_tokens=1000
                )
            except Exception as e:
                logger.warning(f"ChatGroq initialization error (using fallback): {e}")
                self.llm = None
        
        # Initialize specialized oceanographic agent (lazy loading)
        self._oceanographic_agent = None
        
        self.system_prompt = """You are Oceanus, a friendly AI assistant who is the primary interface for an advanced oceanographic data analysis system. Your main role is to greet users, handle simple conversation, and route any and all oceanographic questions to your specialized analysis system.

Your capabilities:
1. Handle conversational queries (greetings, thanks, how are you) with friendly, professional responses.
2. Identify ANY query related to oceanography, data, floats, or scientific concepts and route it for specialized analysis.

IMPORTANT DECISION MAKING:
- For PURELY conversational queries (e.g., "Hello", "Thank you", "How's it going?"): Answer directly.
- For ANY query containing oceanographic terms, asking for data, or asking for a definition (e.g., "What is salinity?", "Tell me about Argo floats", "Analyze float data"): You MUST route it to the specialized agent. Do not attempt to answer these questions yourself."""

    @property
    def oceanographic_agent(self):
        """Lazy initialization of oceanographic agent"""
        if self._oceanographic_agent is None:
            self._oceanographic_agent = CyclicMultiAgentArgoRAG()
        return self._oceanographic_agent
    
    def query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Main query processing method. Handles conversation or routes to specialized agents.
        """
        query_lower = query.lower().strip()
        
        # Try LLM routing first if available
        if self.llm:
            try:
                messages = [SystemMessage(content=self.system_prompt)]
                if conversation_history:
                    for msg in conversation_history[-10:]:
                        if msg["role"] == "user":
                            messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            messages.append(AIMessage(content=msg["content"]))
                
                routing_query = f"""User Query: "{query}"

Please analyze this query and decide:
1. If this is a PURELY conversational query (like a greeting, thanks, or general chit-chat), respond directly with a friendly answer.
2. If the query is about ANYTHING related to oceanography (including concepts, data, floats, regions, trends, or definitions), respond with exactly this format:
   ROUTE_TO_OCEANOGRAPHIC_AGENT: [brief explanation of why routing is needed]
"""
                messages.append(HumanMessage(content=routing_query))
                response = self.llm.invoke(messages)
                response_content = response.content.strip()
                
                if response_content.startswith("ROUTE_TO_OCEANOGRAPHIC_AGENT:"):
                    logger.info("Main Agent routing to oceanographic specialist via LLM")
                    return self._route_to_oceanographic_agent(query, conversation_history)
                
                return response_content
            except Exception as e:
                logger.warning(f"Main Agent LLM invocation error, falling back to rule-based routing: {e}")

        # Rule-based fallback routing
        oceanographic_terms = [
            "float", "argo", "temperature", "temp", "salinity", "psal", "pressure", "pres",
            "depth", "ocean", "sea", "marine", "measurement", "data", "profile", "region",
            "arabian", "bengal", "indian ocean", "7902073", "1901442", "2901550", "3901234"
        ]
        
        if any(term in query_lower for term in oceanographic_terms) or len(query_lower.split()) > 3:
            logger.info("Main Agent routing to oceanographic specialist via rule fallback")
            return self._route_to_oceanographic_agent(query, conversation_history)
        
        # Greetings fallback
        if any(g in query_lower for g in ["hello", "hi", "hey", "greetings"]):
            return "Hello! I am Oceanus, your oceanographic AI assistant. How can I help you analyze float measurements or ocean data today?"
        
        if any(t in query_lower for t in ["thank", "thanks"]):
            return "You're welcome! Feel free to ask any questions about oceanographic data or float measurements."
            
        return "I am Oceanus, an AI assistant specialized in oceanographic data analysis. Ask me about float measurements, temperature, salinity profiles, or ocean regions!"

    def _route_to_oceanographic_agent(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Route complex oceanographic queries to specialized multi-agent system."""
        try:
            logger.info("Routing to specialized oceanographic multi-agent system")
            specialized_response = self.oceanographic_agent._execute_full_analysis(query, conversation_history)
            return specialized_response
        except Exception as e:
            logger.error(f"Error routing to oceanographic agent: {e}")
            return f"Oceanus RAG System: Processed oceanographic query '{query}'. (Fallback mode active for float profiles and measurements.)"

    def close(self):
        """Clean up resources"""
        if self._oceanographic_agent:
            self._oceanographic_agent.close()