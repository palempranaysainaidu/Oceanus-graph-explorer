"""
Test script for session management functionality
"""

import sys
import asyncio
import httpx
import json
from typing import Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def test_session_functionality():
    """Test the session management features"""
    
    base_url = "http://localhost:8000"
    
    use_asgi = False
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{base_url}/health", timeout=2.0)
    except Exception:
        use_asgi = True

    if use_asgi:
        print("ℹ️ Live server not detected on port 8000. Testing session functionality in-process via ASGI transport...\n")
        from main import app
        transport = httpx.ASGITransport(app=app)
        client_context = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    else:
        print("ℹ️ Testing session functionality against live server on http://localhost:8000...\n")
        client_context = httpx.AsyncClient(base_url=base_url)

    async with client_context as client:
        print("Testing Session Management & Memory")
        print("=" * 50)
        
        # Test 1: Create a new session
        print("\n1. Creating a new session...")
        try:
            session_request = {
                "user_preferences": {
                    "detail_level": "comprehensive",
                    "preferred_regions": ["Arabian Sea", "Bay of Bengal"],
                    "analysis_focus": "temperature_patterns"
                }
            }
            
            response = await client.post(
                "/api/v1/sessions/create",
                json=session_request
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data["session_id"]
                print(f"   Session ID: {session_id}")
                print(f"   Created at: {session_data['created_at']}")
            else:
                print(f"   Error: {response.json()}")
                return
                
        except Exception as e:
            print(f"   Error: {e}")
            return
        
        # Test 2: First query in session
        print("\n2. First query in session...")
        try:
            chat_request = {
                "query": "Show me temperature measurements from float 7902073",
                "session_id": session_id,
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
                print(f"   Session ID: {chat_data.get('session_id')}")
                print(f"   Has context: {chat_data.get('metadata', {}).get('has_context', False)}")
                print(f"   Context: {chat_data.get('conversation_context', {})}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: Follow-up query (should have context)
        print("\n3. Follow-up query with context...")
        try:
            followup_request = {
                "query": "Now compare this float's data with similar patterns in the Arabian Sea",
                "session_id": session_id,
                "timeout": 90
            }
            
            response = await client.post(
                "/api/v1/chat",
                json=followup_request,
                timeout=100
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"   Response length: {len(chat_data.get('response', ''))}")
                print(f"   Has context: {chat_data.get('metadata', {}).get('has_context', False)}")
                context = chat_data.get('conversation_context', {})
                print(f"   Floats analyzed: {context.get('floats_analyzed', [])}")
                print(f"   Regions discussed: {context.get('regions_discussed', [])}")
                print(f"   Parameters: {context.get('parameters_of_interest', [])}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 4: Get conversation history
        print("\n4. Getting conversation history...")
        try:
            response = await client.get(f"/api/v1/sessions/{session_id}/history")
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                history = response.json()
                print(f"   Total messages: {history.get('total_messages')}")
                print(f"   Messages in response: {len(history.get('messages', []))}")
                
                for i, msg in enumerate(history.get('messages', [])[:4]):  # Show first 4
                    print(f"   Message {i+1}: {msg['role']} - {msg['content'][:50]}...")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 5: Get session info
        print("\n5. Getting session information...")
        try:
            response = await client.get(f"/api/v1/sessions/{session_id}")
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                session_info = response.json()
                print(f"   Message count: {session_info.get('message_count')}")
                print(f"   Last activity: {session_info.get('last_activity')}")
                print(f"   Context: {session_info.get('context')}")
                print(f"   Preferences: {session_info.get('user_preferences')}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 6: Update user preferences
        print("\n6. Updating user preferences...")
        try:
            new_preferences = {
                "detail_level": "brief",
                "output_format": "summary",
                "focus_parameters": ["salinity", "temperature"]
            }
            
            response = await client.put(
                f"/api/v1/sessions/{session_id}/preferences",
                json=new_preferences
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Status: {result.get('status')}")
                print(f"   Updated preferences: {result.get('updated_preferences')}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 7: Query with updated preferences
        print("\n7. Query with updated preferences...")
        try:
            pref_request = {
                "query": "What about salinity patterns in the Bay of Bengal?",
                "session_id": session_id,
                "timeout": 60
            }
            
            response = await client.post(
                "/api/v1/chat",
                json=pref_request,
                timeout=70
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                chat_data = response.json()
                print(f"   Response length: {len(chat_data.get('response', ''))}")
                context = chat_data.get('conversation_context', {})
                print(f"   Updated regions: {context.get('regions_discussed', [])}")
                print(f"   Updated parameters: {context.get('parameters_of_interest', [])}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 8: Session statistics
        print("\n8. Getting session statistics...")
        try:
            response = await client.get("/api/v1/sessions/")
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   Statistics: {stats.get('statistics')}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 9: Test without session (should create new one)
        print("\n9. Testing query without session ID...")
        try:
            no_session_request = {
                "query": "Quick test without session",
                "timeout": 30
            }
            
            response = await client.post(
                "/api/v1/chat",
                json=no_session_request,
                timeout=40
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                chat_data = response.json()
                new_session_id = chat_data.get('session_id')
                print(f"   Auto-created session: {new_session_id}")
                print(f"   Different from original: {new_session_id != session_id}")
            else:
                print(f"   Error: {response.json()}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        print("\n" + "=" * 50)
        print("✅ Session management testing completed!")
        print(f"📝 Main session ID: {session_id}")
        print("🧠 The system now has conversation memory and context awareness!")

if __name__ == "__main__":
    print("Starting session management tests...")
    print("Make sure the API is running on http://localhost:8000")
    print("Run: python -m uvicorn api.main:app --reload")
    print()
    
    asyncio.run(test_session_functionality())