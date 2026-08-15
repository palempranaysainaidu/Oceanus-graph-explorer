"""
Tool factory and common interfaces for the Argo data tools.
Provides a unified interface to access all tools and handle initialization/cleanup.
"""

from typing import Optional
from .cockroach_tool import CockroachDBTool
from .neo4j_tool import Neo4jTool
from .pinecone_tool import PineconeTool

class ArgoToolFactory:
    """Factory class to manage all Argo data tools"""
    
    def __init__(self):
        self._cockroach_tool: Optional[CockroachDBTool] = None
        self._neo4j_tool: Optional[Neo4jTool] = None
        self._pinecone_tool: Optional[PineconeTool] = None

    @property
    def cockroach(self) -> CockroachDBTool:
        """Get CockroachDB tool instance"""
        if self._cockroach_tool is None:
            self._cockroach_tool = CockroachDBTool()
        return self._cockroach_tool

    @property
    def neo4j(self) -> Neo4jTool:
        """Get Neo4j tool instance"""
        if self._neo4j_tool is None:
            self._neo4j_tool = Neo4jTool()
        return self._neo4j_tool

    @property
    def pinecone(self) -> PineconeTool:
        """Get Pinecone tool instance"""
        if self._pinecone_tool is None:
            self._pinecone_tool = PineconeTool()
        return self._pinecone_tool

    def close_all(self):
        """Close all tool connections"""
        if self._cockroach_tool:
            self._cockroach_tool.close()
            self._cockroach_tool = None
            
        if self._neo4j_tool:
            self._neo4j_tool.close()
            self._neo4j_tool = None
            
        if self._pinecone_tool:
            self._pinecone_tool.close()
            self._pinecone_tool = None