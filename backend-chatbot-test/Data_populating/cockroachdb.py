import os
import sys
import pandas as pd
import psycopg2.extras
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # CockroachDB connection string
CSV_FILE_PATH = 'argo_data1.csv'  # Path to your CSV file
TABLE_NAME = 'argo_measurements'  # Target table name

if not DATABASE_URL:
    print("Error: DATABASE_URL is not set in .env file.", file=sys.stderr)
    sys.exit(1)

def create_table(engine):
    """Creates the table if it doesn't exist, without a primary key."""
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        platform_number STRING NOT NULL,
        time TIMESTAMPTZ NOT NULL,
        latitude FLOAT,
        longitude FLOAT,
        pres_adjusted FLOAT,
        temp_adjusted FLOAT,
        psal_adjusted FLOAT
    );
    """
    with engine.connect() as conn:
        conn.execute(text(create_table_query))
        conn.commit()
    print(f"Table '{TABLE_NAME}' ensured in database.")

def ingest_csv():
    """Ingests CSV data, with logic to resume if interrupted."""
    engine = create_engine(DATABASE_URL)
    
    # This won't harm your existing table because of "IF NOT EXISTS"
    create_table(engine)

    chunk_size = 5000
    total_lines = sum(1 for _ in open(CSV_FILE_PATH)) - 2  # exclude header + metadata row
    columns = ['platform_number', 'time', 'latitude', 'longitude', 'pres_adjusted', 'temp_adjusted', 'psal_adjusted']

    # --- Logic to resume progress ---
    rows_to_skip = 0
    with engine.connect() as conn:
        # Check if the table already has data
        if engine.dialect.has_table(conn, TABLE_NAME):
            # Get the count of rows already inserted
            result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
            rows_to_skip = result.scalar_one()
    
    if rows_to_skip > 0:
        print(f"Database already contains {rows_to_skip} rows. Resuming...")
    # --- End of resume logic ---

    # Get the raw psycopg2 connection
    conn = engine.raw_connection()
    try:
        # Update tqdm to show the correct resumed progress
        with tqdm(total=total_lines, initial=rows_to_skip, desc="Uploading CSV to CockroachDB") as pbar:
            with conn.cursor() as cur:
                
                # Create an iterator to efficiently skip processed rows
                # We skip the units row (row index 1) AND all previously inserted data rows
                csv_iterator = pd.read_csv(
                    CSV_FILE_PATH, 
                    chunksize=chunk_size, 
                    skiprows=range(1, rows_to_skip + 2), 
                    iterator=True,
                    header=0, # The header is on the first line (index 0)
                    names=columns # Explicitly provide column names
                )

                for chunk in csv_iterator:
                    # OPTIMIZED: Convert date/time format efficiently
                    chunk['time'] = pd.to_datetime(chunk['time'], format='%Y-%m-%dT%H:%M:%SZ')
                    
                    data_to_insert = [tuple(row) for row in chunk[columns].itertuples(index=False, name=None)]
                    insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(columns)}) VALUES ({', '.join(['%s'] * len(columns))})"
                    
                    # Use the highly efficient execute_batch for bulk inserts
                    psycopg2.extras.execute_batch(cur, insert_query, data_to_insert, page_size=len(data_to_insert))
                    conn.commit()
                    pbar.update(len(data_to_insert))
    finally:
        # Ensure the connection is always closed
        conn.close()

    print("CSV ingestion completed.")


if __name__ == "__main__":
    ingest_csv()