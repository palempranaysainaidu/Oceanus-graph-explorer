#!/usr/bin/env python3
"""
Interactive Test Client for Oceanographic Data Analysis API
Provides a conversational interface to test the FastAPI multi-agent system
"""

import requests
import json
from typing import Optional
import sys
from datetime import datetime

class OceanographicAPIClient:
    """
    Client for testing the Oceanographic Data Analysis API
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.query_count = 0
        
    def create_session(self) -> bool:
        """Create a new session"""
        try:
            response = requests.post(f"{self.base_url}/session/create")
            response.raise_for_status()
            
            data = response.json()
            self.session_id = data["session_id"]
            print(f"\n✓ Session created: {self.session_id}")
            return True
            
        except requests.exceptions.ConnectionError:
            print(f"\n✗ ERROR: Cannot connect to {self.base_url}")
            print("  Make sure the FastAPI server is running:")
            print("  python main.py")
            return False
        except Exception as e:
            print(f"\n✗ Error creating session: {e}")
            return False
    
    def send_query(self, query: str) -> dict:
        """Send a query to the API"""
        try:
            headers = {}
            if self.session_id:
                headers["X-Session-ID"] = self.session_id
            
            response = requests.post(
                f"{self.base_url}/query",
                json={"query": query},
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Update session ID if returned
            if "session_id" in data and not self.session_id:
                self.session_id = data["session_id"]
            
            self.query_count += 1
            return data
            
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to API server"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_conversation_history(self) -> dict:
        """Get conversation history from current session"""
        try:
            if not self.session_id:
                return {"error": "No active session"}
            
            response = requests.get(
                f"{self.base_url}/session/{self.session_id}/history"
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            return {"error": str(e)}
    
    def delete_session(self) -> bool:
        """Delete current session"""
        try:
            if not self.session_id:
                return False
            
            response = requests.delete(
                f"{self.base_url}/session/{self.session_id}"
            )
            response.raise_for_status()
            
            print(f"\n✓ Session deleted: {self.session_id}")
            self.session_id = None
            self.query_count = 0
            return True
            
        except Exception as e:
            print(f"\n✗ Error deleting session: {e}")
            return False
    
    def print_response(self, result: dict):
        """Pretty print API response"""
        print("\n" + "="*70)
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
            return
        
        # Print response
        print(f"\n{result['response']}")
        
        # Print metadata
        print("\n" + "-"*70)
        print(f"📊 Agents Used: {', '.join(result.get('agents_used', [])) or 'None (direct LLM response)'}")
        print(f"⏱️  Execution Time: {result.get('execution_time', 0):.2f}s")
        print(f"🔑 Session ID: {result.get('session_id', 'N/A')}")
        print("="*70)

def print_header():
    """Print welcome header"""
    print("\n" + "="*70)
    print("🌊 OCEANOGRAPHIC DATA ANALYSIS - INTERACTIVE TEST CLIENT")
    print("="*70)
    print("\nCommands:")
    print("  /help      - Show available commands")
    print("  /history   - View conversation history")
    print("  /new       - Start a new session")
    print("  /info      - Show session information")
    print("  /quit      - Exit the client")
    print("\nExample Queries:")
    print("  - Hello, what can you do?")
    print("  - Show me temperature data for float 1901442")
    print("  - List all floats in the Arabian Sea")
    print("  - What is salinity?")
    print("="*70 + "\n")

def print_help():
    """Print help information"""
    print("\n" + "="*70)
    print("📖 HELP - AVAILABLE COMMANDS")
    print("="*70)
    print("\nCommands:")
    print("  /help      - Show this help message")
    print("  /history   - View full conversation history for current session")
    print("  /new       - Delete current session and start a new one")
    print("  /info      - Show current session information")
    print("  /quit      - Exit the client and delete session")
    print("\nQuery Types:")
    print("\n  1. Conversational:")
    print("     - Hello / Hi / Thanks")
    print("     - What can you do?")
    print("     - What is [oceanographic term]?")
    print("\n  2. Data Queries (CockroachDB):")
    print("     - Show me temperature data for float [ID]")
    print("     - List all floats in [region]")
    print("     - Get measurements from the Arabian Sea")
    print("\n  3. Metadata Queries (Neo4j):")
    print("     - What parameters does float [ID] measure?")
    print("     - Show me all regions")
    print("     - How many floats are in the Bay of Bengal?")
    print("\n  4. Semantic Queries (Pinecone):")
    print("     - Find similar patterns to [description]")
    print("     - Search for temperature inversions")
    print("="*70 + "\n")

def main():
    """Main interactive loop"""
    # Initialize client
    client = OceanographicAPIClient()
    
    # Print header
    print_header()
    
    # Create initial session
    if not client.create_session():
        print("\n❌ Failed to connect to API. Exiting...")
        sys.exit(1)
    
    print("\n💬 Ready! Type your query or /help for commands.\n")
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                command = user_input.lower()
                
                if command == "/quit":
                    print("\n👋 Goodbye!")
                    client.delete_session()
                    break
                
                elif command == "/help":
                    print_help()
                    continue
                
                elif command == "/history":
                    print("\n📜 Fetching conversation history...")
                    history = client.get_conversation_history()
                    
                    if "error" in history:
                        print(f"❌ Error: {history['error']}")
                    else:
                        print("\n" + "="*70)
                        print(f"CONVERSATION HISTORY ({history['message_count']} messages)")
                        print("="*70)
                        
                        for msg in history['conversation_history']:
                            role = "You" if msg['role'] == 'user' else "Assistant"
                            timestamp = msg['timestamp'][:19]  # Remove microseconds
                            print(f"\n[{timestamp}] {role}:")
                            print(f"{msg['content'][:200]}...")  # Truncate long messages
                        print("\n" + "="*70 + "\n")
                    continue
                
                elif command == "/new":
                    print("\n🔄 Starting new session...")
                    client.delete_session()
                    client.create_session()
                    print("Ready for new conversation!\n")
                    continue
                
                elif command == "/info":
                    print("\n" + "="*70)
                    print("📋 SESSION INFORMATION")
                    print("="*70)
                    print(f"Session ID: {client.session_id or 'None'}")
                    print(f"Queries Made: {client.query_count}")
                    print(f"API URL: {client.base_url}")
                    print("="*70 + "\n")
                    continue
                
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type /help for available commands\n")
                    continue
            
            # Send query to API
            print("\n🤔 Processing query...")
            result = client.send_query(user_input)
            
            # Print response
            client.print_response(result)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            client.delete_session()
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}\n")

if __name__ == "__main__":
    main()