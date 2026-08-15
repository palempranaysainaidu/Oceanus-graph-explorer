"""
Exception handlers for the API
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

class AgentException(Exception):
    """Base exception for agent-related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AgentTimeoutException(AgentException):
    """Exception raised when agent execution times out"""
    pass

class AgentQualityException(AgentException):
    """Exception raised when agent quality is consistently poor"""
    pass

class DatabaseConnectionException(AgentException):
    """Exception raised when database connection fails"""
    pass

def setup_exception_handlers(app: FastAPI):
    """Setup global exception handlers"""
    
    @app.exception_handler(AgentException)
    async def agent_exception_handler(request: Request, exc: AgentException):
        """Handle agent-specific exceptions"""
        logger.error(f"Agent error: {exc.message}", extra={"details": exc.details})
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Agent Error",
                "message": exc.message,
                "details": exc.details,
                "type": "agent_error"
            }
        )
    
    @app.exception_handler(AgentTimeoutException)
    async def agent_timeout_handler(request: Request, exc: AgentTimeoutException):
        """Handle agent timeout exceptions"""
        logger.error(f"Agent timeout: {exc.message}", extra={"details": exc.details})
        
        return JSONResponse(
            status_code=408,
            content={
                "error": "Request Timeout",
                "message": "Agent execution timed out. Please try a simpler query or try again later.",
                "details": exc.details,
                "type": "timeout_error"
            }
        )
    
    @app.exception_handler(DatabaseConnectionException)
    async def database_exception_handler(request: Request, exc: DatabaseConnectionException):
        """Handle database connection exceptions"""
        logger.error(f"Database error: {exc.message}", extra={"details": exc.details})
        
        return JSONResponse(
            status_code=503,
            content={
                "error": "Service Unavailable",
                "message": "Database connection error. Please try again later.",
                "details": exc.details,
                "type": "database_error"
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "type": "http_error"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "type": "validation_error"
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle Starlette HTTP exceptions"""
        logger.warning(f"Starlette HTTP error {exc.status_code}: {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTP Error",
                "message": exc.detail,
                "type": "http_error"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "type": "internal_error"
            }
        )