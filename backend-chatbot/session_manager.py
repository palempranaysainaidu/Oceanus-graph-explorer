import uuid
import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading
import logging
import shutil

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Manages user sessions and conversation history with file-based storage
    """
    def __init__(self, expiry_minutes: int = 30):
        self.sessions_dir = "/sessions"  # Directory to store session files
        self.expiry_minutes = expiry_minutes
        self.lock = threading.Lock()

        # Create sessions directory if it doesn't exist
        os.makedirs(self.sessions_dir, exist_ok=True)

        # Start cleanup thread
        self._start_cleanup_thread()

    def _get_session_path(self, session_id: str) -> str:
        """Get the file path for a session"""
        return os.path.join(self.sessions_dir, f"{session_id}.json")

    def create_session(self) -> str:
        """
        Create a new session and return session ID
        """
        session_id = str(uuid.uuid4())
        session_path = self._get_session_path(session_id)

        with self.lock:
            session_data = {
                "created_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "conversation_history": []
            }

            # Save session to file
            with open(session_path, 'w') as f:
                json.dump(session_data, f)

        logger.info(f"Created session: {session_id}")
        return session_id

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session
        """
        session_path = self._get_session_path(session_id)

        with self.lock:
            if not os.path.exists(session_path):
                logger.warning(f"Session {session_id} not found")
                raise ValueError(f"Session {session_id} not found or expired")

            # Load session from file
            with open(session_path, 'r') as f:
                session_data = json.load(f)

            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()

            # Save updated session
            with open(session_path, 'w') as f:
                json.dump(session_data, f)

            return session_data["conversation_history"]

    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to session conversation history
        """
        session_path = self._get_session_path(session_id)

        with self.lock:
            if not os.path.exists(session_path):
                raise ValueError(f"Session {session_id} not found")

            # Load session from file
            with open(session_path, 'r') as f:
                session_data = json.load(f)

            # Add new message
            session_data["conversation_history"].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })

            # Update last accessed time
            session_data["last_accessed"] = datetime.now().isoformat()

            # Save updated session
            with open(session_path, 'w') as f:
                json.dump(session_data, f)

    def delete_session(self, session_id: str):
        """
        Delete a session
        """
        session_path = self._get_session_path(session_id)

        with self.lock:
            if os.path.exists(session_path):
                os.remove(session_path)
                logger.info(f"Deleted session: {session_id}")
            else:
                raise ValueError(f"Session {session_id} not found")

    def cleanup_expired_sessions(self):
        """
        Remove expired sessions
        """
        with self.lock:
            now = datetime.now()
            expired_sessions = []

            # Get all session files
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith(".json"):
                    session_id = filename[:-5]  # Remove .json extension
                    session_path = self._get_session_path(session_id)

                    # Load session data
                    with open(session_path, 'r') as f:
                        session_data = json.load(f)

                    last_accessed = datetime.fromisoformat(session_data["last_accessed"])
                    if now - last_accessed > timedelta(minutes=self.expiry_minutes):
                        expired_sessions.append(session_path)

            # Delete expired sessions
            for session_path in expired_sessions:
                session_id = os.path.basename(session_path)[:-5]  # Extract session_id
                os.remove(session_path)
                logger.info(f"Expired session removed: {session_id}")

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    def cleanup_all(self):
        """
        Clear all sessions (for shutdown)
        """
        with self.lock:
            if os.path.exists(self.sessions_dir):
                shutil.rmtree(self.sessions_dir)
                os.makedirs(self.sessions_dir, exist_ok=True)  # Recreate directory
                logger.info("All sessions cleared")

    def _start_cleanup_thread(self):
        """
        Start background thread for cleaning up expired sessions
        """
        def cleanup_loop():
            import time
            while True:
                time.sleep(300)  # Check every 5 minutes
                try:
                    self.cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        logger.info("Session cleanup thread started")
