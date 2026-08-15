"""
Neo4j / CognoDB tool for querying Argo float metadata and graph relationships.
Uses the official Neo4j Python driver against CognoDB (bolt+s, openCypher).
Includes safe fallback when the graph database is unreachable.
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from .cognodb_client import CognodbClient
from .graph_queries import GraphQueries

logger = logging.getLogger(__name__)


@dataclass
class FloatMetadata:
    """Data class for float metadata"""
    platform_number: str
    subregion: str
    parameters: List[str]


@dataclass
class RegionMetadata:
    """Data class for region metadata"""
    name: str
    parent_region: Optional[str]
    float_count: int
    subregions: List[str]


class Neo4jTool:
    """Tool for interacting with the Argo knowledge graph on CognoDB."""

    def __init__(self):
        self._client = CognodbClient()
        self._queries = GraphQueries(self._client)

    @property
    def client(self) -> CognodbClient:
        return self._client

    @property
    def queries(self) -> GraphQueries:
        return self._queries

    @property
    def driver(self):
        """Legacy accessor — returns underlying driver if connected."""
        return self._client.driver

    def health_check(self) -> Dict[str, Any]:
        return self._client.health_check()

    def get_float_metadata(self, platform_number: str) -> Optional[FloatMetadata]:
        graph = self._queries.get_float_graph(str(platform_number))
        if graph:
            params = [p["parameter"] for p in graph.get("parameters", [])]
            return FloatMetadata(
                platform_number=graph["platform_number"],
                subregion=graph.get("region") or "Unknown",
                parameters=params or ["temperature", "salinity", "pressure"],
            )
        if not self._client.driver:
            return FloatMetadata(
                platform_number=str(platform_number),
                subregion="Arabian Sea",
                parameters=["temperature", "salinity", "pressure"],
            )
        return None

    def get_region_metadata(self, region_name: str) -> Optional[RegionMetadata]:
        regions = self._queries.list_regions()
        match = next((r for r in regions if r.get("name") == region_name), None)
        if match:
            return RegionMetadata(
                name=match["name"],
                parent_region="Indian Ocean",
                float_count=match.get("float_count") or 0,
                subregions=[s for s in (match.get("subregions") or []) if s],
            )
        if not self._client.driver:
            return RegionMetadata(
                name=region_name,
                parent_region="Indian Ocean",
                float_count=15,
                subregions=["Northern", "Central", "Southern"],
            )
        return None

    def get_floats_in_region(
        self,
        region_name: str,
        include_subregions: bool = False,
    ) -> List[str]:
        if include_subregions:
            rows = self._client.run_query(
                """
                MATCH (r:Region {name: $region_name})
                OPTIONAL MATCH (sub:Region)-[:PART_OF*]->(r)
                WITH r, collect(sub) AS subs
                UNWIND subs + [r] AS region
                MATCH (f:Float)-[:LOCATED_IN]->(region)
                RETURN DISTINCT f.platform_number AS platform_number
                """,
                {"region_name": region_name},
            )
        else:
            rows = self._queries.floats_in_region(region_name)
        ids = [r["platform_number"] for r in rows]
        if ids:
            return ids
        if not self._client.driver:
            return ["7902073", "1901442", "2901550", "3901234"]
        return []

    def get_region_hierarchy(self) -> Dict[str, Dict]:
        rows = self._client.run_query(
            """
            MATCH (r:Region)
            OPTIONAL MATCH (r)-[:PART_OF]->(parent:Region)
            OPTIONAL MATCH (f:Float)-[:LOCATED_IN]->(r)
            RETURN r.name AS region, parent.name AS parent, count(DISTINCT f) AS float_count
            """
        )
        if not rows and not self._client.driver:
            return {
                "Indian Ocean": {
                    "name": "Indian Ocean",
                    "float_count": 50,
                    "children": {
                        "Arabian Sea": {"name": "Arabian Sea", "float_count": 25, "children": {}},
                        "Bay of Bengal": {"name": "Bay of Bengal", "float_count": 25, "children": {}},
                    },
                }
            }
        hierarchy: Dict[str, Dict] = {}
        for record in rows:
            region = record["region"]
            hierarchy[region] = {
                "name": region,
                "float_count": record["float_count"],
                "children": {},
            }
        for record in rows:
            parent = record.get("parent")
            region = record["region"]
            if parent and parent in hierarchy:
                hierarchy[parent]["children"][region] = hierarchy[region]
        roots = {
            name: data
            for name, data in hierarchy.items()
            if not any(name in h["children"] for h in hierarchy.values())
        }
        return dict(roots)

    def get_parameter_coverage(self, region_name: Optional[str] = None) -> Dict[str, int]:
        if region_name:
            rows = self._client.run_query(
                """
                MATCH (r:Region {name: $region_name})
                MATCH (f:Float)-[:LOCATED_IN]->(r)
                MATCH (m:Measurement)-[:RECORDED_BY]->(f)
                MATCH (m)-[:MEASURED]->(p:Parameter)
                RETURN p.name AS parameter, count(DISTINCT f) AS float_count
                """,
                {"region_name": region_name},
            )
        else:
            rows = self._client.run_query(
                """
                MATCH (m:Measurement)-[:MEASURED]->(p:Parameter)
                MATCH (m)-[:RECORDED_BY]->(f:Float)
                RETURN p.name AS parameter, count(DISTINCT f) AS float_count
                """
            )
        result = {r["parameter"]: r["float_count"] for r in rows}
        if result:
            return result
        if not self._client.driver:
            return {"temperature": 45, "salinity": 45, "pressure": 45}
        return {}

    def floats_in_region_with_parameter_during_cruise(
        self, region_name: str, parameter_name: str, cruise_id: str,
    ) -> List[Dict[str, Any]]:
        return self._queries.floats_in_region_with_parameter_during_cruise(
            region_name, parameter_name, cruise_id,
        )

    def shortest_path_between_floats(self, float_a: str, float_b: str) -> Dict[str, Any]:
        return self._queries.shortest_path_between_floats(float_a, float_b)

    def floats_with_overlapping_patterns(self, float_id: str) -> List[Dict[str, Any]]:
        return self._queries.floats_with_overlapping_patterns(float_id)

    def execute_custom_query(
        self, query: str, params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return self._client.run_query(query, params)

    def close(self):
        self._client.close()
