from fastapi.testclient import TestClient
import json
import sys

from main import app

client = TestClient(app)

def run_tests():
    print("--- 1. GET /api/graph/floats ---")
    res1 = client.get("/api/graph/floats")
    floats_data = res1.json()
    print(json.dumps(floats_data[:3], indent=2))
    if len(floats_data) > 3:
        print(f"... and {len(floats_data) - 3} more floats")
    
    if not floats_data:
        print("No floats found!")
        return
        
    float_id = floats_data[0]["float_id"]
    
    print(f"\n--- 2. GET /api/graph/floats/{float_id} ---")
    res2 = client.get(f"/api/graph/floats/{float_id}")
    print(json.dumps(res2.json(), indent=2))
    
    print(f"\n--- 3. GET /api/graph/floats/{float_id}/cycles ---")
    res3 = client.get(f"/api/graph/floats/{float_id}/cycles")
    cycles = res3.json()
    print(json.dumps(cycles[:2], indent=2))
    if len(cycles) > 2:
         print(f"... and {len(cycles) - 2} more cycles")
         
    print(f"\n--- 4. GET /api/graph/floats/{float_id}/history ---")
    res4 = client.get(f"/api/graph/floats/{float_id}/history")
    history = res4.json()
    print(json.dumps(history[:2], indent=2))
    if len(history) > 2:
         print(f"... and {len(history) - 2} more history records")
         
    print(f"\n--- 5. GET /api/graph/floats/{float_id}/stats ---")
    res5 = client.get(f"/api/graph/floats/{float_id}/stats")
    stats = res5.json()
    print(json.dumps(stats, indent=2))
    
    print("\n--- 6. GET /api/graph/search/cycles?min_temp=10&max_temp=15 ---")
    res6 = client.get("/api/graph/search/cycles?min_temp=10&max_temp=15")
    search = res6.json()
    print(json.dumps(search[:2], indent=2))
    if len(search) > 2:
         print(f"... and {len(search) - 2} more search results")

if __name__ == "__main__":
    run_tests()
