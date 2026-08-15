"""
Metrics endpoints for monitoring and observability
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends
from dependencies import get_agent_manager
from core.agent_manager import AgentManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_metrics(
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Get system metrics in Prometheus format.
    
    Returns performance and operational metrics for monitoring.
    """
    
    try:
        metrics = await agent_manager.get_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "labels": {
                "service": "oceanographic_multi_agent_rag",
                "version": "1.0.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "metrics": {}
        }

@router.get("/prometheus")
async def get_prometheus_metrics(
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> str:
    """
    Get metrics in Prometheus exposition format.
    
    Returns metrics formatted for Prometheus scraping.
    """
    
    try:
        metrics = await agent_manager.get_metrics()
        
        # Format metrics in Prometheus format
        prometheus_metrics = []
        
        # Add help and type information
        prometheus_metrics.extend([
            "# HELP oceanographic_queries_total Total number of queries processed",
            "# TYPE oceanographic_queries_total counter",
            f"oceanographic_queries_total {metrics['queries_total']}",
            "",
            "# HELP oceanographic_errors_total Total number of query errors",
            "# TYPE oceanographic_errors_total counter", 
            f"oceanographic_errors_total {metrics['errors_total']}",
            "",
            "# HELP oceanographic_error_rate Current error rate",
            "# TYPE oceanographic_error_rate gauge",
            f"oceanographic_error_rate {metrics['error_rate']}",
            "",
            "# HELP oceanographic_response_time_seconds Average response time in seconds",
            "# TYPE oceanographic_response_time_seconds gauge",
            f"oceanographic_response_time_seconds {metrics['avg_response_time_seconds']}",
            "",
            "# HELP oceanographic_agent_healthy Agent system health status (1=healthy, 0=unhealthy)",
            "# TYPE oceanographic_agent_healthy gauge",
            f"oceanographic_agent_healthy {1 if metrics['agent_healthy'] else 0}",
            ""
        ])
        
        return "\n".join(prometheus_metrics)
        
    except Exception as e:
        logger.error(f"Failed to generate Prometheus metrics: {e}")
        return f"# Error generating metrics: {str(e)}\n"

@router.post("/reset")
async def reset_metrics(
    agent_manager: AgentManager = Depends(get_agent_manager)
) -> Dict[str, Any]:
    """
    Reset performance metrics.
    
    Useful for testing or after maintenance windows.
    """
    
    try:
        agent_manager.reset_metrics()
        
        return {
            "status": "success",
            "message": "Metrics reset successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset metrics: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }