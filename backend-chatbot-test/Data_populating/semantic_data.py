import os
import pandas as pd
from sqlalchemy import create_engine, text
from tqdm import tqdm
from dotenv import load_dotenv
import torch
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import sys
from datetime import datetime
import time

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# CUDA setup
device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cpu":
    print("Warning: CUDA not available, using CPU")

# Initialize clients
engine = create_engine(DATABASE_URL)
pc = Pinecone(api_key=PINECONE_API_KEY)

# Pinecone index setup
INDEX_NAME = "argo-floats"
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=384,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
    )
index = pc.Index(INDEX_NAME)

# Load model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2").to(device)

def create_profile_summary(group_data):
    """Create a semantic summary for a group of measurements"""
    return (
        f"Argo float {group_data['platform_number'].iloc[0]} profile in "
        f"region lat:{group_data['latitude'].mean():.2f}°, "
        f"lon:{group_data['longitude'].mean():.2f}°. "
        f"Temperature range: {group_data['temp_adjusted'].min():.1f}-"
        f"{group_data['temp_adjusted'].max():.1f}°C, "
        f"Salinity range: {group_data['psal_adjusted'].min():.1f}-"
        f"{group_data['psal_adjusted'].max():.1f}, "
        f"Depth range: {group_data['pres_adjusted'].min():.1f}-"
        f"{group_data['pres_adjusted'].max():.1f}m. "
        f"Time period: {group_data['time'].min():%Y-%m-%d} to {group_data['time'].max():%Y-%m-%d}"
    )

def get_total_groups(conn):
    """Get total number of semantic groups"""
    query = text("""
        WITH float_bounds AS (
            SELECT 
                platform_number,
                DATE_TRUNC('month', time) as month,
                FLOOR(latitude/5)*5 as lat_grid,
                FLOOR(longitude/5)*5 as lon_grid,
                COUNT(*) as measurement_count
            FROM argo_measurements
            WHERE temp_adjusted IS NOT NULL 
              AND psal_adjusted IS NOT NULL
              AND pres_adjusted IS NOT NULL
            GROUP BY 
                platform_number,
                DATE_TRUNC('month', time),
                FLOOR(latitude/5)*5,
                FLOOR(longitude/5)*5
            HAVING COUNT(*) >= 10
        )
        SELECT COUNT(*) as total_groups,
               SUM(measurement_count) as total_measurements
        FROM float_bounds
    """)
    return conn.execute(query).fetchone()

