"""
Load 88 Argo floats from argo_data.csv into CognoDB using the assignment graph schema.

Nodes:
  (:Float {id, wmo_id, lat, lon, status})
  (:Cruise {id, name, start_date, end_date})
  (:Region {name})
  (:Parameter {name})
  (:Measurement {id, value, depth, timestamp})

Relationships:
  (:Float)-[:PART_OF_CRUISE]->(:Cruise)
  (:Float)-[:LOCATED_IN]->(:Region)
  (:Float)-[:RECORDED]->(:Measurement)
  (:Measurement)-[:MEASURES]->(:Parameter)
  (:Float)-[:NEAR {distance_km}]->(:Float)

Usage:
  cd backend-chatbot-test
  python Data_populating/seed_graph.py [--csv PATH] [--clear] [--full-depth]

Default mode creates profile-level measurements (one per float+cycle+parameter).
--full-depth creates one Measurement node per CSV row per parameter (~1.4M nodes).
"""

import argparse
import math
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.cognodb_client import CognodbClient

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

DEFAULT_CSV = ROOT.parent / "backend-maps" / "argo_data.csv"
BATCH_SIZE = 1500
PROXIMITY_KM = 120.0

PARAMETERS = [
    ("Temperature", "temp"),
    ("Salinity", "psal"),
    ("Pressure", "pres"),
]


def map_region(lat: float, lon: float) -> str:
    if lat is None or lon is None:
        return "Unknown"
    if 10 <= lat <= 25 and 55 <= lon <= 75:
        return "Arabian Sea"
    if 10 <= lat <= 25 and 80 <= lon <= 95:
        return "Bay of Bengal"
    if -5 <= lat <= 5 and 40 <= lon <= 80:
        return "Equatorial Indian Ocean"
    if -40 <= lat <= -20 and 20 <= lon <= 80:
        return "Southern Indian Ocean"
    return "Other"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def create_constraints(client: CognodbClient):
    for stmt in [
        "CREATE CONSTRAINT float_id IF NOT EXISTS FOR (f:Float) REQUIRE f.id IS UNIQUE",
        "CREATE CONSTRAINT cruise_id IF NOT EXISTS FOR (c:Cruise) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT region_name IF NOT EXISTS FOR (r:Region) REQUIRE r.name IS UNIQUE",
        "CREATE CONSTRAINT parameter_name IF NOT EXISTS FOR (p:Parameter) REQUIRE p.name IS UNIQUE",
        "CREATE CONSTRAINT measurement_id IF NOT EXISTS FOR (m:Measurement) REQUIRE m.id IS UNIQUE",
    ]:
        try:
            client.run_query(stmt)
        except Exception:
            pass


def clear_graph(client: CognodbClient):
    client.run_query("MATCH (n) DETACH DELETE n")


def seed_parameters_and_regions(client: CognodbClient, regions: list[str]):
    client.run_query(
        """
        MERGE (parent:Region {name: 'Indian Ocean'})
        WITH parent
        UNWIND $regions AS name
        MERGE (r:Region {name: name})
        MERGE (r)-[:PART_OF]->(parent)
        """,
        {"regions": regions},
    )
    for name in [p[0] for p in PARAMETERS]:
        client.run_query("MERGE (p:Parameter {name: $name})", {"name": name})


def seed_floats(client: CognodbClient, float_rows: list[dict]):
    client.run_query(
        """
        UNWIND $rows AS row
        MERGE (f:Float {id: row.id})
        SET f.wmo_id = row.wmo_id,
            f.lat = row.lat,
            f.lon = row.lon,
            f.status = row.status
        MERGE (r:Region {name: row.region})
        MERGE (f)-[:LOCATED_IN]->(r)
        """,
        {"rows": float_rows},
    )


def seed_cruises(client: CognodbClient, cruise_rows: list[dict]):
    for i in range(0, len(cruise_rows), BATCH_SIZE):
        chunk = cruise_rows[i : i + BATCH_SIZE]
        client.run_query(
            """
            UNWIND $rows AS row
            MERGE (c:Cruise {id: row.id})
            SET c.name = row.name,
                c.start_date = row.start_date,
                c.end_date = row.end_date
            MERGE (f:Float {id: row.float_id})
            MERGE (f)-[:PART_OF_CRUISE]->(c)
            """,
            {"rows": chunk},
        )


def seed_profile_measurements(client: CognodbClient, profiles: pd.DataFrame):
    """One Measurement per float+cycle+parameter (default, ~20k nodes)."""
    rows = []
    for _, row in profiles.iterrows():
        float_id = str(row["platform_number"])
        cycle = int(row["cycle_number"])
        cruise_id = f"{float_id}_{cycle}"
        base = {
            "float_id": float_id,
            "cruise_id": cruise_id,
            "timestamp": str(row["time"]),
            "depth": float(row["pres_max"]),
        }
        for param_name, col in PARAMETERS:
            val_col = f"{col}_mean" if col != "pres" else "pres_max"
            value = row[val_col]
            if pd.isna(value):
                continue
            rows.append(
                {
                    "id": f"{cruise_id}_{param_name}",
                    "float_id": float_id,
                    "parameter": param_name,
                    "value": float(value),
                    "depth": base["depth"],
                    "timestamp": base["timestamp"],
                }
            )

    for i in tqdm(range(0, len(rows), BATCH_SIZE), desc="Profile measurements"):
        chunk = rows[i : i + BATCH_SIZE]
        client.run_query(
            """
            UNWIND $rows AS row
            MERGE (m:Measurement {id: row.id})
            SET m.value = row.value,
                m.depth = row.depth,
                m.timestamp = row.timestamp
            MERGE (f:Float {id: row.float_id})
            MERGE (f)-[:RECORDED]->(m)
            MERGE (p:Parameter {name: row.parameter})
            MERGE (m)-[:MEASURES]->(p)
            """,
            {"rows": chunk},
        )


