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


class MongoMCPClient:
    """
    Official MongoDB MCP client wrapper for LangChain agents.

    Responsibilities:
    - Load MCP server config (config/mcp.json)
    - Allow environment overrides for transport + URL
    - Create MultiServerMCPClient
    - Fetch and cache LangChain-compatible tools
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
