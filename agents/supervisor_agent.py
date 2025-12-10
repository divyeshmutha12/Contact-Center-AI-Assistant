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
    Build supervisor agent using official langchain.agents.create_agent pattern.

    Features:
    - SummarizationMiddleware: Automatically summarizes old messages to reduce latency
    - Data agent wrapped as tool: Supervisor routes to data_agent for DB queries
    - Checkpointer: Maintains conversation memory across requests
    """
    global _supervisor_agent, _data_agent
    if _supervisor_agent is not None:
        return _supervisor_agent

    logger.info("Building supervisor agent with SummarizationMiddleware...")

    model = get_model()

    # Create data agent (sub-agent)
    data_agent = await get_data_agent()
    _data_agent = data_agent  # Keep reference to prevent garbage collection

    # Wrap data agent as a tool (official supervisor pattern)
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
        # Invoke the data agent asynchronously
        result = await data_agent.ainvoke(
            {"messages": [{"role": "user", "content": request}]}
        )

        # Return the last message content
        if "messages" in result and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            return getattr(last_msg, 'content', str(last_msg))
        return str(result)

    SYSTEM_PROMPT = load_prompt("prompts/supervisor_system.txt")

    # Get summarization config from environment variables
    summarization_model = os.getenv("SUMMARIZATION_MODEL", "gpt-5-mini")
    max_tokens = int(os.getenv("SUMMARIZATION_MAX_TOKENS", "2000"))
    messages_to_keep = int(os.getenv("SUMMARIZATION_MESSAGES_TO_KEEP", "5"))

    # Create supervisor with SummarizationMiddleware for memory optimization
    # This reduces latency by summarizing old messages instead of sending all
    _supervisor_agent = create_agent(
        model=model,
        tools=[query_database],
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

    logger.info("Supervisor agent built successfully with:")
    logger.info(f"  - SummarizationMiddleware (model: {summarization_model}, max_tokens: {max_tokens}, keep: {messages_to_keep} messages)")
    logger.info("  - Conversation memory via checkpointer")
    logger.info("  - query_database tool for data agent delegation")

    return _supervisor_agent


# Keep reference to data agent to prevent garbage collection
_data_agent = None
supervisor_agent = None
