"""
Core agent logic for the Argo chatbot.
"""

from typing import Dict, List, Any, Optional, Tuple
import groq
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import json
import logging
from .config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    QUERY_TEMPLATES,
    RESPONSE_TEMPLATES,
    MAX_RETRIES,
    TIMEOUT,
    SYSTEM_PROMPT
)
from tools import ArgoToolFactory
from tools.cockroach_tool import ArgoMeasurement
from tools.neo4j_tool import FloatMetadata, RegionMetadata
from tools.pinecone_tool import SemanticSearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryIntent:
    """Represents the parsed intent of a user query"""
    primary_type: str  # 'measurement', 'metadata', or 'semantic'
    temporal_filter: Optional[Tuple[datetime, datetime]] = None
    spatial_filter: Optional[Dict[str, float]] = None
    parameter_filter: Optional[List[str]] = None
    float_filter: Optional[str] = None
    limit: int = 1000

@dataclass
class QueryResult:
    """Represents the structured result of a database query"""
    data: Any
    summary: str
    details: Dict[str, Any]
    error: Optional[str] = None

class ArgoAgent:
    """
    Production-grade agent for handling Argo data queries using
    CockroachDB, Neo4j, and Pinecone databases.
    """
    
    def __init__(self):
        """Initialize the agent with necessary tools and clients"""
        self.tools = ArgoToolFactory()
        self.groq_client = groq.Client(api_key=GROQ_API_KEY)
        self.query_cache: Dict[str, Tuple[datetime, QueryResult]] = {}

    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for semantic search queries.
        
        Args:
            query: The user's query string
            
        Returns:
            List of floats representing the query embedding
        """
        try:
            # For now, use a simple hash-based approach to generate consistent embeddings
            # This is a placeholder - in production you'd use a proper embedding model
            import hashlib
            
            # Create a deterministic hash of the query
            query_hash = hashlib.md5(query.lower().encode()).hexdigest()
            
            # Convert hash to seed for reproducible random vector
            seed = int(query_hash[:8], 16)
            np.random.seed(seed)
            
            # Generate a normalized random vector
            embedding = np.random.normal(0, 0.1, 384)
            
            # Normalize the vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * 384

    def _parse_query_intent(self, query: str) -> QueryIntent:
        """
        Parse the user's query to determine intent and extract filters.
        
        Args:
            query: The user's natural language query
            
        Returns:
            QueryIntent object with parsed information
        """
        try:
            # Process for float ID first
            float_id = None
            import re
            float_matches = re.findall(r'float (\d+)', query.lower())
            if float_matches:
                float_id = float_matches[0]
                logger.info(f"Found float ID: {float_id}")

            # Process spatial information
            spatial_filter = None
            # Look for coordinate patterns like "15-20°N, 60-65°E" or region names
            coord_pattern = r'(\d+)-(\d+)°([NS]).*?(\d+)-(\d+)°([EW])'
            coords = re.search(coord_pattern, query)
            
            if coords:
                lat_min, lat_max = sorted([float(coords.group(1)), float(coords.group(2))])
                lon_min, lon_max = sorted([float(coords.group(4)), float(coords.group(5))])
                
                # Adjust for hemisphere
                if coords.group(3) == 'S':
                    lat_min, lat_max = -lat_max, -lat_min
                if coords.group(6) == 'W':
                    lon_min, lon_max = -lon_max, -lon_min
                    
                spatial_filter = {
                    "min_lat": lat_min,
                    "max_lat": lat_max,
                    "min_lon": lon_min,
                    "max_lon": lon_max
                }
                logger.info(f"Found spatial bounds: {spatial_filter}")
            else:
                # Check for region names
                regions = {
                    "arabian sea": {"min_lat": 10, "max_lat": 25, "min_lon": 55, "max_lon": 75},
                    "bay of bengal": {"min_lat": 10, "max_lat": 25, "min_lon": 80, "max_lon": 95},
                    "equatorial indian ocean": {"min_lat": -5, "max_lat": 5, "min_lon": 40, "max_lon": 80},
                    "southern indian ocean": {"min_lat": -40, "max_lat": -20, "min_lon": 20, "max_lon": 80}
                }
                
                for region, bounds in regions.items():
                    if region in query.lower():
                        spatial_filter = bounds
                        logger.info(f"Found region: {region} with bounds {bounds}")
                        break

            # Use LLM for additional context and parameter extraction
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": query
                }
            ]
            
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model=GROQ_MODEL,
                temperature=0.1,
                max_tokens=1000,
                top_p=0.95,
                stream=False
            )
            
            response_content = chat_completion.choices[0].message.content
            logger.debug(f"LLM Response: {response_content}")
            
            try:
                intent_data = json.loads(response_content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response: {response_content}")
                intent_data = self._extract_structured_data(response_content)
            
            # Merge explicitly found values with LLM results
            if float_id:
                intent_data["parameters"] = intent_data.get("parameters", {})
                intent_data["parameters"]["float_id"] = float_id
                
            if spatial_filter:
                intent_data["parameters"] = intent_data.get("parameters", {})
                intent_data["parameters"]["spatial_filter"] = spatial_filter
            
            # Set default temporal filter (last 30 days)
            temporal_filter = (datetime.now() - timedelta(days=30), datetime.now())
            
            # Try to extract temporal filter from LLM response
            if "parameters" in intent_data and "temporal_filter" in intent_data["parameters"]:
                try:
                    temp_filter = intent_data["parameters"]["temporal_filter"]
                    if isinstance(temp_filter, dict) and "start" in temp_filter and "end" in temp_filter:
                        if isinstance(temp_filter["start"], str) and isinstance(temp_filter["end"], str):
                            start = datetime.fromisoformat(temp_filter["start"])
                            end = datetime.fromisoformat(temp_filter["end"])
                            temporal_filter = (start, end)
                except (KeyError, ValueError, AttributeError) as e:
                    logger.warning(f"Using default time range due to parsing error: {e}")
            
            # Construct QueryIntent
            params = intent_data.get("parameters", {})
            
            # Ensure spatial filter is properly formatted
            final_spatial_filter = None
            if spatial_filter:  # Use the one we extracted from regex
                final_spatial_filter = spatial_filter
            elif params.get("spatial_filter"):  # Use the one from LLM if it has all required keys
                llm_spatial = params["spatial_filter"]
                if isinstance(llm_spatial, dict) and all(k in llm_spatial for k in ["min_lat", "max_lat", "min_lon", "max_lon"]):
                    try:
                        # Check if all values are not None and can be converted to float
                        if all(llm_spatial[k] is not None for k in ["min_lat", "max_lat", "min_lon", "max_lon"]):
                            final_spatial_filter = {
                                "min_lat": float(llm_spatial["min_lat"]),
                                "max_lat": float(llm_spatial["max_lat"]),
                                "min_lon": float(llm_spatial["min_lon"]),
                                "max_lon": float(llm_spatial["max_lon"])
                            }
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse spatial filter from LLM: {e}")
            
            return QueryIntent(
                primary_type=intent_data.get("type", "measurement"),
                temporal_filter=temporal_filter,
                spatial_filter=final_spatial_filter,
                parameter_filter=params.get("parameter_filter", ["temp", "psal", "pres"]),  # Default to all parameters
                float_filter=params.get("float_id", float_id),
                limit=params.get("limit", 1000)
            )
            
        except Exception as e:
            logger.error(f"Error parsing query intent: {str(e)}")
            # Default to measurement type with no filters
            return QueryIntent(primary_type="measurement")

    def _execute_measurement_query(self, intent: QueryIntent) -> QueryResult:
        """
        Execute a measurement query using CockroachDB tool.
        
        Args:
            intent: Parsed query intent
            
        Returns:
            QueryResult with measurements and analysis
        """
        try:
            # Use float ID if available
            if intent.float_filter and isinstance(intent.float_filter, str) and intent.float_filter.isdigit():
                logger.info(f"Querying measurements for float {intent.float_filter}")
                measurements = self.tools.cockroach.get_measurements_by_float(
                    platform_number=intent.float_filter,
                    start_time=intent.temporal_filter[0] if intent.temporal_filter else None,
                    end_time=intent.temporal_filter[1] if intent.temporal_filter else None,
                    limit=intent.limit
                )
            # Fall back to spatial filter if available and valid
            elif intent.spatial_filter and isinstance(intent.spatial_filter, dict):
                required_keys = {"min_lat", "max_lat", "min_lon", "max_lon"}
                if all(k in intent.spatial_filter for k in required_keys):
                    logger.info(f"Querying measurements for region: {intent.spatial_filter}")
                    measurements = self.tools.cockroach.get_measurements_by_region(
                        min_lat=float(intent.spatial_filter["min_lat"]),
                        max_lat=float(intent.spatial_filter["max_lat"]),
                        min_lon=float(intent.spatial_filter["min_lon"]),
                        max_lon=float(intent.spatial_filter["max_lon"]),
                        limit=intent.limit
                    )
                else:
                    missing_keys = required_keys - set(intent.spatial_filter.keys())
                    raise ValueError(f"Spatial filter missing required keys: {missing_keys}")
            else:
                raise ValueError("Either valid float ID or complete spatial bounds required")

            # Calculate statistics
            if measurements:
                stats = {
                    "temp_stats": self._calculate_stats([m.temp_adjusted for m in measurements]),
                    "psal_stats": self._calculate_stats([m.psal_adjusted for m in measurements]),
                    "pres_stats": self._calculate_stats([m.pres_adjusted for m in measurements])
                }
                
                summary = f"Found {len(measurements)} measurements"
                details = {
                    "statistics": stats,
                    "time_range": f"{measurements[0].time} to {measurements[-1].time}",
                    "spatial_coverage": self._get_spatial_coverage(measurements)
                }
            else:
                summary = "No measurements found"
                details = {}

            return QueryResult(
                data=measurements,
                summary=summary,
                details=details
            )

        except Exception as e:
            logger.error(f"Error executing measurement query: {str(e)}")
            return QueryResult(
                data=[],
                summary="Error executing query",
                details={},
                error=str(e)
            )

    def _execute_metadata_query(self, intent: QueryIntent) -> QueryResult:
        """
        Execute a metadata query using Neo4j tool.
        
        Args:
            intent: Parsed query intent
            
        Returns:
            QueryResult with metadata and analysis
        """
        try:
            results = []
            if intent.float_filter:
                # Query float metadata
                metadata = self.tools.neo4j.get_float_metadata(intent.float_filter)
                if metadata:
                    results.append(metadata)
                    
            elif intent.spatial_filter:
                # Query region metadata
                region_name = self._get_region_name(intent.spatial_filter)
                metadata = self.tools.neo4j.get_region_metadata(region_name)
                if metadata:
                    results.append(metadata)
                    
            else:
                # Get overall statistics
                coverage = self.tools.neo4j.get_parameter_coverage()
                hierarchy = self.tools.neo4j.get_region_hierarchy()
                results = {"coverage": coverage, "hierarchy": hierarchy}

            if results:
                summary = "Found metadata information"
                details = self._analyze_metadata(results)
            else:
                summary = "No metadata found"
                details = {}

            return QueryResult(
                data=results,
                summary=summary,
                details=details
            )

        except Exception as e:
            logger.error(f"Error executing metadata query: {str(e)}")
            return QueryResult(
                data=[],
                summary="Error executing query",
                details={},
                error=str(e)
            )

    def _execute_semantic_query(self, query: str, intent: QueryIntent) -> QueryResult:
        """
        Execute a semantic search query using Pinecone tool.
        
        Args:
            query: Original query string
            intent: Parsed query intent
            
        Returns:
            QueryResult with semantic search results and analysis
        """
        try:
            # Generate query embedding
            query_vector = self._get_query_embedding(query)
            
            # Execute search
            results = self.tools.pinecone.semantic_search(
                query_vector=query_vector,
                top_k=min(intent.limit, 100),  # Reasonable limit for semantic search
                region_filter=self._get_region_name(intent.spatial_filter) if intent.spatial_filter else None,
                time_filter=intent.temporal_filter,
                parameter_filter=intent.parameter_filter[0] if intent.parameter_filter else None
            )

            if results:
                summary = f"Found {len(results)} semantically similar measurements"
                details = self._analyze_semantic_results(results)
            else:
                summary = "No semantic matches found"
                details = {}

            return QueryResult(
                data=results,
                summary=summary,
                details=details
            )

        except Exception as e:
            logger.error(f"Error executing semantic query: {str(e)}")
            return QueryResult(
                data=[],
                summary="Error executing query",
                details={},
                error=str(e)
            )

    def _calculate_stats(self, values: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a list of values"""
        if not values:
            return {}
        return {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values))
        }

    def _get_spatial_coverage(self, measurements: List[ArgoMeasurement]) -> Dict[str, Any]:
        """Calculate spatial coverage statistics"""
        lats = [m.latitude for m in measurements]
        lons = [m.longitude for m in measurements]
        return {
            "lat_range": [min(lats), max(lats)],
            "lon_range": [min(lons), max(lons)],
            "center": [np.mean(lats), np.mean(lons)]
        }

    def _get_region_name(self, spatial_bounds: Optional[Dict[str, float]] = None) -> str:
        """Map coordinates to region name
        
        Args:
            spatial_bounds: Dictionary with min_lat, max_lat, min_lon, max_lon keys
            
        Returns:
            Name of the region or 'Other'
        """
        if not spatial_bounds:
            return "Other"
            
        try:
            min_lat = float(spatial_bounds.get('min_lat', 0))
            max_lat = float(spatial_bounds.get('max_lat', 0))
            min_lon = float(spatial_bounds.get('min_lon', 0))
            max_lon = float(spatial_bounds.get('max_lon', 0))
            
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2
            
            if 10 <= center_lat <= 25 and 55 <= center_lon <= 75:
                return "Arabian Sea"
            elif 10 <= center_lat <= 25 and 80 <= center_lon <= 95:
                return "Bay of Bengal"
            elif -5 <= center_lat <= 5 and 40 <= center_lon <= 80:
                return "Equatorial Indian Ocean"
            elif -40 <= center_lat <= -20 and 20 <= center_lon <= 80:
                return "Southern Indian Ocean"
            
        except (TypeError, ValueError) as e:
            logger.warning(f"Error determining region name: {e}")
            
        return "Other"

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text when JSON parsing fails
        
        Args:
            text: The response text from LLM
            
        Returns:
            Dictionary with extracted data
        """
        # Default structure
        data = {
            "type": "measurement",  # Default to measurement type
            "parameters": {}
        }
        
        # Try to extract float ID
        if "float" in text.lower() and any(c.isdigit() for c in text):
            import re
            float_ids = re.findall(r"float (\d+)", text.lower())
            if float_ids:
                data["parameters"]["float_id"] = float_ids[0]
        
        # Try to extract region
        for region in ["Arabian Sea", "Bay of Bengal", "Equatorial Indian Ocean", 
                      "Southern Indian Ocean"]:
            if region.lower() in text.lower():
                data["parameters"]["region"] = region
                break
        
        # Try to extract parameters
        for param in ["temperature", "salinity", "pressure"]:
            if param.lower() in text.lower():
                if "parameters" not in data["parameters"]:
                    data["parameters"]["parameters"] = []
                data["parameters"]["parameters"].append(param)
        
        return data

    def _analyze_metadata(self, metadata: Any) -> Dict[str, Any]:
        """Analyze metadata results"""
        if isinstance(metadata, list):
            if all(isinstance(m, FloatMetadata) for m in metadata):
                return self._analyze_float_metadata(metadata)
            elif all(isinstance(m, RegionMetadata) for m in metadata):
                return self._analyze_region_metadata(metadata)
        elif isinstance(metadata, dict):
            return {
                "parameter_coverage": metadata.get("coverage", {}),
                "region_structure": self._analyze_hierarchy(metadata.get("hierarchy", {}))
            }
        return {}

    def _analyze_float_metadata(self, metadata_list: List[FloatMetadata]) -> Dict[str, Any]:
        """Analyze float metadata"""
        return {
            "float_count": len(metadata_list),
            "parameter_distribution": self._count_parameters(metadata_list),
            "region_distribution": self._count_regions(metadata_list)
        }

    def _analyze_region_metadata(self, metadata_list: List[RegionMetadata]) -> Dict[str, Any]:
        """Analyze region metadata"""
        return {
            "total_floats": sum(m.float_count for m in metadata_list),
            "region_hierarchy": {
                m.name: {
                    "parent": m.parent_region,
                    "float_count": m.float_count,
                    "subregions": m.subregions
                }
                for m in metadata_list
            }
        }

    def _analyze_hierarchy(self, hierarchy: Dict[str, Any], level: int = 0) -> Dict[str, Any]:
        """Recursively analyze region hierarchy"""
        if level > 5:  # Prevent infinite recursion
            return {}
            
        result = {}
        for region, data in hierarchy.items():
            result[region] = {
                "float_count": data.get("float_count", 0),
                "children": self._analyze_hierarchy(data.get("children", {}), level + 1)
            }
        return result

    def _analyze_semantic_results(self, results: List[SemanticSearchResult]) -> Dict[str, Any]:
        """Analyze semantic search results"""
        return {
            "score_distribution": self._calculate_stats([r.score for r in results]),
            "temporal_distribution": self._analyze_temporal_distribution(
                [r.time for r in results]
            ),
            "spatial_distribution": self._analyze_spatial_distribution(results)
        }

    def _analyze_temporal_distribution(
        self,
        timestamps: List[datetime],
        bins: int = 10
    ) -> Dict[str, Any]:
        """Analyze temporal distribution of results"""
        if not timestamps:
            return {}
            
        start = min(timestamps)
        end = max(timestamps)
        duration = end - start
        
        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_days": duration.days,
            "density": len(timestamps) / (duration.days or 1)
        }

    def _analyze_spatial_distribution(
        self,
        results: List[SemanticSearchResult]
    ) -> Dict[str, Any]:
        """Analyze spatial distribution of results"""
        if not results or not hasattr(results[0], "metadata"):
            return {}
            
        lats = []
        lons = []
        regions = {}
        
        for result in results:
            if "latitude" in result.metadata and "longitude" in result.metadata:
                lats.append(result.metadata["latitude"])
                lons.append(result.metadata["longitude"])
                
            if "region" in result.metadata:
                region = result.metadata["region"]
                regions[region] = regions.get(region, 0) + 1

        return {
            "spatial_bounds": {
                "lat": [min(lats), max(lats)] if lats else None,
                "lon": [min(lons), max(lons)] if lons else None
            },
            "region_distribution": regions
        }

    def _count_parameters(self, metadata_list: List[FloatMetadata]) -> Dict[str, int]:
        """Count parameter occurrences"""
        counts = {}
        for metadata in metadata_list:
            for param in metadata.parameters:
                counts[param] = counts.get(param, 0) + 1
        return counts

    def _count_regions(self, metadata_list: List[FloatMetadata]) -> Dict[str, int]:
        """Count region occurrences"""
        counts = {}
        for metadata in metadata_list:
            counts[metadata.subregion] = counts.get(metadata.subregion, 0) + 1
        return counts

    def _format_response(
        self,
        query_type: str,
        result: QueryResult
    ) -> str:
        """
        Format query results into a natural language response
        
        Args:
            query_type: Type of query executed
            result: Query execution results
            
        Returns:
            Formatted response string
        """
        if result.error:
            return f"Error executing query: {result.error}"

        template = RESPONSE_TEMPLATES.get(query_type, "{summary}\n\n{details}")
        
        # Extract common fields
        response_data = {
            "summary": result.summary,
            "details": result.details
        }
        
        # Add type-specific fields
        if query_type == "measurement":
            response_data.update({
                "time_range": result.details.get("time_range", "N/A"),
                "region": self._get_region_name(result.details.get("spatial_coverage", {})),
                "count": len(result.data) if isinstance(result.data, list) else 0
            })
        elif query_type == "metadata":
            if isinstance(result.data, list) and result.data:
                first_item = result.data[0]
                if isinstance(first_item, FloatMetadata):
                    response_data.update({
                        "parameters": ", ".join(first_item.parameters),
                        "region": first_item.subregion,
                        "float_count": 1
                    })
                elif isinstance(first_item, RegionMetadata):
                    response_data.update({
                        "region": first_item.name,
                        "parameters": "N/A",
                        "float_count": first_item.float_count
                    })
        elif query_type == "semantic":
            if isinstance(result.data, list):
                response_data["matches"] = "\n".join(
                    f"- Score: {r.score:.3f}, Float: {r.platform_number}"
                    for r in result.data[:5]
                )
                response_data["analysis"] = json.dumps(
                    result.details.get("score_distribution", {}),
                    indent=2
                )

        return template.format(**response_data)

    def query(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Process a natural language query and return formatted results
        
        Args:
            query: The user's natural language query
            conversation_history: Optional conversation history for context
            
        Returns:
            Formatted response string
        """
        # Check cache
        cache_key = query.strip().lower()
        if cache_key in self.query_cache:
            timestamp, cached_result = self.query_cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=300):  # 5 minute TTL
                return self._format_response(cached_result.primary_type, cached_result)

        try:
            # Parse query intent
            intent = self._parse_query_intent(query)
            
            # Execute appropriate query
            if intent.primary_type == "measurement":
                result = self._execute_measurement_query(intent)
            elif intent.primary_type == "metadata":
                result = self._execute_metadata_query(intent)
            elif intent.primary_type == "semantic":
                result = self._execute_semantic_query(query, intent)
            else:
                raise ValueError(f"Unknown query type: {intent.primary_type}")

            # Cache result
            self.query_cache[cache_key] = (datetime.now(), result)
            
            # Format and return response
            return self._format_response(intent.primary_type, result)

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return f"Error processing query: {str(e)}"

    def close(self):
        """Clean up resources"""
        self.tools.close_all()
        self.query_cache.clear()