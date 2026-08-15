import os
import csv
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER")
PASSWORD = os.getenv("COGNODB_PASSWORD")
CSV_PATH = os.path.join(os.path.dirname(__file__), "argo_data_sample.csv")
BATCH_SIZE = 500

def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("time") and r["time"] != "UTC"]  # skip units row
    return rows

def to_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def batch(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

SEED_QUERY = """
UNWIND $rows AS row
MERGE (f:Float {platform_number: row.platform_number})

MERGE (c:Cycle {platform_number: row.platform_number, cycle_number: row.cycle_number})
ON CREATE SET
    c.time = row.time,
    c.latitude = row.latitude,
    c.longitude = row.longitude,
    c.direction = row.direction
MERGE (f)-[:HAS_CYCLE]->(c)

CREATE (m:Measurement {
    pres: row.pres,
    temp: row.temp,
    psal: row.psal,
    temp_qc: row.temp_qc,
    psal_qc: row.psal_qc,
    pres_qc: row.pres_qc,
    data_mode: row.data_mode
})
CREATE (c)-[:HAS_MEASUREMENT]->(m)
"""

def seed():
    rows = read_rows(CSV_PATH)
    print(f"Loaded {len(rows)} rows from CSV")

    payload = [{
        "platform_number": r["platform_number"],
        "cycle_number": r["cycle_number"],
        "time": r["time"],
        "latitude": to_float(r["latitude"]),
        "longitude": to_float(r["longitude"]),
        "direction": r.get("direction"),
        "pres": to_float(r["pres"]),
        "temp": to_float(r["temp"]),
        "psal": to_float(r["psal"]),
        "temp_qc": r.get("temp_qc"),
        "psal_qc": r.get("psal_qc"),
        "pres_qc": r.get("pres_qc"),
        "data_mode": r.get("data_mode"),
    } for r in rows]

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()

    with driver.session() as session:
        for i, chunk in enumerate(batch(payload, BATCH_SIZE)):
            session.run(SEED_QUERY, rows=chunk)
            print(f"Batch {i + 1} inserted ({len(chunk)} rows)")

    driver.close()
    print("✅ Seeding complete.")

if __name__ == "__main__":
    seed()
