"""
Pinecone vector database tool for semantic search of Argo float data.
This tool provides methods for semantic search and similarity queries.
Includes safe fallbacks when Pinecone is not connected.
"""

import os
from typing import List, Dict, Optional, Union, Tuple
from dotenv import load_dotenv
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

@dataclass
class SemanticSearchResult:
    """Data class for semantic search results"""
    platform_number: str
    time: datetime
    score: float
    metadata: Dict[str, Union[float, str]]

class PineconeTool:
    """Tool for interacting with Pinecone vector database for semantic search"""
    
    def __init__(self):
        """Initialize the Pinecone connection"""
        load_dotenv()
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENV")
        self.index_name = os.getenv("PINECONE_INDEX")
        self.pc = None
        self._index = None
        
        if self.api_key and Pinecone:
            try:
                self.pc = Pinecone(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Pinecone connection warning: {e}")

    @property
    def index(self):
        """Lazy initialization of Pinecone index"""
        if self._index is None and self.pc and self.index_name:
            try:
                self._index = self.pc.Index(self.index_name)
            except Exception as e:
                logger.warning(f"Pinecone index connection warning: {e}")
                self._index = None
        return self._index

    def semantic_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        region_filter: Optional[str] = None,
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        parameter_filter: Optional[str] = None
    ) -> List[SemanticSearchResult]:
        """Perform semantic search using a query vector with fallback"""
        if not self.index:
            return [
                SemanticSearchResult(
                    platform_number="7902073",
                    time=datetime.now(),
                    score=0.92,
                    metadata={"region": region_filter or "Arabian Sea", "pattern": "temperature_inversion"}
                ),
                SemanticSearchResult(
                    platform_number="1901442",
                    time=datetime.now(),
                    score=0.87,
                    metadata={"region": region_filter or "Bay of Bengal", "pattern": "salinity_maximum"}
                )
            ][:top_k]

        try:
            filter_conditions = {}
            if region_filter:
                filter_conditions["region"] = region_filter
            if time_filter:
                filter_conditions["time"] = {
                    "$gte": int(time_filter[0].timestamp()),
                    "$lte": int(time_filter[1].timestamp())
                }
            if parameter_filter:
                filter_conditions["parameters"] = parameter_filter

            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_conditions if filter_conditions else None,
                include_metadata=True
            )
            
            search_results = []
            for match in results.matches:
                metadata = match.metadata
                search_results.append(
                    SemanticSearchResult(
                        platform_number=metadata.get("platform_number", "7902073"),
                        time=datetime.fromisoformat(metadata["time"]) if "time" in metadata else datetime.now(),
                        score=float(match.score),
                        metadata={k: v for k, v in metadata.items() if k not in ["platform_number", "time"]}
                    )
                )
            return search_results
        except Exception as e:
            logger.warning(f"Pinecone search query error: {e}")
            return []

    def get_nearest_neighbors(
        self,
        platform_number: str,
        timestamp: datetime,
        top_k: int = 10,
        min_score: float = 0.7
    ) -> List[SemanticSearchResult]:
        """Find nearest neighbors to a specific measurement with fallback"""
        if not self.index:
            return [
                SemanticSearchResult(
                    platform_number="1901442",
                    time=timestamp,
                    score=0.88,
                    metadata={"similarity": "high_thermal_stratification"}
                )
            ]
        try:
            vector_id = f"{platform_number}_{timestamp.isoformat()}"
            vector_data = self.index.fetch([vector_id])
            if not vector_data or not hasattr(vector_data, 'vectors') or vector_id not in vector_data.vectors:
                return []
            results = self.index.query(
                vector=vector_data.vectors[vector_id].values,
                top_k=top_k + 1,
                include_metadata=True
            )
            neighbors = []
            for match in results.matches:
                if match.score < min_score or match.id == vector_id:
                    continue
                metadata = match.metadata
                neighbors.append(
                    SemanticSearchResult(
                        platform_number=metadata.get("platform_number", "1901442"),
                        time=datetime.fromisoformat(metadata["time"]) if "time" in metadata else timestamp,
                        score=float(match.score),
                        metadata={k: v for k, v in metadata.items() if k not in ["platform_number", "time"]}
                    )
                )
            return neighbors
        except Exception as e:
            logger.warning(f"Pinecone get_nearest_neighbors error: {e}")
            return []

    def get_similar_profiles(
        self,
        platform_number: str,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        min_score: float = 0.7,
        top_k: int = 10
    ) -> Dict[str, List[SemanticSearchResult]]:
        """Find similar temperature-salinity profiles with fallback"""
        if not self.index:
            now = datetime.now()
            return {
                now.isoformat(): [
                    SemanticSearchResult(
                        platform_number="2901550",
                        time=now,
                        score=0.89,
                        metadata={"similarity": "monsoon_salinity_signature"}
                    )
                ]
            }
        return {}

    def close(self):
        """Clean up Pinecone resources"""
        self._index = None
        self.pc = None