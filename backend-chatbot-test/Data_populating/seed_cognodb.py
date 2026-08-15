"""
Seed CognoDB with Argo float knowledge graph from argo_data.csv.

Graph schema:
  (:Float) (:Cruise) (:Region) (:Measurement) (:Parameter)
  (Measurement)-[:RECORDED_BY]->(Float)
  (Float)-[:LOCATED_IN]->(Region)
  (Float)-[:PART_OF_CRUISE]->(Cruise)
  (Measurement)-[:PART_OF_CRUISE]->(Cruise)
  (Measurement)-[:MEASURED]->(Parameter)
  (Region)-[:PART_OF]->(Region)
  (Float)-[:NEAR_FLOAT]->(Float)  — proximity network for path queries

Usage:
  cd backend-chatbot-test
  python Data_populating/seed_cognodb.py [--csv PATH] [--clear] [--skip-measurements]
"""

import argparse
import math
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Allow imports from backend-chatbot-test root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.cognodb_client import CognodbClient

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

DEFAULT_CSV = ROOT.parent / "backend-maps" / "argo_data.csv"
BATCH_SIZE = 2000
PROXIMITY_KM = 120.0


def map_subregion(lat: float, lon: float) -> str:
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
    return "Other"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def create_constraints(client: CognodbClient):
    stmts = [
        "CREATE CONSTRAINT float_id IF NOT EXISTS FOR (f:Float) REQUIRE f.platform_number IS UNIQUE",
        "CREATE CONSTRAINT cruise_id IF NOT EXISTS FOR (c:Cruise) REQUIRE c.cruise_id IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT parameter_name IF NOT EXISTS FOR (p:Parameter) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT measurement_id IF NOT EXISTS FOR (m:Measurement) REQUIRE m.measurement_id IS UNIQUE",
    ]
    for stmt in stmts:
        try:
            client.run_query(stmt)
        except Exception as e:
            print(f"  Constraint note: {e}")


def clear_graph(client: CognodbClient):
    client.run_query("MATCH (n) DETACH DELETE n")
    print("Graph cleared.")


def seed_base_schema(client: CognodbClient, float_centroids: list):
    """Create Region, Parameter, Float nodes and LOCATED_IN / PART_OF."""
    regions = sorted({f["subregion"] for f in float_centroids})
    client.run_query(
        """
        MERGE (parent:Region {name: 'Indian Ocean'})
        WITH parent
        UNWIND $regions AS region_name
        MERGE (r:Region {name: region_name})
        MERGE (r)-[:PART_OF]->(parent)
        """,
        {"regions": regions},
    )
    for pname in ["temperature", "salinity", "pressure"]:
        client.run_query("MERGE (p:Parameter {name: $name})", {"name": pname})

    batch = []
    for f in float_centroids:
        batch.append(
            {
                "platform_number": f["platform_number"],
                "latitude": f["latitude"],
                "longitude": f["longitude"],
                "subregion": f["subregion"],
            }
        )
    client.run_query(
        """
        UNWIND $rows AS row
        MERGE (f:Float {platform_number: row.platform_number})
        SET f.latitude = row.latitude, f.longitude = row.longitude
        MERGE (r:Region {name: row.subregion})
        MERGE (f)-[:LOCATED_IN]->(r)
        """,
        {"rows": batch},
    )
    print(f"Seeded {len(batch)} Float nodes and {len(regions)} regions.")


