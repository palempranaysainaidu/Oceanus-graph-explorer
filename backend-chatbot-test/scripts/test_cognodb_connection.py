"""Test CognoDB connection from the Oceanus backend."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")

from tools.cognodb_client import CognodbClient


def main():
    client = CognodbClient()
    health = client.health_check()

    print("=== CognoDB Connection Test ===")
    print(f"URI:     {health.get('uri')}")
    print(f"Status:  {health.get('status')}")
    print(f"Message: {health.get('message')}")

    if health.get("connected"):
        rows = client.run_query(
            "RETURN 'Oceanus connected to CognoDB' AS message, datetime() AS server_time"
        )
        if rows:
            print(f"Query:   {rows[0]}")
        stats = client.run_query("MATCH (n) RETURN count(n) AS nodes")
        print(f"Nodes:   {stats[0]['nodes'] if stats else 0} (run seed_cognodb.py if 0)")
        print("\n✅ Connection successful.")
    else:
        print("\n❌ Connection failed. Check COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD in .env")
        sys.exit(1)

    client.close()


if __name__ == "__main__":
    main()
