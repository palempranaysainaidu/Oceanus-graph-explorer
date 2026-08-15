"""
Session management endpoints
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from dependencies import get_session_manager
from core.session_manager import SessionManager
from models.chat import (
    SessionCreateRequest, 
    SessionResponse, 
    ConversationHistoryResponse
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionResponse:
    """
    Create a new conversation session.
    
    Sessions enable conversation continuity and context awareness:
    - **Memory**: Remembers previous queries and responses
    - **Context**: Tracks regions, floats, and parameters discussed
    - **Preferences**: Stores user analysis preferences
    - **Continuity**: Maintains conversation flow across requests
    """
    
    try:
        session_id = await session_manager.create_session(
            user_preferences=request.user_preferences
        )
        
        session = await session_manager.get_session(session_id)
        
        return SessionResponse(
            session_id=session_id,
            created_at=session.created_at,
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session_info(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Get session information and status.
    
    Returns detailed information about a conversation session including:
    - Session metadata (creation time, last activity)
    - Message count and conversation statistics
    - Accumulated context (regions, floats, parameters discussed)
    - User preferences
    """
    
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "message_count": len(session.messages),
        "context": session.context,
        "user_preferences": session.user_preferences,
        "status": "active"
    }

@router.get("/{session_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    session_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Limit number of messages returned"),
    session_manager: SessionManager = Depends(get_session_manager)
) -> ConversationHistoryResponse:
    """
    Get conversation history for a session.
    
    Returns the complete conversation history including:
    - All messages (user queries and assistant responses)
    - Message metadata (timestamps, IDs)
    - Accumulated conversation context
    - Session statistics
    """
    
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    messages = await session_manager.get_conversation_history(session_id, limit)
    
    return ConversationHistoryResponse(
        session_id=session_id,
        messages=[msg.to_dict() for msg in messages],
        context=session.context,
        total_messages=len(session.messages)
    )

@router.put("/{session_id}/preferences")
async def update_user_preferences(
    session_id: str,
    preferences: Dict[str, Any],
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Update user preferences for a session.
    
    User preferences influence how the multi-agent system processes queries:
    - **detail_level**: "brief", "standard", "comprehensive"
    - **preferred_regions**: List of regions to focus on
    - **analysis_focus**: "temperature", "salinity", "patterns", "comparisons"
    - **output_format**: "scientific", "summary", "detailed"
    """
    
    success = await session_manager.update_user_preferences(session_id, preferences)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return {
        "status": "success",
        "message": "User preferences updated",
        "session_id": session_id,
        "updated_preferences": preferences
    }

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Delete a conversation session.
    
    Permanently removes the session and all associated:
    - Conversation history
    - Accumulated context
    - User preferences
    - Session metadata
    """
    
    success = await session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return {
        "status": "success",
        "message": "Session deleted successfully",
        "session_id": session_id
    }

@router.get("/{session_id}/context")
async def get_session_context(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Get accumulated context for a session.
    
    Returns the context that the multi-agent system uses to understand
    the conversation flow and provide more relevant responses:
    - **regions_discussed**: Oceanographic regions mentioned
    - **floats_analyzed**: Float IDs that have been analyzed
    - **parameters_of_interest**: Oceanographic parameters discussed
    - **previous_queries**: Recent query types and patterns
    """
    
    context = await session_manager.get_session_context(session_id)
    
    if not context:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return {
        "session_id": session_id,
        "context": context,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/")
async def get_session_stats(
    session_manager: SessionManager = Depends(get_session_manager)
) -> Dict[str, Any]:
    """
    Get session system statistics.
    
    Returns overall statistics about the session management system:
    - Total number of sessions
    - Active sessions count
    - Total messages across all sessions
    - Average messages per session
    """
    
    stats = await session_manager.get_session_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "statistics": stats,
        "status": "operational"
    }