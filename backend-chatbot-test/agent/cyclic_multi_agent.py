"""
Cyclic Multi-Agent RAG system for iterative oceanographic data analysis using LangGraph.
"""

from typing import Dict, List, Any, Optional, TypedDict, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
import json
import logging
from datetime import datetime, timedelta
import numpy as np
import re

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import ArgoToolFactory
from .config import GROQ_API_KEY, GROQ_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CyclicAgentState(TypedDict):
    """State for the cyclic multi-agent RAG system"""
    messages: List[Any]
    query: str
    intent: Optional[Dict[str, Any]]
    cycle_count: int
    max_cycles: int
    
    # Agent results
    measurement_results: Optional[Dict[str, Any]]
    metadata_results: Optional[Dict[str, Any]]
    semantic_results: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    
    # Cycle control
    needs_refinement: bool
    refinement_suggestions: List[str]
    quality_score: float
    
    # Final output
    final_response: Optional[str]
    error: Optional[str]

class AnalysisAgent:
    """Agent that analyzes results and suggests refinements"""
    
    def __init__(self):
        self.llm = None
        if GROQ_API_KEY and GROQ_API_KEY.strip():
            try:
                self.llm = ChatGroq(
                    api_key=GROQ_API_KEY,
                    model_name=GROQ_MODEL,
                    temperature=0.2
                )
            except Exception as e:
                logger.warning(f"AnalysisAgent ChatGroq init error: {e}")
    
    def analyze_results(
        self,
        query: str,
        measurement_results: Optional[Dict[str, Any]],
        metadata_results: Optional[Dict[str, Any]],
        semantic_results: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the quality and completeness of results"""
        try:
            logger.info("AnalysisAgent evaluating results quality")
            
            # Calculate quality metrics
            quality_metrics = {
                "measurement_quality": self._assess_measurement_quality(measurement_results),
                "metadata_quality": self._assess_metadata_quality(metadata_results),
                "semantic_quality": self._assess_semantic_quality(semantic_results),
                "completeness": self._assess_completeness(query, measurement_results, metadata_results, semantic_results)
            }
            
            # Overall quality score (0-1)
            overall_quality = np.mean(list(quality_metrics.values()))
            
            # Generate refinement suggestions
            suggestions = self._generate_refinement_suggestions(
                query, quality_metrics, measurement_results, metadata_results, semantic_results
            )
            
            # Determine if refinement is needed
            needs_refinement = overall_quality < 0.7 or len(suggestions) > 0
            
            return {
                "agent": "AnalysisAgent",
                "quality_metrics": quality_metrics,
                "overall_quality": overall_quality,
                "needs_refinement": needs_refinement,
                "refinement_suggestions": suggestions,
                "analysis_summary": self._generate_analysis_summary(quality_metrics, overall_quality)
            }
            
        except Exception as e:
            logger.error(f"AnalysisAgent error: {e}")
            return {
                "agent": "AnalysisAgent",
                "error": str(e),
                "overall_quality": 0.0,
                "needs_refinement": True,
                "refinement_suggestions": ["Error in analysis - retry with different parameters"]
            }
    
    def _assess_measurement_quality(self, results: Optional[Dict[str, Any]]) -> float:
        """Assess quality of measurement results (0-1)"""
        if not results or "error" in results:
            return 0.0
        
        score = 0.0
        if results.get("count", 0) > 0:
            score += 0.4  # Has data
        if results.get("statistics"):
            score += 0.3  # Has statistics
        if results.get("time_range"):
            score += 0.2  # Has temporal info
        if results.get("spatial_coverage"):
            score += 0.1  # Has spatial info
            
        return min(score, 1.0)
    
    def _assess_metadata_quality(self, results: Optional[Dict[str, Any]]) -> float:
        """Assess quality of metadata results (0-1)"""
        if not results or "error" in results:
            return 0.0
        
        score = 0.0
        if results.get("float_metadata") or results.get("region_metadata"):
            score += 0.5  # Has metadata
        if results.get("summary"):
            score += 0.3  # Has summary
        if "float_count" in results or "total_floats" in results:
            score += 0.2  # Has count info
            
        return min(score, 1.0)
    
    def _assess_semantic_quality(self, results: Optional[Dict[str, Any]]) -> float:
        """Assess quality of semantic results (0-1)"""
        if not results or "error" in results:
            return 0.0
        
        score = 0.0
        if results.get("count", 0) > 0:
            score += 0.6  # Has matches
        if results.get("top_matches"):
            score += 0.4  # Has detailed matches
            
        return min(score, 1.0)
    
    def _assess_completeness(
        self,
        query: str,
        measurement_results: Optional[Dict[str, Any]],
        metadata_results: Optional[Dict[str, Any]],
        semantic_results: Optional[Dict[str, Any]]
    ) -> float:
        """Assess how completely the query was answered (0-1)"""
        query_lower = query.lower()
        
        # Check if query asks for specific types of information
        needs_measurements = any(word in query_lower for word in 
            ["temperature", "salinity", "pressure", "measurement", "data", "profile"])
        needs_metadata = any(word in query_lower for word in 
            ["metadata", "instrument", "parameter", "deployment", "coverage"])
        needs_semantic = any(word in query_lower for word in 
            ["similar", "pattern", "compare", "find", "anomal"])
        
        completeness_score = 0.0
        total_needed = 0
        
        if needs_measurements:
            total_needed += 1
            if measurement_results and "error" not in measurement_results:
                completeness_score += 1
        
        if needs_metadata:
            total_needed += 1
            if metadata_results and "error" not in metadata_results:
                completeness_score += 1
        
        if needs_semantic:
            total_needed += 1
            if semantic_results and "error" not in semantic_results:
                completeness_score += 1
        
        return completeness_score / max(total_needed, 1)
    
    def _generate_refinement_suggestions(
        self,
        query: str,
        quality_metrics: Dict[str, float],
        measurement_results: Optional[Dict[str, Any]],
        metadata_results: Optional[Dict[str, Any]],
        semantic_results: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate specific suggestions for improving results"""
        suggestions = []
        
        # Check measurement quality
        if quality_metrics["measurement_quality"] < 0.5:
            if not measurement_results or measurement_results.get("count", 0) == 0:
                suggestions.append("Try expanding spatial or temporal search criteria for measurements")
            elif "error" in measurement_results:
                suggestions.append("Retry measurement query with different parameters")
        
        # Check metadata quality
        if quality_metrics["metadata_quality"] < 0.5:
            if not metadata_results or "error" in metadata_results:
                suggestions.append("Query additional metadata sources or expand search criteria")
        
        # Check semantic quality
        if quality_metrics["semantic_quality"] < 0.5:
            if not semantic_results or semantic_results.get("count", 0) == 0:
                suggestions.append("Broaden semantic search terms or adjust similarity thresholds")
        
        # Check completeness
        if quality_metrics["completeness"] < 0.7:
            suggestions.append("Query additional data sources to provide more comprehensive analysis")
        
        return suggestions
    
    def _generate_analysis_summary(self, quality_metrics: Dict[str, float], overall_quality: float) -> str:
        """Generate a summary of the analysis quality"""
        quality_level = "excellent" if overall_quality > 0.8 else \
                       "good" if overall_quality > 0.6 else \
                       "fair" if overall_quality > 0.4 else "poor"
        
        return f"Analysis quality: {quality_level} (score: {overall_quality:.2f}). " + \
               f"Measurement: {quality_metrics['measurement_quality']:.2f}, " + \
               f"Metadata: {quality_metrics['metadata_quality']:.2f}, " + \
               f"Semantic: {quality_metrics['semantic_quality']:.2f}, " + \
               f"Completeness: {quality_metrics['completeness']:.2f}"

class RefinementAgent:
    """Agent that refines queries and parameters based on analysis feedback"""
    
    def __init__(self, tools: ArgoToolFactory):
        self.tools = tools
        self.llm = None
        if GROQ_API_KEY and GROQ_API_KEY.strip():
            try:
                self.llm = ChatGroq(
                    api_key=GROQ_API_KEY,
                    model_name=GROQ_MODEL,
                    temperature=0.1
                )
            except Exception as e:
                logger.warning(f"RefinementAgent ChatGroq init error: {e}")
    
    def refine_and_retry(
        self,
        original_intent: Dict[str, Any],
        suggestions: List[str],
        cycle_count: int
    ) -> Dict[str, Any]:
        """Refine the query intent based on suggestions"""
        try:
            logger.info(f"RefinementAgent refining intent (cycle {cycle_count})")
            
            refined_intent = original_intent.copy()
            
            for suggestion in suggestions:
                if "expand" in suggestion.lower() and "spatial" in suggestion.lower():
                    refined_intent = self._expand_spatial_criteria(refined_intent)
                elif "expand" in suggestion.lower() and "temporal" in suggestion.lower():
                    refined_intent = self._expand_temporal_criteria(refined_intent)
                elif "broaden" in suggestion.lower() and "semantic" in suggestion.lower():
                    refined_intent = self._broaden_semantic_search(refined_intent)
                elif "additional" in suggestion.lower() and "metadata" in suggestion.lower():
                    refined_intent = self._enhance_metadata_search(refined_intent)
            
            return {
                "agent": "RefinementAgent",
                "refined_intent": refined_intent,
                "applied_refinements": suggestions,
                "cycle": cycle_count
            }
            
        except Exception as e:
            logger.error(f"RefinementAgent error: {e}")
            return {
                "agent": "RefinementAgent",
                "error": str(e),
                "refined_intent": original_intent
            }
    
    def _expand_spatial_criteria(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Expand spatial search area"""
        if intent.get("spatial_filter"):
            sf = intent["spatial_filter"]
            # Expand by 2 degrees in each direction
            sf["min_lat"] = max(sf["min_lat"] - 2, -90)
            sf["max_lat"] = min(sf["max_lat"] + 2, 90)
            sf["min_lon"] = max(sf["min_lon"] - 2, -180)
            sf["max_lon"] = min(sf["max_lon"] + 2, 180)
            logger.info(f"Expanded spatial criteria: {sf}")
        
        return intent
    
    def _expand_temporal_criteria(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Expand temporal search window"""
        # For now, we don't have temporal filters in the intent
        # This could be added in future iterations
        logger.info("Temporal expansion not implemented yet")
        return intent
    
    def _broaden_semantic_search(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Broaden semantic search parameters"""
        intent["semantic_broadened"] = True
        logger.info("Broadened semantic search parameters")
        return intent
    
    def _enhance_metadata_search(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata search scope"""
        intent["metadata_enhanced"] = True
        logger.info("Enhanced metadata search scope")
        return intent

class CyclicMultiAgentArgoRAG:
    """Cyclic multi-agent RAG system for iterative oceanographic analysis"""
    
    def __init__(self, max_cycles: int = 3):
        """Initialize the cyclic multi-agent system"""
        self.tools = ArgoToolFactory()
        self.max_cycles = max_cycles
        
        # Import agents from the previous multi-agent system
        from .multi_agent_rag import MeasurementAgent, MetadataAgent, SemanticAgent, CoordinatorAgent
        
        # Initialize all agents
        self.measurement_agent = MeasurementAgent(self.tools)
        self.metadata_agent = MetadataAgent(self.tools)
        self.semantic_agent = SemanticAgent(self.tools)
        self.coordinator_agent = CoordinatorAgent()
        self.analysis_agent = AnalysisAgent()
        self.refinement_agent = RefinementAgent(self.tools)
        
        # Create the cyclic graph
        self.graph = self._create_cyclic_graph()
    
    def _create_cyclic_graph(self) -> StateGraph:
        """Create the cyclic multi-agent workflow graph"""
        
        def parse_intent(state: CyclicAgentState) -> CyclicAgentState:
            """Parse user query to determine intent"""
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
                
                # Determine which agents to activate
                needs_measurements = any(word in query.lower() for word in 
                    ["temperature", "salinity", "pressure", "measurement", "data", "profile"])
                needs_metadata = any(word in query.lower() for word in 
                    ["metadata", "instrument", "parameter", "deployment", "coverage", "available"])
                needs_semantic = any(word in query.lower() for word in 
                    ["similar", "pattern", "inversion", "anomal", "compare", "find"])
                
                # If no specific indicators, activate all agents
                if not any([needs_measurements, needs_metadata, needs_semantic]):
                    needs_measurements = needs_metadata = needs_semantic = True
                
                intent = {
                    "float_id": float_id,
                    "spatial_filter": spatial_filter,
                    "region_name": region_name,
                    "needs_measurements": needs_measurements,
                    "needs_metadata": needs_metadata,
                    "needs_semantic": needs_semantic
                }
                
                state["intent"] = intent
                state["cycle_count"] = 0
                state["needs_refinement"] = False
                state["quality_score"] = 0.0
                
                logger.info(f"Parsed intent: {intent}")
                return state
                
            except Exception as e:
                logger.error(f"Error parsing intent: {e}")
                state["error"] = str(e)
                return state
        
        def execute_agents(state: CyclicAgentState) -> CyclicAgentState:
            """Execute relevant agents"""
            try:
                intent = state["intent"]
                query = state["query"]
                cycle = state["cycle_count"]
                
                logger.info(f"Executing agents (cycle {cycle})")
                
                # Execute agents based on intent
                if intent["needs_measurements"]:
                    state["measurement_results"] = self.measurement_agent.process(query, intent)
                
                if intent["needs_metadata"]:
                    state["metadata_results"] = self.metadata_agent.process(query, intent)
                
                if intent["needs_semantic"]:
                    state["semantic_results"] = self.semantic_agent.process(query, intent)
                
                return state
                
            except Exception as e:
                logger.error(f"Error executing agents: {e}")
                state["error"] = str(e)
                return state
        
        def analyze_quality(state: CyclicAgentState) -> CyclicAgentState:
            """Analyze the quality of results and determine if refinement is needed"""
            try:
                analysis = self.analysis_agent.analyze_results(
                    query=state["query"],
                    measurement_results=state.get("measurement_results"),
                    metadata_results=state.get("metadata_results"),
                    semantic_results=state.get("semantic_results")
                )
                
                state["analysis_results"] = analysis
                state["quality_score"] = analysis.get("overall_quality", 0.0)
                state["needs_refinement"] = analysis.get("needs_refinement", False)
                state["refinement_suggestions"] = analysis.get("refinement_suggestions", [])
                
                logger.info(f"Quality analysis: {analysis.get('analysis_summary', 'No summary')}")
                return state
                
            except Exception as e:
                logger.error(f"Error analyzing quality: {e}")
                state["error"] = str(e)
                return state
        
        def should_refine(state: CyclicAgentState) -> Literal["refine", "synthesize"]:
            """Decide whether to refine or proceed to synthesis"""
            if state.get("error"):
                return "synthesize"
            
            cycle_count = state.get("cycle_count", 0)
            max_cycles = state.get("max_cycles", self.max_cycles)
            needs_refinement = state.get("needs_refinement", False)
            
            if needs_refinement and cycle_count < max_cycles:
                logger.info(f"Refinement needed, continuing cycle {cycle_count + 1}")
                return "refine"
            else:
                logger.info(f"No refinement needed or max cycles reached, proceeding to synthesis")
                return "synthesize"
        
        def refine_intent(state: CyclicAgentState) -> CyclicAgentState:
            """Refine the intent based on analysis feedback"""
            try:
                refinement = self.refinement_agent.refine_and_retry(
                    original_intent=state["intent"],
                    suggestions=state.get("refinement_suggestions", []),
                    cycle_count=state["cycle_count"]
                )
                
                # Update intent with refinements
                if "refined_intent" in refinement:
                    state["intent"] = refinement["refined_intent"]
                
                # Increment cycle count
                state["cycle_count"] = state["cycle_count"] + 1
                
                logger.info(f"Refined intent for cycle {state['cycle_count']}")
                return state
                
            except Exception as e:
                logger.error(f"Error refining intent: {e}")
                state["error"] = str(e)
                return state
        
        def synthesize_response(state: CyclicAgentState) -> CyclicAgentState:
            """Synthesize final response including cycle information"""
            try:
                if state.get("error"):
                    state["final_response"] = f"Error: {state['error']}"
                    return state
                
                # Include cycle information in synthesis
                cycle_info = {
                    "total_cycles": state.get("cycle_count", 0),
                    "final_quality_score": state.get("quality_score", 0.0),
                    "analysis_summary": state.get("analysis_results", {}).get("analysis_summary", "")
                }
                
                response = self.coordinator_agent.synthesize_results(
                    query=state["query"],
                    measurement_results=state.get("measurement_results"),
                    metadata_results=state.get("metadata_results"),
                    semantic_results=state.get("semantic_results")
                )
                
                # Add cycle information to response
                cycle_summary = f"\n\n---\n**Analysis Process Summary:**\n" + \
                               f"- Completed {cycle_info['total_cycles']} analysis cycles\n" + \
                               f"- Final quality score: {cycle_info['final_quality_score']:.2f}\n" + \
                               f"- {cycle_info['analysis_summary']}"
                
                state["final_response"] = response + cycle_summary
                return state
                
            except Exception as e:
                logger.error(f"Error synthesizing response: {e}")
                state["final_response"] = f"Error synthesizing response: {str(e)}"
                return state
        
        # Create the cyclic graph
        workflow = StateGraph(CyclicAgentState)
        
        # Add nodes
        workflow.add_node("parse_intent", parse_intent)
        workflow.add_node("execute_agents", execute_agents)
        workflow.add_node("analyze_quality", analyze_quality)
        workflow.add_node("refine_intent", refine_intent)
        workflow.add_node("synthesize_response", synthesize_response)
        
        # Add edges
        workflow.set_entry_point("parse_intent")
        workflow.add_edge("parse_intent", "execute_agents")
        workflow.add_edge("execute_agents", "analyze_quality")
        
        # Conditional edge for cycling
        workflow.add_conditional_edges(
            "analyze_quality",
            should_refine,
            {
                "refine": "refine_intent",
                "synthesize": "synthesize_response"
            }
        )
        
        # Cycle back to execute_agents after refinement
        workflow.add_edge("refine_intent", "execute_agents")
        workflow.add_edge("synthesize_response", END)
        
        return workflow.compile()
    
    def query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Process a query using the cyclic multi-agent system with conversation memory"""
        try:
            # First, classify the query to determine if it needs full multi-agent processing
            classification_result = self._classify_query(query, conversation_history)
            
            if not classification_result["needs_multi_agent"]:
                return classification_result["response"]
            
            # For oceanographic queries, proceed with full multi-agent processing
            # Build conversation context (keep only last 2 exchanges for efficiency)
            messages = []
            if conversation_history:
                for msg in conversation_history[-4:]:  # Keep last 2 exchanges (4 messages)
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
                "cycle_count": 0,
                "max_cycles": self.max_cycles,
                "measurement_results": None,
                "metadata_results": None,
                "semantic_results": None,
                "analysis_results": None,
                "needs_refinement": False,
                "refinement_suggestions": [],
                "quality_score": 0.0,
                "final_response": None,
                "error": None
            }
            
            # Run the cyclic graph
            final_state = self.graph.invoke(initial_state)
            
            return final_state.get("final_response", "No response generated")
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"Error processing query: {str(e)}"
    
    def _execute_full_analysis(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Execute full multi-agent analysis without classification (used by Main Agent)"""
        try:
            # Build conversation context
            messages = []
            if conversation_history:
                for msg in conversation_history[-4:]:  # Keep last 2 exchanges (4 messages)
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
                "cycle_count": 0,
                "max_cycles": self.max_cycles,
                "measurement_results": None,
                "metadata_results": None,
                "semantic_results": None,
                "analysis_results": None,
                "needs_refinement": False,
                "refinement_suggestions": [],
                "quality_score": 0.0,
                "final_response": None,
                "error": None
            }
            
            # Run the cyclic graph
            final_state = self.graph.invoke(initial_state)
            
            return final_state.get("final_response", "No response generated")
            
        except Exception as e:
            logger.error(f"Error in full analysis: {e}")
            return f"Error processing oceanographic analysis: {str(e)}"
    
    def _classify_query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Classify query to determine if it needs multi-agent processing"""
        query_lower = query.lower().strip()
        
        # Quick exit for simple list queries (should be handled by Main Agent)
        if any(pattern in query_lower for pattern in ["list all float", "all float id", "show me all float"]):
            return {
                "needs_multi_agent": False,
                "response": "This query should be handled by the Main Agent for better performance."
            }
        
        # Simple conversational patterns
        conversational_patterns = [
            "hello", "hi", "hey", "greetings",
            "thank you", "thanks", "thx",
            "goodbye", "bye", "see you",
            "how are you", "what can you do", "help",
            "who are you", "what is your name"
        ]
        
        # Previous question patterns
        previous_patterns = [
            "what was my previous question",
            "what did i ask before",
            "what was my last query",
            "previous question",
            "last question"
        ]
        
        # Check for conversational queries
        for pattern in conversational_patterns:
            if pattern in query_lower:
                return {
                    "needs_multi_agent": False,
                    "response": self._get_conversational_response(pattern)
                }
        
        # Check for previous question queries
        for pattern in previous_patterns:
            if pattern in query_lower:
                return {
                    "needs_multi_agent": False,
                    "response": self._get_previous_question_response(conversation_history)
                }
        
        # Check for oceanographic terms that indicate need for multi-agent processing
        oceanographic_terms = [
            "temperature", "temp", "salinity", "salt", "pressure", "depth",
            "float", "argo", "ocean", "sea", "marine", "measurement", "data",
            "analysis", "trend", "pattern", "arabian sea", "bay of bengal",
            "indian ocean", "latitude", "longitude", "cycle", "profile"
        ]
        
        # Check for float ID patterns (like 1901740)
        float_id_pattern = re.search(r'\b\d{7}\b', query_lower)  # 7-digit float IDs
        
        oceanographic_count = sum(1 for term in oceanographic_terms if term in query_lower)
        
        # If multiple oceanographic terms, specific data request, or float ID mentioned, use multi-agent
        if (oceanographic_count >= 2 or 
            any(term in query_lower for term in ["float", "argo", "measurement", "data", "analysis"]) or
            float_id_pattern):
            return {
                "needs_multi_agent": True,
                "response": None
            }
        
        # For simple definitions or single term queries
        if oceanographic_count == 1 and any(word in query_lower for word in ["what is", "define", "explain", "meaning"]):
            return {
                "needs_multi_agent": False,
                "response": self._get_simple_definition(query_lower)
            }
        
        # Default to conversational for unclear queries
        return {
            "needs_multi_agent": False,
            "response": "I'm Oceanus, your oceanographic data analysis assistant. I can help you analyze Argo float data, ocean measurements, and provide insights about marine conditions. Could you please specify what ocean data or measurements you'd like to explore?"
        }
    
    def _get_conversational_response(self, pattern: str) -> str:
        """Get appropriate response for conversational queries"""
        responses = {
            "hello": "Hello! I'm Oceanus, your oceanographic data analysis assistant. I can help you analyze Argo float data, ocean measurements, and provide insights about marine conditions. What would you like to explore?",
            "hi": "Hi there! I'm here to help with oceanographic data analysis. What ocean data would you like to explore?",
            "hey": "Hey! Ready to dive into some oceanographic data analysis? What can I help you with?",
            "thank": "You're welcome! Feel free to ask me anything about oceanographic data or Argo float measurements.",
            "goodbye": "Goodbye! Feel free to return anytime you need oceanographic data analysis.",
            "bye": "See you later! Come back anytime for ocean data insights.",
            "how are you": "I'm doing great and ready to help with oceanographic analysis! What data would you like to explore?",
            "what can you do": "I can analyze oceanographic data from Argo floats including temperature, salinity, and pressure measurements. I can provide insights about ocean conditions, trends, and patterns across different regions and time periods. Try asking about specific floats, regions, or oceanographic parameters!",
            "help": "I'm here to help with oceanographic data analysis! You can ask me about:\n- Specific Argo float data (e.g., 'Show me data for float 1901442')\n- Ocean conditions in regions (e.g., 'Temperature in Arabian Sea')\n- Trends and patterns in oceanographic measurements\n- Comparisons between different regions or time periods\n\nWhat would you like to explore?",
            "who are you": "I'm Oceanus, an AI assistant specialized in oceanographic data analysis. I work with Argo float data to provide insights about ocean conditions, temperature, salinity, and pressure measurements.",
        }
        
        for key, response in responses.items():
            if key in pattern:
                return response
        
        return responses["hello"]
    
    def _get_previous_question_response(self, conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Get response about previous question"""
        if not conversation_history:
            return "This is the start of our conversation. You haven't asked any previous questions yet. What oceanographic data would you like to explore?"
        
        # Find the last user question
        for msg in reversed(conversation_history):
            if msg["role"] == "user":
                return f"Your previous question was: \"{msg['content']}\"\n\nWould you like to continue with that topic or ask something new about oceanographic data?"
        
        return "I don't see any previous questions in our conversation. What oceanographic data would you like to explore?"
    
    def _get_simple_definition(self, query_lower: str) -> str:
        """Provide simple definitions for oceanographic terms"""
        definitions = {
            "temperature": "**Ocean Temperature**: Measured in degrees Celsius (°C), ocean temperature varies with depth, season, and location. Surface waters are typically warmer than deep waters due to solar heating. Temperature affects water density and ocean circulation patterns.",
            "salinity": "**Salinity**: Measures the salt content in seawater, expressed in Practical Salinity Units (PSU). Average ocean salinity is about 35 PSU. Salinity affects water density and is influenced by evaporation, precipitation, and freshwater input.",
            "pressure": "**Ocean Pressure**: Increases with depth, measured in decibars (dbar). Approximately 1 dbar equals 1 meter of depth. Pressure measurements help determine the exact depth of oceanographic observations.",
            "argo": "**Argo Program**: A global network of autonomous profiling floats that measure temperature, salinity, and pressure in the upper 2000m of the ocean. These floats drift with currents and surface periodically to transmit data.",
            "float": "**Argo Float**: An autonomous instrument that drifts with ocean currents and periodically profiles the water column, measuring temperature, salinity, and pressure as it ascends to the surface.",
        }
        
        for term, definition in definitions.items():
            if term in query_lower:
                return definition
        
        return "I can provide detailed analysis of oceanographic data. Please specify what measurements, regions, or phenomena you'd like to explore."
    
    def close(self):
        """Clean up resources"""
        self.tools.close_all()