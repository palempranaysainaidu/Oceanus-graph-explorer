from fastapi.testclient import TestClient
import json

from main import app

client = TestClient(app)

def run_failure_test():
    print("--- 7. GET /api/graph/floats (FAILURE TEST) ---")
    res = client.get("/api/graph/floats")
    print(f"Status Code: {res.status_code}")
    print("Response JSON:")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    run_failure_test()
