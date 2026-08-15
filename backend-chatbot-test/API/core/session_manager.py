"""
Session management with conversation memory for the multi-agent RAG system
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

@dataclass
class ConversationMessage:
    """Single message in a conversation"""
    id: str
    session_id: str
    timestamp: datetime
    role: str  # 'user' or 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class ConversationSession:
    """Complete conversation session"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    messages: List[ConversationMessage]
    context: Dict[str, Any]
    user_preferences: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages],
            'context': self.context,
            'user_preferences': self.user_preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """Create from dictionary"""
        return cls(
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            messages=[ConversationMessage.from_dict(msg) for msg in data['messages']],
            context=data['context'],
            user_preferences=data['user_preferences']
        )

class SessionManager:
    """Manages conversation sessions with memory and context"""
    
    def __init__(self, session_timeout: int = 3600, max_messages_per_session: int = 100):
        self.session_timeout = session_timeout  # seconds
        self.max_messages_per_session = max_messages_per_session
        self.sessions: Dict[str, ConversationSession] = {}
        self.cleanup_task = None
        
        # Start cleanup task
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired sessions safely"""
        try:
            loop = asyncio.get_running_loop()
            async def cleanup_expired_sessions():
                while True:
                    try:
                        await asyncio.sleep(300)  # Check every 5 minutes
                        await self.cleanup_expired_sessions()
                    except Exception as e:
                        logger.error(f"Error in session cleanup: {e}")
            
            self.cleanup_task = loop.create_task(cleanup_expired_sessions())
        except RuntimeError:
            self.cleanup_task = None
    
    async def create_session(self, user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = ConversationSession(
            session_id=session_id,
            created_at=now,
            last_activity=now,
            messages=[],
            context={
                'regions_discussed': [],
                'floats_analyzed': [],
                'parameters_of_interest': [],
                'analysis_preferences': {},
                'previous_queries': []
            },
            user_preferences=user_preferences or {}
        )
        
        self.sessions[session_id] = session
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Get session by ID"""
        session = self.sessions.get(session_id)
        
        if session:
            # Check if session is expired
            if self._is_session_expired(session):
                await self.delete_session(session_id)
                return None
            
            # Update last activity
            session.last_activity = datetime.now()
        
        return session
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ConversationMessage]:
        """Add a message to the session"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        message_id = str(uuid.uuid4())
        message = ConversationMessage(
            id=message_id,
            session_id=session_id,
            timestamp=datetime.now(),
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_activity = datetime.now()
        
        # Update context based on message content
        await self._update_session_context(session, message)
        
        # Limit message history
        if len(session.messages) > self.max_messages_per_session:
            # Keep recent messages and summary of older ones
            session.messages = session.messages[-self.max_messages_per_session:]
        
        logger.debug(f"Added message to session {session_id}: {role}")
        return message
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Get conversation history for a session"""
        session = await self.get_session(session_id)
        if not session:
            return []
        
        messages = session.messages
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get accumulated context for a session"""
        session = await self.get_session(session_id)
        if not session:
            return {}
        
        return session.context
    
    async def update_user_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences for a session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.user_preferences.update(preferences)
        session.last_activity = datetime.now()
        
        logger.info(f"Updated preferences for session {session_id}")
        return True
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if self._is_session_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.delete_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        now = datetime.now()
        active_sessions = 0
        total_messages = 0
        
        for session in self.sessions.values():
            if not self._is_session_expired(session):
                active_sessions += 1
                total_messages += len(session.messages)
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_sessions,
            'total_messages': total_messages,
            'avg_messages_per_session': total_messages / max(active_sessions, 1)
        }
    
    def _is_session_expired(self, session: ConversationSession) -> bool:
        """Check if a session is expired"""
        return (datetime.now() - session.last_activity).total_seconds() > self.session_timeout
    
    async def _update_session_context(
        self,
        session: ConversationSession,
        message: ConversationMessage
    ):
        """Update session context based on message content"""
        content_lower = message.content.lower()
        
        # Extract and track regions
        regions = ['arabian sea', 'bay of bengal', 'indian ocean', 'equatorial indian ocean', 'southern indian ocean']
        for region in regions:
            if region in content_lower and region not in session.context['regions_discussed']:
                session.context['regions_discussed'].append(region)
        
        # Extract and track float IDs
        import re
        float_matches = re.findall(r'float (\d+)', content_lower)
        for float_id in float_matches:
            if float_id not in session.context['floats_analyzed']:
                session.context['floats_analyzed'].append(float_id)
        
        # Extract and track parameters
        parameters = ['temperature', 'salinity', 'pressure', 'depth']
        for param in parameters:
            if param in content_lower and param not in session.context['parameters_of_interest']:
                session.context['parameters_of_interest'].append(param)
        
        # Track query types for user preferences
        if message.role == 'user':
            query_type = 'unknown'
            if any(word in content_lower for word in ['compare', 'comparison', 'versus', 'vs']):
                query_type = 'comparative'
            elif any(word in content_lower for word in ['pattern', 'similar', 'anomal', 'unusual']):
                query_type = 'pattern_analysis'
            elif any(word in content_lower for word in ['metadata', 'instrument', 'deployment']):
                query_type = 'metadata'
            elif any(word in content_lower for word in ['measurement', 'data', 'temperature', 'salinity']):
                query_type = 'measurement'
            
            session.context['previous_queries'].append({
                'type': query_type,
                'timestamp': message.timestamp.isoformat(),
                'content': message.content[:100]  # First 100 chars
            })
            
            # Keep only recent queries
            if len(session.context['previous_queries']) > 20:
                session.context['previous_queries'] = session.context['previous_queries'][-20:]
    
    async def generate_context_summary(self, session_id: str) -> str:
        """Generate a context summary for the agent"""
        session = await self.get_session(session_id)
        if not session:
            return ""
        
        context = session.context
        summary_parts = []
        
        # Add conversation context
        if context['regions_discussed']:
            summary_parts.append(f"Regions discussed: {', '.join(context['regions_discussed'])}")
        
        if context['floats_analyzed']:
            summary_parts.append(f"Floats analyzed: {', '.join(context['floats_analyzed'])}")
        
        if context['parameters_of_interest']:
            summary_parts.append(f"Parameters of interest: {', '.join(context['parameters_of_interest'])}")
        
        # Add recent query context
        recent_queries = context['previous_queries'][-3:]  # Last 3 queries
        if recent_queries:
            query_types = [q['type'] for q in recent_queries]
            summary_parts.append(f"Recent query types: {', '.join(query_types)}")
        
        # Add user preferences
        if session.user_preferences:
            prefs = []
            for key, value in session.user_preferences.items():
                prefs.append(f"{key}: {value}")
            if prefs:
                summary_parts.append(f"User preferences: {'; '.join(prefs)}")
        
        return "Previous conversation context: " + " | ".join(summary_parts) if summary_parts else ""
    
    async def shutdown(self):
        """Shutdown the session manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Session manager shutdown complete")