"""
Examples and usage patterns for the Argo data tools.
"""

from datetime import datetime, timedelta
from tools import ArgoToolFactory

def measurement_example():
    """Example of querying measurements"""
    factory = ArgoToolFactory()
    
    try:
        # Get measurements for a specific float
        measurements = factory.cockroach.get_measurements_by_float(
            platform_number="5906432",
            start_time=datetime.now() - timedelta(days=30),
            limit=10
        )
        
        print("Recent measurements:")
        for m in measurements:
            print(f"Time: {m.time}, Temp: {m.temp_adjusted}°C, "
                  f"Salinity: {m.psal_adjusted}")
            
        # Get regional measurements
        region_data = factory.cockroach.get_measurements_by_region(
            min_lat=10,
            max_lat=25,
            min_lon=55,
            max_lon=75,  # Arabian Sea region
            limit=5
        )
        
        print("\nArabian Sea measurements:")
        for m in region_data:
            print(f"Float: {m.platform_number}, "
                  f"Location: ({m.latitude}, {m.longitude})")
            
    finally:
        factory.close_all()

def metadata_example():
    """Example of querying metadata"""
    factory = ArgoToolFactory()
    
    try:
        # Get float metadata
        float_meta = factory.neo4j.get_float_metadata("5906432")
        if float_meta:
            print(f"Float {float_meta.platform_number}:")
            print(f"Region: {float_meta.subregion}")
            print(f"Parameters: {', '.join(float_meta.parameters)}")
        
        # Get region data
        region_meta = factory.neo4j.get_region_metadata("Arabian Sea")
        if region_meta:
            print(f"\nRegion: {region_meta.name}")
            print(f"Parent: {region_meta.parent_region}")
            print(f"Float count: {region_meta.float_count}")
            print(f"Subregions: {', '.join(region_meta.subregions)}")
            
        # Get complete hierarchy
        hierarchy = factory.neo4j.get_region_hierarchy()
        print("\nRegion hierarchy:")
        for region, data in hierarchy.items():
            print(f"{region}: {data['float_count']} floats")
            
    finally:
        factory.close_all()

def semantic_search_example():
    """Example of semantic search"""
    factory = ArgoToolFactory()
    
    try:
        # Search with a sample vector (replace with actual embedding)
        sample_vector = [0.1] * 768  # Assuming 768-dimensional embeddings
        
        results = factory.pinecone.semantic_search(
            query_vector=sample_vector,
            top_k=5,
            region_filter="Arabian Sea"
        )
        
        print("Semantic search results:")
        for r in results:
            print(f"Float: {r.platform_number}, Score: {r.score:.3f}")
            print(f"Time: {r.time}")
            print(f"Metadata: {r.metadata}\n")
            
        # Get similar profiles
        similar = factory.pinecone.get_similar_profiles(
            platform_number="5906432",
            time_range=(
                datetime.now() - timedelta(days=30),
                datetime.now()
            ),
            top_k=3
        )
        
        print("\nSimilar profiles:")
        for time, profiles in similar.items():
            print(f"\nProfiles similar to {time}:")
            for p in profiles:
                print(f"Float: {p.platform_number}, Score: {p.score:.3f}")
                
    finally:
        factory.close_all()

if __name__ == "__main__":
    measurement_example()
    metadata_example()
    semantic_search_example()