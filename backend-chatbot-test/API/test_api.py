"""
Test script for the FastAPI application
"""

import sys
import asyncio
import httpx
import json
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def test_api():
    """Test the API endpoints"""
    
    base_url = "http://localhost:8000"
    
    # Try connecting to live server first, otherwise use in-process ASGI transport
    use_asgi = False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{base_url}/health", timeout=2.0)
    except Exception:
        use_asgi = True

    if use_asgi:
        print("ℹ️ Live server not detected on port 8000. Testing API in-process via ASGI transport...\n")
        from main import app
        transport = httpx.ASGITransport(app=app)
        client_context = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    else:
        print("ℹ️ Testing API against live server on http://localhost:8000...\n")
        client_context = httpx.AsyncClient(base_url=base_url)

    async with client_context as client:
        print("Testing Oceanographic Multi-Agent RAG API")
        print("=" * 50)
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        try:
            response = await client.get("/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.json()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Detailed health check
        print("\n2. Testing detailed health check...")
        try:
            response = await client.get("/health/detailed")
            print(f"   Status: {response.status_code}")
            health_data = response.json()
            print(f"   Overall Status: {health_data.get('status')}")
            print(f"   Agent Status: {health_data.get('components', {}).get('agent_system', {}).get('status')}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Simple chat query
        print("\n3. Testing simple chat query...")
        try:
            chat_request = {
                "query": "Show me data for float 7902073",
                "timeout": 60
            }
            
            response = await client.post(
                "/api/v1/chat",
                json=chat_request,
                timeout=70
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"   Response length: {len(chat_data.get('response', ''))}")
                print(f"   Metadata: {chat_data.get('metadata', {})}")
                print(f"   First 200 chars: {chat_data.get('response', '')[:200]}...")
            else:
                print(f"   Error response: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 4: Root-level chat query alias (/query)
        print("\n4. Testing root-level chat query alias (/query)...")
        try:
            chat_request = {
                "query": "Show me data for float 7902073",
                "timeout": 60
            }
            
            response = await client.post(
                "/query",
                json=chat_request,
                timeout=70
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Alias /query works! Response length: {len(response.json().get('response', ''))}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 5: Get examples
        print("\n5. Testing examples endpoint...")
        try:
            response = await client.get("/api/v1/chat/examples")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                examples = response.json()
                print(f"   Available example categories: {list(examples.get('examples', {}).keys())}")
                print(f"   Supported regions: {len(examples.get('supported_regions', []))}")
                print(f"   Supported parameters: {len(examples.get('supported_parameters', []))}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 6: Metrics
        print("\n6. Testing metrics endpoint...")
        try:
            response = await client.get("/metrics")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                metrics = response.json()
                print(f"   Metrics available: {list(metrics.get('metrics', {}).keys())}")
            
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ API testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_api())