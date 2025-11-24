import os
import logging
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from agents.data_extraction_agent import create_data_agent
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


# ---------------------------------------------------------
# 🔥 SMART DB QUERY DETECTION
# ---------------------------------------------------------
def is_db_query(text: str) -> bool:
    """
    Smart detection for routing queries to MongoDB.
    Works even when user never mentions words like "find", "query", "collection".
    """

    if not text:
        return False

    t = text.lower()

    # 1️⃣ Detect dates → strong indicator of querying call logs / tickets
    date_patterns = [
        r"\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}\b",    # 08-09-2025
        r"\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b",      # 2025-09-08
    ]
    if any(re.search(p, t) for p in date_patterns):
        if any(w in t for w in ["call", "calls", "interaction", "log", "logs"]):
            return True

    # 2️⃣ Phone numbers or IDs
    if re.search(r"\b\d{10,12}\b", t):
        return True

    # 3️⃣ Count queries
    if any(x in t for x in ["how many", "number of", "count", "total"]):
        if any(e in t for e in ["call", "calls", "ticket", "tickets", "customer"]):
            return True

    # 4️⃣ Status + entity detection
    statuses = ["success", "successful", "completed", "failed", "missed", "answered"]
    entities = ["call", "calls", "record", "records", "customer", "ticket", "interaction"]
    if any(s in t for s in statuses) and any(e in t for e in entities):
        return True

    # 5️⃣ Mention of call logs or customer data
    if any(w in t for w in ["call log", "call logs", "customer", "customers"]):
        return True

    return False


# ---------------------------------------------------------
# MODEL FUNCTIONS
# ---------------------------------------------------------

def get_model():
    global _model
    if _model is None:
        logger.info(f"Creating OpenAI model: {model_name}")
        _model = ChatOpenAI(model=model_name, temperature=temperature)
    return _model


async def get_data_agent():
    global _data_agent
    if _data_agent is None:
        logger.info("Creating data extraction agent...")
        _data_agent = await create_data_agent(get_model())
    return _data_agent


async def get_supervisor_agent():

    global _supervisor_agent
    if _supervisor_agent is not None:
        return _supervisor_agent

    logger.info("Building supervisor agent...")

    model = get_model()
    data_agent = await get_data_agent()

    SYSTEM_PROMPT = """
You are a routing supervisor.
DO NOT access MongoDB yourself.

RULES:
1. If the user request requires database access → forward it EXACTLY to the data agent.
2. Do NOT rewrite, modify, or summarize DB queries.
3. For non-database queries, answer normally using the supervisor model.
"""

    supervisor_graph = create_supervisor(
        agents=[],
        model=model,
        system_prompt=SYSTEM_PROMPT
    ).compile()

    logger.info("Supervisor agent built successfully")

    async def _rotate_to_model(new_model: str):
        global model_name, _model, _data_agent, _supervisor_agent
        logger.info(f"Rotating model to fallback: {new_model}")
        model_name = new_model
        _model = None
        _data_agent = None
        _supervisor_agent = None

    # ---------------------------------------------------------
    # SUPERVISOR PROXY — routing logic
    # ---------------------------------------------------------
    class SupervisorProxy:

        def __init__(self, sv, data_agent, model):
            self._supervisor = sv
            self._data_agent = data_agent
            self._model = model

        async def ainvoke(self, message, config=None):

            # Extract the user message content
            if isinstance(message, dict) and "messages" in message:
                msgs = message["messages"]
                user_text = msgs[-1]["content"] if msgs else ""
            elif isinstance(message, str):
                user_text = message
            else:
                user_text = str(message)

            # SMART DETECTION — NEW LOGIC
            requires_db = is_db_query(user_text)

            try:
                if requires_db:
                    logger.info("Routing → DATA AGENT (detected DB query)")
                    return await self._data_agent.ainvoke(message)

                else:
                    logger.info("Routing → SUPERVISOR MODEL (non-DB query)")
                    return await self._supervisor.ainvoke(message, config=config)

            except Exception as e:
                msg = str(e).lower()

                if "model_not_found" in msg or "does not have access" in msg:
                    # Attempt fallbacks
                    for fm in FALLBACK_MODELS:
                        if fm == model_name:
                            continue
                        try:
                            await _rotate_to_model(fm)
                            new_model = get_model()
                            new_data_agent = await get_data_agent()
                            new_supervisor = create_supervisor(
                                agents=[], model=new_model, system_prompt=SYSTEM_PROMPT
                            ).compile()

                            self._model = new_model
                            self._data_agent = new_data_agent
                            self._supervisor = new_supervisor

                            logger.info(f"Retrying with fallback {fm}")
                            if requires_db:
                                return await self._data_agent.ainvoke(message)
                            return await self._supervisor.ainvoke(message)

                        except Exception:
                            continue

                raise e

    _supervisor_agent = SupervisorProxy(supervisor_graph, data_agent, model)
    return _supervisor_agent


supervisor_agent = None
