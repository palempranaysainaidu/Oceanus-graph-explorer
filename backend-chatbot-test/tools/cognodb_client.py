"""
CognoDB connection client (Neo4j-compatible Bolt + openCypher).
Credentials are read from environment variables — never hardcoded.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase, Driver
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    GraphDatabase = None
    Driver = None
    ServiceUnavailable = Exception
    AuthError = Exception

logger = logging.getLogger(__name__)

load_dotenv()
# Also load project root .env when running from backend-chatbot-test
_root_env = Path(__file__).resolve().parents[2] / ".env"
if _root_env.exists():
    load_dotenv(_root_env)


def _get_cognodb_uri() -> Optional[str]:
    return os.getenv("COGNODB_URI") or os.getenv("NEO4J_URI")


def _get_cognodb_user() -> Optional[str]:
    return os.getenv("COGNODB_USER") or os.getenv("NEO4J_USER")


def _get_cognodb_password() -> Optional[str]:
    return os.getenv("COGNODB_PASSWORD") or os.getenv("NEO4J_PASS")


def _uri_variants(base_uri: str) -> List[str]:
    """Try configured URI plus bolt+s / bolt+ssc variants (CognoDB custom CA)."""
    if "://" not in base_uri:
        return [base_uri]
    host = base_uri.split("://", 1)[-1]
    variants = [base_uri, f"bolt+s://{host}", f"bolt+ssc://{host}"]
    seen: set[str] = set()
    ordered: List[str] = []
    for u in variants:
        if u not in seen:
            seen.add(u)
            ordered.append(u)
    return ordered


class CognodbClient:
    """Thin wrapper around the official Neo4j Python driver for CognoDB."""

    def __init__(self):
        self.uri = _get_cognodb_uri()
        self.user = _get_cognodb_user()
        self.password = _get_cognodb_password()
        self._driver: Optional[Driver] = None
        self._last_error: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        return bool(self.uri and self.user and self.password)

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    @property
    def driver(self) -> Optional[Driver]:
        if self._driver is not None:
            return self._driver
        if not self.is_configured or GraphDatabase is None:
            self._last_error = "CognoDB credentials or neo4j driver not configured"
            return None
        for uri in _uri_variants(self.uri):
            try:
                candidate = GraphDatabase.driver(uri, auth=(self.user, self.password))
                candidate.verify_connectivity()
                self._driver = candidate
                self.uri = uri
                self._last_error = None
                logger.info("CognoDB connection established via %s", uri)
                return self._driver
            except AuthError as e:
                self._last_error = f"Authentication failed: {e}"
                logger.error(self._last_error)
                return None
            except ServiceUnavailable as e:
                self._last_error = f"CognoDB unreachable ({uri}): {e}"
                logger.warning(self._last_error)
            except Exception as e:
                self._last_error = f"Connection error ({uri}): {e}"
                logger.warning(self._last_error)
        self._driver = None
        return None

    def health_check(self) -> Dict[str, Any]:
        """Return connection status for health endpoints."""
        if not self.is_configured:
            return {
                "status": "unconfigured",
                "connected": False,
                "uri": self.uri,
                "message": "Set COGNODB_URI, COGNODB_USER, COGNODB_PASSWORD in .env",
            }
        driver = self.driver
        if driver is None:
            return {
                "status": "disconnected",
                "connected": False,
                "uri": self.uri,
                "message": self._last_error or "Unable to connect",
            }
        try:
            with driver.session() as session:
                record = session.run("RETURN 1 AS ok").single()
                ok = record and record["ok"] == 1
            return {
                "status": "connected",
                "connected": ok,
                "uri": self.uri,
                "message": "CognoDB is reachable",
            }
        except Exception as e:
            self._last_error = str(e)
            return {
                "status": "error",
                "connected": False,
                "uri": self.uri,
                "message": str(e),
            }

    def run_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a parameterized Cypher query and return plain dict rows."""
        driver = self.driver
        if driver is None:
            logger.warning("CognoDB query skipped — no connection")
            return []
        try:
            with driver.session() as session:
                result = session.run(query, **(params or {}))
                rows: List[Dict[str, Any]] = []
                for record in result:
                    row: Dict[str, Any] = {}
                    for key in record.keys():
                        value = record[key]
                        if hasattr(value, "_properties"):
                            row[key] = dict(value._properties)
                        elif isinstance(value, list):
                            row[key] = [
                                dict(v._properties) if hasattr(v, "_properties") else v
                                for v in value
                            ]
                        else:
                            row[key] = value
                    rows.append(row)
                return rows
        except Exception as e:
            logger.error(f"CognoDB query failed: {e}")
            self._last_error = str(e)
            return []

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
