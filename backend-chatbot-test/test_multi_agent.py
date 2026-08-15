import sys
import logging
from agent.multi_agent_rag import MultiAgentArgoRAG

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create multi-agent instance
agent = MultiAgentArgoRAG()

try:
    # Test 1: Complex query that benefits from multi-agent approach
    query1 = "Analyze float 7902073: show me its measurements, metadata, and find similar patterns in the Arabian Sea"
    logger.info(f"Executing multi-agent query 1: {query1}")
    response = agent.query(query1)
    print("\nMulti-Agent Response 1:")
    print(response)
    
    # Test 2: Regional analysis query
    query2 = "Compare the data coverage and measurement patterns between Arabian Sea and Bay of Bengal"
    logger.info(f"Executing multi-agent query 2: {query2}")
    response = agent.query(query2)
    print("\nMulti-Agent Response 2:")
    print(response)
    
    # Test 3: Semantic pattern search
    query3 = "Find unusual temperature inversion patterns and provide metadata about the floats that detected them"
    logger.info(f"Executing multi-agent query 3: {query3}")
    response = agent.query(query3)
    print("\nMulti-Agent Response 3:")
    print(response)
    
except Exception as e:
    logger.error(f"Error during testing: {e}", exc_info=True)
finally:
    # Clean up resources
    agent.close()