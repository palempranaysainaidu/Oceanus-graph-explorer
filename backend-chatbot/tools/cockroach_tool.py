"""
CockroachDB tool for querying Argo float measurement data.
This tool provides methods to query and analyze the time series data from Argo floats.
"""

import os
from typing import List, Dict, Optional, Tuple, Union, Any
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ArgoMeasurement:
    """Data class for Argo float measurements"""
    platform_number: str
    time: datetime
    latitude: float
    longitude: float
    pres_adjusted: float
    temp_adjusted: float
    psal_adjusted: float

class CockroachDBTool:
    """Tool for interacting with CockroachDB Argo measurements database"""
    
    def __init__(self):
        """Initialize the CockroachDB connection"""
        load_dotenv()
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        self._engine: Optional[Engine] = None

    @property
    def engine(self) -> Engine:
        """Lazy initialization of database engine"""
        if self._engine is None:
            self._engine = create_engine(self.database_url)
        return self._engine

    def get_measurements_by_float(
        self,
        platform_number: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[ArgoMeasurement]:
        """
        Get measurements for a specific float within a time range
        
        Args:
            platform_number: The float's platform number
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of records to return
            
        Returns:
            List of ArgoMeasurement objects
        """
        query = """
            SELECT platform_number, time, latitude, longitude,
                   pres_adjusted, temp_adjusted, psal_adjusted
            FROM argo_measurements
            WHERE platform_number = :platform_number
        """
        params = {"platform_number": platform_number}
        
        if start_time:
            query += " AND time >= :start_time"
            params["start_time"] = start_time
            
        if end_time:
            query += " AND time <= :end_time"
            params["end_time"] = end_time
            
        query += " ORDER BY time DESC LIMIT :limit"
        params["limit"] = limit

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            measurements = [
                ArgoMeasurement(
                    platform_number=row.platform_number,
                    time=row.time,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    pres_adjusted=row.pres_adjusted,
                    temp_adjusted=row.temp_adjusted,
                    psal_adjusted=row.psal_adjusted
                )
                for row in result
            ]
            
        return measurements

    def get_measurements_by_region(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[ArgoMeasurement]:
        """
        Get measurements within a geographic region and time range
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of records to return
            
        Returns:
            List of ArgoMeasurement objects
        """
        query = """
            SELECT platform_number, time, latitude, longitude,
                   pres_adjusted, temp_adjusted, psal_adjusted
            FROM argo_measurements
            WHERE latitude BETWEEN :min_lat AND :max_lat
            AND longitude BETWEEN :min_lon AND :max_lon
        """
        params = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon
        }
        
        if start_time:
            query += " AND time >= :start_time"
            params["start_time"] = start_time
            
        if end_time:
            query += " AND time <= :end_time"
            params["end_time"] = end_time
            
        query += " ORDER BY time DESC LIMIT :limit"
        params["limit"] = limit

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            measurements = [
                ArgoMeasurement(
                    platform_number=row.platform_number,
                    time=row.time,
                    latitude=row.latitude,
                    longitude=row.longitude,
                    pres_adjusted=row.pres_adjusted,
                    temp_adjusted=row.temp_adjusted,
                    psal_adjusted=row.psal_adjusted
                )
                for row in result
            ]
            
        return measurements

    def get_profile_statistics(
        self,
        platform_number: str,
        parameter: str,
        depth_range: Tuple[float, float] = (0, 2000),
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, float]:
        """
        Calculate statistics for a parameter within a depth range
        
        Args:
            platform_number: The float's platform number
            parameter: One of 'temp_adjusted', 'psal_adjusted'
            depth_range: Tuple of (min_depth, max_depth) in meters
            time_range: Optional tuple of (start_time, end_time)
            
        Returns:
            Dictionary with statistics (mean, std, min, max, etc.)
        """
        if parameter not in ['temp_adjusted', 'psal_adjusted']:
            raise ValueError("Parameter must be 'temp_adjusted' or 'psal_adjusted'")

        query = f"""
            SELECT {parameter}
            FROM argo_measurements
            WHERE platform_number = :platform_number
            AND pres_adjusted BETWEEN :min_depth AND :max_depth
        """
        params = {
            "platform_number": platform_number,
            "min_depth": depth_range[0],
            "max_depth": depth_range[1]
        }

        if time_range:
            query += " AND time BETWEEN :start_time AND :end_time"
            params.update({
                "start_time": time_range[0],
                "end_time": time_range[1]
            })

        with self.engine.connect() as conn:
            result = conn.execute(text(query), params)
            values = [row[0] for row in result if row[0] is not None]

        if not values:
            return {}

        return {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "count": len(values)
        }

    def get_temporal_aggregation(
        self,
        platform_number: str,
        parameter: str,
        freq: str = 'M',
        depth_range: Optional[Tuple[float, float]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> pd.DataFrame:
        """
        Get temporal aggregation of measurements
        
        Args:
            platform_number: The float's platform number
            parameter: One of 'temp_adjusted', 'psal_adjusted'
            freq: Pandas frequency string ('D' for daily, 'M' for monthly, etc.)
            depth_range: Optional tuple of (min_depth, max_depth)
            time_range: Optional tuple of (start_time, end_time)
            
        Returns:
            DataFrame with temporal aggregation
        """
        if parameter not in ['temp_adjusted', 'psal_adjusted']:
            raise ValueError("Parameter must be 'temp_adjusted' or 'psal_adjusted'")

        query = f"""
            SELECT time, {parameter}
            FROM argo_measurements
            WHERE platform_number = :platform_number
        """
        params = {"platform_number": platform_number}

        if depth_range:
            query += " AND pres_adjusted BETWEEN :min_depth AND :max_depth"
            params.update({
                "min_depth": depth_range[0],
                "max_depth": depth_range[1]
            })

        if time_range:
            query += " AND time BETWEEN :start_time AND :end_time"
            params.update({
                "start_time": time_range[0],
                "end_time": time_range[1]
            })

        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn, params=params)

        if df.empty:
            return pd.DataFrame()

        # Resample and aggregate
        df.set_index('time', inplace=True)
        agg_df = df.resample(freq).agg(['mean', 'std', 'count'])
        agg_df.columns = [f"{parameter}_{col}" for col in ['mean', 'std', 'count']]
        
        return agg_df.reset_index()

    def execute_custom_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query against the CockroachDB database
        
        Args:
            query: SQL query string
            params: Optional parameters for the query
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(query), params)
                else:
                    result = conn.execute(text(query))
                
                # Convert result to list of dictionaries
                columns = result.keys()
                rows = []
                for row in result:
                    row_dict = {}
                    for i, column in enumerate(columns):
                        row_dict[column] = row[i]
                    rows.append(row_dict)
                
                return rows
                
        except Exception as e:
            logger.error(f"Error executing custom query: {e}")
            return []

    def close(self):
        """Close the database connection"""
        if self._engine:
            self._engine.dispose()
            self._engine = None