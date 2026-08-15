"""
Chat endpoints for the multi-agent RAG system
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
import json
import asyncio

from dependencies import get_agent_manager, get_session_manager
from core.agent_manager import AgentManager
from core.session_manager import SessionManager
from core.exceptions import AgentException, AgentTimeoutException
from models.chat import ChatRequest, ChatResponse, StreamingChatResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@router.post("/query", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    session_manager: SessionManager = Depends(get_session_manager),
    background_tasks: BackgroundTasks = None
) -> ChatResponse:
    """
    Process a chat request using the multi-agent RAG system.
    
    This endpoint processes oceanographic queries using a sophisticated multi-agent system:
    - **MeasurementAgent**: Analyzes time-series data from CockroachDB
    - **MetadataAgent**: Retrieves float and region metadata from Neo4j
    - **SemanticAgent**: Performs pattern matching using Pinecone vector search
    - **AnalysisAgent**: Assesses result quality and suggests improvements
    - **RefinementAgent**: Adjusts parameters for better results
    - **CoordinatorAgent**: Synthesizes findings into research-grade responses
    
    The system uses cyclic refinement (up to 3 cycles) to improve result quality.
    """
    
    try:
        logger.info(f"Processing chat request: {request.query[:100]}...")
        
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Handle session
        session_id = request.session_id
        if not session_id:
            # Create new session if none provided
            session_id = await session_manager.create_session(
                user_preferences=request.user_preferences
            )
            logger.info(f"Created new session: {session_id}")
        else:
            # Validate existing session
            session = await session_manager.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Session not found or expired. Please create a new session."
                )
            
            # Update preferences if provided
            if request.user_preferences:
                await session_manager.update_user_preferences(
                    session_id, request.user_preferences
                )
        
        # Add user message to session
        await session_manager.add_message(
            session_id=session_id,
            role="user",
            content=request.query,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Execute query with session context
        result = await agent_manager.query(
            query=request.query,
            session_id=session_id,
            timeout=request.timeout,
            session_manager=session_manager
        )
        
        # Add assistant response to session
        await session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=result["response"],
            metadata=result["metadata"]
        )
        
        # Get updated context
        context = await session_manager.get_session_context(session_id)
        
        # Log successful request
        if background_tasks:
            background_tasks.add_task(
                log_request,
                request.query,
                result["metadata"]["response_time"],
                "success"
            )
        
        return ChatResponse(
            response=result["response"],
            session_id=session_id,
            metadata=result["metadata"],
            status="success",
            conversation_context=context
        )
        
    except AgentTimeoutException as e:
        logger.warning(f"Chat request timeout: {e.message}")
        
        if background_tasks:
            background_tasks.add_task(
                log_request,
                request.query,
                request.timeout,
                "timeout"
            )
        
        raise HTTPException(
            status_code=408,
            detail={
                "error": "Request Timeout",
                "message": e.message,
                "suggestion": "Try a simpler query or increase timeout"
            }
        )
        
    except AgentException as e:
        logger.error(f"Chat request failed: {e.message}")
        
        if background_tasks:
            background_tasks.add_task(
                log_request,
                request.query,
                0,
                "error"
            )
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Agent Error",
                "message": e.message,
                "details": e.details
            }
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        
        if background_tasks:
            background_tasks.add_task(
                log_request,
                request.query,
                0,
                "error"
            )
        
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    agent_manager: AgentManager = Depends(get_agent_manager),
    session_manager: SessionManager = Depends(get_session_manager)
) -> StreamingResponse:
    """
    Process a chat request with streaming response.
    
    This endpoint provides real-time updates during query processing,
    useful for long-running oceanographic analyses.
    """
    
    async def generate_stream():
        """Generate streaming response"""
        try:
            # Send initial status
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Initializing multi-agent system...'})}\n\n"
            
            # Process query with progress updates
            result = await agent_manager.query(
                query=request.query,
                timeout=request.timeout
            )
            
            # Send progress updates (simulated for now)
            stages = [
                "Parsing query intent...",
                "Executing measurement agent...",
                "Executing metadata agent...",
                "Executing semantic agent...",
                "Analyzing result quality...",
                "Synthesizing final response..."
            ]
            
            for i, stage in enumerate(stages):
                yield f"data: {json.dumps({'status': 'processing', 'message': stage, 'progress': (i + 1) / len(stages) * 100})}\n\n"
                await asyncio.sleep(0.1)  # Small delay for demo
            
            # Send final response
            response = StreamingChatResponse(
                response=result["response"],
                metadata=result["metadata"],
                status="completed"
            )
            
            yield f"data: {json.dumps(response.dict())}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_response = {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

@router.get("/chat/examples")
async def get_examples() -> Dict[str, Any]:
    """
    Get example queries for the oceanographic system.
    """
    
    examples = {
        "measurement_queries": [
            {
                "query": "Show me temperature measurements from float 7902073",
                "description": "Retrieve and analyze temperature data from a specific Argo float",
                "expected_agents": ["MeasurementAgent", "AnalysisAgent", "CoordinatorAgent"]
            },
            {
                "query": "What are the salinity patterns in the Arabian Sea during monsoon season?",
                "description": "Analyze regional salinity data with seasonal context",
                "expected_agents": ["MeasurementAgent", "MetadataAgent", "CoordinatorAgent"]
            }
        ],
        "metadata_queries": [
            {
                "query": "What instruments and parameters are available on float 7902073?",
                "description": "Get detailed metadata about float capabilities and deployment",
                "expected_agents": ["MetadataAgent", "CoordinatorAgent"]
            },
            {
                "query": "How many active floats are in the Bay of Bengal?",
                "description": "Regional coverage and float distribution analysis",
                "expected_agents": ["MetadataAgent", "CoordinatorAgent"]
            }
        ],
        "semantic_queries": [
            {
                "query": "Find profiles showing strong temperature inversions in the Bay of Bengal",
                "description": "Pattern-based search for specific oceanographic phenomena",
                "expected_agents": ["SemanticAgent", "MeasurementAgent", "CoordinatorAgent"]
            },
            {
                "query": "Compare unusual patterns between Arabian Sea and Bay of Bengal",
                "description": "Cross-regional comparative analysis using semantic search",
                "expected_agents": ["SemanticAgent", "MeasurementAgent", "MetadataAgent", "CoordinatorAgent"]
            }
        ],
        "complex_queries": [
            {
                "query": "Analyze float 7902073: show measurements, metadata, and find similar patterns in the Arabian Sea",
                "description": "Comprehensive multi-agent analysis combining all data sources",
                "expected_agents": ["All agents with cyclic refinement"]
            }
        ]
    }
    
    return {
        "examples": examples,
        "tips": [
            "Be specific about float IDs (e.g., 'float 7902073')",
            "Mention regions by name (e.g., 'Arabian Sea', 'Bay of Bengal')",
            "Include parameters of interest (e.g., 'temperature', 'salinity')",
            "Ask for comparisons to trigger semantic search",
            "Complex queries will automatically use multiple cycles for refinement"
        ],
        "supported_regions": [
            "Arabian Sea",
            "Bay of Bengal", 
            "Equatorial Indian Ocean",
            "Southern Indian Ocean"
        ],
        "supported_parameters": [
            "Temperature",
            "Salinity", 
            "Pressure",
            "Depth"
        ]
    }

async def log_request(query: str, response_time: float, status: str):
    """Background task to log request details"""
    logger.info(
        f"Chat request logged",
        extra={
            "query_length": len(query),
            "response_time": response_time,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    )