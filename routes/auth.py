"""
Authentication routes for Contact Center Agent API.

Provides simple token-based authentication for demo purposes.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory session storage
# Format: {token: {"username": str, "login_time": datetime}}
SESSIONS = {}


def get_user_for_token(token: str) -> str | None:
    """Get username for a given token."""
    session = SESSIONS.get(token)
    return session.get("username") if session else None


def is_valid_token(token: str) -> bool:
    """Check if a token is valid."""
    return token in SESSIONS


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login endpoint to get an authentication token.

    Request JSON:
        {
            "username": "your_username",
            "password": "your_password"
        }

    Response JSON:
        {
            "token": "uuid-token",
            "username": "your_username",
            "status": "success"
        }
    """
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

        # Generate token and store session
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


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Logout endpoint to invalidate a token.

    Request JSON:
        {
            "token": "your-token"
        }

    Response JSON:
        {
            "message": "Logged out successfully",
            "status": "success"
        }
    """
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


@auth_bp.route("/session", methods=["POST"])
def session_info():
    """
    Get session information for a token.

    Request JSON:
        {
            "token": "your-token"
        }

    Response JSON:
        {
            "username": "your_username",
            "login_time": "ISO datetime",
            "status": "success"
        }
    """
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
