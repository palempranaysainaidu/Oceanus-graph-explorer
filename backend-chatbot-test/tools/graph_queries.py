"""
Parameterized openCypher queries for the Argo float knowledge graph.
Used by agents, API routes, and the graph explorer UI.
"""

from typing import Any, Dict, List, Optional

from .cognodb_client import CognodbClient


class GraphQueries:
    """Collection of graph retrieval queries backed by CognoDB."""

    def __init__(self, client: Optional[CognodbClient] = None):
        self.client = client or CognodbClient()

    def get_stats(self) -> Dict[str, Any]:
        rows = self.client.run_query(
            """
            MATCH (n)
            WITH labels(n) AS lbl
            UNWIND lbl AS label
            RETURN label, count(*) AS count
            ORDER BY count DESC
            """
        )
        rel_rows = self.client.run_query(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC"
        )
        return {
            "node_counts": {r["label"]: r["count"] for r in rows},
            "relationship_counts": {r["type"]: r["count"] for r in rel_rows},
            "connected": self.client.health_check().get("connected", False),
        }

    def floats_in_region_with_parameter_during_cruise(
        self,
        region_name: str,
        parameter_name: str,
        cruise_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Multi-hop (3+ hops): Region <- LOCATED_IN <- Float <- RECORDED_BY <- Measurement
        -[:PART_OF_CRUISE]-> Cruise, -[:MEASURED]-> Parameter
        """
        return self.client.run_query(
            """
            MATCH (r:Region {name: $region_name})
            MATCH (f:Float)-[:LOCATED_IN]->(r)
            MATCH (m:Measurement)-[:RECORDED_BY]->(f)
            MATCH (m)-[:PART_OF_CRUISE]->(c:Cruise {cruise_id: $cruise_id})
            MATCH (m)-[:MEASURED]->(p:Parameter {name: $parameter_name})
            RETURN DISTINCT
                f.platform_number AS platform_number,
                c.cruise_id AS cruise_id,
                p.name AS parameter,
                m.time AS time,
                m.latitude AS latitude,
                m.longitude AS longitude
            ORDER BY f.platform_number
            """,
            {
                "region_name": region_name,
                "parameter_name": parameter_name,
                "cruise_id": cruise_id,
            },
        )

    def shortest_path_between_floats(
        self,
        float_a: str,
        float_b: str,
        max_hops: int = 6,
    ) -> Dict[str, Any]:
        """
        Shortest path via NEAR_FLOAT proximity network — awkward in SQL without
        recursive CTEs and precomputed distance tables.
        """
        rows = self.client.run_query(
            f"""
            MATCH (a:Float {{platform_number: $float_a}}),
                  (b:Float {{platform_number: $float_b}})
            MATCH path = shortestPath((a)-[:NEAR_FLOAT*..{max_hops}]-(b))
            RETURN [n IN nodes(path) | n.platform_number] AS float_path,
                   length(path) AS hops,
                   [r IN relationships(path) | r.distance_km] AS distances_km
            """,
            {"float_a": float_a, "float_b": float_b},
        )
        if not rows:
            return {"float_path": [], "hops": None, "distances_km": [], "found": False}
        row = rows[0]
        return {
            "float_path": row.get("float_path") or [],
            "hops": row.get("hops"),
            "distances_km": row.get("distances_km") or [],
            "found": True,
        }

    def floats_with_overlapping_patterns(
        self,
        float_id: str,
        min_shared_cruises: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Find floats sharing overlapping measurement patterns: same region,
        overlapping cruises with similar temperature/salinity profiles.
        """
        return self.client.run_query(
            """
            MATCH (f:Float {platform_number: $float_id})-[:LOCATED_IN]->(r:Region)
            MATCH (other:Float)-[:LOCATED_IN]->(r)
            WHERE other.platform_number <> $float_id
            MATCH (m1:Measurement)-[:RECORDED_BY]->(f)
            MATCH (m1)-[:PART_OF_CRUISE]->(c:Cruise)
            MATCH (m2:Measurement)-[:RECORDED_BY]->(other)
            MATCH (m2)-[:PART_OF_CRUISE]->(c)
            WITH other, count(DISTINCT c) AS shared_cruises,
                 avg(abs(m1.temp_mean - m2.temp_mean)) AS avg_temp_diff,
                 avg(abs(m1.sal_mean - m2.sal_mean)) AS avg_sal_diff
            WHERE shared_cruises >= $min_shared_cruises
            RETURN other.platform_number AS platform_number,
                   shared_cruises,
                   avg_temp_diff,
                   avg_sal_diff,
                   r.name AS region
            ORDER BY shared_cruises DESC, avg_temp_diff ASC
            LIMIT 15
            """,
            {"float_id": float_id, "min_shared_cruises": min_shared_cruises},
        )

    def list_regions(self) -> List[Dict[str, Any]]:
        return self.client.run_query(
            """
            MATCH (r:Region)
            OPTIONAL MATCH (f:Float)-[:LOCATED_IN]->(r)
            OPTIONAL MATCH (sub:Region)-[:PART_OF]->(r)
            RETURN r.name AS name,
                   count(DISTINCT f) AS float_count,
                   collect(DISTINCT sub.name) AS subregions
            ORDER BY float_count DESC
            """
        )

    def get_float_graph(self, platform_number: str) -> Dict[str, Any]:
        meta_rows = self.client.run_query(
            """
            MATCH (f:Float {platform_number: $platform_number})
            OPTIONAL MATCH (f)-[:LOCATED_IN]->(r:Region)
            OPTIONAL MATCH (f)-[:NEAR_FLOAT]-(neighbor:Float)
            RETURN f.platform_number AS platform_number,
                   f.latitude AS latitude,
                   f.longitude AS longitude,
                   r.name AS region,
                   collect(DISTINCT neighbor.platform_number) AS neighbors
            """,
            {"platform_number": platform_number},
        )
        cruise_rows = self.client.run_query(
            """
            MATCH (f:Float {platform_number: $platform_number})-[:PART_OF_CRUISE]->(c:Cruise)
            RETURN c.cruise_id AS cruise_id,
                   c.cycle_number AS cycle_number,
                   c.time AS time
            ORDER BY c.time DESC
            LIMIT 20
            """,
            {"platform_number": platform_number},
        )
        param_rows = self.client.run_query(
            """
            MATCH (m:Measurement)-[:RECORDED_BY]->(f:Float {platform_number: $platform_number})
            MATCH (m)-[:MEASURED]->(p:Parameter)
            RETURN p.name AS parameter, count(m) AS measurement_count
            ORDER BY measurement_count DESC
            """,
            {"platform_number": platform_number},
        )
        if not meta_rows:
            return {}
        meta = meta_rows[0]
        return {
            "platform_number": meta.get("platform_number"),
            "latitude": meta.get("latitude"),
            "longitude": meta.get("longitude"),
            "region": meta.get("region"),
            "neighbors": meta.get("neighbors") or [],
            "cruises": cruise_rows,
            "parameters": param_rows,
        }

    def floats_in_region(self, region_name: str) -> List[Dict[str, Any]]:
        return self.client.run_query(
            """
            MATCH (r:Region {name: $region_name})
            MATCH (f:Float)-[:LOCATED_IN]->(r)
            RETURN f.platform_number AS platform_number,
                   f.latitude AS latitude,
                   f.longitude AS longitude
            ORDER BY f.platform_number
            """,
            {"region_name": region_name},
        )
