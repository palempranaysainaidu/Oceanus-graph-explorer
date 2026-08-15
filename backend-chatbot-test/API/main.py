"""
Production-grade FastAPI application for Oceanographic Multi-Agent RAG System
"""

import os
import sys
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers import chat, health, metrics, sessions, floats, graph
from middleware import LoggingMiddleware, RateLimitMiddleware, SecurityMiddleware
from core.config import get_settings
from core.logging_config import setup_logging
from core.exceptions import setup_exception_handlers
from dependencies import get_agent_manager

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global agent manager
agent_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent_manager
    
    # Startup
    logger.info("Starting Oceanographic Multi-Agent RAG API...")
    
    # Initialize session manager
    from core.session_manager import SessionManager
    from core.agent_manager import AgentManager
    settings = get_settings()
    
    session_manager = SessionManager(
        session_timeout=settings.SESSION_TIMEOUT,
        max_messages_per_session=settings.MAX_MESSAGES_PER_SESSION
    )
    app.state.session_manager = session_manager

    try:
        # Initialize agent manager
        agent_manager = AgentManager()
        await agent_manager.initialize()
        app.state.agent_manager = agent_manager
        logger.info("Multi-Agent system initialized successfully")
    except Exception as e:
        logger.warning(f"Agent manager initialized in degraded mode: {e}")
        # Attach uninitialized agent manager so app doesn't crash on startup
        if not hasattr(app.state, 'agent_manager') or app.state.agent_manager is None:
            agent_manager = AgentManager()
            app.state.agent_manager = agent_manager

    yield
    
    # Shutdown
    logger.info("Shutting down Oceanographic Multi-Agent RAG API...")
    
    if agent_manager:
        await agent_manager.cleanup()
        logger.info("Agent manager cleaned up")
    
    # Cleanup session manager
    session_manager = getattr(app.state, 'session_manager', None)
    if session_manager:
        await session_manager.shutdown()
        logger.info("Session manager cleaned up")

def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Oceanographic Multi-Agent RAG API",
        description="""
        Production-grade API for oceanographic data analysis using multi-agent RAG system.
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app, settings)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include routers (both v1 and legacy root aliases for frontend compatibility)
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
    app.include_router(chat.router, prefix="", tags=["Chat Aliases"])
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    app.include_router(sessions.router, prefix="/session", tags=["Session Aliases"])
    app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
    app.include_router(floats.router, tags=["Floats"])
    app.include_router(graph.router, tags=["Graph"])
    
    # Setup metrics
    if settings.ENABLE_METRICS:
        instrumentator = Instrumentator()
        instrumentator.instrument(app).expose(app)
    
    return app

def setup_middleware(app: FastAPI, settings):
    """Setup application middleware"""
    
    # Security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Rate limiting
    if settings.ENABLE_RATE_LIMITING:
        app.add_middleware(
            RateLimitMiddleware,
            calls=settings.RATE_LIMIT_CALLS,
            period=settings.RATE_LIMIT_PERIOD
        )
    
    # CORS
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
    
    # Trusted hosts
    if settings.ALLOWED_HOSTS:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )
    
    # Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Logging
    app.add_middleware(LoggingMiddleware)

# Create app instance
app = create_application()

@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint"""
    return {
        "message": "Oceanographic Multi-Agent RAG API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.ENVIRONMENT == "development" else settings.WORKERS
    )