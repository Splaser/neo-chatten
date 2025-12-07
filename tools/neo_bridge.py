"""
Neo Bridge Tool

Core SpoonOS tool for connecting agents to the Neo N3 blockchain.
Handles RPC communication, transaction signing, and contract invocation.
"""
import httpx

from typing import Any, Optional
from dataclasses import dataclass

# SpoonOS SDK imports
try:
    from spoon_ai_sdk import Tool, ToolResult
    from spoon_ai_sdk.tools import BaseTool
except ImportError:
    # Development fallback
    Tool = object
    ToolResult = dict
    BaseTool = object

# Neo3 Python SDK imports
try:
    from neo3.api.wrappers import ChainFacade, NeoRpcClient
    from neo3.wallet import Wallet, Account
    from neo3.core.types import UInt160, UInt256
    from neo3.network.payloads.transaction import Transaction
    NEO3_AVAILABLE = True
except ImportError:
    # Development fallback
    NEO3_AVAILABLE = False
    ChainFacade = object
    NeoRpcClient = object
    Wallet = object
    Account = object
    UInt160 = bytes
    UInt256 = bytes
    Transaction = object


@dataclass
class NeoConfig:
    """Configuration for Neo N3 connection."""
    
    rpc_url: str = "https://mainnet1.neo.coz.io:443"
    network_magic: int = 860833102  # MainNet magic
    wallet_path: Optional[str] = None
    wallet_password: Optional[str] = None


@dataclass
class TransactionResult:
    """Result of a Neo N3 transaction."""
    
    tx_hash: str
    block_height: Optional[int] = None
    gas_consumed: float = 0.0
    state: str = "NONE"
    notifications: list = None
    
    def __post_init__(self):
        if self.notifications is None:
            self.notifications = []


