from flask import Blueprint, request, jsonify, send_file
import asyncio
import threading
import logging
import re
import json
import io
import pandas as pd
from datetime import datetime
import time

from routes.auth import SESSIONS

# Langfuse for observability and tracing
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

# MCP connection error patterns that should trigger retry
MCP_CONNECTION_ERROR_PATTERNS = [
    "connection string is not valid",
    "connect to a MongoDB instance",
    "ClosedResourceError",
    "BrokenResourceError",
    "connection refused",
    "connection reset",
    "not connected",
]


def is_mcp_connection_error(error_msg: str) -> bool:
    """Check if the error is related to MCP connection issues."""
    error_lower = error_msg.lower()
    return any(pattern.lower() in error_lower for pattern in MCP_CONNECTION_ERROR_PATTERNS)

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")
# Initialize Langfuse (reads LANGFUSE_* env vars automatically)
try:
    Langfuse()
    logger.info("Langfuse initialized successfully")
except Exception as e:
    logger.warning(f"Langfuse initialization failed (tracing disabled): {e}")

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def extract_best_response(messages: list) -> str:
    """
    Pick the best response from messages.
    Logic:
    1. First, find the LAST HumanMessage (user's latest query)
    2. Only look at AIMessages AFTER that HumanMessage
    3. Among those, prefer JSON without _id, else return text response

    This prevents returning old JSON data when the latest response is text.
    """
    from langchain_core.messages import AIMessage, HumanMessage

    # Step 1: Find index of last HumanMessage
    last_human_idx = -1
    for i, msg in enumerate(messages):
        if isinstance(msg, HumanMessage):
            last_human_idx = i

    # Step 2: Only consider messages AFTER the last HumanMessage
    if last_human_idx >= 0:
        recent_messages = messages[last_human_idx + 1:]
    else:
        recent_messages = messages

    # Step 3: Find best response from recent messages only
    formatted_response = None  # JSON without _id (Data Agent)
    last_text_response = None  # Fallback for non-report queries

    for msg in reversed(recent_messages):
        if not isinstance(msg, AIMessage):
            continue

        content = getattr(msg, 'content', '')
        if not content or not content.strip():
            continue

        # Skip transfer messages
        if 'transferring' in content.lower():
            continue

        # Check if it's a JSON array
        if content.strip().startswith('['):
            try:
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    # Check if it has _id (raw MongoDB) or not (formatted)
                    if '_id' not in data[0]:
                        # This is the Data Agent's formatted response - USE THIS
                        formatted_response = content
                        logger.info("Found formatted response (no _id) from Data Agent")
                        break  # Best match found
            except json.JSONDecodeError:
                pass

        # Keep track of last text response as fallback
        if last_text_response is None:
            last_text_response = content

    # Return formatted response if found, otherwise fallback
    if formatted_response:
        return formatted_response
    if last_text_response:
        return last_text_response

    # Absolute fallback
    if recent_messages:
        last_msg = recent_messages[-1]
        return getattr(last_msg, 'content', str(last_msg))
    return ""


# ------------------------------------------------------
# Persistent Event Loop for Async Operations
# ------------------------------------------------------
# We need a single persistent event loop to keep MCP connections alive
# across multiple requests. Creating new loops (via asyncio.run())
# would break the MCP SSE stream.

_loop = None
_loop_thread = None
_supervisor = None
_initialized = False
_init_lock = threading.Lock()


