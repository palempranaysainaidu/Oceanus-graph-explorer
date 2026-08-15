"""
Graph database API routes for CognoDB exploration and agent integration.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from tools.cognodb_client import CognodbClient
from tools.graph_queries import GraphQueries

logger = logging.getLogger(__name__)
router = APIRouter()

_client = CognodbClient()
_queries = GraphQueries(_client)


class GraphHealthResponse(BaseModel):
    status: str
    connected: bool
    uri: Optional[str] = None
    message: Optional[str] = None


@router.get("/api/graph/health", response_model=GraphHealthResponse)
@router.get("/graph/health", response_model=GraphHealthResponse)
async def graph_health():
    """CognoDB connectivity check."""
    h = _client.health_check()
    return GraphHealthResponse(
        status=h.get("status", "unknown"),
        connected=h.get("connected", False),
        uri=h.get("uri"),
        message=h.get("message"),
    )


@router.get("/api/graph/stats")
@router.get("/graph/stats")
async def graph_stats():
    """Node and relationship counts."""
    return _queries.get_stats()


@router.get("/api/graph/regions")
@router.get("/graph/regions")
async def list_regions():
    """All regions with float counts."""
    regions = _queries.list_regions()
    if not regions and not _client.health_check().get("connected"):
        raise HTTPException(status_code=503, detail="CognoDB is not connected. Check .env credentials.")
    return {"regions": regions, "count": len(regions)}


@router.get("/api/graph/regions/{region_name}/floats")
@router.get("/graph/regions/{region_name}/floats")
async def region_floats(region_name: str):
    floats = _queries.floats_in_region(region_name)
    if not floats:
        return {"region": region_name, "floats": [], "count": 0}
    return {"region": region_name, "floats": floats, "count": len(floats)}


@router.get("/api/graph/floats/{platform_number}")
@router.get("/graph/floats/{platform_number}")
async def float_detail(platform_number: str):
    graph = _queries.get_float_graph(platform_number)
    if not graph:
        raise HTTPException(status_code=404, detail=f"Float {platform_number} not found in graph")
    return graph


@router.get("/api/graph/query/multi-hop")
@router.get("/graph/query/multi-hop")
async def query_multi_hop(
    region: str = Query(..., description="Region name, e.g. Arabian Sea"),
    parameter: str = Query("temperature", description="Parameter name"),
    cruise_id: str = Query(..., description="Cruise id, e.g. 1901442_295"),
):
    """
  Multi-hop traversal: floats in a region that recorded a parameter during a cruise.
  """
    results = _queries.floats_in_region_with_parameter_during_cruise(region, parameter, cruise_id)
    return {
        "query": "floats_in_region_with_parameter_during_cruise",
        "params": {"region": region, "parameter": parameter, "cruise_id": cruise_id},
        "results": results,
        "count": len(results),
    }


@router.get("/api/graph/query/shortest-path")
@router.get("/graph/query/shortest-path")
async def query_shortest_path(
    float_a: str = Query(..., description="Source float platform number"),
    float_b: str = Query(..., description="Target float platform number"),
):
    """Shortest path between floats via NEAR_FLOAT proximity network."""
    result = _queries.shortest_path_between_floats(float_a, float_b)
    return {
        "query": "shortest_path_between_floats",
        "params": {"float_a": float_a, "float_b": float_b},
        **result,
    }


@router.get("/api/graph/query/similar-patterns/{float_id}")
@router.get("/graph/query/similar-patterns/{float_id}")
async def query_similar_patterns(float_id: str, min_shared_cruises: int = 2):
    """Floats sharing overlapping measurement patterns in the same region."""
    results = _queries.floats_with_overlapping_patterns(float_id, min_shared_cruises)
    return {
        "query": "floats_with_overlapping_patterns",
        "params": {"float_id": float_id, "min_shared_cruises": min_shared_cruises},
        "results": results,
        "count": len(results),
    }
