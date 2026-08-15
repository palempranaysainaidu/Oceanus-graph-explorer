# agents/response_agent.py - Final Response Formatting Agent
import logging
import time
import json
from typing import Dict, Any
import google.generativeai as genai
from .config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

class ResponseAgent:
    """
    Agent responsible for formatting final responses to users
    """
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.system_prompt = """You are an expert oceanographer responsible for presenting data analysis results to users.
Your task is to take raw data from specialized agents and create a clear, informative response.
Guidelines:
1. Provide direct, focused answers to the user's question
2. Use markdown tables for numerical data
3. Include key findings and statistics
4. Use **bold** for emphasis and ### for section headings
5. Keep responses concise and actionable
6. If data shows interesting patterns or anomalies, highlight them
7. Do NOT include generic "Recommendations" or "Further Investigation" sections unless explicitly asked
8. Focus on answering what the user actually asked
CRITICAL - Data Completeness:
- If user asks for "whole data", "all data", "complete data", "full data", or "all measurements":
  * Display EVERY SINGLE ROW in a markdown table
  * Do NOT summarize, sample, or truncate
  * Do NOT say "only a few rows shown" or "sample of the data"
  * Include ALL rows even if there are 50, 100, or 200 rows
  * Format as a complete markdown table with all rows visible
Format numerical data clearly:
- Use tables for comparisons
- Round to appropriate decimal places (4-5 decimals for lat/lon, 2-4 for measurements)
- Include units (°C, PSU, dbar)"""

        self.llm = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=self.system_prompt,
            generation_config={"temperature": 0.3}
        )

    def format_response(self, query: str, agent_results: Dict[str, Any]) -> str:
        """
        Format the final response from all agent results
        """
        try:
            logger.info("ResponseAgent formatting final response")

            # Check if user wants complete/whole data
            wants_full_data = any(phrase in query.lower() for phrase in [
                "whole data", "all data", "complete data", "entire data",
                "full data", "all measurements", "every measurement",
                "all rows", "complete list", "entire list"
            ])

            # Check if we have a large dataset
            result_count = 0
            if agent_results.get('cockroachdb') and agent_results['cockroachdb'].get('results'):
                result_count = len(agent_results['cockroachdb']['results'])

            # For large datasets, return a simplified response unless user explicitly asks for all data
            if result_count > 100 and not wants_full_data:
                start_time = time.time()
                results = agent_results['cockroachdb']['results']
                sample_results = results[:10]  # Show a sample

                # Create a simple markdown table for the sample
                if sample_results:
                    headers = list(sample_results[0].keys())
                    table = "| " + " | ".join(headers) + " |\n"
                    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                    for row in sample_results:
                        table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

                    processing_time = time.time() - start_time
                    logger.info(f"Formatted sample response in {processing_time:.2f} seconds")

                    base_note = f"The query returned {result_count} rows. Here's a sample of the first 10 rows:\n\n{table}\n\n" + \
                           f"Note: Only a sample is shown. Total rows: {result_count}. " + \
                           f"If you need the complete data, please ask for 'all data' or 'complete data'."
                    # Try to attach a visualization spec from the results
                    viz_block = self._build_visualization_block(results)
                    return base_note + ("\n\n" + viz_block if viz_block else "")
                else:
                    return "No data found for your query."

            # Prepare context from agent results
            start_time = time.time()
            context = self._prepare_context(agent_results, include_full_data=wants_full_data)
            logger.info(f"Prepared context in {time.time() - start_time:.2f} seconds")

            # Add instruction about data completeness
            data_instruction = ""
            if wants_full_data:
                data_instruction = "\n\nIMPORTANT: The user asked for COMPLETE/WHOLE data. Display ALL rows in a markdown table."

            # Generate natural language response with a longer timeout
            response_prompt = f"""Answer this oceanographic query: "{query}"
Data from specialized agents:
{context}{data_instruction}
Create a clear, concise response that directly answers the user's question using the available data.
If the data contains many rows, summarize the key findings rather than listing all rows."""

            start_time = time.time()
            messages = [
                {"role": "user", "parts": [f"{self.system_prompt}\n\n{response_prompt}"]}
            ]

            # Use a longer timeout for the Gemini API
            try:
                response = self.llm.generate_content(messages, request_options={"timeout": 300})  # 300 seconds timeout
                processing_time = time.time() - start_time
                logger.info(f"Generated response in {processing_time:.2f} seconds")
                # Try to append visualization spec when we have structured results
                nl_text = response.text
                cockroach = agent_results.get('cockroachdb', {})
                results = cockroach.get('results') or []
                viz_block = self._build_visualization_block(results)
                if viz_block:
                    nl_text += "\n\n" + viz_block
                return nl_text
            except Exception as gemini_error:
                logger.error(f"Gemini API error: {gemini_error}")

                # Fallback: return raw data if Gemini API fails
                if agent_results.get('cockroachdb') and agent_results['cockroachdb'].get('results'):
                    results = agent_results['cockroachdb']['results']
                    if wants_full_data:
                        # For full data requests, return a simple table format
                        headers = list(results[0].keys()) if results else []
                        table = "| " + " | ".join(headers) + " |\n"
                        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                        # Limit to first 1000 rows to prevent huge responses
                        limited_results = results[:1000]
                        for row in limited_results:
                            table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

                        return f"The query returned {len(results)} rows. Here are the first 1000 rows:\n\n{table}\n\n" + \
                               f"Note: Only the first 1000 rows are shown. Total rows: {len(results)}."
                    else:
                        # For regular requests, return a sample
                        sample = results[:10] if len(results) > 10 else results
                        base = f"The query returned {len(results)} rows. Here's a sample:\n\n{json.dumps(sample, indent=2)}"
                        viz_block = self._build_visualization_block(results)
                        return base + ("\n\n" + viz_block if viz_block else "")

                return f"Error generating response: {str(gemini_error)}"

        except Exception as e:
            logger.error(f"Error formatting response: {e}")

            # Fallback: return raw data if formatting fails
            if agent_results.get('cockroachdb') and agent_results['cockroachdb'].get('results'):
                results = agent_results['cockroachdb']['results']
                if wants_full_data and len(results) <= 1000:
                    # For full data requests with reasonable size, return a simple table format
                    headers = list(results[0].keys()) if results else []
                    table = "| " + " | ".join(headers) + " |\n"
                    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                    for row in results:
                        table += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

                    return f"The query returned {len(results)} rows:\n\n{table}"
                else:
                    # For regular requests or very large datasets, return a sample
                    sample = results[:10] if len(results) > 10 else results
                    base = f"The query returned {len(results)} rows. Here's a sample:\n\n{json.dumps(sample, indent=2)}"
                    viz_block = self._build_visualization_block(results)
                    return base + ("\n\n" + viz_block if viz_block else "")

            return f"Error formatting response: {str(e)}"

    def _prepare_context(self, agent_results: Dict[str, Any], include_full_data: bool = False) -> str:
        """
        Prepare context string from agent results
        """
        context_parts = []

        for agent_name, result in agent_results.items():
            if result and not result.get("error"):
                context_parts.append(f"\n**{agent_name.upper()} Results:**")

                # If user wants full data and we have results, include all of them
                if include_full_data and "results" in result:
                    results = result["results"]
                    result_count = len(results)
                    context_parts.append(f"Count: {result_count} rows")

                    # For large datasets, limit the context to prevent overwhelming the LLM
                    if result_count > 100:
                        context_parts.append("FULL DATA (sample of first 10 rows):")
                        context_parts.append(json.dumps(results[:10], indent=2, default=str))
                    else:
                        context_parts.append("FULL DATA (all rows):")
                        context_parts.append(json.dumps(results, indent=2, default=str))
                else:
                    # Normal summary
                    context_parts.append(json.dumps(result, indent=2, default=str))

        if not context_parts:
            return "No data available from agents"

        return "\n".join(context_parts)

    def _build_visualization_block(self, results: Any) -> str:
        """
        Build an advanced visualization spec block in a code fence that the frontend can parse.
        The fence language tag is 'viz'. The payload contains an object with 'visualizations' array.
        """
        try:
            if not results or not isinstance(results, list) or len(results) == 0:
                return ""

            # Infer available fields
            sample = results[0]
            fields = list(sample.keys())
            fset = set([f.lower() for f in fields])

            visualizations = []

            # Advanced time series with multiple metrics
            time_key = next((f for f in fields if f.lower() in ["time", "timestamp", "date"]), None)
            value_candidates = [f for f in fields if f.lower() in ["temp_adjusted", "psal_adjusted", "pres_adjusted", "temperature", "salinity", "pressure"]]
            
            if time_key and value_candidates:
                # Single metric line chart
                for val in value_candidates[:1]:
                    visualizations.append({
                        "type": "line",
                        "title": f"{val.replace('_', ' ').title()} Over Time",
                        "subtitle": f"Time series analysis of {val} measurements",
                        "data": {"fields": [time_key, val], "rows": results[:500]},
                        "encodings": {"x": time_key, "y": val},
                        "options": {
                            "tooltip": True, 
                            "connectNulls": True,
                            "animation": True,
                            "showLegend": True,
                            "showGrid": True,
                            "showAxes": True,
                            "interactive": True
                        },
                        "styling": {
                            "height": 400,
                            "margin": {"top": 20, "right": 30, "left": 20, "bottom": 20}
                        }
                    })
                
                # Area chart for temperature trends
                if "temp_adjusted" in fset:
                    visualizations.append({
                        "type": "area",
                        "title": "Temperature Profile Trend",
                        "subtitle": "Temperature variations over time with gradient fill",
                        "data": {"fields": [time_key, "temp_adjusted"], "rows": results[:500]},
                        "encodings": {"x": time_key, "y": "temp_adjusted"},
                        "options": {
                            "tooltip": True,
                            "animation": True,
                            "gradient": True,
                            "showLegend": True
                        },
                        "styling": {"height": 400}
                    })

            # Advanced scatter plots with pressure-depth relationships
            if "pres_adjusted" in fset:
                y_key = "temp_adjusted" if "temp_adjusted" in fset else ("psal_adjusted" if "psal_adjusted" in fset else None)
                if y_key:
                    visualizations.append({
                        "type": "scatter",
                        "title": f"{y_key.replace('_', ' ').title()} vs Pressure Profile",
                        "subtitle": f"Depth-pressure relationship analysis for {y_key}",
                        "data": {"fields": ["pres_adjusted", y_key], "rows": results[:1000]},
                        "encodings": {"x": "pres_adjusted", "y": y_key},
                        "options": {
                            "tooltip": True,
                            "animation": True,
                            "interactive": True,
                            "colors": ["#82ca9d", "#8884d8"]
                        },
                        "styling": {"height": 400}
                    })

            # Composed chart for multiple metrics
            if time_key and len(value_candidates) >= 2:
                visualizations.append({
                    "type": "composed",
                    "title": "Multi-Parameter Oceanographic Profile",
                    "subtitle": "Combined view of temperature, salinity, and pressure over time",
                    "data": {"fields": [time_key, "temp_adjusted", "psal_adjusted"], "rows": results[:300]},
                    "encodings": {"x": time_key, "y1": "temp_adjusted", "y2": "psal_adjusted"},
                    "options": {
                        "tooltip": True,
                        "animation": True,
                        "showLegend": True,
                        "colors": ["#8884d8", "#82ca9d"]
                    },
                    "styling": {"height": 400}
                })

            # Advanced map visualizations
            if "latitude" in fset and "longitude" in fset:
                # Enhanced map points with better styling
                visualizations.append({
                    "type": "map_points",
                    "title": "Argo Float Deployment Locations",
                    "subtitle": "Geographic distribution of oceanographic measurement points",
                    "data": {"fields": ["latitude", "longitude"], "rows": results[:2000]},
                    "encodings": {"lat": "latitude", "lon": "longitude"},
                    "options": {
                        "tooltip": True,
                        "interactive": True
                    },
                    "styling": {"height": 400}
                })
                
                # Advanced heatmap with temperature gradients
                color_key = "temp_adjusted" if "temp_adjusted" in fset else None
                if color_key:
                    visualizations.append({
                        "type": "heatmap",
                        "title": f"Spatial Temperature Distribution",
                        "subtitle": f"Heat map showing {color_key} variations across geographic regions",
                        "data": {"fields": ["latitude", "longitude", color_key], "rows": results[:5000]},
                        "encodings": {"lat": "latitude", "lon": "longitude", "value": color_key},
                        "options": {
                            "tooltip": True,
                            "interactive": True
                        },
                        "styling": {"height": 400}
                    })

            # Advanced 3D visualizations
            if {"latitude", "longitude", "pres_adjusted"}.issubset(fset):
                visualizations.append({
                    "type": "scatter3d",
                    "title": "3D Oceanographic Profile",
                    "subtitle": "Interactive 3D visualization of latitude, longitude, and pressure depth",
                    "data": {"fields": ["latitude", "longitude", "pres_adjusted"], "rows": results[:3000]},
                    "encodings": {"x": "longitude", "y": "latitude", "z": "pres_adjusted"},
                    "options": {
                        "tooltip": True,
                        "interactive": True,
                        "animation": True
                    },
                    "styling": {"height": 400}
                })

            # Bar chart for statistical summaries
            if len(results) > 10:
                # Create summary data for bar chart
                platform_counts = {}
                for row in results:
                    platform = row.get('platform_number', 'Unknown')
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
                
                summary_data = [{"platform": k, "measurements": v} for k, v in list(platform_counts.items())[:10]]
                if summary_data:
                    visualizations.append({
                        "type": "bar",
                        "title": "Measurement Count by Platform",
                        "subtitle": "Number of measurements per Argo float platform",
                        "data": {"fields": ["platform", "measurements"], "rows": summary_data},
                        "encodings": {"x": "platform", "y": "measurements"},
                        "options": {
                            "tooltip": True,
                            "animation": True,
                            "showLegend": False
                        },
                        "styling": {"height": 300}
                    })

            if not visualizations:
                return ""

            payload = {"visualizations": visualizations}
            fenced = "```viz\n" + json.dumps(payload, default=str) + "\n```"
            return fenced
        except Exception as e:
            logger.error(f"Failed building visualization block: {e}")
            return ""
