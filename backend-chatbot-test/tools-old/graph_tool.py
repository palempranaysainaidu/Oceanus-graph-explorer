from langchain.tools import tool
from neo4j import GraphDatabase
import json

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "12345678")

@tool
def graph_query_tool(query: str) -> str:
    """
    Executes a Cypher query against the Argo knowledge graph.
    Use this to find relationships between floats and profiles, or to find floats based on metadata.
    Nodes are :ArgoFloat(wmo_id) and :Profile(unique_id, cycle_number, timestamp, latitude, longitude).
    Relationship is (ArgoFloat)-[:HAS_PROFILE]->(Profile).
    Returns a JSON string of the results.
    """
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        try:
            result = session.run(query)
            return json.dumps([r.data() for r in result], default=str)
        except Exception as e:
            return f"Error executing query: {e}"
    driver.close()