def _start_background_loop(loop):
    """Run the event loop in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_event_loop():
    """Get or create the persistent event loop."""
    global _loop, _loop_thread

    if _loop is None:
        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(target=_start_background_loop, args=(_loop,), daemon=True)
        _loop_thread.start()

    return _loop


def run_async(coro):
    """Run an async coroutine in the persistent event loop."""
    loop = get_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()  # No timeout - wait until complete


def initialize_supervisor(force_reinit: bool = False):
    """
    Initialize the supervisor agent once, or reinitialize if forced.

    Args:
        force_reinit: If True, force reinitialization even if already initialized.
                      Used when MCP connection errors occur.
    """
    global _supervisor, _initialized

    with _init_lock:
        if _initialized and not force_reinit:
            return _supervisor

        try:
            if force_reinit:
                logger.warning("Force reinitializing supervisor agent due to connection error...")
                _supervisor = None
                _initialized = False
                # Reset the cached instances in supervisor_agent module
                try:
                    import agents.supervisor_agent as sup_module
                    sup_module._supervisor_agent = None
                    sup_module._data_agent = None
                    sup_module._model = None
                except Exception as e:
                    logger.warning(f"Could not reset supervisor module: {e}")

            logger.info("Initializing supervisor agent for Flask API...")
            from agents.supervisor_agent import get_supervisor_agent
            _supervisor = run_async(get_supervisor_agent())
            _initialized = True
            logger.info("Supervisor agent initialized successfully!")
            return _supervisor
        except Exception as e:
            logger.error(f"Failed to initialize supervisor: {e}")
            raise


# ------------------------------------------------------
# Chat Endpoint
# ------------------------------------------------------

@chat_bp.route("/", methods=["POST"])
def chat():
    """
    Chat endpoint for querying the contact center agent.

    Request JSON:
        {
            "token": "your-auth-token",
            "message": "your query here"
        }

    Response JSON:
        {
            "reply": "agent response",
            "status": "success"
        }
    """
    return _process_chat_request(retry_count=0)


def _process_chat_request(retry_count: int = 0):
    """
    Internal function to process chat request with retry logic.

    Args:
        retry_count: Number of retries attempted so far (max 1 retry)
    """
    MAX_RETRIES = 1

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        token = data.get("token")
        message = data.get("message")

        # Validate token
        if not token or token not in SESSIONS:
            return jsonify({"error": "Invalid or missing token", "status": "error"}), 401

        # Validate message
        if not message or not message.strip():
            return jsonify({"error": "Message is required", "status": "error"}), 400

        # Get or initialize supervisor
        supervisor = initialize_supervisor()

        if supervisor is None:
            return jsonify({
                "error": "Agent not initialized. Please try again.",
                "status": "error"
            }), 503

        # Process the message
        session = SESSIONS.get(token, {})
        username = session.get("username", "unknown") if isinstance(session, dict) else session
        logger.info(f"Processing chat request from user: {username}")

        # Use token as thread_id for conversation memory
        # Each user (token) gets their own conversation history

        # Create Langfuse callback handler for tracing
        langfuse_handler = CallbackHandler()
        langfuse_handler.user_id = username
        langfuse_handler.session_id = token[:8]  # Use first 8 chars of token as session

        config = {
            "configurable": {"thread_id": token},
            "callbacks": [langfuse_handler]
        }

        result = run_async(
            supervisor.ainvoke(
                {"messages": [{"role": "user", "content": message.strip()}]},
                config=config
            )
        )

        # Extract the reply - look for JSON arrays or the last assistant message
        logger.info(f"Raw result keys: {result.keys() if isinstance(result, dict) else type(result)}")

        if "messages" in result and len(result["messages"]) > 0:
            # Log all messages for debugging
            logger.info(f"Total messages in result: {len(result['messages'])}")
            for i, msg in enumerate(result["messages"]):
                msg_type = type(msg).__name__
                msg_content = getattr(msg, 'content', str(msg))[:200] if hasattr(msg, 'content') else str(msg)[:200]
                logger.info(f"  Message {i}: type={msg_type}, content_preview={msg_content}")

            # Smart response selection: prefer formatted JSON from data agent
            reply = extract_best_response(result["messages"])
            logger.info(f"Selected reply: {reply[:500] if reply else 'EMPTY'}")

            # Check if the reply contains MCP connection error
            if reply and is_mcp_connection_error(reply) and retry_count < MAX_RETRIES:
                logger.warning(f"MCP connection error detected in response, retrying (attempt {retry_count + 1})...")
                # Force reinitialize and retry
                initialize_supervisor(force_reinit=True)
                time.sleep(1)  # Brief pause before retry
                return _process_chat_request(retry_count=retry_count + 1)
        else:
            reply = str(result)
            logger.info(f"No messages found, using str(result): {reply[:500]}")

        return jsonify({
            "reply": reply,
            "status": "success"
        })

    except Exception as e:
        error_str = str(e)
        logger.error(f"Chat error: {error_str}")

        # Check if this is an MCP connection error and we haven't retried yet
        if is_mcp_connection_error(error_str) and retry_count < MAX_RETRIES:
            logger.warning(f"MCP connection error in exception, reinitializing and retrying (attempt {retry_count + 1})...")
            try:
                initialize_supervisor(force_reinit=True)
                time.sleep(1)  # Brief pause before retry
                return _process_chat_request(retry_count=retry_count + 1)
            except Exception as retry_error:
                logger.error(f"Retry also failed: {retry_error}")
                return jsonify({
                    "error": f"Connection error persists after retry: {str(retry_error)}",
                    "status": "error"
                }), 500

        return jsonify({
            "error": f"An error occurred: {error_str}",
            "status": "error"
        }), 500


# ------------------------------------------------------
# Clear Conversation History Endpoint
# ------------------------------------------------------

@chat_bp.route("/clear", methods=["POST"])
def clear_history():
    """
    Clear conversation history for a user.

    Request JSON:
        {
            "token": "your-auth-token"
        }

    Response JSON:
        {
            "message": "Conversation history cleared",
            "status": "success"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        token = data.get("token")

        if not token or token not in SESSIONS:
            return jsonify({"error": "Invalid or missing token", "status": "error"}), 401

        # Note: With MemorySaver, we can't directly clear history
        # The user can start a new conversation by logging out and logging in again
        # Or we could implement a more sophisticated clearing mechanism

        logger.info(f"Conversation history clear requested for token: {token[:8]}...")

        return jsonify({
            "message": "To start a fresh conversation, please logout and login again",
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500

# ------------------------------------------------------
# Excel Export Endpoint
# ------------------------------------------------------

@chat_bp.route("/export-excel", methods=["POST"])
def export_excel():
    """
    Convert JSON data to Excel file and return for download.

    Request JSON:
        {
            "token": "your-auth-token",
            "data": [{"col1": "val1", ...}, ...],
            "filename": "optional_filename"
        }

    Response: Excel file download
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        token = data.get("token")
        json_data = data.get("data")
        filename = data.get("filename", f"report_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}")

        # Validate token
        if not token or token not in SESSIONS:
            return jsonify({"error": "Invalid or missing token", "status": "error"}), 401

        # Validate data
        if not json_data or not isinstance(json_data, list):
            return jsonify({"error": "Data must be a non-empty JSON array", "status": "error"}), 400

        # Process and format the data
        formatted_data = []
        for row in json_data:
            formatted_row = {}
            for key, value in row.items():
                # Format datetime fields (ISO format like 2025-09-08T07:24:57.786Z)
                if isinstance(value, str) and 'T' in value and value.endswith('Z'):
                    try:
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        formatted_row[key] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        formatted_row[key] = value
                # Format large numbers (VMN) as string to prevent scientific notation
                elif isinstance(value, (int, float)) and value > 1000000:
                    formatted_row[key] = str(int(value))
                else:
                    formatted_row[key] = value
            formatted_data.append(formatted_row)

        # Convert JSON to DataFrame
        df = pd.DataFrame(formatted_data)

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')

            # Auto-adjust column widths and format columns
            worksheet = writer.sheets['Report']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                # Limit max width to 50
                col_letter = chr(65 + idx) if idx < 26 else f"A{chr(65 + idx - 26)}"
                worksheet.column_dimensions[col_letter].width = min(max_length, 50)

        output.seek(0)

        # Ensure filename ends with .xlsx
        if not filename.endswith('.xlsx'):
            filename = f"{filename}.xlsx"

        logger.info(f"Excel export successful: {filename}")

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        return jsonify({
            "error": f"Failed to export Excel: {str(e)}",
            "status": "error"
        }), 500
