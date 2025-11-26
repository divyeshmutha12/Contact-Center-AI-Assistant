import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from utils.prompt_loader import load_prompt

from agents.mongo_mcp_client import MongoMCPClient

load_dotenv()
logger = logging.getLogger(__name__)
logger.info("Data extraction agent module initialized")


async def create_data_agent(model: ChatOpenAI):
    logger.info("Creating data extraction agent with MongoDB MCP tools...")

    mcp_client = MongoMCPClient()
    tools = await mcp_client.get_tools();
    logger.info(f"Got {len(tools)} tools from MCP: {[t.name for t in tools]}")

    SYSTEM_PROMPT = SYSTEM_PROMPT = load_prompt("prompts/data_agent_system.txt")


    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="data_extraction_agent"
    )

    logger.info("Data extraction agent successfully created.")
    return agent
