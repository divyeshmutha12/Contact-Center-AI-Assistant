import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from utils.prompt_loader import load_prompt

from agents.mongo_mcp_client import MongoMCPClient

load_dotenv()
logger = logging.getLogger(__name__)
logger.info("Data extraction agent module initialized")


async def create_data_agent(model: ChatOpenAI, checkpointer: MemorySaver = None):
    """
    Create data extraction agent with MongoDB MCP tools.

    Args:
        model: The ChatOpenAI model to use
        checkpointer: Optional MemorySaver for conversation memory.
                      If provided, the agent will remember previous messages.
    """
    logger.info("Creating data extraction agent with MongoDB MCP tools...")

    mcp_client = MongoMCPClient()
    tools = await mcp_client.get_tools();
    logger.info(f"Got {len(tools)} tools from MCP: {[t.name for t in tools]}")

    SYSTEM_PROMPT = load_prompt("prompts/data_agent_system.txt")

    # create_agent returns an already-compiled CompiledStateGraph
    # Pass checkpointer directly if conversation memory is needed
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="data_extraction_agent",
        checkpointer=checkpointer
    )

    if checkpointer:
        logger.info("Data extraction agent created WITH conversation memory")
    else:
        logger.info("Data extraction agent created WITHOUT conversation memory")

    # CRITICAL: Keep MCP client reference alive to prevent connection closure
    # The tools have internal references to the client's SSE stream.
    # If the client is garbage collected, the stream closes and causes ClosedResourceError.
    agent._mcp_client = mcp_client

    logger.info("Data extraction agent successfully created.")
    return agent
