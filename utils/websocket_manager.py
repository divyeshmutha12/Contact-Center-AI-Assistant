"""
WebSocket connection manager for tracking active connections.

Manages WebSocket connections for chat sessions, allowing async background
tasks to send results to the appropriate client connections.

Features:
- Message queuing when WebSocket disconnected
- Automatic flush of queued messages on reconnect
- No data loss during temporary disconnections
"""
import asyncio
import json
import logging
import time
from collections import defaultdict
from typing import Dict, Optional, Any
from threading import Lock

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for chat sessions."""

    # Message types that should be queued for reconnection
    # Control messages (connected, pong, error, complete) are NOT queued
    QUEUEABLE_MESSAGE_TYPES = {"message", "stream", "final", "data"}

    def __init__(self):
        # Maps session_id -> WebSocket connection
        self.active_connections: Dict[str, Any] = {}
        # Message queue for disconnected sessions
        self._message_queue: Dict[str, list] = defaultdict(list)
        # Lock for thread-safe operations
        self._lock = Lock()

    def register(self, session_id: str, websocket: Any) -> None:
        """
        Register a new WebSocket connection for a NEW session (no flush).
        Use this for brand new sessions where no queued messages can exist.
        """
        with self._lock:
            self.active_connections[session_id] = websocket
            logger.info(f"[WS_MANAGER] Registered WebSocket for NEW session: {session_id}")

    def connect(self, session_id: str, websocket: Any) -> list:
        """
        Register a WebSocket connection for RECONNECTION (with flush).
        Use this when client reconnects to an existing session.
        Returns queued messages that should be sent to the client.
        """
        with self._lock:
            self.active_connections[session_id] = websocket
            logger.info(f"[WS_MANAGER] Registered WebSocket for RECONNECT session: {session_id}")

            # Get and clear queued messages
            queued = self._message_queue.pop(session_id, [])
            if queued:
                logger.info(f"[WS_MANAGER] Flushing {len(queued)} queued messages for session: {session_id}")
            return queued

    def disconnect(self, session_id: str) -> None:
        """Remove a WebSocket connection for a session."""
        with self._lock:
            if session_id in self.active_connections:
                del self.active_connections[session_id]
                logger.info(f"[WS_MANAGER] Disconnected WebSocket for session: {session_id}")

    def queue_message(self, session_id: str, message: dict) -> None:
        """Queue a message for later delivery when session reconnects."""
        msg_type = message.get("type")
        if msg_type in self.QUEUEABLE_MESSAGE_TYPES:
            with self._lock:
                self._message_queue[session_id].append(message)
                logger.debug(f"[WS_MANAGER] Queued message for session {session_id}: type={msg_type}")

    def get_connection(self, session_id: str) -> Optional[Any]:
        """Get the WebSocket connection for a session."""
        return self.active_connections.get(session_id)

    def has_connection(self, session_id: str) -> bool:
        """Check if a session has an active WebSocket connection."""
        return session_id in self.active_connections

    def get_active_sessions(self) -> list:
        """Get list of all active session IDs."""
        return list(self.active_connections.keys())

    def get_queued_count(self, session_id: str) -> int:
        """Get number of queued messages for a session."""
        return len(self._message_queue.get(session_id, []))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
