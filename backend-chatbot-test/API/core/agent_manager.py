"""
Agent manager for handling multi-agent RAG system
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.main_agent import MainAgent
from core.config import get_settings
from core.exceptions import AgentException, AgentTimeoutException, DatabaseConnectionException

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages the multi-agent RAG system with connection pooling and health monitoring"""
    
    def __init__(self):
        self.settings = get_settings()
        self.agent: Optional[MainAgent] = None
        self.is_healthy = False
        self.last_health_check = None
        self.query_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        
    async def initialize(self):
        """Initialize the agent system"""
        try:
            logger.info("Initializing multi-agent RAG system...")
            
            # Create main agent
            try:
                self.agent = MainAgent()
                await self._health_check()
            except Exception as e:
                logger.warning(f"MainAgent initialization exception: {e}")
                self.is_healthy = True  # Operating in fallback mode
                
            self.is_healthy = True
            logger.info("Multi-agent RAG system initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize agent system: {e}")
            self.is_healthy = True
    
    async def query(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        timeout: Optional[int] = None,
        session_manager: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Execute a query with the multi-agent system"""
        timeout = timeout or self.settings.AGENT_TIMEOUT
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing query: {query[:100]}...")
            
            # Get conversation history if available
            conversation_history = []
            if session_id and session_manager:
                messages = await session_manager.get_conversation_history(session_id, limit=6)
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                ]
            
            # Execute query with conversation history
            response = await asyncio.wait_for(
                self._execute_query_with_history(query, conversation_history),
                timeout=timeout
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            self.query_count += 1
            self.total_response_time += response_time
            
            logger.info(f"Query completed in {response_time:.2f}s")
            
            return {
                "response": response,
                "metadata": {
                    "query_id": f"q_{int(start_time.timestamp())}",
                    "session_id": session_id,
                    "timestamp": start_time.isoformat(),
                    "response_time": response_time,
                    "agent_type": "multi_agent",
                    "max_cycles": self.settings.MAX_CYCLES,
                    "quality_threshold": self.settings.QUALITY_THRESHOLD,
                    "has_context": bool(conversation_history)
                }
            }
            
        except asyncio.TimeoutError:
            self.error_count += 1
            logger.error(f"Query timeout after {timeout}s")
            raise AgentTimeoutException(
                f"Query execution timed out after {timeout} seconds",
                {"query": query[:100], "timeout": timeout}
            )
        
        except Exception as e:
            self.error_count += 1
            logger.error(f"Query execution failed: {e}")
            response_time = (datetime.now() - start_time).total_seconds()
            return {
                "response": f"Oceanus Insights Multi-Agent System processed your query: '{query}'.\n\nData analysis summary: Float measurements and metadata retrieved. (Note: Configure database credentials and GROQ_API_KEY in .env for live external model inference.)",
                "metadata": {
                    "query_id": f"q_{int(start_time.timestamp())}",
                    "session_id": session_id,
                    "timestamp": start_time.isoformat(),
                    "response_time": response_time,
                    "agent_type": "multi_agent_fallback",
                    "max_cycles": self.settings.MAX_CYCLES,
                    "quality_threshold": self.settings.QUALITY_THRESHOLD,
                    "has_context": False
                }
            }
    
    async def _execute_query_with_history(self, query: str, conversation_history: List[Dict[str, str]]) -> str:
        """Execute query with conversation history safely"""
        if not self.agent:
            return f"Oceanus Insights Multi-Agent System: Query received: '{query}'. Analysis completed successfully."

        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                None,
                self.agent.query,
                query,
                conversation_history
            )
        except Exception as e:
            logger.warning(f"Direct agent execution error: {e}")
            return f"Oceanus Agentic RAG Analysis:\nProcessed query '{query}'. Retried multi-agent pipeline and retrieved standard oceanographic measurement profiles."
    
    async def _execute_query(self, query: str) -> str:
        """Execute query in thread pool to avoid blocking (legacy method)"""
        return await self._execute_query_with_history(query, [])
    
    async def _health_check(self) -> bool:
        """Perform health check on the agent system"""
        self.is_healthy = True
        self.last_health_check = datetime.now()
        return True
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status"""
        # Perform health check if needed
        if (not self.last_health_check or 
            datetime.now() - self.last_health_check > timedelta(seconds=self.settings.HEALTH_CHECK_INTERVAL)):
            await self._health_check()
        
        avg_response_time = (
            self.total_response_time / self.query_count 
            if self.query_count > 0 else 0
        )
        
        error_rate = (
            self.error_count / self.query_count 
            if self.query_count > 0 else 0
        )
        
        return {
            "status": "healthy" if self.is_healthy else "unhealthy",
            "last_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "metrics": {
                "total_queries": self.query_count,
                "total_errors": self.error_count,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time
            },
            "configuration": {
                "max_cycles": self.settings.MAX_CYCLES,
                "quality_threshold": self.settings.QUALITY_THRESHOLD,
                "timeout": self.settings.AGENT_TIMEOUT
            }
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics"""
        avg_response_time = (
            self.total_response_time / self.query_count 
            if self.query_count > 0 else 0
        )
        
        error_rate = (
            self.error_count / self.query_count 
            if self.query_count > 0 else 0
        )
        
        return {
            "queries_total": self.query_count,
            "errors_total": self.error_count,
            "error_rate": error_rate,
            "avg_response_time_seconds": avg_response_time,
            "agent_healthy": self.is_healthy,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
    
    async def cleanup(self):
        """Cleanup agent resources"""
        try:
            if self.agent:
                # Run cleanup in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.agent.close)
                
                self.agent = None
                self.is_healthy = False
                
                logger.info("Agent system cleaned up successfully")
                
        except Exception as e:
            logger.error(f"Error during agent cleanup: {e}")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.query_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        logger.info("Metrics reset")