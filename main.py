"""
Contact Center Agent System - Main Entry Point
Interactive CLI for querying call logs using AI agents
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv
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

# Only import get_supervisor_agent (avoid duplicate import)
from agents.supervisor_agent import get_supervisor_agent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContactCenterCLI:
    """Interactive CLI for the Contact Center Agent System"""

    def __init__(self):
        self.supervisor = None
        self.running = False

    def print_banner(self):
        print("\n" + "="*70)
        print("     CONTACT CENTER AGENT SYSTEM")
        print("     AI-Powered Customer Data Assistant")
        print("="*70)
        print("\nPowered by:")
        print("  🤖 OpenAI (Supervisor Agent)")
        print("  🗄️  MongoDB MCP Server (Data Extraction)")
        print("  🔀 LangGraph Agents (Workflow Orchestration)")
        print("\n" + "="*70 + "\n")

    def print_help(self):
        print("\n📚 Available Commands:")
        print("  - Type any natural language query")
        print("  - 'help' or '?' - Show this help message")
        print("  - 'examples' - Show example queries")
        print("  - 'status' - Show system status")
        print("  - 'quit' or 'exit' - Exit")
        print()

    def print_examples(self):
        print("\n💡 Example Queries:")
        print("  1. How many outgoing calls were successful on 08-09-2025?")
        print("  2. Show all incoming calls for customer 9876543210")
        print("  3. Count failed calls between 1 Aug 2025 and 10 Aug 2025")
        print("  4. Total call duration for agent John?")
        print("  5. List calls for customer 9823456789 on 2025-08-15")
        print("  6. How many calls were not answered yesterday?")
        print()

    async def initialize(self):
        print("🔧 Initializing agent system...\n")

        load_dotenv()

        try:
            self.supervisor = await get_supervisor_agent()

            print("\n✅ System ready! Type 'help' for help.\n")
            return True

        except RuntimeError as e:
            print("\n❌ Failed to load MCP tools – MongoDB MCP Server may not be running.")
            print("   Start server with:  npm run mcp:server")
            logger.error("MCP initialization error", exc_info=True)
            return False

        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            logger.error("Initialization error", exc_info=True)
            return False

    async def process_command(self, command: str) -> bool:
        c = command.strip().lower()

        if c in ("quit", "exit", "q"):
            return False

        if c in ("help", "?"):
            self.print_help()
            return True

        if c == "examples":
            self.print_examples()
            return True

        if c == "status":
            print("\n📊 System Status:")
            print(f"  Supervisor: {'✅ Active' if self.supervisor else '❌ Inactive'}")
            from agents.mongo_mcp_client import MongoMCPClient
            mcp = MongoMCPClient()
            print(f"  MCP Config: {mcp.config_path}  (Server: {mcp.server_name})")
            print()
            return True

        if not command.strip():
            return True

        try:
            print("\n🔍 Processing query...\n")

            result = await self.supervisor.ainvoke(
                {"messages": [{"role": "user", "content": command}]},
                config={"recursion_limit": 30}
            )

            try:
                response = result["messages"][-1].content
            except Exception:
                response = str(result)

            print("\n" + "="*70)
            print("RESPONSE:")
            print("="*70)
            print(response)
            print("="*70 + "\n")

        except Exception as e:
            print(f"\n❌ Error processing query: {e}\n")
            logger.error("Query error", exc_info=True)

        return True

    async def run(self):
        self.print_banner()

        if not await self.initialize():
            return

        self.running = True

        try:
            while self.running:
                user_input = input("👤 You: ").strip()
                should_continue = await self.process_command(user_input)
                if not should_continue:
                    print("\n👋 Goodbye! Shutting down...")
                    break

        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ Interrupted, shutting down.")

        finally:
            print("✅ System shutdown complete\n")


async def main():
    cli = ContactCenterCLI()
    await cli.run()


def check_prerequisites():
    print("Checking prerequisites...\n")
    errors = []

    if sys.version_info < (3, 8):
        errors.append("Python 3.8+ required")

    try:
        import pymongo
        print("✅ PyMongo installed")
    except ImportError:
        errors.append("PyMongo not installed")

    try:
        import openai
        print("✅ OpenAI SDK installed")
    except ImportError:
        errors.append("OpenAI SDK missing")

    try:
        import langgraph
        print("✅ LangGraph installed")
    except ImportError:
        errors.append("LangGraph missing")

    try:
        import mcp
        print("✅ MCP SDK installed")
    except ImportError:
        errors.append("MCP SDK missing")

    import subprocess
    try:
        r = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            print(f"✅ Node.js installed: {r.stdout.strip()}")
        else:
            errors.append("Node.js not found")
    except:
        errors.append("Node.js missing")

    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("⚠️ .env file missing")

    print()
    if errors:
        print("❌ Missing prerequisites:")
        for e in errors:
            print(" -", e)
        return False

    print("✅ All prerequisites satisfied!\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  CONTACT CENTER AGENT SYSTEM - Startup")
    print("="*70 + "\n")

    if not check_prerequisites():
        print("\nInstall dependencies & retry.\n")
        sys.exit(1)

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logger.error("Fatal error", exc_info=True)
        sys.exit(1)
