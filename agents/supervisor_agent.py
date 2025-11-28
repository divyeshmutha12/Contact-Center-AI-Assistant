import os
import re
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from agents.data_extraction_agent import create_data_agent
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

# Lazy instances
_model = None
_data_agent = None
_supervisor_agent = None

# Checkpointer for conversation memory (short-term memory)
# This enables the bot to remember previous messages in the same conversation
# Using JsonPlusSerializer to properly serialize LangChain message types (ToolMessage, etc.)
_checkpointer = MemorySaver(serde=JsonPlusSerializer())


# ---------------------------------------------------------
# MODEL FUNCTIONS
# ---------------------------------------------------------

def get_model():
    global _model
    if _model is None:
        logger.info(f"Creating OpenAI model: {model_name}")
        _model = ChatOpenAI(model=model_name )
    return _model


async def get_data_agent():
    global _data_agent
    if _data_agent is None:
        logger.info("Creating data extraction agent...")
        # Pass the shared checkpointer so data agent also has conversation memory
        _data_agent = await create_data_agent(get_model(), checkpointer=_checkpointer)
    return _data_agent


async def get_supervisor_agent():
    """
    Build supervisor agent following official langgraph-supervisor pattern.
    The supervisor LLM intelligently routes to data_agent when DB access is needed.
    """
    global _supervisor_agent
    if _supervisor_agent is not None:
        return _supervisor_agent

    logger.info("Building supervisor agent...")

    model = get_model()
    data_agent = await get_data_agent()

    SYSTEM_PROMPT = load_prompt("prompts/supervisor_system.txt")

    # Official pattern: Pass agents to create_supervisor
    # The supervisor LLM will automatically get handoff tools to delegate to data_agent
    _supervisor_agent = create_supervisor(
        agents=[data_agent],  # Pass the data agent here!
        model=model,
        prompt=SYSTEM_PROMPT,
        output_mode="full_history"  # Include full conversation history
    ).compile(checkpointer=_checkpointer)

    logger.info("Supervisor agent built successfully with conversation memory")
    logger.info(f"Supervisor can delegate to: {data_agent.name if hasattr(data_agent, 'name') else 'data_agent'}")

    return _supervisor_agent


supervisor_agent = None
