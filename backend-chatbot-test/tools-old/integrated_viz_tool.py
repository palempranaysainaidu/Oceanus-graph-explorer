from langchain.tools import tool
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import json
import io
import base64
import psycopg2

POSTGRES_CONN_STRING = "dbname='argo_data' user='postgres' password='8099' host='localhost'"

@tool
def create_visualization_from_query(sql_query: str, chart_type: str = "scatter", title: str = "Data Visualization") -> str:
    """
    Executes a SQL query and creates a visualization from the results.
    
    Args:
        sql_query: SQL query to get data for visualization
        chart_type: Type of chart ('line', 'scatter', 'bar', 'histogram', 'map')
        title: Title for the chart
    
    Returns:
        Description of the created visualization with data insights
    """
    print(f"[VIZ] Starting visualization: {title}")
    print(f"[VIZ] Query: {sql_query}")
    print(f"[VIZ] Chart type: {chart_type}")
    
    try:
        # Execute SQL query
        print(f"[VIZ] Connecting to database...")
        conn = psycopg2.connect(POSTGRES_CONN_STRING)
        print(f"[VIZ] Executing query...")
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        print(f"[VIZ] Query completed, got {len(df)} rows")
        
        if df.empty:
            return "No data returned from query. Cannot create visualization."
        
        # Set up the plot
        print(f"[VIZ] Creating plot...")
        plt.figure(figsize=(12, 8))
        plt.style.use('default')
        
        if chart_type == "scatter" and 'latitude' in df.columns and 'longitude' in df.columns:
            # Geographic scatter plot
            plt.scatter(df['longitude'], df['latitude'], alpha=0.6, s=50)
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.title(f'{title} - Geographic Distribution')
            plt.grid(True, alpha=0.3)
            
        elif chart_type == "scatter":
            # Regular scatter plot with first two numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]], alpha=0.6)
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
                plt.grid(True, alpha=0.3)
            else:
                return "Error: Need at least 2 numeric columns for scatter plot"
                
        elif chart_type == "line":
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 2:
                plt.plot(df[numeric_cols[0]], df[numeric_cols[1]], marker='o', markersize=4)
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
                plt.grid(True, alpha=0.3)
            else:
                return "Error: Need at least 2 numeric columns for line plot"
                
        elif chart_type == "histogram":
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) >= 1:
                plt.hist(df[numeric_cols[0]], bins=30, alpha=0.7, edgecolor='black')
                plt.xlabel(numeric_cols[0])
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
            else:
                return "Error: Need at least 1 numeric column for histogram"
                
        elif chart_type == "bar":
            # Group by first column and count, or use first two columns
            cols = df.columns.tolist()
            if len(cols) >= 2:
                # If second column is numeric, use it as values
                if df[cols[1]].dtype in ['int64', 'float64']:
                    plt.bar(df[cols[0]], df[cols[1]])
                    plt.xlabel(cols[0])
                    plt.ylabel(cols[1])
                else:
                    # Count occurrences
                    counts = df[cols[0]].value_counts()
                    plt.bar(counts.index, counts.values)
                    plt.xlabel(cols[0])
                    plt.ylabel('Count')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
            else:
                return "Error: Need at least 2 columns for bar plot"
        
        plt.title(title)
        plt.tight_layout()
        
        # Convert plot to base64 string for frontend display
        print(f"[VIZ] Converting to base64...")
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        print(f"[VIZ] Visualization complete, image size: {len(image_base64)} chars")
        
        # Generate insights
        insights = []
        if 'temperature' in df.columns:
            temp_stats = df['temperature'].describe()
            insights.append(f"Temperature ranges from {temp_stats['min']:.2f}°C to {temp_stats['max']:.2f}°C with mean {temp_stats['mean']:.2f}°C")
        
        if 'pressure' in df.columns:
            pressure_stats = df['pressure'].describe()
            insights.append(f"Pressure ranges from {pressure_stats['min']:.2f} to {pressure_stats['max']:.2f} with mean {pressure_stats['mean']:.2f}")
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            lat_range = df['latitude'].max() - df['latitude'].min()
            lon_range = df['longitude'].max() - df['longitude'].min()
            insights.append(f"Geographic coverage: {lat_range:.2f}° latitude × {lon_range:.2f}° longitude")
        
        # Create response with embedded image
        response = f"""Created {chart_type} visualization with {len(df)} data points.

Data Summary:
- Rows: {len(df)}
- Columns: {', '.join(df.columns)}

Key Insights:
{chr(10).join(f'• {insight}' for insight in insights)}

![Visualization](data:image/png;base64,{image_base64})

The visualization shows the {chart_type} chart of your Argo data."""
        
        return response
        
    except Exception as e:
        return f"Error creating visualization: {str(e)}"