"""
Configuration settings for the Argo agent.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Groq API Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# System prompts for LLM
SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing Argo float oceanographic data.
Your task is to parse user queries about oceanographic measurements, metadata, and patterns.
Your response must be in valid JSON format with the following structure:
{
    "type": "measurement|metadata|semantic",
    "parameters": {
        "float_id": "extract any float ID mentioned (e.g., 5906432)",
        "spatial_filter": {
            "min_lat": "minimum latitude as float",
            "max_lat": "maximum latitude as float",
            "min_lon": "minimum longitude as float",
            "max_lon": "maximum longitude as float"
        },
        "temporal_filter": {
            "start": "ISO date",
            "end": "ISO date"
        },
        "parameter_filter": ["temp", "psal", "pres"]
    }
}

For float IDs: Extract any number following 'float' (e.g., 'float 5906432' → "float_id": "5906432")
For coordinates: Convert lat/lon ranges (e.g., '15-20°N, 60-65°E' → spatial_filter with min_lat=15, max_lat=20, min_lon=60, max_lon=65)
For regions: Include coordinates for known regions (Arabian Sea: 10-25°N, 55-75°E)
"""

# Agent Configuration
MAX_RETRIES = 3
TIMEOUT = 30  # seconds
CACHE_TTL = 300  # 5 minutes

# Query Templates
QUERY_TEMPLATES: Dict[str, str] = {
    "measurement": """
    Given the user query about Argo float measurements:
    {query}
    
    Generate an appropriate database query considering:
    1. Temporal aspects (time ranges, aggregations)
    2. Spatial aspects (regions, coordinates)
    3. Parameters (temperature, salinity, pressure)
    4. Float-specific information
    
    Focus on query efficiency and relevance.
    """,
    
    "metadata": """
    Given the user query about Argo float metadata:
    {query}
    
    Generate an appropriate graph query considering:
    1. Regional hierarchies
    2. Float relationships
    3. Parameter coverage
    4. Measurement capabilities
    
    Focus on efficient graph traversal.
    """,
    
    "semantic": """
    Given the user query for semantic search:
    {query}
    
    Generate appropriate search parameters considering:
    1. Contextual similarity
    2. Regional filters
    3. Temporal aspects
    4. Parameter relevance
    
    Focus on semantic relevance and search precision.
    """
}

# Response Templates
RESPONSE_TEMPLATES: Dict[str, str] = {
    "measurement": """
    Based on the Argo float measurements:
    
    {summary}
    
    Key Statistics:
    - Time Range: {time_range}
    - Region: {region}
    - Number of Measurements: {count}
    
    {details}
    """,
    
    "metadata": """
    Metadata Analysis:
    
    {summary}
    
    Coverage:
    - Region: {region}
    - Parameters: {parameters}
    - Float Count: {float_count}
    
    {details}
    """,
    
    "semantic": """
    Semantic Search Results:
    
    {summary}
    
    Top Matches:
    {matches}
    
    Similarity Analysis:
    {analysis}
    """
}