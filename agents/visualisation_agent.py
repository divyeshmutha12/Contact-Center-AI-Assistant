import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from utils.prompt_loader import load_prompt

load_dotenv()
logger = logging.getLogger(__name__)
logger.info("Visualisation agent module initialized")


def create_visualisation_agent(model: ChatOpenAI, session_id: str):
    """
    Create visualisation agent for generating Chart.js visualizations.

    Args:
        model: The ChatOpenAI model to use
        session_id: Unique session ID for tracking
    """
    logger.info(f"Creating visualisation agent for session: {session_id}")

    SYSTEM_PROMPT = load_prompt("prompts/visualisation_prompt.txt")

    agent = create_agent(
        model=model,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
        name="visualisation_agent",
        checkpointer=True
    )

    logger.info(f"Visualisation agent created for session: {session_id}")
    return agent
