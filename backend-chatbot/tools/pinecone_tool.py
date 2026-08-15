"""
Pinecone vector database tool for semantic search of Argo float data.
This tool provides methods for semantic search and similarity queries.
"""

import os
from typing import List, Dict, Optional, Union, Tuple
from pinecone import Pinecone
from dotenv import load_dotenv
import numpy as np
from dataclasses import dataclass
from datetime import datetime

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
        
        if not all([self.api_key, self.environment, self.index_name]):
            raise ValueError(
                "PINECONE_API_KEY, PINECONE_ENV, and PINECONE_INDEX "
                "environment variables must be set"
            )
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)
        self._index = None

    @property
    def index(self):
        """Lazy initialization of Pinecone index"""
        if self._index is None:
            if self.index_name not in self.pc.list_indexes().names():
                raise ValueError(f"Index '{self.index_name}' does not exist")
            self._index = self.pc.Index(self.index_name)
        return self._index

    def semantic_search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        region_filter: Optional[str] = None,
        time_filter: Optional[Tuple[datetime, datetime]] = None,
        parameter_filter: Optional[str] = None
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search using a query vector
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            region_filter: Optional region name to filter by
            time_filter: Optional tuple of (start_time, end_time)
            parameter_filter: Optional parameter name to filter by
            
        Returns:
            List of SemanticSearchResult objects
        """
        # Build filter conditions
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
        
        # Perform query
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter_conditions if filter_conditions else None,
            include_metadata=True
        )
        
        # Process results
        search_results = []
        for match in results.matches:
            metadata = match.metadata
            search_results.append(
                SemanticSearchResult(
                    platform_number=metadata["platform_number"],
                    time=datetime.fromisoformat(metadata["time"]),
                    score=float(match.score),
                    metadata={
                        k: v for k, v in metadata.items()
                        if k not in ["platform_number", "time"]
                    }
                )
            )
            
        return search_results

    def get_nearest_neighbors(
        self,
        platform_number: str,
        timestamp: datetime,
        top_k: int = 10,
        min_score: float = 0.7
    ) -> List[SemanticSearchResult]:
        """
        Find nearest neighbors to a specific measurement
        
        Args:
            platform_number: The float's platform number
            timestamp: The timestamp of the measurement
            top_k: Number of neighbors to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of SemanticSearchResult objects
        """
        # Build query filter
        query_filter = {
            "platform_number": platform_number,
            "time": timestamp.isoformat()
        }
        
        # Get the vector for the specified measurement
        vector_id = f"{platform_number}_{timestamp.isoformat()}"
        vector_data = self.index.fetch([vector_id])
        
        if not vector_data.vectors:
            raise ValueError(
                f"No vector found for platform {platform_number} "
                f"at time {timestamp}"
            )
        
        # Query nearest neighbors
        results = self.index.query(
            vector=vector_data.vectors[vector_id].values,
            top_k=top_k + 1,  # Add 1 to account for self-match
            include_metadata=True
        )
        
        # Process results, excluding self-match
        neighbors = []
        for match in results.matches:
            if match.score < min_score:
                continue
                
            # Skip self-match
            if match.id == vector_id:
                continue
                
            metadata = match.metadata
            neighbors.append(
                SemanticSearchResult(
                    platform_number=metadata["platform_number"],
                    time=datetime.fromisoformat(metadata["time"]),
                    score=float(match.score),
                    metadata={
                        k: v for k, v in metadata.items()
                        if k not in ["platform_number", "time"]
                    }
                )
            )
            
        return neighbors

    def get_similar_profiles(
        self,
        platform_number: str,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        min_score: float = 0.7,
        top_k: int = 10
    ) -> Dict[str, List[SemanticSearchResult]]:
        """
        Find similar temperature-salinity profiles
        
        Args:
            platform_number: The float's platform number
            time_range: Optional tuple of (start_time, end_time)
            min_score: Minimum similarity score threshold
            top_k: Number of similar profiles to return per profile
            
        Returns:
            Dictionary mapping timestamps to lists of similar profiles
        """
        # Build filter for target float
        filter_conditions = {"platform_number": platform_number}
        if time_range:
            filter_conditions["time"] = {
                "$gte": int(time_range[0].timestamp()),
                "$lte": int(time_range[1].timestamp())
            }
            
        # Get vectors for the target float
        results = self.index.query(
            vector=[0.0] * self.index.describe_index_stats().dimension,
            filter=filter_conditions,
            include_vectors=True,
            include_metadata=True
        )
        
        similar_profiles = {}
        
        # For each profile of the target float
        for match in results.matches:
            metadata = match.metadata
            timestamp = datetime.fromisoformat(metadata["time"])
            
            # Query similar profiles
            similar = self.index.query(
                vector=match.values,
                top_k=top_k + 1,  # Add 1 to account for self-match
                include_metadata=True
            )
            
            # Process similar profiles
            profiles = []
            for similar_match in similar.matches:
                if similar_match.score < min_score:
                    continue
                    
                # Skip self-match
                if similar_match.id == match.id:
                    continue
                    
                similar_metadata = similar_match.metadata
                profiles.append(
                    SemanticSearchResult(
                        platform_number=similar_metadata["platform_number"],
                        time=datetime.fromisoformat(similar_metadata["time"]),
                        score=float(similar_match.score),
                        metadata={
                            k: v for k, v in similar_metadata.items()
                            if k not in ["platform_number", "time"]
                        }
                    )
                )
            
            if profiles:
                similar_profiles[timestamp] = profiles
                
        return similar_profiles

    def close(self):
        """Clean up Pinecone resources"""
        self._index = None
        del self.pc  # Clean up Pinecone client