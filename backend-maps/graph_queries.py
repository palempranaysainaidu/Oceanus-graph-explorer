import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER")
PASSWORD = os.getenv("COGNODB_PASSWORD")

driver = None
if URI and USER and PASSWORD:
    try:
        driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    except Exception as e:
        print(f"⚠️ Failed to initialize Neo4j driver: {e}")

def _execute_read_query(query, **kwargs):
    if not driver:
        raise Exception("CognoDB is unreachable or not configured.")
    try:
        with driver.session() as session:
            result = session.run(query, **kwargs)
            return [record.data() for record in result]
    except Exception as e:
        raise Exception(f"Database query failed: {str(e)}")

def get_float_history(float_id: str):
    """
    Multi-hop traversal (2+ hops): Given a float_id, traverse Float -> Cycle -> Measurement 
    to return that float's full measurement history in chronological order.
    
    Why graph?: This is the natural 2-hop query our model is built for. It traverses explicit 
    relationships without needing expensive JOINs across massive tables, maintaining constant 
    time performance relative to the number of relationships for the node.
    """
    query = """
    MATCH (f:Float {platform_number: $float_id})-[:HAS_CYCLE]->(c:Cycle)-[:HAS_MEASUREMENT]->(m:Measurement)
    RETURN c.cycle_number AS cycle_number, c.time AS time, c.latitude AS latitude, c.longitude AS longitude,
           m.temp AS temperature, m.psal AS salinity, m.pres AS pressure
    ORDER BY c.time ASC
    """
    return _execute_read_query(query, float_id=float_id)

def search_cycles_by_measurement_range(min_temp: float, max_temp: float):
    """
    Find all Cycles across any Float where the Measurement's temperature falls within a given range, 
    then return the parent Float and Cycle info.
    
    Why graph?: This pattern (search by leaf property, return ancestor) is awkward and slow in SQL, 
    often requiring subqueries or deep JOINs. In Cypher, it's a simple, expressive pattern match that 
    leverages graph locality.
    """
    query = """
    MATCH (f:Float)-[:HAS_CYCLE]->(c:Cycle)-[:HAS_MEASUREMENT]->(m:Measurement)
    WHERE m.temp >= $min_temp AND m.temp <= $max_temp
    RETURN f.platform_number AS float_id, c.cycle_number AS cycle_number, c.time AS time, 
           c.latitude AS latitude, c.longitude AS longitude, m.temp AS temperature
    ORDER BY c.time DESC LIMIT 100
    """
    return _execute_read_query(query, min_temp=min_temp, max_temp=max_temp)

def get_all_floats():
    """
    List all floats with basic metadata.
    
    Why graph?: Standard node enumeration. Very fast as it just scans the Float labels.
    """
    query = """
    MATCH (f:Float)
    RETURN f.platform_number AS float_id
    """
    return _execute_read_query(query)

def get_float_by_id(float_id: str):
    """
    Get single float details and count of its cycles.
    
    Why graph?: Graph databases natively support degree-counting (number of relationships). 
    Counting cycles connected to a float is highly optimized compared to SQL aggregate COUNT().
    """
    query = """
    MATCH (f:Float {platform_number: $float_id})
    OPTIONAL MATCH (f)-[:HAS_CYCLE]->(c:Cycle)
    RETURN f.platform_number AS float_id, count(c) AS total_cycles
    """
    res = _execute_read_query(query, float_id=float_id)
    return res[0] if res else None

def get_cycles_for_float(float_id: str):
    """
    List all cycles for a specific float.
    
    Why graph?: 1-hop traversal. Very fast pointer-chasing operation rather than index-lookup 
    for a foreign key.
    """
    query = """
    MATCH (f:Float {platform_number: $float_id})-[:HAS_CYCLE]->(c:Cycle)
    RETURN c.cycle_number AS cycle_number, c.time AS time, c.latitude AS latitude, c.longitude AS longitude
    ORDER BY c.time DESC
    """
    return _execute_read_query(query, float_id=float_id)

def get_measurement_stats(float_id: str):
    """
    Aggregate min/max/avg temperature and salinity for a float.
    
    Why graph?: 2-hop aggregation. Computes statistics only over the localized subgraph 
    connected to the specific float, completely ignoring the rest of the database.
    """
    query = """
    MATCH (f:Float {platform_number: $float_id})-[:HAS_CYCLE]->(:Cycle)-[:HAS_MEASUREMENT]->(m:Measurement)
    RETURN min(m.temp) AS min_temp, max(m.temp) AS max_temp, avg(m.temp) AS avg_temp,
           min(m.psal) AS min_psal, max(m.psal) AS max_psal, avg(m.psal) AS avg_psal
    """
    res = _execute_read_query(query, float_id=float_id)
    return res[0] if res else None