class NeoBridgeTool(BaseTool):
    """
    SpoonOS Tool for Neo N3 blockchain interaction.
    
    This tool provides the core bridge between SpoonOS agents and the
    Neo N3 blockchain, enabling:
    - RPC node communication
    - Wallet management and transaction signing
    - Smart contract invocation
    - Transaction monitoring
    
    Attributes:
        name: Tool identifier
        description: Tool description for agent context
        config: Neo N3 connection configuration
    """
    
    name: str = "neo_bridge"
    description: str = """
    Bridge tool for Neo N3 blockchain operations. Use this tool to:
    - Connect to Neo N3 RPC nodes
    - Read blockchain state
    - Sign and broadcast transactions
    - Invoke smart contracts
    """
    
    def __init__(self, config: Optional[NeoConfig] = None) -> None:
        """
        Initialize the Neo Bridge Tool.
        
        Args:
            config: Neo N3 connection configuration
        """
        super().__init__()
        self.config = config or NeoConfig()
        self._client: Optional[NeoRpcClient] = None
        self._facade: Optional[ChainFacade] = None
        self._wallet: Optional[Wallet] = None
        self._account: Optional[Account] = None
    
    # =========================================================================
    # CONNECTION MANAGEMENT
    # =========================================================================
    
    async def connect(self) -> bool:
        """
        Establish connection to Neo N3 RPC node.
        """
        try:
            # 打一条 getblockcount 当作健康检查
            result = await self._rpc_call("getblockcount")
            # 如果没有异常，就认为连通
            return isinstance(result, int) and result > 0
        except Exception as e:
            # 失败就清空 client，方便重试
            self._client = None
            print(f"[NeoBridge] Failed to connect RPC: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection to Neo N3 RPC node."""
        if self._client is not None:
            try:
                await self._client.aclose()  # httpx.AsyncClient.close
            finally:
                self._client = None
    
    def is_connected(self) -> bool:
        """
        Check if connected to RPC node.
        """
        return self._client is not None
    
    # =========================================================================
    # WALLET OPERATIONS
    # =========================================================================
    
    async def load_wallet(
        self,
        wallet_path: str,
        password: str
    ) -> bool:
        """
        Load a Neo N3 wallet for signing transactions.
        
        Args:
            wallet_path: Path to NEP-6 wallet file
            password: Wallet decryption password
            
        Returns:
            bool: True if wallet loaded successfully
        """
        # TODO: Implement wallet loading
        # self._wallet = Wallet.load(wallet_path, password)
        # self._account = self._wallet.accounts[0]
        return False
    
    def get_address(self) -> Optional[str]:
        """
        Get the current wallet address.
        
        Returns:
            str: Neo N3 address or None if no wallet loaded
        """
        # TODO: Implement address retrieval
        # if self._account:
        #     return self._account.address
        return None
    
    # =========================================================================
    # BLOCKCHAIN QUERIES
    # =========================================================================
    
    async def get_block_height(self) -> int:
        """
        Get current block height from the Neo node.
        """
        result = await self._rpc_call("getblockcount")
        # Neo N3 通常返回整数
        return int(result)
    
    async def get_transaction(self, tx_hash: str) -> Optional[dict]:
        """
        Get transaction details by hash.
        
        Args:
            tx_hash: Transaction hash (hex string)
            
        Returns:
            dict: Transaction details or None if not found
        """
        # TODO: Implement transaction query
        return None
    
    async def wait_for_transaction(
        self,
        tx_hash: str,
        timeout: int = 60
    ) -> TransactionResult:
        """
        Wait for a transaction to be confirmed.
        
        Args:
            tx_hash: Transaction hash to monitor
            timeout: Maximum seconds to wait
            
        Returns:
            TransactionResult: Final transaction result
        """
        # TODO: Implement transaction monitoring
        return TransactionResult(tx_hash=tx_hash)
    
    # =========================================================================
    # CONTRACT INVOCATION
    # =========================================================================
    
    async def invoke_contract(
        self,
        contract_hash: str,
        method: str,
        params: list[Any] | None = None,
        sign: bool = True,
    ) -> TransactionResult:
        """
        Invoke a smart contract method.
        当前实现仍然是 test invoke，只是把结果包装成 TransactionResult。
        """
        rpc_params = [contract_hash, method, params or []]
        result = await self._rpc_call("invokefunction", rpc_params)

        tx_hash = result.get("txid", "") or result.get("hash", "")
        gas = float(result.get("gasconsumed", 0.0))
        state = result.get("state", "HALT")
        notifications = result.get("notifications", [])

        return TransactionResult(
            tx_hash=tx_hash,
            gas_consumed=gas,
            state=state,
            notifications=notifications,
        )

    
    async def test_invoke(
        self,
        contract_hash: str,
        method: str,
        params: list[Any] | None = None,
    ) -> dict:
        """
        Perform a test invoke of a smart contract (read-only).
        `params` 这里暂时假定已经是 Neo N3 RPC 期望的参数对象列表。
        """
        rpc_params = [contract_hash, method, params or []]
        result = await self._rpc_call("invokefunction", rpc_params)
        return result

    async def _rpc_call(self, method: str, params: list[Any] | None = None) -> Any:
        """
        Internal helper to perform a JSON-RPC call to the Neo node.
        """
        if self._client is None:
            # Lazy init HTTP client
            self._client = httpx.AsyncClient(
                base_url=self.config.rpc_url,
                timeout=10.0,
            )

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1,
        }

        resp = await self._client.post("", json=payload)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"Neo RPC error: {data['error']}")

        return data.get("result")

    
    # =========================================================================
    # TOOL INTERFACE (SpoonOS)
    # =========================================================================
    
    async def run(self, **kwargs: Any) -> ToolResult:
        """
        Dispatch method for SpoonOS.
        """
        action = kwargs.get("action", "")

        if action == "connect":
            ok = await self.connect()
            return {"connected": ok}

        if action == "block_height":
            height = await self.get_block_height()
            return {"block_height": height}

        if action == "invokefunction":
            return await self.test_invoke(
                contract_hash=kwargs.get("contract_hash", ""),
                method=kwargs.get("method", ""),
                params=kwargs.get("params") or [],
            )

        return {"error": "Unknown action", "action": action}
