from flask import Blueprint, request, jsonify, send_file
import asyncio
import threading
import logging
import re
import json
import io
import pandas as pd
from datetime import datetime

from routes.auth import SESSIONS

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


def extract_best_response(messages: list) -> str:
    """
    Pick the best response from messages.

    Logic:
    - If JSON array has "_id" → it's raw MongoDB data (Supervisor's response) → SKIP
    - If JSON array has NO "_id" → it's formatted data (Data Agent's response) → USE THIS
    - For non-JSON responses, use the last non-empty AI message
    """
    from langchain_core.messages import AIMessage

    formatted_response = None  # JSON without _id (Data Agent)
    last_text_response = None  # Fallback for non-report queries

    for msg in reversed(messages):
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
    if messages:
        last_msg = messages[-1]
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


def initialize_supervisor():
    """Initialize the supervisor agent once."""
    global _supervisor, _initialized

    with _init_lock:
        if _initialized:
            return _supervisor

        try:
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
        config = {"configurable": {"thread_id": token}}

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
        else:
            reply = str(result)
            logger.info(f"No messages found, using str(result): {reply[:500]}")

        return jsonify({
            "reply": reply,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({
            "error": f"An error occurred: {str(e)}",
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
# Health Check Endpoint
# ------------------------------------------------------

@chat_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint to verify API status."""
    return jsonify({
        "status": "healthy",
        "agent_initialized": _initialized
    })


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
