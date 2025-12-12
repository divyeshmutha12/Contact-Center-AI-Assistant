"""
Contact Center Agent System
Multi-agent system using LangGraph and MongoDB MCP

Session-based architecture:
- Each WebSocket connection gets its own agent instance
- MCP tools are shared across all sessions
"""

__version__ = "1.0.0"

from agents.mongo_mcp_client import MongoMCPClient, init_shared_mcp_tools, get_shared_mcp_tools
from agents.data_extraction_agent import create_data_agent
from agents.supervisor_agent import create_session_agent, get_session_agent, cleanup_session

__all__ = [
    "MongoMCPClient",
    "init_shared_mcp_tools",
    "get_shared_mcp_tools",
    "create_data_agent",
    "create_session_agent",
    "get_session_agent",
    "cleanup_session",
]
