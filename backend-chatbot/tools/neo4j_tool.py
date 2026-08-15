"""
Neo4j tool for querying Argo float metadata and graph relationships.
This tool provides methods to query the hierarchical structure of regions and float metadata.
"""

import os
from typing import List, Dict, Optional, Union, Any
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
from dataclasses import dataclass
from collections import defaultdict
import logging

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
    """Tool for interacting with Neo4j Argo metadata database"""
    
    def __init__(self):
        """Initialize the Neo4j connection"""
        load_dotenv()
        self.uri = "neo4j+s://dddeab17.databases.neo4j.io"
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASS")
        
        if not all([self.user, self.password]):
            raise ValueError("NEO4J_USER and NEO4J_PASS environment variables must be set")
        
        self._driver: Optional[Driver] = None

    @property
    def driver(self) -> Driver:
        """Lazy initialization of Neo4j driver"""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self._driver

    def get_float_metadata(self, platform_number: str) -> Optional[FloatMetadata]:
        """
        Get metadata for a specific float
        
        Args:
            platform_number: The float's platform number
            
        Returns:
            FloatMetadata object if found, None otherwise
        """
        query = """
        MATCH (f:Float {platform_number: $platform_number})
        MATCH (f)-[:LOCATED_IN]->(r:Region)
        MATCH (f)-[:MEASURES]->(p:Parameter)
        RETURN f.platform_number as platform_number,
               r.name as subregion,
               collect(p.name) as parameters
        """
        
        with self.driver.session() as session:
            result = session.run(query, platform_number=platform_number)
            record = result.single()
            
            if not record:
                return None
                
            return FloatMetadata(
                platform_number=record["platform_number"],
                subregion=record["subregion"],
                parameters=record["parameters"]
            )

    def get_region_metadata(self, region_name: str) -> Optional[RegionMetadata]:
        """
        Get metadata for a specific region
        
        Args:
            region_name: Name of the region
            
        Returns:
            RegionMetadata object if found, None otherwise
        """
        query = """
        MATCH (r:Region {name: $region_name})
        OPTIONAL MATCH (r)-[:PART_OF]->(parent:Region)
        OPTIONAL MATCH (sub:Region)-[:PART_OF]->(r)
        OPTIONAL MATCH (f:Float)-[:LOCATED_IN]->(r)
        RETURN r.name as name,
               parent.name as parent_region,
               count(DISTINCT f) as float_count,
               collect(DISTINCT sub.name) as subregions
        """
        
        with self.driver.session() as session:
            result = session.run(query, region_name=region_name)
            record = result.single()
            
            if not record:
                return None
                
            return RegionMetadata(
                name=record["name"],
                parent_region=record["parent_region"],
                float_count=record["float_count"],
                subregions=record["subregions"]
            )

    def get_floats_in_region(
        self,
        region_name: str,
        include_subregions: bool = False
    ) -> List[str]:
        """
        Get all float platform numbers in a region
        
        Args:
            region_name: Name of the region
            include_subregions: Whether to include floats in subregions
            
        Returns:
            List of float platform numbers
        """
        if include_subregions:
            query = """
            MATCH (r:Region {name: $region_name})
            OPTIONAL MATCH (sub:Region)-[:PART_OF*]->(r)
            MATCH (f:Float)-[:LOCATED_IN]->(region)
            WHERE region IN [r] + collect(sub)
            RETURN DISTINCT f.platform_number as platform_number
            """
        else:
            query = """
            MATCH (r:Region {name: $region_name})
            MATCH (f:Float)-[:LOCATED_IN]->(r)
            RETURN f.platform_number as platform_number
            """
        
        with self.driver.session() as session:
            result = session.run(query, region_name=region_name)
            return [record["platform_number"] for record in result]

    def get_region_hierarchy(self) -> Dict[str, Dict]:
        """
        Get complete region hierarchy with float counts
        
        Returns:
            Nested dictionary representing the region hierarchy
        """
        query = """
        MATCH (r:Region)
        OPTIONAL MATCH (r)-[:PART_OF]->(parent:Region)
        OPTIONAL MATCH (f:Float)-[:LOCATED_IN]->(r)
        RETURN r.name as region,
               parent.name as parent,
               count(DISTINCT f) as float_count
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            
            # Build hierarchy
            hierarchy = defaultdict(lambda: {
                "name": "",
                "float_count": 0,
                "children": {}
            })
            
            # First pass: create all nodes
            for record in result:
                region = record["region"]
                hierarchy[region]["name"] = region
                hierarchy[region]["float_count"] = record["float_count"]
                
            # Second pass: build parent-child relationships
            for record in result:
                region = record["region"]
                parent = record["parent"]
                
                if parent:
                    hierarchy[parent]["children"][region] = hierarchy[region]
                    
            # Find root nodes (those without parents)
            root_nodes = {
                name: data 
                for name, data in hierarchy.items()
                if not any(
                    name in h["children"] 
                    for h in hierarchy.values()
                )
            }
            
            return dict(root_nodes)

    def get_parameter_coverage(self, region_name: Optional[str] = None) -> Dict[str, int]:
        """
        Get parameter measurement coverage statistics
        
        Args:
            region_name: Optional region name to filter by
            
        Returns:
            Dictionary mapping parameter names to float counts
        """
        query = """
        MATCH (p:Parameter)<-[:MEASURES]-(f:Float)
        """
        
        if region_name:
            query += """
            MATCH (f)-[:LOCATED_IN]->(r:Region {name: $region_name})
            """
        
        query += """
        RETURN p.name as parameter,
               count(DISTINCT f) as float_count
        """
        
        params = {"region_name": region_name} if region_name else {}
        
        with self.driver.session() as session:
            result = session.run(query, **params)
            return {
                record["parameter"]: record["float_count"]
                for record in result
            }

    def execute_custom_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query against the Neo4j database
        
        Args:
            query: Cypher query string
            params: Optional parameters for the query
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.driver.session() as session:
                if params:
                    result = session.run(query, **params)
                else:
                    result = session.run(query)
                
                # Convert result to list of dictionaries
                rows = []
                for record in result:
                    row_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Handle Neo4j node/relationship objects
                        if hasattr(value, '_properties'):
                            row_dict[key] = dict(value._properties)
                        elif hasattr(value, 'items'):
                            row_dict[key] = dict(value)
                        else:
                            row_dict[key] = value
                    rows.append(row_dict)
                
                return rows
                
        except Exception as e:
            logger.error(f"Error executing custom Neo4j query: {e}")
            return []

    def close(self):
        """Close the Neo4j driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None