"""
Health check endpoints
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_agent_manager
from core.agent_manager import AgentManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns basic API status without checking agent system.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Oceanographic Multi-Agent RAG API",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check(
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Detailed health check including agent system status.
    
    Performs comprehensive health checks on:
    - API service status
    - Multi-agent system health
    - Database connectivity
    - Performance metrics
    """
    
    try:
        # Get agent health status
        agent_health = await agent_manager.get_health_status()
        
        # Overall system health
        overall_status = "healthy" if agent_health["status"] == "healthy" else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "service": "Oceanographic Multi-Agent RAG API",
            "version": "1.0.0",
            "components": {
                "api": {
                    "status": "healthy",
                    "message": "API service is operational"
                },
                "agent_system": {
                    "status": agent_health["status"],
                    "last_check": agent_health["last_check"],
                    "configuration": agent_health["configuration"]
                },
                "databases": {
                    "status": "healthy" if agent_health["status"] == "healthy" else "unknown",
                    "message": "Database connectivity checked via agent system"
                }
            },
            "metrics": agent_health["metrics"]
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Oceanographic Multi-Agent RAG API",
            "version": "1.0.0",
            "error": str(e),
            "components": {
                "api": {
                    "status": "healthy",
                    "message": "API service is operational"
                },
                "agent_system": {
                    "status": "unhealthy",
                    "error": str(e)
                }
            }
        }

@router.get("/ready")
async def readiness_check(
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/container orchestration.
    
    Returns 200 if the service is ready to accept requests,
    503 if not ready.
    """
    
    try:
        agent_health = await agent_manager.get_health_status()
        
        if agent_health["status"] == "healthy":
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "reason": "Agent system is not healthy",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "reason": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/container orchestration.
    
    Returns 200 if the service is alive (basic API functionality),
    regardless of agent system status.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "service": "Oceanographic Multi-Agent RAG API"
    }