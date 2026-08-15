from langchain.tools import tool
import psycopg2
import json

POSTGRES_CONN_STRING = "dbname='argo_data' user='postgres' password='8099' host='localhost'"

@tool
def sql_query_tool(query: str) -> str:
    """
    Executes a SQL query against the Argo measurements database.
    Use this to get raw numerical data for specific floats, times, or locations.
    The table is named 'measurements' and has columns: platform_number, cycle_num, utc_time, latitude, longitude, pressure, temperature.
    Returns a JSON string of the results.
    """
    conn = psycopg2.connect(POSTGRES_CONN_STRING)
    cur = conn.cursor()
    try:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        results = [dict(zip(columns, row)) for row in cur.fetchall()]
        return json.dumps(results, default=str) # Use default=str to handle datetimes
    except Exception as e:
        return f"Error executing query: {e}"
    finally:
        cur.close()
        conn.close()