def seed_full_depth_measurements(client: CognodbClient, df: pd.DataFrame):
    """One Measurement per CSV row per parameter (~1.4M nodes)."""
    total_batches = math.ceil(len(df) / BATCH_SIZE)
    for batch_idx in tqdm(range(total_batches), desc="Full-depth measurements"):
        chunk_df = df.iloc[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        rows = []
        for _, row in chunk_df.iterrows():
            float_id = str(row["platform_number"])
            cycle = int(row["cycle_number"])
            depth = float(row["pres"])
            ts = str(row["time"])
            for param_name, col in PARAMETERS:
                val = row[col]
                if pd.isna(val):
                    continue
                rows.append(
                    {
                        "id": f"{float_id}_{cycle}_{depth}_{param_name}",
                        "float_id": float_id,
                        "parameter": param_name,
                        "value": float(val),
                        "depth": depth,
                        "timestamp": ts,
                    }
                )
        if rows:
            client.run_query(
                """
                UNWIND $rows AS row
                MERGE (m:Measurement {id: row.id})
                SET m.value = row.value,
                    m.depth = row.depth,
                    m.timestamp = row.timestamp
                MERGE (f:Float {id: row.float_id})
                MERGE (f)-[:RECORDED]->(m)
                MERGE (p:Parameter {name: row.parameter})
                MERGE (m)-[:MEASURES]->(p)
                """,
                {"rows": rows},
            )


def seed_near_edges(client: CognodbClient, float_rows: list[dict]):
    pairs = []
    for i, a in enumerate(float_rows):
        for b in float_rows[i + 1 :]:
            dist = haversine_km(a["lat"], a["lon"], b["lat"], b["lon"])
            if dist <= PROXIMITY_KM:
                pairs.append({"a": a["id"], "b": b["id"], "distance_km": round(dist, 2)})
    for i in range(0, len(pairs), BATCH_SIZE):
        chunk = pairs[i : i + BATCH_SIZE]
        client.run_query(
            """
            UNWIND $rows AS row
            MATCH (a:Float {id: row.a}), (b:Float {id: row.b})
            MERGE (a)-[r:NEAR]->(b)
            SET r.distance_km = row.distance_km
            MERGE (b)-[r2:NEAR]->(a)
            SET r2.distance_km = row.distance_km
            """,
            {"rows": chunk},
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--clear", action="store_true")
    parser.add_argument(
        "--full-depth",
        action="store_true",
        help="Load every depth row as Measurement nodes (slow, ~1.4M nodes)",
    )
    args = parser.parse_args()

    client = CognodbClient()
    health = client.health_check()
    if not health.get("connected"):
        print(f"Cannot connect: {health.get('message')}")
        sys.exit(1)

    print(f"Connected via {client.uri}")
    df = pd.read_csv(args.csv, skiprows=[1], low_memory=False)
    df["platform_number"] = df["platform_number"].astype(str)
    print(f"CSV: {len(df):,} rows, {df['platform_number'].nunique()} floats")

    if args.clear:
        clear_graph(client)

    create_constraints(client)

    centroids = (
        df.groupby("platform_number")
        .agg(lat=("latitude", "mean"), lon=("longitude", "mean"), status=("data_mode", "last"))
        .reset_index()
    )

    float_rows = []
    regions = set()
    for _, row in centroids.iterrows():
        region = map_region(row["lat"], row["lon"])
        regions.add(region)
        float_rows.append(
            {
                "id": str(row["platform_number"]),
                "wmo_id": str(row["platform_number"]),
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "status": str(row["status"]) if pd.notna(row["status"]) else "active",
                "region": region,
            }
        )

    seed_parameters_and_regions(client, sorted(regions))
    seed_floats(client, float_rows)

    cruise_agg = (
        df.groupby(["platform_number", "cycle_number"])
        .agg(start_date=("time", "min"), end_date=("time", "max"))
        .reset_index()
    )
    cruise_rows = []
    for _, row in cruise_agg.iterrows():
        fid = str(row["platform_number"])
        cycle = int(row["cycle_number"])
        cruise_rows.append(
            {
                "id": f"{fid}_{cycle}",
                "float_id": fid,
                "name": f"Cycle {cycle}",
                "start_date": str(row["start_date"]),
                "end_date": str(row["end_date"]),
            }
        )
    seed_cruises(client, cruise_rows)

    if args.full_depth:
        seed_full_depth_measurements(client, df)
    else:
        profiles = (
            df.groupby(["platform_number", "cycle_number"])
            .agg(
                time=("time", "first"),
                temp_mean=("temp", "mean"),
                psal_mean=("psal", "mean"),
                pres_max=("pres", "max"),
            )
            .reset_index()
        )
        seed_profile_measurements(client, profiles)

    seed_near_edges(client, float_rows)

    stats = client.run_query(
        "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS c ORDER BY c DESC"
    )
    print("\nNode counts:")
    for r in stats:
        print(f"  {r['label']}: {r['c']}")

    client.close()
    print("\nDone — graph seeded with assignment schema.")


if __name__ == "__main__":
    main()
