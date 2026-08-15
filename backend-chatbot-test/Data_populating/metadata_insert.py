import os
from sqlalchemy import create_engine, text
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ------------------------
# CockroachDB
# ------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# ------------------------
# Neo4j AuraDB
# ------------------------
NEO4J_URI = "neo4j+s://dddeab17.databases.neo4j.io"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

BATCH_SIZE = 10000

# ------------------------
# Neo4j insert function with hierarchical regions
# ------------------------
def insert_metadata(tx, rows):
    query = """
    UNWIND $rows AS row
    // Float node
    MERGE (f:Float {platform_number: row.platform_number})
    
    // Subregion node
    MERGE (subregion:Region {name: row.subregion})
    
    // Parent region (Indian Ocean)
    MERGE (parent:Region {name: 'Indian Ocean'})
    
    // Hierarchy link
    MERGE (subregion)-[:PART_OF]->(parent)
    
    // Float located in subregion
    MERGE (f)-[:LOCATED_IN]->(subregion)
    
    // Parameter nodes (shared)
    MERGE (p_temp:Parameter {name: 'temperature'})
    MERGE (p_sal:Parameter {name: 'salinity'})
    MERGE (p_pres:Parameter {name: 'pressure'})
    
    // Float measures all parameters
    MERGE (f)-[:MEASURES]->(p_temp)
    MERGE (f)-[:MEASURES]->(p_sal)
    MERGE (f)-[:MEASURES]->(p_pres)
    """
    tx.run(query, rows=rows)

# ------------------------
# Map lat/lon to hierarchical subregions
# ------------------------
def map_subregion(lat, lon):
    if lat is None or lon is None:
        return "Unknown"
    if 10 <= lat <= 25 and 55 <= lon <= 75:
        return "Arabian Sea"
    elif 10 <= lat <= 25 and 80 <= lon <= 95:
        return "Bay of Bengal"
    elif -5 <= lat <= 5 and 40 <= lon <= 80:
        return "Equatorial Indian Ocean"
    elif -40 <= lat <= -20 and 20 <= lon <= 80:
        return "Southern Indian Ocean"
    else:
        return "Other"

# ------------------------
# ETL process
# ------------------------
with engine.connect() as conn, driver.session() as session:
    # Count total distinct floats for progress bar
    result = conn.execute(text("SELECT COUNT(DISTINCT platform_number) FROM argo_measurements"))
    total_floats = result.scalar_one()

    offset = 0
    pbar = tqdm(total=total_floats, desc="Uploading metadata to Neo4j")

    while True:
        # Fetch a batch of distinct floats
        result = conn.execute(
            text(f"""
            SELECT DISTINCT platform_number, latitude, longitude
            FROM argo_measurements
            ORDER BY platform_number
            LIMIT {BATCH_SIZE} OFFSET {offset}
            """)
        )
        rows = result.fetchall()
        if not rows:
            break

        batch = []
        for platform_number, lat, lon in rows:
            subregion = map_subregion(lat, lon)
            batch.append({"platform_number": platform_number, "subregion": subregion})

        # Insert batch into Neo4j
        session.execute_write(insert_metadata, batch)

        pbar.update(len(batch))
        offset += BATCH_SIZE

    pbar.close()

print("✅ Neo4j hierarchical metadata insertion completed.")
