"""
Example usage and testing of the Argo agent.
"""

from datetime import datetime, timedelta
from .core import ArgoAgent

def test_measurement_queries():
    """Test various measurement-related queries"""
    agent = ArgoAgent()
    
    try:
        # Test specific float query
        print("\nQuerying specific float:")
        response = agent.query(
            "Show me the temperature measurements from float 5906432 "
            "in the last 30 days"
        )
        print(response)
        
        # Test regional query
        print("\nQuerying by region:")
        response = agent.query(
            "What are the average temperature and salinity values in the "
            "Arabian Sea between 15-20°N and 60-65°E?"
        )
        print(response)
        
        # Test temporal aggregation
        print("\nTemporal aggregation query:")
        response = agent.query(
            "Show me the monthly average temperature profile for float "
            "5906432 over the past year"
        )
        print(response)
        
    finally:
        agent.close()

def test_metadata_queries():
    """Test various metadata-related queries"""
    agent = ArgoAgent()
    
    try:
        # Test float metadata
        print("\nQuerying float metadata:")
        response = agent.query(
            "What parameters does float 5906432 measure and in which "
            "region is it located?"
        )
        print(response)
        
        # Test region metadata
        print("\nQuerying region metadata:")
        response = agent.query(
            "How many floats are currently active in the Bay of Bengal "
            "and what parameters do they measure?"
        )
        print(response)
        
        # Test hierarchy query
        print("\nQuerying region hierarchy:")
        response = agent.query(
            "Show me the complete hierarchy of Indian Ocean regions and "
            "their float distribution"
        )
        print(response)
        
    finally:
        agent.close()

def test_semantic_queries():
    """Test various semantic search queries"""
    agent = ArgoAgent()
    
    try:
        # Test similarity search
        print("\nSemantic similarity search:")
        response = agent.query(
            "Find measurements similar to those from float 5906432 "
            "showing a temperature inversion"
        )
        print(response)
        
        # Test pattern search
        print("\nPattern search:")
        response = agent.query(
            "Find instances of unusual salinity patterns in the "
            "Arabian Sea during monsoon season"
        )
        print(response)
        
        # Test complex query
        print("\nComplex semantic query:")
        response = agent.query(
            "Find measurements showing strong correlation between "
            "temperature and salinity anomalies in the Bay of Bengal"
        )
        print(response)
        
    finally:
        agent.close()

if __name__ == "__main__":
    test_measurement_queries()
    test_metadata_queries()
    test_semantic_queries()