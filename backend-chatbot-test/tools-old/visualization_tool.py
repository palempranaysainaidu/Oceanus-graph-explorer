from langchain.tools import tool
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import json
import io
import base64
from typing import Dict, Any

@tool
def visualization_tool(data_json: str, chart_type: str = "line", title: str = "Data Visualization") -> str:
    """
    Creates visualizations from structured data (JSON format).
    
    Args:
        data_json: JSON string containing the data to visualize
        chart_type: Type of chart ('line', 'scatter', 'bar', 'histogram', 'heatmap', 'map')
        title: Title for the chart
    
    Returns:
        JSON string with base64 encoded image and chart description
    """
    try:
        # Parse the input data
        data = json.loads(data_json)
        
        # Convert to DataFrame if it's a list of dictionaries
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            return "Error: Data must be a list of dictionaries"
        
        # Create the plot
        plt.figure(figsize=(10, 6))
        
        if chart_type == "line":
            # Assume first numeric column is x, second is y
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                plt.plot(df[numeric_cols[0]], df[numeric_cols[1]])
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
            else:
                return "Error: Need at least 2 numeric columns for line plot"
                
        elif chart_type == "scatter":
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]])
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
            else:
                return "Error: Need at least 2 numeric columns for scatter plot"
                
        elif chart_type == "bar":
            # Use first column as x, second as y
            cols = df.columns.tolist()
            if len(cols) >= 2:
                plt.bar(df[cols[0]], df[cols[1]])
                plt.xlabel(cols[0])
                plt.ylabel(cols[1])
                plt.xticks(rotation=45)
            else:
                return "Error: Need at least 2 columns for bar plot"
                
        elif chart_type == "histogram":
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 1:
                plt.hist(df[numeric_cols[0]], bins=20)
                plt.xlabel(numeric_cols[0])
                plt.ylabel('Frequency')
            else:
                return "Error: Need at least 1 numeric column for histogram"
                
        elif chart_type == "map":
            # Assume we have latitude and longitude columns
            if 'latitude' in df.columns and 'longitude' in df.columns:
                plt.scatter(df['longitude'], df['latitude'], alpha=0.6)
                plt.xlabel('Longitude')
                plt.ylabel('Latitude')
                plt.title('Geographic Distribution')
            else:
                return "Error: Need 'latitude' and 'longitude' columns for map"
        
        plt.title(title)
        plt.tight_layout()
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        # Create response
        response = {
            "image_base64": image_base64,
            "chart_type": chart_type,
            "title": title,
            "description": f"Generated {chart_type} chart with {len(df)} data points",
            "data_summary": {
                "rows": len(df),
                "columns": list(df.columns),
                "numeric_columns": df.select_dtypes(include=['number']).columns.tolist()
            }
        }
        
        return json.dumps(response)
        
    except Exception as e:
        return f"Error creating visualization: {e}"