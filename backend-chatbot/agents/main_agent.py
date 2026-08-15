# agents/main_agent.py - Main Orchestrator Agent
import time
import logging
from typing import Dict, List, Any, Optional
# from langchain_core.messages import HumanMessage, SystemMessage  # Removed unused imports
import google.generativeai as genai
from .cockroachdb_agent import CockroachDBAgent
from .metadata_agent import MetadataAgent
from .semantic_agent import SemanticAgent
from .response_agent import ResponseAgent
from .config import GEMINI_API_KEY, GEMINI_MODEL
logger = logging.getLogger(__name__)

class MainAgent:
    """
    Main orchestrator that decides which agents to invoke and coordinates their execution
    """

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)

        
        self.system_prompt = """You are the Main Orchestrator Agent for an oceanographic data analysis system.
Your role is to analyze user queries and determine which specialized agents need to be involved:
1. **CockroachDBAgent** - For queries about:
   - Temperature, salinity, pressure measurements
   - Float data and profiles
   - Regional oceanographic data
   - Time-series analysis
   - Statistical queries
2. **MetadataAgent** - For queries about:
   - Float metadata (deployment info, parameters measured)
   - Region hierarchies and relationships
   - Float counts and coverage
   - Instrument information
3. **SemanticAgent** - For queries about:
   - Pattern recognition
   - Anomaly detection
   - Similarity searches
   - Comparing phenomena
Respond with a JSON object indicating which agents to use:
{
    "agents_needed": ["cockroachdb", "metadata", "semantic"],
    "reasoning": "Brief explanation of why each agent is needed"
}
Guidelines:
- Most queries will need CockroachDBAgent for actual data
- MetadataAgent provides context about floats and regions
- SemanticAgent is for pattern/similarity analysis
- Simple conversational queries need no agents"""


        self.llm = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=self.system_prompt,  # Use system_instruction
            generation_config={"temperature": 0.1}  # Lower temperature for SQL generation
        )

        # Initialize specialized agents
        self.cockroach_agent = CockroachDBAgent()
        self.metadata_agent = MetadataAgent()
        self.semantic_agent = SemanticAgent()
        self.response_agent = ResponseAgent()

    def process_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main query processing orchestration
        """
        start_time = time.time()

        try:
            # Step 1: Determine which agents are needed
            agents_decision = self._decide_agents(query, conversation_history)

            # Step 2: Check if it's a conversational query (no agents needed)
            if not agents_decision["agents_needed"]:
                response = self._handle_conversational_query(query, conversation_history)
                return {
                    "response": response,
                    "agents_used": [],
                    "execution_time": time.time() - start_time
                }

            # Step 3: Execute required agents in parallel
            agent_results = self._execute_agents(
                query,
                agents_decision["agents_needed"],
                conversation_history
            )

            # Step 4: Pass results to Response Agent for final formatting
            final_response = self.response_agent.format_response(
                query=query,
                agent_results=agent_results
            )

            return {
                "response": final_response,
                "agents_used": agents_decision["agents_needed"],
                "execution_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Error in MainAgent: {e}")
            return {
                "response": f"I encountered an error processing your query: {str(e)}",
                "agents_used": [],
                "execution_time": time.time() - start_time
            }

    def _decide_agents(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Use LLM to decide which agents are needed
        """
        try:
            messages = []

            # Add system prompt as part of the first user message
            system_context = f"{self.system_prompt}\n\n"

            # Add conversation context
            if conversation_history:
                for msg in conversation_history[-4:]:
                    messages.append({"role": "user", "parts": [f"{msg['role']}: {msg['content']}"]})

            decision_prompt = f"""Analyze this query and determine which agents are needed:
Query: "{query}"
Respond ONLY with a JSON object in this exact format:
{{
    "agents_needed": ["agent1", "agent2"],
    "reasoning": "explanation"
}}
Valid agent names: "cockroachdb", "metadata", "semantic"
If no agents needed (conversational query), use empty array: []"""

            messages.append({"role": "user", "parts": [system_context + decision_prompt]})

            response = self.llm.generate_content(messages)

            # Parse LLM response
            import json
            response_text = response.text.strip()  # Changed from response.content to response.text

            # Clean up markdown formatting if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text = response_text.replace("```", "").strip()

            decision = json.loads(response_text)
            logger.info(f"Agent decision: {decision}")

            return decision

        except Exception as e:
            logger.error(f"Error deciding agents: {e}")
            # Default to using all agents if decision fails
            return {
                "agents_needed": ["cockroachdb", "metadata"],
                "reasoning": "Error in decision, using default agents"
            }

    def _execute_agents(
        self,
        query: str,
        agents_needed: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Execute the required agents and gather their results
        """
        results = {}

        if "cockroachdb" in agents_needed:
            logger.info("Executing CockroachDBAgent")
            results["cockroachdb"] = self.cockroach_agent.process(query, conversation_history)

        if "metadata" in agents_needed:
            logger.info("Executing MetadataAgent")
            results["metadata"] = self.metadata_agent.process(query, conversation_history)

        if "semantic" in agents_needed:
            logger.info("Executing SemanticAgent")
            results["semantic"] = self.semantic_agent.process(query, conversation_history)

        return results

    def _handle_conversational_query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Handle queries that don't require specialized agents using LLM
        """
        conversational_system_prompt = """You are a friendly oceanographic data analysis assistant named Oceanus.
Handle general conversational queries directly without accessing any databases or specialized agents.
For queries about:
- Greetings, thanks, farewells
- General questions about your capabilities
- Oceanographic concepts and definitions
- Previous conversation context
Provide helpful, informative responses. For oceanographic concepts, give educational explanations.
Be conversational and natural."""

        messages = []

        # Add conversation context
        if conversation_history:
            for msg in conversation_history[-4:]:
                messages.append({"role": "user", "parts": [f"{msg['role']}: {msg['content']}"]})

        messages.append({"role": "user", "parts": [f"{conversational_system_prompt}\n\n{query}"]})

        response = self.llm.generate_content(messages)
        return response.text  # Changed from response.content to response.text

    def close(self):
        """Cleanup resources"""
        self.cockroach_agent.close()
        self.metadata_agent.close()
        self.semantic_agent.close()
