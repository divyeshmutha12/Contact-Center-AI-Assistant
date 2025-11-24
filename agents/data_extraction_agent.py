import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from agents.mongo_mcp_client import MongoMCPClient

load_dotenv()
logger = logging.getLogger(__name__)
logger.info("Data extraction agent module initialized")


async def create_data_agent(model: ChatOpenAI):
    logger.info("Creating data extraction agent with MongoDB MCP tools...")

    mcp_client = MongoMCPClient()
    tools = await mcp_client.get_tools();
    logger.info(f"Got {len(tools)} tools from MCP: {[t.name for t in tools]}")

    SYSTEM_PROMPT = """
You are a MongoDB Data Extraction Agent using MCP tools.

Your behavior MUST follow these rules:

1. ALWAYS automatically detect the correct collection.
   - First call `list-collections`
   - Then for each returned collection, call `collection-schema`
   - Compare field names to the user's query
   - Pick the collection with the closest schema match

2. NEVER ask the user:
   - “Which database?”
   - “Which collection?”
   - “Provide schema”
   - “Specify collection name”

3. ALWAYS think step-by-step internally:
   a. list collections  
   b. fetch schemas  
   c. analyze which collection matches  
   d. run the correct MCP tool (`find`, `aggregate`, `count`, etc.)  
   e. produce the final answer

4. ALL collection access must be dynamic — 
   you must handle ANY number of collections (like 18).

5. Use multiple MCP tool calls when needed.

6. NEVER guess the collection without checking schemas.

7. ALWAYS ensure results are accurate.

8. IMPORTANT:
   - NEVER reveal tool calls, schemas, reasoning, or chain-of-thought.
   - NEVER show internal steps.
   - ONLY output the final plain-language answer clearly and briefly.
"""

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        name="data_extraction_agent"
    )

    logger.info("Data extraction agent successfully created.")
    return agent
