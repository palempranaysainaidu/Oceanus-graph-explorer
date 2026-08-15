"""
LangGraph-based Argo agent for oceanographic data analysis.
"""

from typing import Dict, List, Any, Optional, TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
import json
import logging
from datetime import datetime, timedelta
import numpy as np
import re

from tools import ArgoToolFactory
from .config import GROQ_API_KEY, GROQ_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: List[Any]
    query: str
    intent: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    response: Optional[str]
    error: Optional[str]

class LangGraphArgoAgent:
    """LangGraph-based agent for Argo oceanographic data"""
    
    def __init__(self):
        """Initialize the LangGraph agent"""
        self.tools = ArgoToolFactory()
        self.llm = ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=GROQ_MODEL,
            temperature=0.1
        )
        
        # Create tools for LangGraph
        self.langgraph_tools = [
            self._create_measurement_tool(),
            self._create_metadata_tool(),
            self._create_semantic_tool()
        ]
        
        # Create the graph
        self.graph = self._create_graph()
    
    def _create_measurement_tool(self):
        """Create measurement query tool"""
        @tool
        def query_measurements(
            float_id: Optional[str] = None,
            min_lat: Optional[float] = None,
            max_lat: Optional[float] = None,
            min_lon: Optional[float] = None,
            max_lon: Optional[float] = None,
            limit: int = 1000
        ) -> Dict[str, Any]:
            """
            Query oceanographic measurements from CockroachDB.
            
            Args:
                float_id: Specific float ID to query
                min_lat: Minimum latitude for spatial filter
                max_lat: Maximum latitude for spatial filter
                min_lon: Minimum longitude for spatial filter
                max_lon: Maximum longitude for spatial filter
                limit: Maximum number of results
                
            Returns:
                Dictionary with measurements and statistics
            """
            try:
                if float_id:
                    measurements = self.tools.cockroach.get_measurements_by_float(
                        platform_number=float_id,
                        limit=limit
                    )
                elif all(coord is not None for coord in [min_lat, max_lat, min_lon, max_lon]):
                    measurements = self.tools.cockroach.get_measurements_by_region(
                        min_lat=min_lat,
                        max_lat=max_lat,
                        min_lon=min_lon,
                        max_lon=max_lon,
                        limit=limit
                    )
                else:
                    return {"error": "Either float_id or complete spatial bounds required"}
                
                if measurements:
                    stats = {
                        "temp_stats": self._calculate_stats([m.temp_adjusted for m in measurements]),
                        "psal_stats": self._calculate_stats([m.psal_adjusted for m in measurements]),
                        "pres_stats": self._calculate_stats([m.pres_adjusted for m in measurements])
                    }
                    
                    return {
                        "count": len(measurements),
                        "statistics": stats,
                        "time_range": f"{measurements[0].time} to {measurements[-1].time}",
                        "spatial_coverage": self._get_spatial_coverage(measurements)
                    }
                else:
                    return {"count": 0, "message": "No measurements found"}
                    
            except Exception as e:
                logger.error(f"Error in measurement query: {e}")
                return {"error": str(e)}
        
        return query_measurements
    
    def _create_metadata_tool(self):
        """Create metadata query tool"""
        @tool
        def query_metadata(
            float_id: Optional[str] = None,
            region: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Query metadata from Neo4j.
            
            Args:
                float_id: Specific float ID to query
                region: Region name to query
                
            Returns:
                Dictionary with metadata information
            """
            try:
                if float_id:
                    metadata = self.tools.neo4j.get_float_metadata(float_id)
                    if metadata:
                        return {
                            "float_count": 1,
                            "parameter_distribution": {param: 1 for param in metadata.parameters},
                            "region_distribution": {metadata.subregion: 1}
                        }
                elif region:
                    metadata = self.tools.neo4j.get_region_metadata(region)
                    if metadata:
                        return {
                            "total_floats": metadata.float_count,
                            "region_hierarchy": {
                                metadata.name: {
                                    "parent": metadata.parent_region,
                                    "float_count": metadata.float_count,
                                    "subregions": metadata.subregions
                                }
                            }
                        }
                
                return {"message": "No metadata found"}
                
            except Exception as e:
                logger.error(f"Error in metadata query: {e}")
                return {"error": str(e)}
        
        return query_metadata
    
    def _create_semantic_tool(self):
        """Create semantic search tool"""
        @tool
        def semantic_search(
            query: str,
            region: Optional[str] = None,
            top_k: int = 10
        ) -> Dict[str, Any]:
            """
            Perform semantic search using Pinecone.
            
            Args:
                query: Search query
                region: Optional region filter
                top_k: Number of results to return
                
            Returns:
                Dictionary with search results
            """
            try:
                # Generate embedding
                query_vector = self._get_query_embedding(query)
                
                # Perform search
                results = self.tools.pinecone.semantic_search(
                    query_vector=query_vector,
                    top_k=top_k,
                    region_filter=region
                )
                
                if results:
                    return {
                        "count": len(results),
                        "results": [
                            {
                                "platform_number": r.platform_number,
                                "score": r.score,
                                "time": r.time.isoformat()
                            }
                            for r in results[:5]  # Top 5 results
                        ]
                    }
                else:
                    return {"count": 0, "message": "No semantic matches found"}
                    
            except Exception as e:
                logger.error(f"Error in semantic search: {e}")
                return {"error": str(e)}
        
        return semantic_search
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        
        def parse_intent(state: AgentState) -> AgentState:
            """Parse user query to determine intent and extract parameters"""
            try:
                query = state["query"]
                
                # Extract float ID
                float_id = None
                float_matches = re.findall(r'float (\d+)', query.lower())
                if float_matches:
                    float_id = float_matches[0]
                
                # Extract spatial information
                spatial_filter = None
                regions = {
                    "arabian sea": {"min_lat": 10, "max_lat": 25, "min_lon": 55, "max_lon": 75},
                    "bay of bengal": {"min_lat": 10, "max_lat": 25, "min_lon": 80, "max_lon": 95},
                    "equatorial indian ocean": {"min_lat": -5, "max_lat": 5, "min_lon": 40, "max_lon": 80},
                    "southern indian ocean": {"min_lat": -40, "max_lat": -20, "min_lon": 20, "max_lon": 80}
                }
                
                region_name = None
                for region, bounds in regions.items():
                    if region in query.lower():
                        spatial_filter = bounds
                        region_name = region.title()
                        break
                
                # Determine query type
                if any(word in query.lower() for word in ["similar", "pattern", "inversion", "anomal"]):
                    query_type = "semantic"
                elif any(word in query.lower() for word in ["metadata", "instrument", "parameter", "deployment"]):
                    query_type = "metadata"
                else:
                    query_type = "measurement"
                
                intent = {
                    "type": query_type,
                    "float_id": float_id,
                    "spatial_filter": spatial_filter,
                    "region_name": region_name
                }
                
                state["intent"] = intent
                logger.info(f"Parsed intent: {intent}")
                return state
                
            except Exception as e:
                logger.error(f"Error parsing intent: {e}")
                state["error"] = str(e)
                return state
        
        def execute_query(state: AgentState) -> AgentState:
            """Execute the appropriate query based on intent"""
            try:
                intent = state["intent"]
                query_type = intent["type"]
                
                if query_type == "measurement":
                    tool = self.langgraph_tools[0]  # measurement tool
                    if intent["float_id"]:
                        results = tool.invoke({"float_id": intent["float_id"]})
                    elif intent["spatial_filter"]:
                        results = tool.invoke(intent["spatial_filter"])
                    else:
                        results = {"error": "No valid parameters for measurement query"}
                        
                elif query_type == "metadata":
                    tool = self.langgraph_tools[1]  # metadata tool
                    if intent["float_id"]:
                        results = tool.invoke({"float_id": intent["float_id"]})
                    elif intent["region_name"]:
                        results = tool.invoke({"region": intent["region_name"]})
                    else:
                        results = {"error": "No valid parameters for metadata query"}
                        
                elif query_type == "semantic":
                    tool = self.langgraph_tools[2]  # semantic tool
                    results = tool.invoke({
                        "query": state["query"],
                        "region": intent["region_name"]
                    })
                else:
                    results = {"error": f"Unknown query type: {query_type}"}
                
                state["results"] = results
                logger.info(f"Query results: {results}")
                return state
                
            except Exception as e:
                logger.error(f"Error executing query: {e}")
                state["error"] = str(e)
                return state
        
        def generate_response(state: AgentState) -> AgentState:
            """Generate natural language response"""
            try:
                if state.get("error"):
                    state["response"] = f"Error: {state['error']}"
                    return state
                
                intent = state["intent"]
                results = state["results"]
                query_type = intent["type"]
                
                if query_type == "measurement":
                    if "error" in results:
                        response = f"Error executing measurement query: {results['error']}"
                    else:
                        response = f"""Based on the Argo float measurements:

Found {results.get('count', 0)} measurements

Key Statistics:
- Time Range: {results.get('time_range', 'N/A')}
- Number of Measurements: {results.get('count', 0)}

{json.dumps(results.get('statistics', {}), indent=2)}"""
                
                elif query_type == "metadata":
                    if "error" in results:
                        response = f"Error executing metadata query: {results['error']}"
                    else:
                        response = f"""Metadata Analysis:

Found metadata information

Coverage:
- Float Count: {results.get('float_count', results.get('total_floats', 0))}

{json.dumps(results, indent=2)}"""
                
                elif query_type == "semantic":
                    if "error" in results:
                        response = f"Error executing semantic search: {results['error']}"
                    else:
                        response = f"""Semantic Search Results:

Found {results.get('count', 0)} semantically similar measurements

Top Matches:
{json.dumps(results.get('results', []), indent=2)}"""
                
                else:
                    response = "Unknown query type"
                
                state["response"] = response
                return state
                
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                state["response"] = f"Error generating response: {str(e)}"
                return state
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", parse_intent)
        workflow.add_node("execute_query", execute_query)
        workflow.add_node("generate_response", generate_response)
        
        # Add edges
        workflow.set_entry_point("parse_intent")
        workflow.add_edge("parse_intent", "execute_query")
        workflow.add_edge("execute_query", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values"""
        if not values:
            return {}
        return {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values))
        }
    
    def _get_spatial_coverage(self, measurements) -> Dict[str, Any]:
        """Calculate spatial coverage statistics"""
        lats = [m.latitude for m in measurements]
        lons = [m.longitude for m in measurements]
        return {
            "lat_range": [min(lats), max(lats)],
            "lon_range": [min(lons), max(lons)],
            "center": [np.mean(lats), np.mean(lons)]
        }
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for semantic search queries"""
        try:
            import hashlib
            
            # Create a deterministic hash of the query
            query_hash = hashlib.md5(query.lower().encode()).hexdigest()
            
            # Convert hash to seed for reproducible random vector
            seed = int(query_hash[:8], 16)
            np.random.seed(seed)
            
            # Generate a normalized random vector
            embedding = np.random.normal(0, 0.1, 384)
            
            # Normalize the vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return [0.0] * 384
    
    def query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a query using the LangGraph workflow"""
        try:
            # Build conversation context
            messages = []
            if conversation_history:
                for msg in conversation_history[-5:]:  # Keep last 5 exchanges
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Initialize state
            initial_state = {
                "messages": messages,
                "query": query,
                "intent": None,
                "results": None,
                "response": None,
                "error": None
            }
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            return final_state.get("response", "No response generated")
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"
    
    def close(self):
        """Clean up resources"""
        self.tools.close_all()