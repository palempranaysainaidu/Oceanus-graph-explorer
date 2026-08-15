"""
FastAPI dependencies
"""

from fastapi import Depends, HTTPException, Request
from core.agent_manager import AgentManager
from core.session_manager import SessionManager

def get_agent_manager(request: Request) -> AgentManager:
    """
    Get the agent manager from application state or create default on-demand.
    """
    if not hasattr(request.app.state, 'agent_manager') or request.app.state.agent_manager is None:
        am = AgentManager()
        am.is_healthy = True
        request.app.state.agent_manager = am

    return request.app.state.agent_manager

def get_session_manager(request: Request) -> SessionManager:
    """
    Get the session manager from application state or create default on-demand.
    """
    if not hasattr(request.app.state, 'session_manager') or request.app.state.session_manager is None:
        from core.config import get_settings
        settings = get_settings()
        sm = SessionManager(
            session_timeout=settings.SESSION_TIMEOUT,
            max_messages_per_session=settings.MAX_MESSAGES_PER_SESSION
        )
        request.app.state.session_manager = sm

    return request.app.state.session_manager