def process_float_data(conn, batch_size=10000):
    """Process float data without limits with progress tracking and error handling"""
    query = text("""
        WITH float_bounds AS (
            SELECT 
                platform_number,
                DATE_TRUNC('month', time) as month,
                FLOOR(latitude/5)*5 as lat_grid,
                FLOOR(longitude/5)*5 as lon_grid,
                AVG(latitude) as avg_lat,
                AVG(longitude) as avg_lon,
                MIN(temp_adjusted) as min_temp,
                MAX(temp_adjusted) as max_temp,
                MIN(psal_adjusted) as min_psal,
                MAX(psal_adjusted) as max_psal,
                MIN(pres_adjusted) as min_pres,
                MAX(pres_adjusted) as max_pres,
                COUNT(*) as measurement_count
            FROM argo_measurements
            WHERE temp_adjusted IS NOT NULL 
              AND psal_adjusted IS NOT NULL
              AND pres_adjusted IS NOT NULL
            GROUP BY 
                platform_number,
                DATE_TRUNC('month', time),
                FLOOR(latitude/5)*5,
                FLOOR(longitude/5)*5
            HAVING COUNT(*) >= 10
        )
        SELECT * FROM float_bounds
        ORDER BY measurement_count DESC
    """)

    # Get total count of groups to process for progress tracking
    total_count = conn.execute(text("SELECT COUNT(*) FROM (" + query.text + ") AS t")).scalar_one()
    print(f"\nTotal groups to process: {total_count:,}")
    
    offset = 0
    total_processed = 0
    
    with tqdm(total=total_count, desc="Processing vectors") as pbar:
        while True:
            batch_query = query.text + f" OFFSET {offset} LIMIT {batch_size}"
            try:
                df = pd.read_sql_query(batch_query, conn)
            except Exception as e:
                print(f"\nError fetching batch at offset {offset}: {e}")
                time.sleep(5)
                continue

            if df.empty:
                break
            
            vectors = []
            for _, group in df.iterrows():
                try:
                    vector_id = f"{group['platform_number']}_{group['lat_grid']}_{group['lon_grid']}_{group['month']:%Y%m}"
                    summary = (
                        f"Monthly profile for float {group['platform_number']} in "
                        f"region {group['lat_grid']}°-{group['lat_grid']+5}°N, "
                        f"{group['lon_grid']}°-{group['lon_grid']+5}°E during {group['month']:%Y-%m}. "
                        f"Temperature range: {group['min_temp']:.1f}-{group['max_temp']:.1f}°C, "
                        f"Salinity range: {group['min_psal']:.1f}-{group['max_psal']:.1f}, "
                        f"Depth range: {group['min_pres']:.1f}-{group['min_pres']:.1f}m. "
                        f"Contains {group['measurement_count']} measurements."
                    )
                    embedding = model.encode(summary, convert_to_tensor=True)
                    
                    vectors.append({
                        "id": vector_id,
                        "values": embedding.cpu().numpy().tolist(),
                        "metadata": {
                            "platform_number": int(group['platform_number']),
                            "month": group['month'].strftime('%Y-%m'),
                            "lat_grid": float(group['lat_grid']),
                            "lon_grid": float(group['lon_grid']),
                            "avg_lat": float(group['avg_lat']),
                            "avg_lon": float(group['avg_lon']),
                            "measurement_count": int(group['measurement_count']),
                            "summary": summary
                        }
                    })
                    
                    if len(vectors) >= 100:
                        try:
                            index.upsert(vectors=vectors)
                            vectors = []
                            time.sleep(1)  # Rate limiting
                        except Exception as upsert_err:
                            print(f"\nError upserting batch at offset {offset}: {upsert_err}")
                            continue
                except Exception as proc_err:
                    print(f"\nError processing a group: {proc_err}")
                    continue

            # Upsert any remaining vectors in the current batch
            if vectors:
                try:
                    index.upsert(vectors=vectors)
                except Exception as e:
                    print(f"\nError upserting final batch at offset {offset}: {e}")
            
            total_processed += len(df)
            offset += batch_size
            pbar.update(len(df))
            if total_processed % 1000 == 0:
                print(f"\nStatus: {total_processed:,}/{total_count:,} groups processed")
        
        print(f"\nCompleted processing {total_processed:,} groups")

def main():
    start_time = time.time()
    print(f"Starting semantic data population at {datetime.now()}")
    print(f"Using device: {device}")
    
    with engine.connect() as conn:
        total_groups, total_measurements = get_total_groups(conn)
        print(f"\nData Analysis Summary:")
        print(f"Total semantic groups available: {total_groups:,}")
        print(f"Total measurements represented: {total_measurements:,}")
        print(f"Original measurements: 13.5M")
        print(f"Aggregation ratio: {total_measurements/13500000:.2%}")
        print(f"\nEstimated Storage:")
        print(f"Vector dimension: 384")
        print(f"Estimated storage per vector: ~500 bytes metadata + ~1.5KB vector")
        estimated_storage_gb = (total_groups * 2000) / (1024*1024*1024)
        print(f"Total estimated storage: {estimated_storage_gb:.2f} GB")
        
        proceed = input("\nWould you like to proceed with data population? (y/n): ")
        if proceed.lower() == 'y':
            print("\nStarting data population...")
            print("Press Ctrl+C to pause/stop processing")
            try:
                process_float_data(conn)
            except KeyboardInterrupt:
                print("\nProcessing paused by user")
                sys.exit(0)
            
    elapsed_time = time.time() - start_time
    print(f"\nExecution Summary:")
    print(f"Total execution time: {elapsed_time/60:.2f} minutes")
    print(f"✅ Completed semantic data population at {datetime.now()}")

if __name__ == "__main__":
    main()