import sys
import logging
from agent.cyclic_multi_agent import CyclicMultiAgentArgoRAG

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create cyclic multi-agent instance with max 3 cycles
agent = CyclicMultiAgentArgoRAG(max_cycles=3)

try:
    # Test 1: Query that might need refinement due to limited results
    query1 = "Find temperature data for float 9999999 in the Arctic Ocean"  # Non-existent float/region
    logger.info(f"Executing cyclic query 1: {query1}")
    response = agent.query(query1)
    print("\nCyclic Agent Response 1 (Expected to cycle due to no results):")
    print(response)
    print("\n" + "="*80 + "\n")
    
    # Test 2: Query that should get good results quickly
    query2 = "Show me data for float 7902073"
    logger.info(f"Executing cyclic query 2: {query2}")
    response = agent.query(query2)
    print("\nCyclic Agent Response 2 (Expected to complete in 1 cycle):")
    print(response)
    print("\n" + "="*80 + "\n")
    
    # Test 3: Complex query that benefits from iterative refinement
    query3 = "Compare unusual patterns between Arabian Sea and Bay of Bengal with detailed analysis"
    logger.info(f"Executing cyclic query 3: {query3}")
    response = agent.query(query3)
    print("\nCyclic Agent Response 3 (Expected to use multiple cycles):")
    print(response)
    
except Exception as e:
    logger.error(f"Error during testing: {e}", exc_info=True)
finally:
    # Clean up resources
    agent.close()