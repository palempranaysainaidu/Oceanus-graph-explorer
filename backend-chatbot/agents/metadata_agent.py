# agents/metadata_agent.py - Neo4j Metadata Agent
import logging
from typing import Dict, Any, Optional, List
# from langchain_core.messages import HumanMessage, SystemMessage  # Removed unused imports
import google.generativeai as genai
from tools import ArgoToolFactory
from .config import GEMINI_API_KEY, GEMINI_MODEL
logger = logging.getLogger(__name__)

class MetadataAgent:
    """
    Specialized agent for querying Neo4j for float and region metadata
    """

    def __init__(self):
        self.tools = ArgoToolFactory()
        genai.configure(api_key=GEMINI_API_KEY)

        self.system_prompt = """You are a Cypher query expert for Neo4j graph database containing oceanographic metadata.
## Graph Schema
**Node Types:**
- `Float` nodes: `(f:Float {platform_number: string, deployment_date: date})`
- `Region` nodes: `(r:Region {name: string})`
- `Parameter` nodes: `(p:Parameter {name: string})`
**Relationships:**
- `(f:Float)-[:LOCATED_IN]->(r:Region)`
- `(f:Float)-[:MEASURES]->(p:Parameter)`
- `(r:Region)-[:PART_OF]->(parent:Region)`
## Query Guidelines
1. Always add **LIMIT 50** for listing queries to prevent large result sets
2. Use **COUNT** for aggregate queries (no limit needed)
3. Filter efficiently using indexed properties
4. Return structured results with clear column names
## Common Query Patterns
- **List regions**: `MATCH (r:Region) RETURN r.name as region_name LIMIT 50`
- **Float count by region**: `MATCH (f:Float)-[:LOCATED_IN]->(r:Region) RETURN r.name as region, count(f) as float_count`
- **Parameters measured**: `MATCH (p:Parameter) RETURN p.name as parameter LIMIT 50`
- **Float metadata**: `MATCH (f:Float {platform_number: 'ID'})-[:MEASURES]->(p:Parameter), (f)-[:LOCATED_IN]->(r:Region) RETURN f, collect(p.name) as parameters, r.name as region`
## Response Format
Generate ONLY the Cypher query, no explanation. Remove any markdown formatting."""

        self.llm = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=self.system_prompt,  # Use system_instruction
            generation_config={"temperature": 0.1}  # Lower temperature for SQL generation
        )

    def process(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process query and execute Neo4j operations
        """
        try:
            logger.info(f"MetadataAgent processing: {query}")

            # Generate Cypher query using LLM
            cypher_query = self._generate_cypher(query)

            if not cypher_query:
                return {"error": "Failed to generate Cypher query"}

            # Execute the query
            results = self.tools.neo4j.execute_custom_query(cypher_query)

            # Process results
            if results:
                return {
                    "agent": "MetadataAgent",
                    "cypher_query": cypher_query,
                    "results": results,
                    "count": len(results),
                    "summary": f"Retrieved {len(results)} metadata records from Neo4j"
                }
            else:
                return {
                    "agent": "MetadataAgent",
                    "cypher_query": cypher_query,
                    "results": [],
                    "count": 0,
                    "summary": "No metadata found matching the query criteria"
                }

        except Exception as e:
            logger.error(f"MetadataAgent error: {e}")
            return {
                "agent": "MetadataAgent",
                "error": str(e),
                "cypher_query": cypher_query if 'cypher_query' in locals() else None
            }

    def _generate_cypher(self, query: str) -> Optional[str]:
        """
        Generate Cypher query using LLM
        """
        try:
            messages = [
                {"role": "user", "parts": [f"{self.system_prompt}\n\nGenerate a Cypher query for: {query}\n\nReturn ONLY the Cypher query."]}
            ]

            response = self.llm.generate_content(messages)
            cypher_query = response.text.strip()  # Changed from response.content to response.text

            # Clean up markdown formatting
            if cypher_query.startswith("```cypher"):
                cypher_query = cypher_query.replace("```cypher", "").replace("```", "").strip()
            elif cypher_query.startswith("```"):
                cypher_query = cypher_query.replace("```", "").strip()

            logger.info(f"Generated Cypher: {cypher_query}")
            return cypher_query

        except Exception as e:
            logger.error(f"Error generating Cypher: {e}")
            return None

    def close(self):
        """Cleanup resources"""
        if hasattr(self, 'tools'):
            self.tools.neo4j.close()
