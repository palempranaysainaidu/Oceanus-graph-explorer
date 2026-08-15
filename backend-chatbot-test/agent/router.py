"""
FastAPI router for the Argo chatbot API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging
from .core import ArgoAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Dependency for ArgoAgent
async def get_agent():
    """Dependency to get ArgoAgent instance"""
    agent = ArgoAgent()
    try:
        yield agent
    finally:
        agent.close()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    agent: ArgoAgent = Depends(get_agent)
):
    """
    Process a chat request and return the response
    
    Args:
        request: ChatRequest object containing query and optional context
        agent: ArgoAgent instance (injected by FastAPI)
        
    Returns:
        ChatResponse object with the agent's response
    """
    try:
        # Log request
        logger.info(f"Received chat request: {request.query}")
        
        # Process query
        response = agent.query(request.query)
        
        # Log success
        logger.info("Successfully processed chat request")
        
        return ChatResponse(
            response=response,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "query_length": len(request.query),
                "response_length": len(response)
            }
        )
        
    except Exception as e:
        # Log error
        logger.error(f"Error processing chat request: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )