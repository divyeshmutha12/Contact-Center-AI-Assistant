
"""
Contact Center Agent - Flask API Server

This module provides REST API endpoints for the Contact Center Agent system.
"""

import os
import logging
import asyncio
import threading
from datetime import datetime
import uuid
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------
# Flask App Setup
# ------------------------------------------------------
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# ------------------------------------------------------
# In-memory Session Storage
# ------------------------------------------------------
SESSIONS = {}  # Format: {token: {"username": str, "login_time": str}}

# ------------------------------------------------------
# Persistent Event Loop for Async Operations
# ------------------------------------------------------
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
    return future.result()  # 2 minute timeout


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
# Auth Routes
# ------------------------------------------------------
@app.route("/auth/login", methods=["POST"])
def login():
    """Login endpoint to get an authentication token."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({
                "error": "Username and password are required",
                "status": "error"
            }), 400

        # Generate token and store session (demo: accepts any credentials)
        token = str(uuid.uuid4())
        SESSIONS[token] = {
            "username": username,
            "login_time": datetime.now().isoformat()
        }

        logger.info(f"User '{username}' logged in successfully")

        return jsonify({
            "token": token,
            "username": username,
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout endpoint to invalidate a token."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        token = data.get("token")

        if not token:
            return jsonify({
                "error": "Token is required",
                "status": "error"
            }), 400

        if token in SESSIONS:
            username = SESSIONS[token].get("username", "unknown")
            del SESSIONS[token]
            logger.info(f"User '{username}' logged out")
            return jsonify({
                "message": "Logged out successfully",
                "status": "success"
            })

        return jsonify({
            "error": "Invalid token",
            "status": "error"
        }), 400

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/auth/session", methods=["POST"])
def session_info():
    """Get session information for a token."""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON body", "status": "error"}), 400

        token = data.get("token")

        if not token or token not in SESSIONS:
            return jsonify({
                "error": "Invalid token",
                "status": "error"
            }), 401

        session = SESSIONS[token]
        return jsonify({
            "username": session.get("username"),
            "login_time": session.get("login_time"),
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Session info error: {str(e)}")
        return jsonify({"error": str(e), "status": "error"}), 500


# ------------------------------------------------------
# Chat Routes
# ------------------------------------------------------
@app.route("/chat/", methods=["POST"])
def chat():
    """Chat endpoint for querying the contact center agent."""
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
        username = session.get("username", "unknown")
        logger.info(f"Processing chat request from user: {username}")

        result = run_async(
            supervisor.ainvoke({"messages": [{"role": "user", "content": message.strip()}]})
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


@app.route("/chat/health", methods=["GET"])
def health():
    """Health check endpoint to verify API status."""
    return jsonify({
        "status": "healthy",
        "agent_initialized": _initialized
    })


# ------------------------------------------------------
# Root Endpoint
# ------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    """Root endpoint showing API information."""
    return jsonify({
        "name": "Contact Center Agent API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "login": "POST /auth/login",
                "logout": "POST /auth/logout",
                "session": "POST /auth/session"
            },
            "chat": {
                "message": "POST /chat/",
                "health": "GET /chat/health"
            }
        }
    })


# ------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 8000))

    print("\n" + "=" * 60)
    print("  CONTACT CENTER AGENT - API SERVER")
    print("=" * 60)
    print(f"\n  Server running at: http://localhost:{port}")
    print("\n  Available Endpoints:")
    print("    POST /auth/login    - Login and get token")
    print("    POST /auth/logout   - Logout and invalidate token")
    print("    POST /auth/session  - Get session info")
    print("    POST /chat/         - Send message to agent")
    print("    GET  /chat/health   - Check API health")
    print("\n" + "=" * 60 + "\n")

    app.run(host="0.0.0.0", port=port, debug=True, threaded=True, use_reloader=False)
