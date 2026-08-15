"""
Pydantic models for chat endpoints
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Oceanographic query to process",
        example="Show me temperature measurements from float 7902073"
    )
    
    session_id: Optional[str] = Field(
        None,
        description="Session ID for conversation continuity",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    timeout: Optional[int] = Field(
        300,
        ge=30,
        le=600,
        description="Query timeout in seconds (30-600)",
        example=300
    )
    
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the query",
        example={"region": "Arabian Sea", "parameter": "temperature"}
    )
    
    user_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="User preferences for analysis",
        example={"detail_level": "comprehensive", "preferred_regions": ["Arabian Sea"]}
    )
    
    @validator("query")
    def validate_query(cls, v):
        """Validate query content"""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Analyze float 7902073: show me its measurements, metadata, and find similar patterns in the Arabian Sea",
                "timeout": 300,
                "context": {
                    "region": "Arabian Sea",
                    "analysis_type": "comprehensive"
                }
            }
        }

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    
    response: str = Field(
        ...,
        description="Generated response from the multi-agent system"
    )
    
    session_id: str = Field(
        ...,
        description="Session ID for this conversation"
    )
    
    metadata: Dict[str, Any] = Field(
        ...,
        description="Query execution metadata"
    )
    
    status: str = Field(
        ...,
        description="Response status",
        example="success"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Response timestamp"
    )
    
    conversation_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Current conversation context"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "response": "Based on the Argo float measurements:\n\nFound 469 measurements...",
                "metadata": {
                    "query_id": "q_1234567890",
                    "timestamp": "2025-01-01T12:00:00",
                    "response_time": 15.2,
                    "agent_type": "cyclic_multi_agent",
                    "max_cycles": 3,
                    "quality_threshold": 0.7
                },
                "status": "success",
                "timestamp": "2025-01-01T12:00:15"
            }
        }

class StreamingChatResponse(BaseModel):
    """Response model for streaming chat endpoint"""
    
    response: Optional[str] = Field(
        None,
        description="Generated response (only in final message)"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Query execution metadata (only in final message)"
    )
    
    status: str = Field(
        ...,
        description="Current status",
        example="processing"
    )
    
    message: Optional[str] = Field(
        None,
        description="Status message",
        example="Executing measurement agent..."
    )
    
    progress: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Progress percentage (0-100)",
        example=75.0
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Message timestamp"
    )

class ErrorResponse(BaseModel):
    """Error response model"""
    
    error: str = Field(
        ...,
        description="Error type",
        example="Agent Error"
    )
    
    message: str = Field(
        ...,
        description="Error message",
        example="Query execution failed"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    
    type: str = Field(
        ...,
        description="Error category",
        example="agent_error"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Error timestamp"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Agent Timeout",
                "message": "Query execution timed out after 300 seconds",
                "details": {
                    "query": "Complex oceanographic analysis...",
                    "timeout": 300
                },
                "type": "timeout_error",
                "timestamp": "2025-01-01T12:05:00"
            }
        }
class SessionCreateRequest(BaseModel):
    """Request to create a new session"""
    
    user_preferences: Optional[Dict[str, Any]] = Field(
        None,
        description="Initial user preferences",
        example={
            "detail_level": "comprehensive",
            "preferred_regions": ["Arabian Sea", "Bay of Bengal"],
            "analysis_focus": "temperature_patterns"
        }
    )

class SessionResponse(BaseModel):
    """Response with session information"""
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    created_at: datetime = Field(
        ...,
        description="Session creation timestamp"
    )
    
    status: str = Field(
        ...,
        description="Session status",
        example="active"
    )

class ConversationHistoryResponse(BaseModel):
    """Response with conversation history"""
    
    session_id: str = Field(
        ...,
        description="Session identifier"
    )
    
    messages: List[Dict[str, Any]] = Field(
        ...,
        description="List of conversation messages"
    )
    
    context: Dict[str, Any] = Field(
        ...,
        description="Accumulated conversation context"
    )
    
    total_messages: int = Field(
        ...,
        description="Total number of messages in session"
    )