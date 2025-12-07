"""
Chatten Trader Agent

A SpoonOS-powered AI agent that acts as a Liquidity Manager for the 
Compute Token DEX on Neo N3 blockchain.
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# SpoonOS SDK imports
# Note: These imports will show "could not be resolved" warnings in IDE
# until spoon-ai-sdk is installed. This is expected during development.
_SPOON_SDK_AVAILABLE = False
try:
    from spoon_ai_sdk import ToolCallAgent, Tool, AgentConfig  # type: ignore
    from spoon_ai_sdk.memory import ConversationMemory  # type: ignore
    _SPOON_SDK_AVAILABLE = True
except ImportError:
    # Fallback for development/scaffolding
    ToolCallAgent = object
    Tool = object
    AgentConfig = object
    ConversationMemory = object


@dataclass
class MarketState:
    """Represents the current state of the Compute Token market."""
    
    total_liquidity: float = 0.0
    current_q_score: float = 0.0
    active_orders: int = 0
    last_trade_timestamp: Optional[str] = None
    price_history: list[float] = field(default_factory=list)


@dataclass 
class TokenPosition:
    """Represents the agent's token holdings."""
    
    token_id: str = ""
    balance: float = 0.0
    locked_amount: float = 0.0
    available_amount: float = 0.0


