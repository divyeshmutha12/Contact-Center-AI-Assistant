"""
Contact Center Agent - Flask API Server

This module provides REST API endpoints for the Contact Center Agent system.
Includes WebSocket support for real-time streaming.
"""

import os
import logging
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sock import Sock

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Sock instance for WebSocket support
sock = Sock()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Initialize WebSocket support
    sock.init_app(app)

    # Import and register blueprints
    from routes.auth import auth_bp
    from routes.chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    # Initialize WebSocket routes
    from routes.websocket import init_websocket
    init_websocket(sock)

    # Root endpoint
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "name": "Contact Center Agent API",
            "version": "1.0.0",
            "endpoints": {
                "auth": {
                    "login": "POST api/auth/login",
                    "logout": "POST api/auth/logout",
                    "session": "POST api/auth/session"
                },
                "chat": {
                    "message": "POST /chat/",
                    "clear": "POST /chat/clear"
                }
            }
        })

    logger.info("Flask app created successfully")
    return app


if __name__ == "__main__":
    app = create_app()

    # Get port from environment or use default
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
    print("    POST /chat/clear    - Clear conversation history")
    print("    GET  /chat/health   - Check API health")
    print("\n" + "=" * 60 + "\n")

    app.run(host="0.0.0.0", port=port, debug=True, threaded=True, use_reloader=False)
