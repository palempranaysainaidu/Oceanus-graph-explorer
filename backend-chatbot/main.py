# main.py - FastAPI Application
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from agents.main_agent import MainAgent
from session_manager import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for agents
main_agent = None
session_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global main_agent, session_manager
    logger.info("Starting up application...")
    main_agent = MainAgent()
    session_manager = SessionManager(expiry_minutes=30)
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if main_agent:
        main_agent.close()
    if session_manager:
        session_manager.cleanup_all()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Oceanographic Data Analysis API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development only)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    agents_used: List[str]
    execution_time: float
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    message: str

@app.post("/session/create", response_model=SessionResponse)
async def create_session():
    """
    Create a new session for conversation tracking
    """
    session_id = session_manager.create_session()
    return {
        "session_id": session_id,
        "message": "Session created successfully"
    }

@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Process user query through the multi-agent system with session tracking
    """
    try:
        # Create session if not provided
        if not session_id:
            session_id = session_manager.create_session()
            logger.info(f"Created new session: {session_id}")
        
        # Get conversation history from session
        conversation_history = session_manager.get_conversation_history(session_id)
        
        # Process query
        result = main_agent.process_query(
            query=request.query,
            conversation_history=conversation_history
        )
        
        # Update session with new query and response
        session_manager.add_message(session_id, "user", request.query)
        session_manager.add_message(session_id, "assistant", result["response"])
        
        # Add session_id to response
        result["session_id"] = session_id
        
        return result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    Get conversation history for a session
    """
    try:
        history = session_manager.get_conversation_history(session_id)
        return {
            "session_id": session_id,
            "conversation_history": history,
            "message_count": len(history)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its conversation history
    """
    try:
        session_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