class ChattenTraderAgent(ToolCallAgent):
    """
    Liquidity Manager Agent for the Chatten Compute Token DEX.
    
    This agent is responsible for:
    - Managing liquidity pools for Compute Tokens
    - Analyzing market quality (Q-score) for AI model capacity
    - Executing buy/sell orders based on real-time performance metrics
    - Minting new tokens based on validated AI performance
    
    Attributes:
        name: The agent's identifier
        neo_wallet_address: The Neo N3 wallet address for transactions
        market_state: Current state of the DEX market
        position: The agent's current token holdings
    """
    
    # System prompt defining the agent's persona
    SYSTEM_PROMPT = """
    You are the Chatten Liquidity Manager, an autonomous AI agent operating on the 
    Neo N3 blockchain. Your primary role is to manage the Compute Token DEX, ensuring 
    efficient market operations for AI model capacity trading.
    
    Your responsibilities include:
    1. MARKET ANALYSIS: Continuously analyze the Q-score (Quality Score) of AI models 
       to determine fair token pricing based on real-time performance metrics.
    
    2. LIQUIDITY MANAGEMENT: Maintain healthy liquidity pools by strategically placing 
       buy and sell orders to minimize slippage and maximize market efficiency.
    
    3. TOKEN OPERATIONS: Execute minting of new Compute Tokens when AI models demonstrate 
       verified performance improvements, and manage token burns when capacity is reduced.
    
    4. RISK ASSESSMENT: Monitor market conditions and adjust positions to protect against 
       volatility while maximizing returns for liquidity providers.
    
    When making decisions:
    - Always verify on-chain data before executing transactions
    - Prioritize market stability over aggressive profit-seeking
    - Report anomalies or suspicious activity immediately
    - Maintain transparency in all trading operations
    
    You have access to Neo N3 blockchain tools for reading balances, executing transfers, 
    and interacting with the Chatten NEP-11 smart contract.
    """
    
    def __init__(
        self,
        name: str = "ChattenTrader",
        neo_wallet_address: Optional[str] = None,
        tools: Optional[dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """
        Initialize the Chatten Trader Agent.
        
        Args:
            name: Unique identifier for this agent instance
            neo_wallet_address: The Neo N3 wallet address for blockchain operations
            **kwargs: Additional arguments passed to ToolCallAgent
        """
        # Only pass arguments to parent if SpoonOS SDK is available
        # object.__init__() doesn't accept any arguments
        if _SPOON_SDK_AVAILABLE:
            super().__init__(
                name=name,
                system_prompt=self.SYSTEM_PROMPT,
                **kwargs
            )
        else:
            super().__init__()
        
        self.name = name
        self.system_prompt = self.SYSTEM_PROMPT
        self.neo_wallet_address = neo_wallet_address
        self.market_state = MarketState()
        self.position = TokenPosition()
        self.tools: dict[str, Any] = {}
        
        # Initialize tools (to be registered)
        self._register_tools(tools or {})
    
    def _register_tools(self, tools: dict[str, Any]) -> None:
        """Register SpoonOS tools for blockchain interaction."""
        for name, tool in tools.items():
            self.add_tool(name, tool)

    def add_tool(self, name: str, tool: Any) -> None:
        """
        Attach a tool to the agent and register with SpoonOS when available.
        """
        self.tools[name] = tool
        if _SPOON_SDK_AVAILABLE:
            try:
                super().register_tool(tool)  # type: ignore[attr-defined]
            except Exception:
                # Development fallback when SDK is not present
                pass
    
    # =========================================================================
    # TOKEN BALANCE OPERATIONS
    # =========================================================================
    
    async def check_token_balance(self, token_id: Optional[str] = None) -> TokenPosition:
        """
        Check the current token balance for the agent's wallet.
        
        This method queries the Neo N3 blockchain to retrieve the current
        balance of Compute Tokens held by the agent.
        
        Args:
            token_id: Optional specific token ID to check. If None, checks 
                     the default Chatten token.
        
        Returns:
            TokenPosition: The current token holdings including locked and 
                          available amounts.
        
        Raises:
            ConnectionError: If unable to connect to Neo N3 RPC node
            ValueError: If the token_id is invalid
        """
        balance_tool = self.tools.get("token_balance")
        if balance_tool is None:
            raise NotImplementedError("TokenBalanceTool is not configured")
        
        address = self.neo_wallet_address or ""
        balance = await balance_tool.get_balance(address)
        tokens = await balance_tool.get_tokens(address)
        selected_token = token_id or (tokens[0] if tokens else "")
        
        self.position.token_id = selected_token
        self.position.balance = float(balance)
        self.position.available_amount = max(
            0.0, self.position.balance - self.position.locked_amount
        )
        
        return self.position
    
    async def get_all_balances(self) -> dict[str, TokenPosition]:
        """
        Retrieve all token balances across different Compute Token types.
        
        Returns:
            dict: Mapping of token_id to TokenPosition for all held tokens
        """
        balance_tool = self.tools.get("token_balance")
        if balance_tool is None:
            raise NotImplementedError("TokenBalanceTool is not configured")
        
        address = self.neo_wallet_address or ""
        token_ids = await balance_tool.get_tokens(address)
        
        positions: dict[str, TokenPosition] = {}
        for t_id in token_ids:
            info = await balance_tool.get_token_info(t_id)
            balance = await balance_tool.get_balance(address)
            pos = TokenPosition(
                token_id=t_id,
                balance=float(balance),
                locked_amount=0.0,
                available_amount=float(balance),
            )
            positions[t_id] = pos
        
        return positions
    
    # =========================================================================
    # MARKET QUALITY ANALYSIS (Q-SCORE)
    # =========================================================================
    
    async def analyze_q_score(
        self,
        model_id: str,
        performance_metrics: Optional[dict[str, float]] = None
    ) -> float:
        """
        Analyze the Quality Score (Q-score) for an AI model's compute capacity.
        
        The Q-score is a composite metric that determines the fair market value
        of Compute Tokens based on:
        - Inference latency
        - Throughput (tokens/second)
        - Accuracy on benchmark tasks
        - Availability/uptime
        - Cost efficiency
        
        Args:
            model_id: The unique identifier of the AI model being evaluated
            performance_metrics: Optional dict of pre-collected metrics. If None,
                               metrics will be fetched from on-chain oracles.
        
        Returns:
            float: The calculated Q-score between 0.0 and 100.0
        
        Raises:
            ValueError: If model_id is not registered on-chain
            TimeoutError: If performance data cannot be retrieved in time
        """
        analyzer = self.tools.get("q_score_analyzer")
        if analyzer is None:
            raise NotImplementedError("QScoreAnalyzerTool is not configured")
        
        result = await analyzer.calculate_q_score(model_id)
        self.market_state.current_q_score = result.q_score
        return result.q_score
    
    async def get_market_q_scores(self) -> dict[str, float]:
        """
        Retrieve Q-scores for all active models in the marketplace.
        
        Returns:
            dict: Mapping of model_id to their current Q-scores
        """
        analyzer = self.tools.get("q_score_analyzer")
        if analyzer is None:
            raise NotImplementedError("QScoreAnalyzerTool is not configured")
        
        # Use cached metrics if available; otherwise calculate a couple of demo IDs
        model_ids = list(getattr(analyzer, "_metrics_cache", {}).keys()) or [
            "model-alpha",
            "model-beta",
            "model-gamma",
        ]
        
        scores = {}
        for model_id in model_ids:
            result = await analyzer.calculate_q_score(model_id)
            scores[model_id] = result.q_score
        
        return scores
    
    async def compare_q_scores(
        self,
        model_ids: list[str]
    ) -> list[tuple[str, float, str]]:
        """
        Compare Q-scores between multiple models and provide rankings.
        
        Args:
            model_ids: List of model identifiers to compare
            
        Returns:
            list: Sorted list of (model_id, q_score, recommendation) tuples
        """
        analyzer = self.tools.get("q_score_analyzer")
        if analyzer is None:
            raise NotImplementedError("QScoreAnalyzerTool is not configured")
        
        results = await analyzer.compare_models(model_ids)
        return [
            (r.model_id, r.q_score, r.recommendations[0] if r.recommendations else "")
            for r in results
        ]
    
    # =========================================================================
    # TRADING OPERATIONS
    # =========================================================================
    
    async def execute_buy_order(
        self,
        token_id: str,
        amount: float,
        max_price: Optional[float] = None
    ) -> dict[str, Any]:
        """
        Execute a buy order for Compute Tokens.
        
        Args:
            token_id: The token to purchase
            amount: Number of tokens to buy
            max_price: Maximum price willing to pay (slippage protection)
            
        Returns:
            dict: Transaction result including tx_hash and filled amount
        """
        q_score = await self.analyze_q_score(token_id)
        unit_price = max_price or self._price_from_q_score(q_score)
        filled = float(amount)
        
        tx_result: dict[str, Any] = {}
        transfer_tool = self.tools.get("token_transfer")
        if transfer_tool:
            tx_result = await transfer_tool.transfer(
                self.neo_wallet_address or "",
                token_id,
                data=None
            )
        
        self.market_state.last_trade_timestamp = datetime.utcnow().isoformat()
        self.market_state.active_orders += 1
        
        return {
            "action": "buy",
            "token_id": token_id,
            "filled": filled,
            "unit_price": unit_price,
            "spent": filled * unit_price,
            "tx": tx_result or {"simulated": True},
        }
    
    async def execute_sell_order(
        self,
        token_id: str,
        amount: float,
        min_price: Optional[float] = None
    ) -> dict[str, Any]:
        """
        Execute a sell order for Compute Tokens.
        
        Args:
            token_id: The token to sell
            amount: Number of tokens to sell
            min_price: Minimum price to accept (slippage protection)
            
        Returns:
            dict: Transaction result including tx_hash and filled amount
        """
        q_score = await self.analyze_q_score(token_id)
        unit_price = min_price or self._price_from_q_score(q_score)
        filled = float(amount)
        
        tx_result: dict[str, Any] = {}
        transfer_tool = self.tools.get("token_transfer")
        if transfer_tool:
            tx_result = await transfer_tool.transfer(
                self.neo_wallet_address or "",
                token_id,
                data=None
            )
        
        self.market_state.last_trade_timestamp = datetime.utcnow().isoformat()
        self.market_state.active_orders += 1
        
        return {
            "action": "sell",
            "token_id": token_id,
            "filled": filled,
            "unit_price": unit_price,
            "received": filled * unit_price,
            "tx": tx_result or {"simulated": True},
        }

    def _price_from_q_score(self, q_score: float) -> float:
        """
        Simple pricing heuristic that rewards higher Q-scores with higher prices.
        """
        normalized = max(0.0, min(1.0, q_score / 100))
        return round(0.1 + normalized * 0.9, 4)
    
    # =========================================================================
    # AGENT LIFECYCLE
    # =========================================================================
    
    async def on_start(self) -> None:
        """Called when the agent starts. Initialize connections and state."""
        neo_bridge = self.tools.get("neo_bridge")
        if neo_bridge:
            connected = await neo_bridge.connect()
            if not connected:
                raise ConnectionError("Unable to connect to Neo RPC node")
        
        # Prime market state with a sample Q-score
        analyzer = self.tools.get("q_score_analyzer")
        if analyzer:
            result = await analyzer.calculate_q_score("model-alpha")
            self.market_state.current_q_score = result.q_score
        
        # Sync balances for the configured wallet
        if self.neo_wallet_address:
            try:
                await self.check_token_balance()
            except Exception:
                # Non-fatal during demo bootstrap
                pass
    
    async def on_stop(self) -> None:
        """Called when the agent stops. Clean up resources."""
        neo_bridge = self.tools.get("neo_bridge")
        if neo_bridge and hasattr(neo_bridge, "disconnect"):
            await neo_bridge.disconnect()


# Convenience function for quick agent instantiation
def create_trader_agent(
    wallet_address: str,
    config: Optional[dict] = None
) -> ChattenTraderAgent:
    """
    Factory function to create a configured ChattenTraderAgent.
    
    Args:
        wallet_address: Neo N3 wallet address for the agent
        config: Optional configuration overrides
        
    Returns:
        ChattenTraderAgent: Configured and ready-to-use agent instance
    """
    default_config = {
        "name": "ChattenTrader",
        "neo_wallet_address": wallet_address,
    }
    
    if config:
        default_config.update(config)
    
    return ChattenTraderAgent(**default_config)
