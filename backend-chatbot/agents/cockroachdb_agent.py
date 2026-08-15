# agents/cockroachdb_agent.py - CockroachDB Query Agent
import logging
from typing import Dict, Any, Optional, List
# from langchain_core.messages import HumanMessage, SystemMessage  # Removed unused imports
import google.generativeai as genai
import json
from tools import ArgoToolFactory
import time
from .config import GEMINI_API_KEY, GEMINI_MODEL
logger = logging.getLogger(__name__)

class CockroachDBAgent:
    """
    Specialized agent for querying CockroachDB for oceanographic measurements
    """
    def __init__(self):
        self.tools = ArgoToolFactory()
        genai.configure(api_key=GEMINI_API_KEY)

        self.system_prompt = """You are an expert SQL agent specialized in **CockroachDB**, tasked with generating **efficient, high-performance queries** for a large oceanographic dataset (`argo_measurements`) containing 13.5M+ records.
            ---
            ## Table Context
            The table `argo_measurements` has the following columns:
            - `platform_number` (STRING, not null) → unique float ID
            - `time` (TIMESTAMPTZ, not null) → timestamp of measurement
            - `latitude` (FLOAT8, nullable) → latitude of the float
            - `longitude` (FLOAT8, nullable) → longitude of the float
            - `pres_adjusted` (FLOAT8, nullable) → pressure, used as a proxy for depth
            - `temp_adjusted` (FLOAT8, nullable) → temperature
            - `psal_adjusted` (FLOAT8, nullable) → salinity
            - `rowid` (INT8, primary key) → unique row identifier
            **Indexes available**:
            - `argo_measurements_pkey` (rowid, platform_number, time, latitude, longitude, pres_adjusted, temp_adjusted, psal_adjusted)
            - `idx_platform_number` (platform_number ASC, rowid ASC)
            - `idx_platform_time` (platform_number ASC, time DESC, rowid ASC)
            ---
            **Data Integrity Rule**:
            My model should create queries that also handle null values. This includes NaN and infinity for floating-point types to prevent calculation errors.

              Add this line to filter out the NaN value
              Ex: temp_adjusted != 'NaN'::FLOAT
            ---
            ## CRITICAL Performance Rules
            1. **ALWAYS filter by `platform_number` in the FIRST CTE/subquery**
              - Put `WHERE platform_number = 'X'` immediately after FROM in the base query
              - This reduces dataset from 13.5M rows to ~1000 rows before any window functions
            2. **Use simple LAG() patterns without PARTITION BY when already filtered by platform_number**
              - Good: `LAG(latitude) OVER (ORDER BY time)`
              - Avoid: `LAG(latitude) OVER (PARTITION BY platform_number ORDER BY time)` (redundant partition)
            3. **Chain CTEs efficiently**:
              - CTE 1: Filter by platform_number + add LAG columns
              - CTE 2: Calculate flags/boundaries using simple CASE
              - CTE 3: Assign cycle IDs using SUM() OVER
              - Final: Filter for specific cycle
            ---
            ## Cycle Detection - EFFICIENT PATTERN
            **Use this pattern for cycle queries:**
            ```sql
            WITH float_data AS (
              SELECT
                *,
                LAG(latitude) OVER (ORDER BY time) AS prev_lat,
                LAG(longitude) OVER (ORDER BY time) AS prev_lon
              FROM argo_measurements
              WHERE platform_number = 'XXXXX'  -- FILTER FIRST!
            ),
            cycle_flag AS (
              SELECT
                *,
                CASE
                  WHEN prev_lat IS NULL THEN 0
                  WHEN ABS(latitude - prev_lat) > 0.05 OR ABS(longitude - prev_lon) > 0.05 THEN 1
                  ELSE 0
                END AS new_cycle
              FROM float_data
            ),
            cycles AS (
              SELECT
                *,
                SUM(new_cycle) OVER (ORDER BY time) AS cycle_id
              FROM cycle_flag
            )
            SELECT *
            FROM cycles
            WHERE cycle_id = (SELECT MAX(cycle_id) FROM cycles)
            ORDER BY time;
            ```
            **Why this is efficient:**
            - Filters to ~1000 rows immediately
            - Simple window functions without unnecessary PARTITION BY
            - Clean CTE chain that's easy to optimize
            - Executes in ~3 seconds
            ---
            ## Common Query Patterns
            ### Latest Month Floats
            ```sql
            WITH latest_month AS (
              SELECT date_trunc('month', MAX(time)) AS month_start
              FROM argo_measurements
            )
            SELECT DISTINCT platform_number
            FROM argo_measurements
            WHERE time >= (SELECT month_start FROM latest_month)
              AND time < (SELECT month_start + INTERVAL '1 month' FROM latest_month);
            ```
            ### Latest Measurement per Float
            ```sql
            SELECT DISTINCT ON (platform_number)
              platform_number,
              time,
              latitude,
              longitude,
              temp_adjusted,
              psal_adjusted,
              pres_adjusted
            FROM argo_measurements
            WHERE platform_number = 'XXXXX'
            ORDER BY platform_number, time DESC;
            ```
            ### Whole Cycle Data (All Cycles)
            ```sql
            WITH float_data AS (
              SELECT
                *,
                LAG(latitude) OVER (ORDER BY time) AS prev_lat,
                LAG(longitude) OVER (ORDER BY time) AS prev_lon
              FROM argo_measurements
              WHERE platform_number = 'XXXXX'
            ),
            cycle_flag AS (
              SELECT
                *,
                CASE
                  WHEN prev_lat IS NULL THEN 0
                  WHEN ABS(latitude - prev_lat) > 0.05 OR ABS(longitude - prev_lon) > 0.05 THEN 1
                  ELSE 0
                END AS new_cycle
              FROM float_data
            ),
            cycles AS (
              SELECT
                *,
                SUM(new_cycle) OVER (ORDER BY time) AS cycle_id
              FROM cycle_flag
            )
            SELECT * FROM cycles ORDER BY time;
            ```
            ---
            ## Response Format
            Generate ONLY the SQL query, no explanation. Always use the efficient pattern above for cycle queries."""


        self.llm = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=self.system_prompt,  # Use system_instruction
            generation_config={"temperature": 0.1}  # Lower temperature for SQL generation
        )

    def process(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
          try:
              logger.info(f"CockroachDBAgent processing: {query}")

              # Build context and generate SQL
              context = self._build_query_context(query, conversation_history)
              sql_query = self._generate_sql(context)

              if not sql_query:
                  return {"error": "Failed to generate SQL query"}

              # Execute the query with timeout handling
              logger.info("Executing SQL query...")
              start_time = time.time()
              try:
                  results = self.tools.cockroach.execute_custom_query(sql_query)
                  execution_time = time.time() - start_time
                  logger.info(f"SQL query executed in {execution_time:.2f} seconds. Retrieved {len(results) if results else 0} rows.")
              except Exception as db_error:
                  logger.error(f"Database execution error: {db_error}")
                  return {
                      "agent": "CockroachDBAgent",
                      "error": f"Database execution failed: {str(db_error)}",
                      "sql_query": sql_query
                  }

              # Process results
              if results:
                  logger.info(f"Returning {len(results)} results to ResponseAgent")
                  return {
                      "agent": "CockroachDBAgent",
                      "sql_query": sql_query,
                      "results": results,
                      "count": len(results),
                      "summary": f"Retrieved {len(results)} records from CockroachDB"
                  }
              else:
                  logger.info("No results found for the query")
                  return {
                      "agent": "CockroachDBAgent",
                      "sql_query": sql_query,
                      "results": [],
                      "count": 0,
                      "summary": "No data found matching the query criteria"
                  }

          except Exception as e:
              logger.error(f"CockroachDBAgent error: {e}")
              return {
                  "agent": "CockroachDBAgent",
                  "error": str(e),
                  "sql_query": sql_query if 'sql_query' in locals() else None
              }

    def _build_query_context(self, query: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Build context-aware query by including relevant conversation history
        """
        if not conversation_history:
            return query

        # Get last 4-6 messages for context
        recent_history = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history

        # Extract important context like float IDs, regions, etc.
        context_info = []
        float_ids = set()
        regions = set()

        for msg in recent_history:
            content = msg.get('content', '').lower()

            # Extract float IDs (7-digit numbers)
            import re
            found_floats = re.findall(r'\b\d{7}\b', content)
            float_ids.update(found_floats)

            # Extract region names
            for region in ['arabian sea', 'bay of bengal', 'indian ocean']:
                if region in content:
                    regions.add(region)

        context_parts = ["Recent conversation context:"]

        # Add extracted context
        if float_ids:
            context_parts.append(f"Float IDs mentioned: {', '.join(float_ids)}")
        if regions:
            context_parts.append(f"Regions mentioned: {', '.join(regions)}")

        # Add recent messages
        for msg in recent_history[-4:]:  # Last 4 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:150]  # Limit length
            context_parts.append(f"{role}: {content}")

        context_parts.append(f"\nCurrent query: {query}")
        context_parts.append("\nIMPORTANT Instructions:")
        context_parts.append("1. If the query refers to 'it', 'that float', 'this cycle', 'last cycle', 'whole cycle', 'complete data', use the float ID from the context above.")
        context_parts.append("2. Replace 'XXXXX' placeholder with the actual float ID from context.")
        context_parts.append("3. If asking for 'last cycle' or 'whole cycle' data, use the most recently mentioned float ID.")

        return "\n".join(context_parts)

    def _generate_sql(self, context_query: str) -> Optional[str]:
        """
        Generate SQL query using LLM with context
        """
        try:
            messages = [
                {"role": "user", "parts": [f"{self.system_prompt}\n\n{context_query}\n\nGenerate an efficient SQL query. IMPORTANT: Always filter by platform_number FIRST before using window functions. Return ONLY the SQL query."]}
            ]

            response = self.llm.generate_content(messages)
            sql_query = response.text.strip()  # Changed from response.content to response.text

            # Clean up markdown formatting
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()

            # Add query timeout (65 seconds)
            if "SET statement_timeout" not in sql_query.upper():
                sql_query = f"SET statement_timeout = '100s';\n{sql_query}"

            logger.info(f"Generated SQL: {sql_query[:500]}...")  # Log first 500 chars
            return sql_query

        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            return None

    def close(self):
        """Cleanup resources"""
        if hasattr(self, 'tools'):
            self.tools.cockroach.close()
