import logging
from agent.langgraph_agent import LangGraphArgoAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create agent instance
agent = LangGraphArgoAgent()

try:
    # Test 1: CockroachDB - Direct measurement query
    query1 = "Show me temperature measurements from float 7902073"
    logger.info(f"Executing query 1 (CockroachDB - Float measurements): {query1}")
    response = agent.query(query1)
    print("\nResponse 1 (CockroachDB - Float measurements):")
    print(response)
    
    # Test 2: Neo4j - Metadata query
    query2 = "What instruments and parameters are available on float 7902073? Show me its deployment history and current status"
    logger.info(f"Executing query 2 (Neo4j - Float metadata): {query2}")
    response = agent.query(query2)
    print("\nResponse 2 (Neo4j - Float metadata):")
    print(response)
    
    # Test 3: Neo4j - Region query
    query3 = "Tell me about the data coverage and available parameters in the Arabian Sea region"
    logger.info(f"Executing query 3 (Neo4j - Region metadata): {query3}")
    response = agent.query(query3)
    print("\nResponse 3 (Neo4j - Region metadata):")
    print(response)
    
    # Test 4: Pinecone - Semantic similarity
    query4 = "Find profiles showing strong temperature inversions in the Bay of Bengal during summer months"
    logger.info(f"Executing query 4 (Pinecone - Semantic search): {query4}")
    response = agent.query(query4)
    print("\nResponse 4 (Pinecone - Semantic search):")
    print(response)
    
    # Test 5: Combined tools
    query5 = (
        "Compare temperature-salinity profiles between float 7902073 and similar floats "
        "in the Arabian Sea, focusing on measurements showing strong stratification"
    )
    logger.info(f"Executing query 5 (Combined tools): {query5}")
    response = agent.query(query5)
    print("\nResponse 5 (Combined tools):")
    print(response)
    
except Exception as e:
    logger.error(f"Error during testing: {e}", exc_info=True)
finally:
    # Clean up resources
    agent.close()