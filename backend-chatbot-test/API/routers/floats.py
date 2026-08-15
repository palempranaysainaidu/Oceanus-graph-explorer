"""
Float location and measurement data router for Oceanus platform
"""
import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

router = APIRouter()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
    except Exception as e:
        logger.warning(f"CockroachDB engine creation skipped: {e}")

class MeasurementPoint(BaseModel):
    date: str
    value: Optional[float]
    latitude: float
    longitude: float

class ArgoFloat(BaseModel):
    id: str
    latitude: float
    longitude: float
    lastReported: str
    temperature: List[MeasurementPoint]
    salinity: List[MeasurementPoint]
    pressure: List[MeasurementPoint]

class FloatLocation(BaseModel):
    id: str
    latitude: float
    longitude: float
    lastReported: str

float_cache: List[dict] = []

def load_float_cache():
    """Fetch latest floats from DB or fallback to local argo_data.csv"""
    global float_cache
    try:
        if engine:
            query = text("""
                WITH latest_measurements AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY platform_number ORDER BY time DESC) AS rn
                    FROM argo_measurements
                    WHERE DATE_TRUNC('month', time) = (
                        SELECT DATE_TRUNC('month', MAX(time))
                        FROM argo_measurements
                    )
                )
                SELECT platform_number AS id, latitude, longitude, time AS "lastReported"
                FROM latest_measurements
                WHERE rn = 1;
            """)
            with engine.connect() as connection:
                df = pd.read_sql(query, connection)
            if not df.empty:
                df['lastReported'] = df['lastReported'].apply(lambda x: x.isoformat() if hasattr(x, 'isoformat') else str(x))
                float_cache = df.to_dict(orient='records')
                logger.info(f"Float cache loaded from CockroachDB with {len(float_cache)} floats")
                return

        # Find argo_data.csv in backend-maps or local directory
        csv_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend-maps", "argo_data.csv"),
            os.path.join(os.path.dirname(__file__), "..", "argo_data.csv"),
            os.path.join(os.getcwd(), "argo_data.csv"),
            os.path.join(os.getcwd(), "..", "backend-maps", "argo_data.csv")
        ]
        csv_path = None
        for path in csv_candidates:
            if os.path.exists(path):
                csv_path = path
                break

        if csv_path:
            logger.info(f"Loading float cache from CSV: {csv_path}")
            df = pd.read_csv(csv_path, skiprows=[1], low_memory=False)
            df = df.rename(columns={"platform_number": "id", "time": "lastReported"})
            df_latest = df.drop_duplicates(subset=["id"], keep="last")
            df_latest = df_latest[["id", "latitude", "longitude", "lastReported"]].dropna()
            df_latest["id"] = df_latest["id"].astype(str)
            df_latest["latitude"] = df_latest["latitude"].astype(float)
            df_latest["longitude"] = df_latest["longitude"].astype(float)
            df_latest["lastReported"] = df_latest["lastReported"].astype(str)
            float_cache = df_latest.to_dict(orient="records")
            logger.info(f"Float cache loaded from CSV with {len(float_cache)} floats")
        else:
            logger.warning("No argo_data.csv found and DB not connected")
            float_cache = []

    except Exception as e:
        logger.error(f"Failed to load float cache: {e}")
        float_cache = []

# Load float cache immediately
load_float_cache()

@router.get("/floats", response_model=List[FloatLocation])
@router.get("/api/floats", response_model=List[FloatLocation])
async def get_float_locations():
    """Return pre-fetched float locations from cache"""
    global float_cache
    return float_cache

@router.get("/refresh-floats")
@router.get("/api/refresh-floats")
async def refresh_float_cache():
    """Manually refresh the float cache"""
    load_float_cache()
    return {"status": "success", "message": f"Float cache refreshed with {len(float_cache)} floats"}

@router.get("/float/{float_id}")
@router.get("/api/float/{float_id}")
async def get_float_details(float_id: str):
    """Get all measurements for a single float"""
    df = pd.DataFrame()
    if engine:
        try:
            query = text("""
                SELECT * FROM argo_measurements
                WHERE platform_number = :id
                ORDER BY time;
            """)
            with engine.connect() as connection:
                df = pd.read_sql(query, connection, params={'id': float_id})
        except Exception as e:
            logger.warning(f"DB query failed in get_float_details: {e}")
            df = pd.DataFrame()

    if df.empty:
        csv_candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend-maps", "argo_data.csv"),
            os.path.join(os.path.dirname(__file__), "..", "argo_data.csv"),
            os.path.join(os.getcwd(), "argo_data.csv"),
            os.path.join(os.getcwd(), "..", "backend-maps", "argo_data.csv")
        ]
        for path in csv_candidates:
            if os.path.exists(path):
                csv_df = pd.read_csv(path, skiprows=[1], low_memory=False)
                csv_df["platform_number"] = csv_df["platform_number"].astype(str)
                df = csv_df[csv_df["platform_number"] == str(float_id)]
                if not df.empty:
                    df = df.rename(columns={"temp": "temp_adjusted", "psal": "psal_adjusted", "pres": "pres_adjusted"})
                break

    if df.empty:
        raise HTTPException(status_code=404, detail=f"Float {float_id} not found")

    latest_data = df.iloc[-1]

    def to_iso(val):
        if hasattr(val, 'isoformat'):
            return val.isoformat()
        return str(val)

    temp_points = [
        MeasurementPoint(date=to_iso(row['time']), value=float(row['temp_adjusted']), latitude=float(row['latitude']), longitude=float(row['longitude']))
        for _, row in df.iterrows() if pd.notna(row.get('temp_adjusted'))
    ]
    salinity_points = [
        MeasurementPoint(date=to_iso(row['time']), value=float(row['psal_adjusted']), latitude=float(row['latitude']), longitude=float(row['longitude']))
        for _, row in df.iterrows() if pd.notna(row.get('psal_adjusted'))
    ]
    pressure_points = [
        MeasurementPoint(date=to_iso(row['time']), value=float(row['pres_adjusted']), latitude=float(row['latitude']), longitude=float(row['longitude']))
        for _, row in df.iterrows() if pd.notna(row.get('pres_adjusted'))
    ]

    return ArgoFloat(
        id=str(latest_data['platform_number']),
        latitude=float(latest_data['latitude']),
        longitude=float(latest_data['longitude']),
        lastReported=to_iso(latest_data['time']),
        temperature=temp_points,
        salinity=salinity_points,
        pressure=pressure_points,
    )
