# main.py (Updated for Cached Float Data)
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import graph_queries as gq
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd

# --- 1. INITIALIZE APP & LOAD ENV ---
load_dotenv()
app = FastAPI(title="Argo Float Data API", version="2.0.0")

# --- 2. CORS MIDDLEWARE ---
# In production, set ALLOWED_ORIGINS env var to a comma-separated list of allowed origins.
# e.g. ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
_extra_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
origins = list(set([
    "http://localhost:3005",
    "http://localhost:3010",
    "http://localhost:9002",
    "http://localhost:9003",
] + _extra_origins))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- 3. DATABASE CONNECTION & FALLBACK ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        print("FastAPI attempting connection to CockroachDB...")
    except Exception as e:
        print(f"⚠️ CockroachDB engine creation failed: {e}")

# --- 4. PYDANTIC MODELS ---
class MeasurementPoint(BaseModel):
    date: str
    value: float | None
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

# --- 5. GLOBAL CACHE ---
float_cache: list[dict] = []  # Cache for pre-fetched float locations

# --- 6. FUNCTION TO LOAD FLOATS INTO CACHE ---
def load_float_cache():
    """Fetch latest floats from DB or fallback to argo_data.csv"""
    global float_cache
    try:
        print("[INFO] Loading float cache at startup...")

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
                print(f"[SUCCESS] Float cache loaded from CockroachDB with {len(float_cache)} floats")
                return

        # Fallback to local CSV if engine is None or DB returned empty
        csv_path = os.path.join(os.path.dirname(__file__), "argo_data.csv")
        if os.path.exists(csv_path):
            print(f"[INFO] Loading float cache from local CSV: {csv_path}")
            df = pd.read_csv(csv_path, skiprows=[1], low_memory=False)  # skip units line
            df = df.rename(columns={"platform_number": "id", "time": "lastReported"})
            # Group by id and take the latest row per float
            df_latest = df.drop_duplicates(subset=["id"], keep="last")
            df_latest = df_latest[["id", "latitude", "longitude", "lastReported"]].dropna()
            df_latest["id"] = df_latest["id"].astype(str)
            df_latest["latitude"] = df_latest["latitude"].astype(float)
            df_latest["longitude"] = df_latest["longitude"].astype(float)
            df_latest["lastReported"] = df_latest["lastReported"].astype(str)
            float_cache = df_latest.to_dict(orient="records")
            print(f"[SUCCESS] Float cache loaded from CSV with {len(float_cache)} floats")
        else:
            print("[ERROR] No CSV found and DB not connected")
            float_cache = []

    except Exception as e:
        print(f"[ERROR] Failed to load float cache: {str(e)}")
        float_cache = []

# --- 7. STARTUP EVENT ---
@app.on_event("startup")
async def on_startup():
    """Load float cache when the app starts"""
    load_float_cache()

# --- 8. API ENDPOINTS ---
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Argo Float Data API", "version": "2.0.0"}

@app.get("/test-db")
async def test_database():
    """Test database connection with a simple query"""
    try:
        print("[INFO] Testing database connection...")
        query = text("SELECT COUNT(*) as count FROM argo_measurements LIMIT 1")
        with engine.connect() as connection:
            result = connection.execute(query)
            count = result.fetchone()[0]
        print(f"✅ Database test successful. Row count: {count}")
        return {"status": "success", "row_count": count}
    except Exception as e:
        print(f"❌ Database test failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/test-floats")
async def test_floats():
    """Test getting a few float records"""
    try:
        print("[INFO] Testing float data retrieval...")
        query = text("""
            SELECT 
                platform_number AS id,
                latitude,
                longitude,
                time AS "lastReported"
            FROM argo_measurements
            LIMIT 5;
        """)
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        print(f"✅ Retrieved {len(df)} test records")
        df['lastReported'] = df['lastReported'].apply(lambda x: x.isoformat())
        result = df.to_dict(orient='records')
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"❌ Test floats failed: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/floats", response_model=List[FloatLocation])
async def get_float_locations():
    """Return pre-fetched float locations from cache"""
    global float_cache
    print(f"🎯 Returning {len(float_cache)} cached float locations")
    return float_cache

@app.get("/api/refresh-floats")
async def refresh_float_cache():
    """Manually refresh the float cache"""
    load_float_cache()
    return {"status": "success", "message": f"Float cache refreshed with {len(float_cache)} floats"}

@app.get("/api/float/{float_id}")
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
            print(f"⚠️ DB query failed in get_float_details: {e}")
            df = pd.DataFrame()

    if df.empty:
        csv_path = os.path.join(os.path.dirname(__file__), "argo_data.csv")
        if os.path.exists(csv_path):
            csv_df = pd.read_csv(csv_path, skiprows=[1], low_memory=False)
            csv_df["platform_number"] = csv_df["platform_number"].astype(str)
            df = csv_df[csv_df["platform_number"] == str(float_id)]
            if not df.empty:
                df = df.rename(columns={"temp": "temp_adjusted", "psal": "psal_adjusted", "pres": "pres_adjusted"})

    if df.empty:
        return {"error": f"Float {float_id} not found"}

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
        MeasurementPoint(date=to_iso(row['time']), value=float(row['pres_adjusted']), latitude=float(row['latitude']), longitude=row['longitude'])
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

# --- 9. GRAPH API ENDPOINTS ---

@app.get("/api/graph/floats")
async def graph_get_floats():
    """List all floats from the graph database."""
    try:
        return gq.get_all_floats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/floats/{float_id}")
async def graph_get_float(float_id: str):
    """Get single float details and cycle count."""
    try:
        data = gq.get_float_by_id(float_id)
        if not data:
            raise HTTPException(status_code=404, detail="Float not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/floats/{float_id}/cycles")
async def graph_get_cycles(float_id: str):
    """Get all cycles for a specific float."""
    try:
        return gq.get_cycles_for_float(float_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/floats/{float_id}/history")
async def graph_get_history(float_id: str):
    """Get the full chronological measurement history (multi-hop) for a float."""
    try:
        return gq.get_float_history(float_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/floats/{float_id}/stats")
async def graph_get_stats(float_id: str):
    """Get aggregate statistics for a float's measurements."""
    try:
        data = gq.get_measurement_stats(float_id)
        if not data:
            raise HTTPException(status_code=404, detail="Float stats not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/search/cycles")
async def graph_search_cycles(min_temp: float, max_temp: float):
    """Find cycles where measurements fall within a temperature range."""
    try:
        return gq.search_cycles_by_measurement_range(min_temp, max_temp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

