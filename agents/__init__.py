"""
Contact Center Agent System
Multi-agent system using LangGraph and MongoDB MCP
"""

__version__ = "1.0.0"

from agents.mongo_mcp_client import MongoMCPClient
from agents.data_extraction_agent import create_data_agent
from agents.supervisor_agent import get_supervisor_agent

__all__ = [
    "MongoMCPClient",
    "create_data_agent",
    "get_supervisor_agent",
]