def seed_cruises_and_profile_measurements(client: CognodbClient, profiles: pd.DataFrame):
    """One Measurement node per profiling cycle (platform + cycle_number)."""
    rows = []
    for _, row in profiles.iterrows():
        platform = str(row["platform_number"])
        cycle = int(row["cycle_number"])
        cruise_id = f"{platform}_{cycle}"
        rows.append(
            {
                "measurement_id": cruise_id,
                "cruise_id": cruise_id,
                "platform_number": platform,
                "cycle_number": cycle,
                "time": str(row["time"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "temp_mean": float(row["temp_mean"]),
                "sal_mean": float(row["sal_mean"]),
                "pres_max": float(row["pres_max"]),
            }
        )

    for i in tqdm(range(0, len(rows), BATCH_SIZE), desc="Cruises + profile measurements"):
        chunk = rows[i : i + BATCH_SIZE]
        client.run_query(
            """
            UNWIND $rows AS row
            MERGE (c:Cruise {cruise_id: row.cruise_id})
            SET c.cycle_number = row.cycle_number, c.time = row.time
            MERGE (f:Float {platform_number: row.platform_number})
            MERGE (f)-[:PART_OF_CRUISE]->(c)
            MERGE (m:Measurement {measurement_id: row.measurement_id})
            SET m.time = row.time,
                m.latitude = row.latitude,
                m.longitude = row.longitude,
                m.temp_mean = row.temp_mean,
                m.sal_mean = row.sal_mean,
                m.pres_max = row.pres_max
            MERGE (m)-[:RECORDED_BY]->(f)
            MERGE (m)-[:PART_OF_CRUISE]->(c)
            WITH m, row
            MATCH (pt:Parameter {name: 'temperature'})
            MATCH (ps:Parameter {name: 'salinity'})
            MATCH (pp:Parameter {name: 'pressure'})
            MERGE (m)-[:MEASURED {value: row.temp_mean}]->(pt)
            MERGE (m)-[:MEASURED {value: row.sal_mean}]->(ps)
            MERGE (m)-[:MEASURED {value: row.pres_max}]->(pp)
            """,
            {"rows": chunk},
        )


def seed_proximity_edges(client: CognodbClient, float_centroids: list):
    pairs = []
    for i, a in enumerate(float_centroids):
        for b in float_centroids[i + 1:]:
            dist = haversine_km(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
            if dist <= PROXIMITY_KM:
                pairs.append(
                    {
                        "a": a["platform_number"],
                        "b": b["platform_number"],
                        "distance_km": round(dist, 2),
                    }
                )
    for i in tqdm(range(0, len(pairs), BATCH_SIZE), desc="NEAR_FLOAT proximity edges"):
        chunk = pairs[i : i + BATCH_SIZE]
        client.run_query(
            """
            UNWIND $rows AS row
            MATCH (a:Float {platform_number: row.a})
            MATCH (b:Float {platform_number: row.b})
            MERGE (a)-[r:NEAR_FLOAT]->(b)
            SET r.distance_km = row.distance_km
            MERGE (b)-[r2:NEAR_FLOAT]->(a)
            SET r2.distance_km = row.distance_km
            """,
            {"rows": chunk},
        )
    print(f"Created {len(pairs)} bidirectional NEAR_FLOAT edges (threshold {PROXIMITY_KM} km).")


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, skiprows=[1], low_memory=False)
    df["platform_number"] = df["platform_number"].astype(str)
    return df


def main():
    parser = argparse.ArgumentParser(description="Seed CognoDB Argo knowledge graph")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to argo_data.csv")
    parser.add_argument("--clear", action="store_true", help="Clear existing graph data")
    parser.add_argument("--skip-measurements", action="store_true", help="Skip cruise/measurement nodes")
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"CSV not found: {args.csv}")
        sys.exit(1)

    client = CognodbClient()
    health = client.health_check()
    if not health.get("connected"):
        print(f"Cannot connect to CognoDB: {health.get('message')}")
        print("Set COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD in .env")
        sys.exit(1)

    print(f"Connected to {health.get('uri')}")

    if args.clear:
        clear_graph(client)

    create_constraints(client)

    print(f"Loading {args.csv} ...")
    df = load_csv(args.csv)
    print(f"  {len(df):,} rows, {df['platform_number'].nunique()} floats")

    centroids = (
        df.groupby("platform_number")
        .agg(
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .reset_index()
    )
    float_centroids = []
    for _, row in centroids.iterrows():
        subregion = map_subregion(row["latitude"], row["longitude"])
        float_centroids.append(
            {
                "platform_number": str(row["platform_number"]),
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "subregion": subregion,
            }
        )

    seed_base_schema(client, float_centroids)

    if not args.skip_measurements:
        profiles = (
            df.groupby(["platform_number", "cycle_number"])
            .agg(
                time=("time", "first"),
                latitude=("latitude", "first"),
                longitude=("longitude", "first"),
                temp_mean=("temp", "mean"),
                sal_mean=("psal", "mean"),
                pres_max=("pres", "max"),
            )
            .reset_index()
        )
        seed_cruises_and_profile_measurements(client, profiles)

    seed_proximity_edges(client, float_centroids)

    stats = client.run_query("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS c")
    print("\nNode counts:")
    for row in stats:
        print(f"  {row['label']}: {row['c']}")

    client.close()
    print("\n✅ CognoDB seed complete.")


if __name__ == "__main__":
    main()
