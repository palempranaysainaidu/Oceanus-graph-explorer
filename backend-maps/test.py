import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# --- 1. INITIALIZE FASTAPI APP ---
app = FastAPI(title="Argo Float Data API")

origins = [
    "http://localhost:9002", # Ensure this matches your frontend port
    "http://localhost:3000", # Common default port, good to keep
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. DEFINE NEW, CLEANER DATA MODELS ---
class Measurement(BaseModel):
    pressure: float | None
    temperature: float | None
    salinity: float | None

class Profile(BaseModel):
    date: str
    measurements: List[Measurement]

class ArgoFloat(BaseModel):
    id: str
    latitude: float
    longitude: float
    lastReported: str
    profiles: List[Profile]


# --- 3. REVISED DATA PROCESSING FUNCTION ---
def process_argo_data(file_path: str) -> List[ArgoFloat]:
    try:
        df = pd.read_csv(file_path, header=0, low_memory=False, parse_dates=['time'])
    except FileNotFoundError:
        return []

    df['platform_number'] = df['platform_number'].astype(str)
    numeric_cols = ['latitude', 'longitude', 'temp', 'psal', 'pres']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows where essential data is missing
    df.dropna(subset=['time', 'platform_number', 'pres', 'temp', 'psal'], inplace=True)
    
    all_floats_data = []
    # Group by each unique float
    for float_id, float_df in df.groupby('platform_number'):
        
        profiles_list = []
        # Now, group that float's data by each unique profile time
        for profile_time, profile_df in float_df.groupby('time'):
            
            # Sort measurements by pressure (depth) for a clean profile
            profile_df = profile_df.sort_values(by='pres')
            
            measurements_list = [
                Measurement(
                    pressure=row['pres'],
                    temperature=row['temp'],
                    salinity=row['psal']
                )
                for index, row in profile_df.iterrows()
            ]
            
            profiles_list.append(
                Profile(
                    date=profile_time.isoformat(),
                    measurements=measurements_list
                )
            )

        # Sort profiles by date
        profiles_list.sort(key=lambda p: p.date)

        if not profiles_list:
            continue

        # Get latest data from the last profile
        last_profile_df = float_df[float_df['time'] == pd.to_datetime(profiles_list[-1].date)]
        latest_pos = last_profile_df.iloc[-1]

        all_floats_data.append(
            ArgoFloat(
                id=float_id,
                latitude=latest_pos['latitude'],
                longitude=latest_pos['longitude'],
                lastReported=profiles_list[-1].date,
                profiles=profiles_list
            )
        )
        
    return all_floats_data

# --- 4. THE API ENDPOINT (no changes here) ---
@app.get("/api/floats", response_model=List[ArgoFloat])
async def get_all_floats():
    file_path = 'argo_data.csv' # Use your smaller test file if needed
    return process_argo_data(file_path)