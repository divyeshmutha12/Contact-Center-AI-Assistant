import os
import re
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from agents.data_extraction_agent import create_data_agent
from agents.visualisation_agent import create_visualisation_agent
from utils.prompt_loader import load_prompt
import warnings

# Suppress MCP ping warnings
warnings.filterwarnings("ignore", message="Failed to validate notification")
warnings.filterwarnings("ignore", message="Input should be")
warnings.filterwarnings("ignore", message="Field required")

# Reduce noisy logs from internal libraries
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("mcp.client.streamable_http").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anyio").setLevel(logging.ERROR)
logging.getLogger("pydantic").setLevel(logging.ERROR)

# Add filter to suppress recurring MCP 'ping' validation warnings that
# appear when the MCP server sends lightweight SSE pings which the
# client's pydantic notification schema rejects (non-fatal but noisy).
class _IgnoreMCPPingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage() or ""
        except Exception:
            return True
        # Known noisy fragments observed in logs
        noisy_phrases = [
            "Failed to validate notification",
            "Input should be 'notifications/cancelled'",
            "Message was: method='ping'",
        ]
        for p in noisy_phrases:
            if p in msg:
                return False
        # Also filter messages that mention validation errors for ServerNotification
        if re.search(r"validation errors for ServerNotification", msg, re.IGNORECASE):
            return False
        return True

# Attach the filter to root and MCP-related loggers
logging.getLogger().addFilter(_IgnoreMCPPingFilter())
logging.getLogger("mcp").addFilter(_IgnoreMCPPingFilter())
logging.getLogger("mcp.client.streamable_http").addFilter(_IgnoreMCPPingFilter())

# Load environment variables
load_dotenv()

# Configure Logging
logger = logging.getLogger(__name__)
logger.info("Supervisor agent module loaded")

# Model configuration
model_name = os.getenv("OPENAI_MODEL", "gpt-5-mini")
temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("Missing OPENAI_API_KEY in .env")

FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("OPENAI_FALLBACK_MODELS", "gpt-4o-mini,gpt-4o,gpt-4").split(",")
    if m.strip()
]

# Shared resources (model and checkpointer can be shared across sessions)
_model = None
_checkpointer = MemorySaver(serde=JsonPlusSerializer())

# Session agents storage: {session_id: {"supervisor": agent, "data_agent": agent}}
_session_agents = {}


# ---------------------------------------------------------
# MODEL FUNCTIONS
# ---------------------------------------------------------

def get_model():
    """Get shared model instance."""
    global _model
    if _model is None:
        logger.info(f"Creating OpenAI model: {model_name}")
        _model = ChatOpenAI(model=model_name)
    return _model


def create_session_agent(session_id: str):
    """
    Create supervisor and data agents for a specific session.

    Args:
        session_id: Unique session ID (ws_id) for filesystem isolation

    Returns:
        Supervisor agent configured for this session
    """
    logger.info(f"Creating agents for session: {session_id}")

    model = get_model()

    # Create session-specific data agent
    data_agent = create_data_agent(model, session_id)

    # Create session-specific visualisation agent
    visualisation_agent = create_visualisation_agent(model, session_id)

    # Wrap data agent as a tool
    @tool
    async def query_database(request: str) -> str:
        """Query contact center database using natural language.

        Use this when the user asks about:
        - Call logs, call records, call history
        - Customer data, customer information
        - Agent performance, agent reports
        - Tickets, interactions, conversations
        - Any database-related queries
        - Counts, totals, statistics

        Input: Natural language query (e.g., 'show all calls from today')
        """
        result = await data_agent.ainvoke(
            {"messages": [{"role": "user", "content": request}]}
        )
        if "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            return getattr(last_msg, 'content', str(last_msg))
        return str(result)

    # Wrap visualisation agent as a tool
    @tool
    async def generate_visualisation(summary: str) -> str:
        """Generate Chart.js visualization from data summary.

        Use this when:
        - You have data that needs to be visualized as a chart
        - The user asks for charts, graphs, or visual representations
        - You want to create bar charts, pie charts, line graphs, etc.

        Input: A summary or dataset (can include markdown tables) that needs visualization
        Returns: JSON with summary and chart_data for Chart.js rendering
        """
        result = await visualisation_agent.ainvoke(
            {"messages": [{"role": "user", "content": summary}]}
        )
        if "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            return getattr(last_msg, 'content', str(last_msg))
        return str(result)

    SYSTEM_PROMPT = load_prompt("prompts/supervisor_system.txt")

    # Get summarization config
    summarization_model = os.getenv("SUMMARIZATION_MODEL", "gpt-5-mini")
    max_tokens = int(os.getenv("SUMMARIZATION_MAX_TOKENS", "2000"))
    messages_to_keep = int(os.getenv("SUMMARIZATION_MESSAGES_TO_KEEP", "5"))

    # Create supervisor agent
    supervisor = create_agent(
        model=model,
        tools=[query_database, generate_visualisation],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            SummarizationMiddleware(
                model=summarization_model,
                max_tokens_before_summary=max_tokens,
                messages_to_keep=messages_to_keep,
            ),
        ],
        checkpointer=_checkpointer,
        name="supervisor_agent",
    )

    # Store agents for this session
    _session_agents[session_id] = {
        "supervisor": supervisor,
        "data_agent": data_agent,
        "visualisation_agent": visualisation_agent
    }

    logger.info(f"Session {session_id} agents created successfully")
    return supervisor


def get_session_agent(session_id: str):
    """Get existing supervisor agent for a session."""
    if session_id not in _session_agents:
        return None
    return _session_agents[session_id]["supervisor"]


def cleanup_session(session_id: str):
    """Clean up agents when session ends."""
    if session_id in _session_agents:
        logger.info(f"Cleaning up session: {session_id}")
        del _session_agents[session_id]
