import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER")
PASSWORD = os.getenv("COGNODB_PASSWORD")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def clear_db():
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Cleared database.")

def count_db():
    with driver.session() as session:
        floats = session.run("MATCH (f:Float) RETURN count(f) AS c").single()["c"]
        cycles = session.run("MATCH (c:Cycle) RETURN count(c) AS cnt").single()["cnt"]
        measurements = session.run("MATCH (m:Measurement) RETURN count(m) AS c").single()["c"]
        rels_fc = session.run("MATCH (f)-[r:HAS_CYCLE]->(c) RETURN count(r) AS cnt").single()["cnt"]
        rels_cm = session.run("MATCH (c)-[r:HAS_MEASUREMENT]->(m) RETURN count(r) AS cnt").single()["cnt"]
        print(f"Floats: {floats}")
        print(f"Cycles: {cycles}")
        print(f"Measurements: {measurements}")
        print(f"Float->Cycle Rels: {rels_fc}")
        print(f"Cycle->Measurement Rels: {rels_cm}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_db()
    else:
        count_db()
