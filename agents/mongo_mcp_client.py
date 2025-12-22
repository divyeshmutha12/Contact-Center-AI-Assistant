import os
import json
import logging
from typing import List, Optional
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# ------------------------------------------------------
# Shared MCP Tools (loaded once at server startup)
# ------------------------------------------------------
_shared_mcp_client: Optional["MongoMCPClient"] = None
_shared_mcp_tools: Optional[List[BaseTool]] = None


async def init_shared_mcp_tools() -> List[BaseTool]:
    """
    Initialize MCP tools once at server startup.
    These tools are shared across all session agents.
    Loads both MongoDB and MariaDB MCP tools.
    """
    global _shared_mcp_client, _shared_mcp_tools

    if _shared_mcp_tools is not None:
        return _shared_mcp_tools

    logger.info("Initializing shared MCP tools (one-time startup)...")
    _shared_mcp_client = MongoMCPClient()
    _shared_mcp_tools = await _shared_mcp_client.get_all_tools()
    logger.info(f"Shared MCP tools initialized: {len(_shared_mcp_tools)} tools")
    return _shared_mcp_tools


def get_shared_mcp_tools() -> List[BaseTool]:
    """Get the shared MCP tools (must be initialized first)."""
    if _shared_mcp_tools is None:
        raise RuntimeError("MCP tools not initialized. Call init_shared_mcp_tools() first.")
    return _shared_mcp_tools


class MongoMCPClient:
    """
    Multi-database MCP client wrapper for LangChain agents.

    Responsibilities:
    - Load MCP server config (config/mcp.json) for all servers
    - Allow environment overrides for transport + URL
    - Create MultiServerMCPClient
    - Fetch and cache LangChain-compatible tools from MongoDB, MariaDB, etc.
    """

    def __init__(
        self,
        config_path: str = "config/mcp.json",
        server_name: str = "mongodb"
    ) -> None:
        self.config_path = config_path
        self.server_name = server_name
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: Optional[List[BaseTool]] = None
        self.all_tools: Optional[List[BaseTool]] = None

        logger.info("MongoMCPClient initialized using LangChain MCP adapter")

    # -------------------------------------------------------------
    # INTERNAL CONFIG LOADER
    # -------------------------------------------------------------
    def _load_config(self) -> dict:
        """Load and validate MCP server config."""
        if not os.path.exists(self.config_path):
            msg = f"MCP config file not found: {self.config_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Loading MCP config from: {self.config_path}")

        with open(self.config_path, "r") as f:
            config = json.load(f)

        logger.debug(f"Raw MCP config: {config}")

        if "servers" not in config:
            raise ValueError("Invalid MCP config: missing 'servers'")

        if self.server_name not in config["servers"]:
            raise ValueError(f"Server '{self.server_name}' not found in MCP config")

        server_cfg = config["servers"][self.server_name]

        # ---------------------------------------------------------
        # Allow user to override transport / URL via .env
        # ---------------------------------------------------------
        env_transport = os.getenv("MDB_MCP_TRANSPORT")
        env_url = os.getenv("MDB_MCP_URL")

        if env_transport:
            server_cfg["transport"] = env_transport

        if env_url:
            server_cfg["url"] = env_url

        # Default to stdio if nothing is set
        server_cfg.setdefault("transport", "stdio")

        logger.info(
            f"MCP server '{self.server_name}' => transport={server_cfg.get('transport')} "
            f"url={server_cfg.get('url')}"
        )

        # MultiServerMCPClient requires: { "mongodb": { ... } }
        return {self.server_name: server_cfg}

    # -------------------------------------------------------------
    # MAIN: FETCH TOOLS
    # -------------------------------------------------------------
    async def get_tools(self) -> List[BaseTool]:
        """
        Returns a list of LangChain BaseTool objects for MongoDB.
        Tools are cached after first load.
        """
        if self.tools is not None:
            logger.info("Returning cached MCP tools")
            return self.tools

        # Load config
        server_cfg = self._load_config()

        logger.info("Creating MultiServerMCPClient...")
        try:
            self.client = MultiServerMCPClient(server_cfg)

            logger.info("Requesting tools from MCP server...")
            self.tools = await self.client.get_tools()

            logger.info(f"Successfully retrieved {len(self.tools)} tools:")
            for tool in self.tools:
                logger.info(f"  • {tool.name}")

            return self.tools

        except Exception as e:
            logger.error("Failed to load tools from MCP", exc_info=True)
            raise RuntimeError(f"Failed to get tools from MCP server: {e}") from e

    # -------------------------------------------------------------
    # FETCH ALL TOOLS FROM ALL SERVERS
    # -------------------------------------------------------------
    async def get_all_tools(self) -> List[BaseTool]:
        """
        Returns LangChain BaseTool objects from ALL MCP servers in config.
        Tools are prefixed with server name to differentiate them (e.g., mongodb_find, mariadb_query).
        Tools are cached after first load.
        """
        if self.all_tools is not None:
            logger.info("Returning cached MCP tools from all servers")
            return self.all_tools

        # Load full config
        if not os.path.exists(self.config_path):
            msg = f"MCP config file not found: {self.config_path}"
            logger.error(msg)
            raise FileNotFoundError(msg)

        logger.info(f"Loading MCP config from: {self.config_path}")
        with open(self.config_path, "r") as f:
            config = json.load(f)

        if "servers" not in config:
            raise ValueError("Invalid MCP config: missing 'servers'")

        # Process each server
        all_server_configs = {}
        for server_name, server_cfg in config["servers"].items():
            # Allow environment overrides
            env_transport_key = f"{server_name.upper()}_MCP_TRANSPORT"
            env_url_key = f"{server_name.upper()}_MCP_URL"

            env_transport = os.getenv(env_transport_key)
            env_url = os.getenv(env_url_key)

            if env_transport:
                server_cfg["transport"] = env_transport
            if env_url:
                server_cfg["url"] = env_url

            # Default to streamable_http if not set
            server_cfg.setdefault("transport", "streamable_http")

            logger.info(
                f"MCP server '{server_name}' => transport={server_cfg.get('transport')} "
                f"url={server_cfg.get('url')}"
            )

            all_server_configs[server_name] = server_cfg

        logger.info(f"Creating MultiServerMCPClient with {len(all_server_configs)} servers...")
        try:
            self.client = MultiServerMCPClient(all_server_configs)

            logger.info("Requesting tools from all MCP servers...")
            self.all_tools = await self.client.get_tools()

            logger.info(f"Successfully retrieved {len(self.all_tools)} tools from all servers:")
            for tool in self.all_tools:
                logger.info(f"  • {tool.name}")

            return self.all_tools

        except Exception as e:
            logger.error("Failed to load tools from MCP servers", exc_info=True)
            raise RuntimeError(f"Failed to get tools from MCP servers: {e}") from e

    # -------------------------------------------------------------
    # CLEANUP
    # -------------------------------------------------------------
    async def close(self):
        """Close MCP client (safe)."""
        if not self.client:
            return

        try:
            logger.info("Closing MCP client...")
            close_method = getattr(self.client, "close", None)

            if callable(close_method):
                result = close_method()
                if hasattr(result, "__await__"):  # async close
                    await result

            self.client = None
            logger.info("MCP client closed successfully")

        except Exception as e:
            logger.warning(f"Error during MCP close: {e}", exc_info=True)

    # -------------------------------------------------------------
    # LEGACY: DO NOT USE
    # -------------------------------------------------------------
    async def call(self, tool: str, args: dict):
        raise NotImplementedError(
            "Direct .call() is deprecated.\n"
            "Use get_tools() and let the LangChain Agent call the tools."
        )
