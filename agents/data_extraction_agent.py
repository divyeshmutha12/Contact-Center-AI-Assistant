import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends import FilesystemBackend
from utils.prompt_loader import load_prompt

from agents.mongo_mcp_client import get_shared_mcp_tools
from tools.excel_converter import create_excel_converter_tool

load_dotenv()
logger = logging.getLogger(__name__)
logger.info("Data extraction agent module initialized")

# ------------------------------------------------------
# Isolated Filesystem Configuration
# ------------------------------------------------------
# Base directory for all agent files
AGENT_FILES_ROOT = os.path.join(os.getcwd(), "agent_files")
SESSIONS_ROOT = os.path.join(AGENT_FILES_ROOT, "sessions")
os.makedirs(SESSIONS_ROOT, exist_ok=True)
logger.info(f"Agent files root: {AGENT_FILES_ROOT}")


def create_session_folder(session_id: str) -> str:
    """Create and return session-specific folder path."""
    session_folder = os.path.join(SESSIONS_ROOT, session_id)
    os.makedirs(session_folder, exist_ok=True)
    os.makedirs(os.path.join(session_folder, "outputs"), exist_ok=True)
    return session_folder


def create_data_agent(model: ChatOpenAI, session_id: str):
    """
    Create data extraction agent with session-specific filesystem.

    Args:
        model: The ChatOpenAI model to use
        session_id: Unique session ID (ws_id) for filesystem isolation
    """
    logger.info(f"Creating data extraction agent for session: {session_id}")

    # Create session-specific folder
    session_folder = create_session_folder(session_id)
    logger.info(f"Session folder: {session_folder}")

    # Get shared MCP tools (loaded once at startup)
    mcp_tools = get_shared_mcp_tools()
    logger.info(f"Using {len(mcp_tools)} shared MCP tools")

    # Create session-specific excel converter tool
    excel_tool = create_excel_converter_tool(session_id, session_folder)

    # Combine MCP tools with custom tools
    tools = mcp_tools + [excel_tool]
    logger.info(f"Total tools: {len(tools)}")

    SYSTEM_PROMPT = load_prompt("prompts/data_agent_system.txt")

    # Create agent with session-specific FilesystemBackend
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="data_extraction_agent",
        middleware=[
            FilesystemMiddleware(
                # Session-isolated filesystem
                backend=FilesystemBackend(root_dir=session_folder),
                tool_token_limit_before_evict=20000,
            ),
        ],
        checkpointer=True
    )

    logger.info(f"Data extraction agent created for session: {session_id}")
    return agent
