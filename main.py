"""
Chatten - Decentralized Exchange for AI Compute Tokens

Main entry point for the Chatten application.
"""

import asyncio
import os
import sys
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on system env vars

# Local imports
from agents import ChattenTraderAgent
from tools import (
    NeoBridgeTool,
    TokenBalanceTool,
    TokenTransferTool,
    QScoreAnalyzerTool,
)
from tools.neo_bridge import NeoConfig


def get_config() -> dict:
    """
    Load configuration from environment variables.

    Returns:
        dict: Application configuration
    """
    return {
        # Neo N3 Configuration
        "neo": {
            "rpc_url": os.getenv("NEO_RPC_URL", "https://testnet1.neo.coz.io:443"),
            "network_magic": int(os.getenv("NEO_NETWORK_MAGIC", "894710606")),
            "private_key": os.getenv("NEO_PRIVATE_KEY"),
            "wallet_address": os.getenv("NEO_WALLET_ADDRESS"),
            "wallet_path": os.getenv("NEO_WALLET_PATH"),
            "wallet_password": os.getenv("NEO_WALLET_PASSWORD"),
        },
        # Chatten Contract
        "contract": {
            "hash": os.getenv("CHATTEN_CONTRACT_HASH"),
            "owner": os.getenv("CHATTEN_OWNER_ADDRESS"),
        },
        # SpoonOS Configuration
        "spoon": {
            "api_key": os.getenv("SPOON_API_KEY"),
            "workspace_id": os.getenv("SPOON_WORKSPACE_ID"),
            "agent_name": os.getenv("SPOON_AGENT_NAME", "ChattenTrader"),
        },
        # OpenAI Configuration
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        },
        # Application Settings
        "app": {
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "dry_run": os.getenv("DRY_RUN", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        },
    }


def validate_config(config: dict) -> list[str]:
    """
    Validate required configuration values.

    Args:
        config: Configuration dictionary

    Returns:
        list: List of validation errors (empty if valid)
    """
    errors: list[str] = []

    # Check critical values
    if not config["neo"]["rpc_url"]:
        errors.append("NEO_RPC_URL is required")

    if not config["openai"]["api_key"]:
        errors.append("OPENAI_API_KEY is required")

    # Warn about optional but recommended values
    if not config["neo"]["wallet_address"]:
        print("Warning: NEO_WALLET_ADDRESS not set - some features will be limited")

    if not config["spoon"]["api_key"]:
        print("Warning: SPOON_API_KEY not set - SpoonOS features disabled")

    return errors


def setup_tools(config: dict) -> dict:
    """
    Initialize and configure SpoonOS tools.

    Args:
        config: Application configuration

    Returns:
        dict: Initialized tools
    """
    neo_config = NeoConfig(
        rpc_url=config["neo"]["rpc_url"],
        network_magic=config["neo"]["network_magic"],
        wallet_path=config["neo"]["wallet_path"],
        wallet_password=config["neo"]["wallet_password"],
    )

    neo_bridge = NeoBridgeTool(config=neo_config)
    contract_hash = config["contract"]["hash"] or ""

    tools = {
        "neo_bridge": neo_bridge,
        "token_balance": TokenBalanceTool(contract_hash, neo_bridge),
        "token_transfer": TokenTransferTool(contract_hash, neo_bridge),
        "q_score_analyzer": QScoreAnalyzerTool(),
    }

    return tools


def create_agent(config: dict, tools: Optional[dict] = None) -> ChattenTraderAgent:
    """
    Create and configure the Chatten Trader Agent.

    Args:
        config: Application configuration
        tools: Pre-initialized tools (optional)

    Returns:
        ChattenTraderAgent: Configured agent instance
    """
    agent = ChattenTraderAgent(
        name=config["spoon"]["agent_name"],
        neo_wallet_address=config["neo"]["wallet_address"],
        tools=tools,
    )
    return agent


async def run_agent(agent: ChattenTraderAgent, config: dict) -> None:
    """
    Run the agent's main loop.

    Args:
        agent: The trader agent to run
        config: Application configuration
    """
    print("== Starting Chatten Trader Agent ==")
    print(f"   Agent: {agent.name}")
    print(f"   Network: {'TestNet' if 'testnet' in config['neo']['rpc_url'] else 'MainNet'}")
    print(f"   Wallet: {agent.neo_wallet_address or 'Not configured'}")
    print()

    try:
        await agent.on_start()

        print("Agent initialized successfully.")
        print()
        print("Agent is ready. In production, this would:")
        print("   - Monitor the Compute Token market")
        print("   - Analyze Q-scores for AI models")
        print("   - Execute buy/sell orders based on performance")
        print("   - Manage liquidity pools")
        print()
        print("Info: This is a scaffold - implement the TODO items to add functionality.")

        # Demo: quick Q-score snapshot and balance check
        try:
            q_score = await agent.analyze_q_score("demo-model")
            print(f"Demo Q-score for demo-model: {q_score:.2f}")
        except Exception as exc:  # pragma: no cover - best effort
            print(f"Q-score demo skipped: {exc}")

        if agent.neo_wallet_address:
            try:
                position = await agent.check_token_balance()
                print(f"Balance for {agent.neo_wallet_address}: {position.balance} units")
            except Exception as exc:  # pragma: no cover
                print(f"Balance demo skipped: {exc}")

        print()

        # Keep running (in production, this would be an event loop)
        # await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\nStopping agent...")
    finally:
        await agent.on_stop()


async def async_main() -> int:
    """
    Async main entry point.

    Returns:
        int: Exit code
    """
    print("=" * 72)
    print(" Chatten - Decentralized Exchange for AI Compute Tokens (Neo N3 Demo)")
    print(" Powered by Neo N3 & SpoonOS")
    print("=" * 72)
    print()

    config = get_config()
    errors = validate_config(config)

    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        print()
        print("Please check your .env file and try again.")
        print("See .env.example for required configuration.")
        return 1

    tools = setup_tools(config)

    # Neo RPC health check
    neo_bridge = tools["neo_bridge"]
    connected = False
    try:
        connected = await neo_bridge.connect()
    except Exception as exc:
        print(f"Neo RPC connection attempt failed: {exc}")

    if not connected and not config["app"]["dry_run"]:
        print("Failed to connect to Neo RPC node:", config["neo"]["rpc_url"])
        return 1

    if connected:
        height = await neo_bridge.get_block_height()
        print(f"Connected to Neo RPC @ {config['neo']['rpc_url']}")
        print(f"   Current block height: {height}")
    else:
        print("Running in dry-run mode without RPC connectivity.")
    print()

    # Create and run agent
    agent = create_agent(config, tools)
    await run_agent(agent, config)

    return 0


def main() -> None:
    """
    Main entry point for the Chatten application.
    """
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
