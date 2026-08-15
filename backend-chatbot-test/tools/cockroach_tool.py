"""
CockroachDB tool for querying Argo float measurement data.
This tool provides methods to query and analyze the time series data from Argo floats.
Includes CSV fallback when database connection is not configured or unavailable.
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
        self._engine: Optional[Engine] = None
        self._csv_df: Optional[pd.DataFrame] = None

    @property
    def engine(self) -> Optional[Engine]:
        """Lazy initialization of database engine"""
        if self._engine is None and self.database_url:
            try:
                self._engine = create_engine(self.database_url)
            except Exception as e:
                logger.warning(f"CockroachDB engine connection warning: {e}")
                self._engine = None
        return self._engine

    def _get_csv_df(self) -> Optional[pd.DataFrame]:
        """Load fallback DataFrame from argo_data.csv if available"""
        if self._csv_df is not None:
            return self._csv_df

        csv_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "backend-maps", "argo_data.csv"),
            os.path.join(os.path.dirname(__file__), "..", "argo_data.csv"),
            os.path.join(os.getcwd(), "argo_data.csv"),
            os.path.join(os.getcwd(), "..", "backend-maps", "argo_data.csv")
        ]
        for path in csv_candidates:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, skiprows=[1], low_memory=False)
                    if "temp" in df.columns and "temp_adjusted" not in df.columns:
                        df = df.rename(columns={"temp": "temp_adjusted", "psal": "psal_adjusted", "pres": "pres_adjusted"})
                    df["platform_number"] = df["platform_number"].astype(str)
                    df["time"] = pd.to_datetime(df["time"], errors="coerce")
                    self._csv_df = df
                    logger.info(f"CockroachDBTool using CSV fallback with {len(df)} rows")
                    return self._csv_df
                except Exception as e:
                    logger.warning(f"Error loading CSV fallback {path}: {e}")
        return None

    def get_measurements_by_float(
        self,
        platform_number: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[ArgoMeasurement]:
        """Get measurements for a specific float within a time range"""
        if self.engine:
            try:
                query = """
                    SELECT platform_number, time, latitude, longitude,
                           pres_adjusted, temp_adjusted, psal_adjusted
                    FROM argo_measurements
                    WHERE platform_number = :platform_number
                """
                params = {"platform_number": str(platform_number)}
                
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
                    return [
                        ArgoMeasurement(
                            platform_number=str(row.platform_number),
                            time=row.time,
                            latitude=float(row.latitude),
                            longitude=float(row.longitude),
                            pres_adjusted=float(row.pres_adjusted) if row.pres_adjusted is not None else 0.0,
                            temp_adjusted=float(row.temp_adjusted) if row.temp_adjusted is not None else 0.0,
                            psal_adjusted=float(row.psal_adjusted) if row.psal_adjusted is not None else 0.0
                        )
                        for row in result
                    ]
            except Exception as e:
                logger.warning(f"CockroachDB query failed, attempting CSV fallback: {e}")

        df = self._get_csv_df()
        if df is not None and not df.empty:
            filtered = df[df["platform_number"] == str(platform_number)]
            if start_time:
                filtered = filtered[filtered["time"] >= start_time]
            if end_time:
                filtered = filtered[filtered["time"] <= end_time]
            filtered = filtered.head(limit)
            return [
                ArgoMeasurement(
                    platform_number=str(row["platform_number"]),
                    time=row["time"].to_pydatetime() if hasattr(row["time"], "to_pydatetime") else datetime.now(),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    pres_adjusted=float(row["pres_adjusted"]) if pd.notna(row.get("pres_adjusted")) else 0.0,
                    temp_adjusted=float(row["temp_adjusted"]) if pd.notna(row.get("temp_adjusted")) else 0.0,
                    psal_adjusted=float(row["psal_adjusted"]) if pd.notna(row.get("psal_adjusted")) else 0.0
                )
                for _, row in filtered.iterrows()
            ]

        return []

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
        """Get measurements within a geographic region and time range"""
        if self.engine:
            try:
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
                    return [
                        ArgoMeasurement(
                            platform_number=str(row.platform_number),
                            time=row.time,
                            latitude=float(row.latitude),
                            longitude=float(row.longitude),
                            pres_adjusted=float(row.pres_adjusted) if row.pres_adjusted is not None else 0.0,
                            temp_adjusted=float(row.temp_adjusted) if row.temp_adjusted is not None else 0.0,
                            psal_adjusted=float(row.psal_adjusted) if row.psal_adjusted is not None else 0.0
                        )
                        for row in result
                    ]
            except Exception as e:
                logger.warning(f"CockroachDB region query failed, using CSV fallback: {e}")

        df = self._get_csv_df()
        if df is not None and not df.empty:
            filtered = df[
                (df["latitude"] >= min_lat) & (df["latitude"] <= max_lat) &
                (df["longitude"] >= min_lon) & (df["longitude"] <= max_lon)
            ]
            if start_time:
                filtered = filtered[filtered["time"] >= start_time]
            if end_time:
                filtered = filtered[filtered["time"] <= end_time]
            filtered = filtered.head(limit)
            return [
                ArgoMeasurement(
                    platform_number=str(row["platform_number"]),
                    time=row["time"].to_pydatetime() if hasattr(row["time"], "to_pydatetime") else datetime.now(),
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    pres_adjusted=float(row["pres_adjusted"]) if pd.notna(row.get("pres_adjusted")) else 0.0,
                    temp_adjusted=float(row["temp_adjusted"]) if pd.notna(row.get("temp_adjusted")) else 0.0,
                    psal_adjusted=float(row["psal_adjusted"]) if pd.notna(row.get("psal_adjusted")) else 0.0
                )
                for _, row in filtered.iterrows()
            ]

        return []

    def get_profile_statistics(
        self,
        platform_number: str,
        parameter: str,
        depth_range: Tuple[float, float] = (0, 2000),
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, float]:
        """Calculate statistics for a parameter within a depth range"""
        if parameter not in ['temp_adjusted', 'psal_adjusted']:
            raise ValueError("Parameter must be 'temp_adjusted' or 'psal_adjusted'")

        measurements = self.get_measurements_by_float(
            platform_number=platform_number,
            start_time=time_range[0] if time_range else None,
            end_time=time_range[1] if time_range else None,
            limit=5000
        )
        values = []
        for m in measurements:
            if depth_range[0] <= m.pres_adjusted <= depth_range[1]:
                val = m.temp_adjusted if parameter == 'temp_adjusted' else m.psal_adjusted
                if val is not None and not np.isnan(val):
                    values.append(val)

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
        """Get temporal aggregation of measurements"""
        if parameter not in ['temp_adjusted', 'psal_adjusted']:
            raise ValueError("Parameter must be 'temp_adjusted' or 'psal_adjusted'")

        measurements = self.get_measurements_by_float(
            platform_number=platform_number,
            start_time=time_range[0] if time_range else None,
            end_time=time_range[1] if time_range else None,
            limit=5000
        )
        data = []
        for m in measurements:
            if depth_range is None or (depth_range[0] <= m.pres_adjusted <= depth_range[1]):
                val = m.temp_adjusted if parameter == 'temp_adjusted' else m.psal_adjusted
                data.append({"time": m.time, parameter: val})

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df.set_index('time', inplace=True)
        agg_df = df.resample(freq).agg(['mean', 'std', 'count'])
        agg_df.columns = [f"{parameter}_{col}" for col in ['mean', 'std', 'count']]
        return agg_df.reset_index()

    def execute_custom_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a custom SQL query against CockroachDB with CSV fallback for basic float listing"""
        if self.engine:
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text(query), params or {})
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in result]
            except Exception as e:
                logger.warning(f"Error executing custom CockroachDB query: {e}")

        # Fallback for listing floats
        df = self._get_csv_df()
        if df is not None and not df.empty:
            if "platform_number" in df.columns:
                unique_floats = df["platform_number"].unique().tolist()
                return [{"platform_number": str(f)} for f in unique_floats[:50]]

        return []

    def close(self):
        """Close the database connection"""
        if self._engine:
            self._engine.dispose()
            self._engine = None