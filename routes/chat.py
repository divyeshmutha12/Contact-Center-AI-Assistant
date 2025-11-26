from flask import Blueprint, request, jsonify
import asyncio
import threading
import logging

from routes.auth import SESSIONS

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

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
    return future.result(timeout=120)  # 2 minute timeout


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

        # Extract the reply
        if "messages" in result and len(result["messages"]) > 0:
            reply = result["messages"][-1].content
        else:
            reply = str(result)

        return jsonify({
            "reply": reply,
            "status": "success"
        })

    except TimeoutError:
        logger.error("Request timed out")
        return jsonify({
            "error": "Request timed out. Please try again.",
            "status": "error"
        }), 504

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
