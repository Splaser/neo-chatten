"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CHATTEN COMPUTE-FI PROTOCOL                              ║
║                     NEP-11 Divisible + Marketplace                           ║
║                                                                              ║
║  A Hyperledger-style Compute Finance Protocol on Neo N3                     ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  BASE ASSET: COMPUTE (NEP-11 SFT)  │  QUOTE ASSET: $GAS            │    ║
║  │  Token ID = Model Hash             │  All prices in GAS             │    ║
║  │  8 Decimals for fractional trading │  Dynamic oracle pricing        │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  Features:                                                                   ║
║  • Semi-Fungible Token (SFT) - Token ID = sha256(model_name)                ║
║  • Built-in DEX - Buy/Sell compute with GAS                                 ║
║  • Oracle Pricing - Dynamic price updates from SpoonOS agents               ║
║  • Provider Registry - Home/Indie/Enterprise compute suppliers              ║
║  • Microfinance - Lock/Unlock for collateralization                         ║
║  • A2A Payments - onNEP11Payment for Pay-and-Execute                        ║
║                                                                              ║
║  Standard: NEP-11 Divisible + NEP-17 Receiver                               ║
║  Compiler: neo3-boa                                                         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from typing import Any, List, Union, cast

# =============================================================================
# NEO3-BOA IMPORTS
# =============================================================================

from boa3.builtin.compile_time import public, NeoMetadata, metadata
from boa3.builtin.contract import Nep11TransferEvent, Nep17TransferEvent, abort
from boa3.builtin.interop import runtime, storage
from boa3.builtin.interop.blockchain import get_contract, current_index, Transaction
from boa3.builtin.interop.contract import (
    call_contract,
    update_contract,
    destroy_contract,
    GAS as GAS_SCRIPT,
    NEO as NEO_SCRIPT,
)
from boa3.builtin.interop.crypto import hash160, hash256, sha256
from boa3.builtin.interop.iterator import Iterator
from boa3.builtin.interop.runtime import (
    check_witness,
    calling_script_hash,
    executing_script_hash,
    script_container,
    get_time,
    get_random,
    get_notifications,
)
from boa3.builtin.interop.storage import (
    get,
    put,
    delete,
    find,
    get_context,
    get_read_only_context,
    StorageContext,
    StorageMap,
)
from boa3.builtin.interop.stdlib import serialize, deserialize, itoa, atoi
from boa3.builtin.type import UInt160, UInt256
from boa3.builtin.nativecontract.gas import GAS


# =============================================================================
# CONTRACT METADATA
# =============================================================================

@metadata
def manifest_metadata() -> NeoMetadata:
    """
    Compute-Fi Protocol metadata for Neo N3 deployment.
    """
    meta = NeoMetadata()
    meta.name = "ChattenComputeFi"
    meta.author = "Chatten DAO"
    meta.description = "Compute-Fi Protocol: NEP-11 SFT + GAS Marketplace"
    meta.email = "protocol@chatten.io"
    meta.version = "3.0.0"
    meta.supported_standards = ["NEP-11", "NEP-17-Receiver"]
    meta.add_permission(contract='*', methods='*')
    return meta


# =============================================================================
# STORAGE PREFIXES (Single-byte for gas efficiency)
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Core Token Storage (0x01-0x0F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_BALANCE = b'\x01'           # {owner}_{token_id} -> amount (int)
PREFIX_SUPPLY = b'\x02'            # {token_id} -> total supply for this token
PREFIX_TOKEN_DATA = b'\x03'        # {token_id} -> serialized token metadata
PREFIX_ACCOUNT_TOKENS = b'\x04'    # {owner} -> serialized list of token_ids held

# ─────────────────────────────────────────────────────────────────────────────
# Provider Registry (0x10-0x1F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_PROVIDER = b'\x10'          # {provider_address} -> serialized provider data
PREFIX_PROVIDER_LIST = b'\x11'     # Single key -> serialized list of all providers

# ─────────────────────────────────────────────────────────────────────────────
# Authorization & Approvals (0x20-0x2F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_APPROVED = b'\x20'          # {owner}_{token_id}_{spender} -> approved amount
PREFIX_ORACLE = b'\x21'            # {oracle_address} -> bool (is authorized oracle)
PREFIX_MINTER = b'\x22'            # {minter_address} -> bool (is authorized minter)

# ─────────────────────────────────────────────────────────────────────────────
# Microfinance / Collateral Locks (0x30-0x3F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_LOCK = b'\x30'              # {owner}_{token_id} -> serialized lock data
PREFIX_TOTAL_LOCKED = b'\x31'      # {owner}_{token_id} -> locked amount (int)

# ─────────────────────────────────────────────────────────────────────────────
# Contract State (0x40-0x4F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_ADMIN = b'\x40'             # Single key -> admin UInt160
PREFIX_PAUSED = b'\x41'            # Single key -> bool (is paused)
PREFIX_TOTAL_SUPPLY = b'\x42'      # Single key -> total supply across all tokens
PREFIX_REENTRANCY = b'\x43'        # Single key -> bool (reentrancy guard)

# ─────────────────────────────────────────────────────────────────────────────
# Governance (0x50-0x5F)
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_GOVERNANCE = b'\x50'        # Single key -> governance contract hash

# ─────────────────────────────────────────────────────────────────────────────
# MARKETPLACE / PRICING ENGINE (0x60-0x7F) *** NEW ***
# ─────────────────────────────────────────────────────────────────────────────
PREFIX_PRICE = b'\x60'             # {token_id} -> current price in GAS (int)
PREFIX_GAS_RESERVE = b'\x61'       # Single key -> total GAS held by contract
PREFIX_SWAP_FEE_BPS = b'\x62'      # Single key -> swap fee in basis points (100 = 1%)
PREFIX_PRICE_HISTORY = b'\x63'     # {token_id}_{block} -> historical price
PREFIX_PRICE_ORACLE = b'\x64'      # {token_id} -> oracle that last updated price
PREFIX_MIN_PRICE = b'\x65'         # {token_id} -> minimum price floor
PREFIX_MODEL_REGISTRY = b'\x66'    # {model_name_hash} -> model_id mapping


# =============================================================================
# CONSTANTS
# =============================================================================

# Token Configuration
TOKEN_SYMBOL: str = "COMPUTE"
TOKEN_DECIMALS: int = 8
TOKEN_NAME: str = "Chatten Compute Token"

# Decimal multipliers
ONE_TOKEN: int = 100_000_000       # 1.0 COMPUTE = 10^8 units
ONE_GAS: int = 100_000_000         # 1.0 GAS = 10^8 units

# Quality Score Thresholds
MIN_QUALITY_SCORE: int = 50
MAX_QUALITY_SCORE: int = 100

# Lock Configuration
MIN_LOCK_BLOCKS: int = 100         # ~25 minutes
MAX_LOCK_BLOCKS: int = 2_102_400   # ~1 year

# Marketplace Configuration
DEFAULT_SWAP_FEE_BPS: int = 30     # 0.3% swap fee (30 basis points)
MAX_SWAP_FEE_BPS: int = 500        # Maximum 5% fee
MIN_SWAP_AMOUNT: int = 1000        # Minimum swap amount (0.00001 tokens)
DEFAULT_PRICE_GAS: int = ONE_GAS   # Default price: 1 COMPUTE = 1 GAS

# Zero address for mint/burn events
ZERO_ADDRESS: UInt160 = UInt160(b'\x00' * 20)


# =============================================================================
# EVENTS
# =============================================================================

# NEP-11 Transfer event
on_transfer = Nep11TransferEvent

# Custom marketplace events (using Nep17 format for simplicity)
# on_swap = Nep17TransferEvent  # Emitted on buy/sell


# =============================================================================
# DEPLOY / INITIALIZATION
# =============================================================================

@public
def _deploy(data: Any, update: bool) -> None:
    """
    Contract deployment/update handler.
    """
    if not update:
        ctx = get_context()
        
        # Set deployer as initial admin
        tx = cast(Transaction, script_container)
        deployer = tx.sender
        put(ctx, PREFIX_ADMIN, deployer)
        
        # Initialize contract state
        put(ctx, PREFIX_PAUSED, False)
        put(ctx, PREFIX_TOTAL_SUPPLY, 0)
        put(ctx, PREFIX_GAS_RESERVE, 0)
        put(ctx, PREFIX_SWAP_FEE_BPS, DEFAULT_SWAP_FEE_BPS)
        put(ctx, PREFIX_REENTRANCY, False)
        
        # Deployer is initial oracle and minter
        _set_oracle(deployer, True)
        _set_minter(deployer, True)


# =============================================================================
# NEP-11 STANDARD METHODS
# =============================================================================

@public(safe=True)
def symbol() -> str:
    """Returns the token symbol: "COMPUTE"."""
    return TOKEN_SYMBOL


@public(safe=True)
def decimals() -> int:
    """Returns decimals: 8 (allows trading 0.00000001 compute units)."""
    return TOKEN_DECIMALS


@public(safe=True)
def totalSupply() -> int:
    """Returns total supply across all token IDs."""
    ctx = get_read_only_context()
    supply = get(ctx, PREFIX_TOTAL_SUPPLY)
    if len(supply) == 0:
        return 0
    return supply.to_int()


@public(safe=True)
def balanceOf(owner: UInt160) -> int:
    """Returns total balance of owner across all token IDs."""
    assert len(owner) == 20, "Invalid owner address"
    
    ctx = get_read_only_context()
    total_balance = 0
    token_ids = _get_account_tokens(ctx, owner)
    for token_id in token_ids:
        balance = _get_balance(ctx, owner, token_id)
        total_balance += balance
    return total_balance


@public(safe=True)
def balanceOfToken(owner: UInt160, token_id: bytes) -> int:
    """Returns balance of specific token ID for owner."""
    assert len(owner) == 20, "Invalid owner address"
    assert len(token_id) > 0, "Invalid token_id"
    
    ctx = get_read_only_context()
    return _get_balance(ctx, owner, token_id)


@public(safe=True)
def tokensOf(owner: UInt160) -> Iterator:
    """Returns iterator of all token IDs owned by address."""
    assert len(owner) == 20, "Invalid owner address"
    ctx = get_read_only_context()
    prefix = PREFIX_BALANCE + owner
    return find(ctx, prefix)


@public(safe=True)
def ownerOf(token_id: bytes) -> Iterator:
    """Returns iterator of all owners of a token ID."""
    assert len(token_id) > 0, "Invalid token_id"
    ctx = get_read_only_context()
    return find(ctx, PREFIX_BALANCE)


@public(safe=True)
def properties(token_id: bytes) -> dict:
    """Returns token properties/metadata."""
    assert len(token_id) > 0, "Invalid token_id"
    ctx = get_read_only_context()
    data = get(ctx, PREFIX_TOKEN_DATA + token_id)
    if len(data) == 0:
        return {}
    return cast(dict, deserialize(data))


@public(safe=True)
def tokenSupply(token_id: bytes) -> int:
    """Returns total supply of specific token ID."""
    assert len(token_id) > 0, "Invalid token_id"
    ctx = get_read_only_context()
    supply = get(ctx, PREFIX_SUPPLY + token_id)
    if len(supply) == 0:
        return 0
    return supply.to_int()


# =============================================================================
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    HYPERLEDGER PRICING ENGINE                            ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  The pricing engine stores current spot prices for each Model ID         ║
# ║  (token_id). All prices are denominated in GAS.                          ║
# ║                                                                          ║
# ║  Price Formula (set by Oracle):                                          ║
# ║  Price = f(Demand, Quality, Supply, Market Conditions)                   ║
# ║                                                                          ║
# ║  The Oracle (SpoonOS Agent) updates prices dynamically based on:         ║
# ║  • Real-time demand metrics                                              ║
# ║  • Quality scores from compute verification                              ║
# ║  • Supply availability                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# =============================================================================

@public(safe=True)
def get_current_price(model_id: bytes) -> int:
    """
    Get the current spot price for a model's compute in GAS.
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  SAFE METHOD - Can be queried by frontend without paying GAS fees   ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    The price represents how much GAS is needed to purchase 1.0 unit
    (10^8 base units) of compute capacity for the specified model.
    
    Args:
        model_id: The model identifier (e.g., b"gpt-4", b"llama-3-70b")
        
    Returns:
        int: Price in GAS base units (10^8 = 1 GAS) for 1.0 COMPUTE
             Returns 0 if model is not registered
    
    Example:
        price = get_current_price(b"gpt-4")
        # If price = 500_000_000 (0.5 GAS)
        # Then 1.0 COMPUTE for gpt-4 costs 0.5 GAS
    """
    assert len(model_id) > 0, "Invalid model_id"
    
    ctx = get_read_only_context()
    token_id = sha256(model_id)
    
    price_data = get(ctx, PREFIX_PRICE + token_id)
    if len(price_data) == 0:
        return 0  # Model not registered
    
    return price_data.to_int()


@public(safe=True)
def get_price_by_token_id(token_id: bytes) -> int:
    """
    Get price by token_id directly (already hashed).
    
    Args:
        token_id: The token hash (sha256 of model_id)
        
    Returns:
        int: Price in GAS base units
    """
    assert len(token_id) > 0, "Invalid token_id"
    
    ctx = get_read_only_context()
    price_data = get(ctx, PREFIX_PRICE + token_id)
    if len(price_data) == 0:
        return 0
    return price_data.to_int()


@public
def update_price_oracle(model_id: bytes, new_price_gas: int) -> bool:
    """
    Update the spot price for a model's compute.
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  RESTRICTED: Only authorized Oracles (SpoonOS Agents) can update    ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  This method supports the "Dynamic Update" requirement.              ║
    ║  SpoonOS agents can call this every minute (or as needed) to keep   ║
    ║  prices aligned with real-time market conditions.                   ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Args:
        model_id: The model identifier (e.g., b"gpt-4")
        new_price_gas: New price in GAS base units (10^8 = 1 GAS)
        
    Returns:
        bool: True if update succeeded
        
    Example:
        # Set gpt-4 compute to 0.5 GAS per unit
        update_price_oracle(b"gpt-4", 50_000_000)
    """
    assert not _is_paused(), "Contract is paused"
    assert len(model_id) > 0, "Invalid model_id"
    assert new_price_gas > 0, "Price must be positive"
    
    # Authorization: Only oracles can update prices
    caller = calling_script_hash()
    assert _is_oracle(caller), "Not authorized oracle"
    
    ctx = get_context()
    token_id = sha256(model_id)
    
    # Check minimum price floor if set
    min_price_data = get(ctx, PREFIX_MIN_PRICE + token_id)
    if len(min_price_data) > 0:
        min_price = min_price_data.to_int()
        assert new_price_gas >= min_price, "Price below minimum floor"
    
    # Store new price
    put(ctx, PREFIX_PRICE + token_id, new_price_gas)
    
    # Store price history (for analytics)
    block_index = current_index()
    history_key = PREFIX_PRICE_HISTORY + token_id + block_index.to_bytes()
    put(ctx, history_key, new_price_gas)
    
    # Record which oracle updated
    put(ctx, PREFIX_PRICE_ORACLE + token_id, caller)
    
    # Initialize token data if first price set (registers the model)
    existing_data = get(ctx, PREFIX_TOKEN_DATA + token_id)
    if len(existing_data) == 0:
        token_data = {
            "name": "Compute: " + model_id.to_str(),
            "model_id": model_id,
            "avg_quality_score": 75,  # Default quality
            "total_mints": 0,
            "created_at": block_index
        }
        put(ctx, PREFIX_TOKEN_DATA + token_id, serialize(token_data))
    
    return True


@public
def set_price_floor(model_id: bytes, min_price: int) -> bool:
    """
    Set minimum price floor for a model (admin only).
    
    Args:
        model_id: Model identifier
        min_price: Minimum allowed price (0 to remove floor)
        
    Returns:
        bool: True if succeeded
    """
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    
    ctx = get_context()
    token_id = sha256(model_id)
    
    if min_price > 0:
        put(ctx, PREFIX_MIN_PRICE + token_id, min_price)
    else:
        delete(ctx, PREFIX_MIN_PRICE + token_id)
    
    return True


@public(safe=True)
def get_price_info(model_id: bytes) -> dict:
    """
    Get comprehensive price information for a model.
    
    Returns:
        dict: Price info including current price, last update, oracle
    """
    ctx = get_read_only_context()
    token_id = sha256(model_id)
    
    price_data = get(ctx, PREFIX_PRICE + token_id)
    if len(price_data) == 0:
        return {}
    
    oracle_data = get(ctx, PREFIX_PRICE_ORACLE + token_id)
    min_price_data = get(ctx, PREFIX_MIN_PRICE + token_id)
    
    return {
        "price_gas": price_data.to_int(),
        "token_id": token_id,
        "oracle": oracle_data if len(oracle_data) > 0 else ZERO_ADDRESS,
        "min_price": min_price_data.to_int() if len(min_price_data) > 0 else 0
    }


# =============================================================================
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    SWAP MECHANISM (DEX TRADING)                          ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  Buy Compute: User sends GAS → Receives COMPUTE tokens                   ║
# ║  Sell Compute: User burns COMPUTE → Receives GAS from reserve            ║
# ║                                                                          ║
# ║  All swaps go through the contract's GAS reserve.                        ║
# ║  A small fee (default 0.3%) is charged on each swap.                     ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# =============================================================================

@public
def buy_compute(buyer: UInt160, model_id: bytes, gas_amount: int) -> int:
    """
    Buy COMPUTE tokens with GAS.
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                      BUY FLOW                                        ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  1. User calls buy_compute() with GAS attached                       ║
    ║  2. Contract reads current price: get_current_price(model_id)        ║
    ║  3. Calculates: compute_amount = (gas_amount - fee) / price          ║
    ║  4. Mints COMPUTE tokens to buyer                                    ║
    ║  5. GAS is added to contract reserve                                 ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    NOTE: The actual GAS must be sent via onNEP17Payment callback first,
    or this can be called atomically after GAS.transfer() to this contract.
    
    Args:
        buyer: Address to receive COMPUTE tokens
        model_id: Which model's compute to buy
        gas_amount: Amount of GAS to spend (including fee)
        
    Returns:
        int: Amount of COMPUTE tokens minted
    """
    assert not _is_paused(), "Contract is paused"
    assert len(buyer) == 20, "Invalid buyer"
    assert len(model_id) > 0, "Invalid model_id"
    assert gas_amount >= MIN_SWAP_AMOUNT, "Amount too small"
    
    # Reentrancy guard
    assert not _is_reentrancy_locked(), "Reentrancy detected"
    _set_reentrancy_lock(True)
    
    ctx = get_context()
    token_id = sha256(model_id)
    
    # Get current price
    price = get_current_price(model_id)
    assert price > 0, "Model not registered or price not set"
    
    # Calculate fee
    fee_bps = _get_swap_fee_bps(ctx)
    fee_amount = (gas_amount * fee_bps) // 10000
    net_gas = gas_amount - fee_amount
    
    # Calculate compute amount to mint
    # compute_amount = net_gas / price * ONE_TOKEN
    # To avoid precision loss: compute_amount = (net_gas * ONE_TOKEN) / price
    compute_amount = (net_gas * ONE_TOKEN) // price
    assert compute_amount > 0, "Compute amount too small"
    
    # Mint COMPUTE tokens to buyer
    _mint_internal(ctx, buyer, token_id, compute_amount, model_id)
    
    # Update GAS reserve
    current_reserve = _get_gas_reserve(ctx)
    put(ctx, PREFIX_GAS_RESERVE, current_reserve + gas_amount)
    
    # Release reentrancy lock
    _set_reentrancy_lock(False)
    
    return compute_amount


@public
def sell_compute(
    seller: UInt160,
    model_id: bytes,
    compute_amount: int
) -> int:
    """
    Sell COMPUTE tokens for GAS.
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                      SELL FLOW                                       ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  1. User calls sell_compute() with amount to sell                    ║
    ║  2. Contract burns user's COMPUTE tokens                             ║
    ║  3. Calculates: gas_out = (compute_amount * price) - fee             ║
    ║  4. Transfers GAS from reserve to seller                             ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    Args:
        seller: Address selling COMPUTE (must be caller or approved)
        model_id: Which model's compute to sell
        compute_amount: Amount of COMPUTE to sell
        
    Returns:
        int: Amount of GAS received
    """
    assert not _is_paused(), "Contract is paused"
    assert check_witness(seller), "Not authorized"
    assert len(model_id) > 0, "Invalid model_id"
    assert compute_amount >= MIN_SWAP_AMOUNT, "Amount too small"
    
    # Reentrancy guard
    assert not _is_reentrancy_locked(), "Reentrancy detected"
    _set_reentrancy_lock(True)
    
    ctx = get_context()
    token_id = sha256(model_id)
    
    # Verify seller has sufficient unlocked balance
    current_balance = _get_balance(ctx, seller, token_id)
    locked_amount = _get_locked_amount(ctx, seller, token_id)
    available = current_balance - locked_amount
    assert available >= compute_amount, "Insufficient unlocked balance"
    
    # Get current price
    price = get_current_price(model_id)
    assert price > 0, "Model not registered or price not set"
    
    # Calculate GAS output
    # gross_gas = compute_amount * price / ONE_TOKEN
    gross_gas = (compute_amount * price) // ONE_TOKEN
    
    # Apply fee
    fee_bps = _get_swap_fee_bps(ctx)
    fee_amount = (gross_gas * fee_bps) // 10000
    net_gas = gross_gas - fee_amount
    assert net_gas > 0, "Output too small after fee"
    
    # Verify reserve has enough GAS
    current_reserve = _get_gas_reserve(ctx)
    assert current_reserve >= net_gas, "Insufficient GAS reserve"
    
    # Burn COMPUTE tokens
    _burn_internal(ctx, seller, token_id, compute_amount)
    
    # Update reserve
    put(ctx, PREFIX_GAS_RESERVE, current_reserve - net_gas)
    
    # Transfer GAS to seller
    # Note: This calls GAS.transfer() which is a native contract call
    success = GAS.transfer(executing_script_hash(), seller, net_gas, None)
    assert success, "GAS transfer failed"
    
    # Release reentrancy lock
    _set_reentrancy_lock(False)
    
    return net_gas


@public(safe=True)
def get_buy_quote(model_id: bytes, gas_amount: int) -> int:
    """
    Get quote for buying compute with GAS (preview without executing).
    
    Args:
        model_id: Model to buy
        gas_amount: GAS to spend
        
    Returns:
        int: COMPUTE tokens that would be received
    """
    if gas_amount < MIN_SWAP_AMOUNT:
        return 0
    
    ctx = get_read_only_context()
    token_id = sha256(model_id)
    
    price_data = get(ctx, PREFIX_PRICE + token_id)
    if len(price_data) == 0:
        return 0
    price = price_data.to_int()
    
    fee_bps = _get_swap_fee_bps(ctx)
    fee_amount = (gas_amount * fee_bps) // 10000
    net_gas = gas_amount - fee_amount
    
    return (net_gas * ONE_TOKEN) // price


@public(safe=True)
def get_sell_quote(model_id: bytes, compute_amount: int) -> int:
    """
    Get quote for selling compute for GAS (preview without executing).
    
    Args:
        model_id: Model to sell
        compute_amount: COMPUTE to sell
        
    Returns:
        int: GAS that would be received
    """
    if compute_amount < MIN_SWAP_AMOUNT:
        return 0
    
    ctx = get_read_only_context()
    token_id = sha256(model_id)
    
    price_data = get(ctx, PREFIX_PRICE + token_id)
    if len(price_data) == 0:
        return 0
    price = price_data.to_int()
    
    gross_gas = (compute_amount * price) // ONE_TOKEN
    
    fee_bps = _get_swap_fee_bps(ctx)
    fee_amount = (gross_gas * fee_bps) // 10000
    
    return gross_gas - fee_amount


@public(safe=True)
def get_gas_reserve() -> int:
    """Get current GAS reserve held by contract."""
    ctx = get_read_only_context()
    return _get_gas_reserve(ctx)


@public(safe=True)
def get_swap_fee_bps() -> int:
    """Get current swap fee in basis points (100 = 1%)."""
    ctx = get_read_only_context()
    return _get_swap_fee_bps(ctx)


@public
def set_swap_fee(fee_bps: int) -> bool:
    """Set swap fee (admin only)."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    assert fee_bps >= 0 and fee_bps <= MAX_SWAP_FEE_BPS, "Invalid fee"
    
    ctx = get_context()
    put(ctx, PREFIX_SWAP_FEE_BPS, fee_bps)
    return True


# =============================================================================
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                    NEP-17 PAYMENT RECEIVER                               ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  This contract can receive GAS payments via the NEP-17 standard.         ║
# ║  When GAS is sent to this contract, onNEP17Payment is triggered.         ║
# ║                                                                          ║
# ║  SECURITY: We strictly verify the asset hash is GAS.                     ║
# ║  Other tokens are REJECTED to prevent attacks.                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
# =============================================================================

@public
def onNEP17Payment(from_address: UInt160, amount: int, data: Any) -> None:
    """
    Handle incoming NEP-17 token payments.
    
    ╔══════════════════════════════════════════════════════════════════════╗
    ║  CRITICAL SECURITY CHECK: Only accept GAS!                          ║
    ╠══════════════════════════════════════════════════════════════════════╣
    ║  The calling_script_hash() tells us which token contract called us. ║
    ║  We ONLY accept the native GAS contract.                            ║
    ║  Any other token transfer is REJECTED (aborted).                    ║
    ╚══════════════════════════════════════════════════════════════════════╝
    
    When data contains a model_id, this triggers an automatic buy_compute().
    Otherwise, GAS is simply added to the reserve for later purchases.
    
    Args:
        from_address: Who sent the tokens
        amount: Amount received
        data: Optional data - if bytes, treated as model_id for auto-buy
    """
    # CRITICAL: Verify this is GAS
    caller = calling_script_hash()
    assert caller == GAS_SCRIPT, "Only GAS accepted"
    
    # Update reserve balance
    ctx = get_context()
    current_reserve = _get_gas_reserve(ctx)
    put(ctx, PREFIX_GAS_RESERVE, current_reserve + amount)
    
    # If data contains a model_id, auto-execute buy
    if data is not None:
        if isinstance(data, bytes) and len(data) > 0:
            # Data is model_id - execute buy
            # Adjust reserve back (buy_compute will add it again)
            put(ctx, PREFIX_GAS_RESERVE, current_reserve)
            buy_compute(from_address, data, amount)


# =============================================================================
# TRANSFER OPERATIONS (A2A PAYMENT LAYER)
# =============================================================================

@public
def transfer(
    from_address: UInt160,
    to: UInt160,
    amount: int,
    token_id: bytes,
    data: Any
) -> bool:
    """
    Transfer tokens from one address to another.
    
    NEP-11 Divisible Required Method.
    When recipient is a contract, triggers onNEP11Payment callback
    for Pay-and-Execute A2A workflows.
    """
    assert len(from_address) == 20, "Invalid from_address"
    assert len(to) == 20, "Invalid to address"
    assert amount > 0, "Amount must be positive"
    assert len(token_id) > 0, "Invalid token_id"
    assert not _is_paused(), "Contract is paused"
    
    assert check_witness(from_address) or \
           _is_approved(from_address, token_id, calling_script_hash(), amount), \
        "Not authorized"
    
    ctx = get_context()
    
    # Check unlocked balance
    current_balance = _get_balance(ctx, from_address, token_id)
    locked_amount = _get_locked_amount(ctx, from_address, token_id)
    available_balance = current_balance - locked_amount
    assert available_balance >= amount, "Insufficient unlocked balance"
    
    # Execute transfer
    _decrease_balance(ctx, from_address, token_id, amount)
    _increase_balance(ctx, to, token_id, amount)
    
    # Fire event
    on_transfer(from_address, to, amount, token_id)
    
    # A2A callback if recipient is contract
    recipient_contract = get_contract(to)
    if recipient_contract is not None:
        call_contract(to, 'onNEP11Payment', [from_address, amount, token_id, data])
    
    return True


@public
def approve(owner: UInt160, spender: UInt160, amount: int, token_id: bytes) -> bool:
    """Approve spender to transfer tokens on behalf of owner."""
    assert len(owner) == 20 and len(spender) == 20, "Invalid address"
    assert len(token_id) > 0, "Invalid token_id"
    assert check_witness(owner), "Not authorized"
    
    ctx = get_context()
    key = PREFIX_APPROVED + owner + token_id + spender
    
    if amount > 0:
        put(ctx, key, amount)
    else:
        delete(ctx, key)
    return True


@public(safe=True)
def allowance(owner: UInt160, spender: UInt160, token_id: bytes) -> int:
    """Check approved amount for spender."""
    ctx = get_read_only_context()
    key = PREFIX_APPROVED + owner + token_id + spender
    value = get(ctx, key)
    if len(value) == 0:
        return 0
    return value.to_int()


# =============================================================================
# PROVIDER REGISTRY (SUPPLY SIDE)
# =============================================================================

@public
def register_provider(name: str, endpoint: str, geo_region: str, provider_type: str) -> bool:
    """
    Register as a compute provider.
    
    Providers supply compute capacity and earn rewards for verified work.
    """
    assert not _is_paused(), "Contract is paused"
    
    provider = calling_script_hash()
    assert check_witness(provider), "Not authorized"
    
    ctx = get_context()
    
    provider_data = {
        "name": name,
        "endpoint": endpoint,
        "geo_region": geo_region,
        "provider_type": provider_type,
        "reputation_score": 50,
        "total_earned": 0,
        "registered_at": current_index(),
        "active": True
    }
    
    put(ctx, PREFIX_PROVIDER + provider, serialize(provider_data))
    _add_to_provider_list(ctx, provider)
    
    return True


@public
def mint_rewards(provider: UInt160, model_id: bytes, amount: int) -> bool:
    """
    Mint reward tokens to a provider for verified compute work.
    
    RESTRICTED: Only authorized minters (oracles) can call this.
    Used when providers prove they completed compute work.
    
    Args:
        provider: Provider address to receive rewards
        model_id: Model they provided compute for
        amount: Reward amount to mint
        
    Returns:
        bool: True if succeeded
    """
    assert not _is_paused(), "Contract is paused"
    assert len(provider) == 20, "Invalid provider"
    assert amount > 0, "Amount must be positive"
    
    caller = calling_script_hash()
    assert _is_minter(caller), "Not authorized to mint rewards"
    
    ctx = get_context()
    
    # Verify provider is registered
    provider_data_bytes = get(ctx, PREFIX_PROVIDER + provider)
    assert len(provider_data_bytes) > 0, "Provider not registered"
    
    token_id = sha256(model_id)
    
    # Mint tokens
    _mint_internal(ctx, provider, token_id, amount, model_id)
    
    # Update provider stats
    provider_data = cast(dict, deserialize(provider_data_bytes))
    provider_data["total_earned"] = provider_data["total_earned"] + amount
    put(ctx, PREFIX_PROVIDER + provider, serialize(provider_data))
    
    return True


@public
def update_provider_reputation(provider: UInt160, new_score: int) -> bool:
    """Update provider reputation (oracle only)."""
    assert not _is_paused(), "Contract is paused"
    assert new_score >= 0 and new_score <= 100, "Score must be 0-100"
    
    caller = calling_script_hash()
    assert _is_oracle(caller) or _is_governance(caller), "Not authorized"
    
    ctx = get_context()
    data = get(ctx, PREFIX_PROVIDER + provider)
    assert len(data) > 0, "Provider not registered"
    
    provider_data = cast(dict, deserialize(data))
    provider_data["reputation_score"] = new_score
    put(ctx, PREFIX_PROVIDER + provider, serialize(provider_data))
    
    return True


@public(safe=True)
def get_provider(provider: UInt160) -> dict:
    """Get provider information."""
    ctx = get_read_only_context()
    data = get(ctx, PREFIX_PROVIDER + provider)
    if len(data) == 0:
        return {}
    return cast(dict, deserialize(data))


# =============================================================================
# MINTING & BURNING
# =============================================================================

@public
def mint(to: UInt160, model_id: bytes, amount: int, quality_score: int) -> bool:
    """
    Mint new COMPUTE tokens (restricted to authorized minters).
    """
    assert not _is_paused(), "Contract is paused"
    assert len(to) == 20, "Invalid recipient"
    assert len(model_id) > 0, "Invalid model_id"
    assert amount > 0, "Amount must be positive"
    assert quality_score >= MIN_QUALITY_SCORE and quality_score <= MAX_QUALITY_SCORE, \
        "Invalid quality score"
    
    caller = calling_script_hash()
    assert _is_minter(caller), "Not authorized to mint"
    
    ctx = get_context()
    token_id = sha256(model_id)
    
    # Apply quality multiplier
    actual_amount = (amount * quality_score) // 100
    assert actual_amount > 0, "Mint amount too small"
    
    _mint_internal(ctx, to, token_id, actual_amount, model_id)
    
    return True


@public
def burn(owner: UInt160, token_id: bytes, amount: int) -> bool:
    """Burn tokens (reduce supply)."""
    assert not _is_paused(), "Contract is paused"
    assert check_witness(owner), "Not authorized"
    assert amount > 0, "Amount must be positive"
    
    ctx = get_context()
    
    current_balance = _get_balance(ctx, owner, token_id)
    locked = _get_locked_amount(ctx, owner, token_id)
    available = current_balance - locked
    assert available >= amount, "Insufficient unlocked balance"
    
    _burn_internal(ctx, owner, token_id, amount)
    
    return True


# =============================================================================
# MICROFINANCE (LOCK/UNLOCK)
# =============================================================================

@public
def lock(owner: UInt160, token_id: bytes, amount: int, duration_blocks: int) -> bool:
    """Lock tokens as collateral."""
    assert not _is_paused(), "Contract is paused"
    assert check_witness(owner), "Not authorized"
    assert amount > 0, "Amount must be positive"
    assert duration_blocks >= MIN_LOCK_BLOCKS and duration_blocks <= MAX_LOCK_BLOCKS, \
        "Invalid duration"
    
    ctx = get_context()
    
    current_balance = _get_balance(ctx, owner, token_id)
    current_locked = _get_locked_amount(ctx, owner, token_id)
    available = current_balance - current_locked
    assert available >= amount, "Insufficient unlocked balance"
    
    unlock_block = current_index() + duration_blocks
    lock_key = PREFIX_LOCK + owner + token_id
    existing_lock = get(ctx, lock_key)
    
    if len(existing_lock) == 0:
        lock_data = {"amount": amount, "unlock_block": unlock_block, "created_at": current_index()}
    else:
        lock_data = cast(dict, deserialize(existing_lock))
        lock_data["amount"] = lock_data["amount"] + amount
        if unlock_block > lock_data["unlock_block"]:
            lock_data["unlock_block"] = unlock_block
    
    put(ctx, lock_key, serialize(lock_data))
    put(ctx, PREFIX_TOTAL_LOCKED + owner + token_id, lock_data["amount"])
    
    return True


@public
def unlock(owner: UInt160, token_id: bytes) -> bool:
    """Unlock tokens after lock period."""
    assert not _is_paused(), "Contract is paused"
    assert check_witness(owner), "Not authorized"
    
    ctx = get_context()
    lock_key = PREFIX_LOCK + owner + token_id
    lock_data_bytes = get(ctx, lock_key)
    assert len(lock_data_bytes) > 0, "No lock found"
    
    lock_data = cast(dict, deserialize(lock_data_bytes))
    assert current_index() >= lock_data["unlock_block"], "Lock not expired"
    
    delete(ctx, lock_key)
    delete(ctx, PREFIX_TOTAL_LOCKED + owner + token_id)
    
    return True


@public(safe=True)
def lockedBalanceOf(owner: UInt160, token_id: bytes) -> int:
    """Get locked balance."""
    ctx = get_read_only_context()
    return _get_locked_amount(ctx, owner, token_id)


@public(safe=True)
def availableBalanceOf(owner: UInt160, token_id: bytes) -> int:
    """Get available (unlocked) balance."""
    ctx = get_read_only_context()
    total = _get_balance(ctx, owner, token_id)
    locked = _get_locked_amount(ctx, owner, token_id)
    return total - locked


# =============================================================================
# ADMIN & GOVERNANCE
# =============================================================================

@public
def pause() -> bool:
    """Pause contract (emergency)."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    ctx = get_context()
    put(ctx, PREFIX_PAUSED, True)
    return True


@public
def resume() -> bool:
    """Resume contract."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    ctx = get_context()
    put(ctx, PREFIX_PAUSED, False)
    return True


@public(safe=True)
def isPaused() -> bool:
    """Check if paused."""
    return _is_paused()


@public
def update_admin(new_admin: UInt160) -> bool:
    """Transfer admin rights."""
    assert len(new_admin) == 20, "Invalid address"
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    ctx = get_context()
    put(ctx, PREFIX_ADMIN, new_admin)
    return True


@public
def set_governance(governance_hash: UInt160) -> bool:
    """Set governance contract."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    ctx = get_context()
    put(ctx, PREFIX_GOVERNANCE, governance_hash)
    return True


@public
def set_oracle(oracle: UInt160, authorized: bool) -> bool:
    """Authorize/deauthorize oracle."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    _set_oracle(oracle, authorized)
    return True


@public
def set_minter(minter: UInt160, authorized: bool) -> bool:
    """Authorize/deauthorize minter."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    _set_minter(minter, authorized)
    return True


@public(safe=True)
def get_admin() -> UInt160:
    """Get admin address."""
    ctx = get_read_only_context()
    admin = get(ctx, PREFIX_ADMIN)
    if len(admin) == 0:
        return ZERO_ADDRESS
    return UInt160(admin)


@public(safe=True)
def is_oracle(address: UInt160) -> bool:
    """Check if oracle."""
    return _is_oracle(address)


@public(safe=True)
def is_minter(address: UInt160) -> bool:
    """Check if minter."""
    return _is_minter(address)


@public
def withdraw_gas(to: UInt160, amount: int) -> bool:
    """
    Withdraw GAS from reserve (admin only, for protocol fees).
    """
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    assert len(to) == 20, "Invalid address"
    assert amount > 0, "Amount must be positive"
    
    ctx = get_context()
    current_reserve = _get_gas_reserve(ctx)
    assert current_reserve >= amount, "Insufficient reserve"
    
    put(ctx, PREFIX_GAS_RESERVE, current_reserve - amount)
    
    success = GAS.transfer(executing_script_hash(), to, amount, None)
    assert success, "GAS transfer failed"
    
    return True


@public
def update(nef_file: bytes, manifest: bytes, data: Any) -> None:
    """Update contract code."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    update_contract(nef_file, manifest, data)


@public
def destroy() -> None:
    """Destroy contract permanently."""
    caller = calling_script_hash()
    assert _is_admin(caller), "Not authorized"
    destroy_contract()


# =============================================================================
# NEP-11 PAYMENT CALLBACK
# =============================================================================

@public
def onNEP11Payment(from_address: UInt160, amount: int, token_id: bytes, data: Any) -> None:
    """Handle incoming NEP-11 payments."""
    pass


# =============================================================================
# INTERNAL FUNCTIONS
# =============================================================================

def _get_balance(ctx: StorageContext, owner: UInt160, token_id: bytes) -> int:
    key = PREFIX_BALANCE + owner + token_id
    value = get(ctx, key)
    if len(value) == 0:
        return 0
    return value.to_int()


def _increase_balance(ctx: StorageContext, owner: UInt160, token_id: bytes, amount: int) -> None:
    key = PREFIX_BALANCE + owner + token_id
    current = _get_balance(ctx, owner, token_id)
    put(ctx, key, current + amount)
    _add_token_to_account(ctx, owner, token_id)


def _decrease_balance(ctx: StorageContext, owner: UInt160, token_id: bytes, amount: int) -> None:
    key = PREFIX_BALANCE + owner + token_id
    current = _get_balance(ctx, owner, token_id)
    new_balance = current - amount
    if new_balance > 0:
        put(ctx, key, new_balance)
    else:
        delete(ctx, key)
        _remove_token_from_account(ctx, owner, token_id)


def _get_locked_amount(ctx: StorageContext, owner: UInt160, token_id: bytes) -> int:
    value = get(ctx, PREFIX_TOTAL_LOCKED + owner + token_id)
    if len(value) == 0:
        return 0
    return value.to_int()


def _get_account_tokens(ctx: StorageContext, owner: UInt160) -> List[bytes]:
    data = get(ctx, PREFIX_ACCOUNT_TOKENS + owner)
    if len(data) == 0:
        return []
    return cast(List[bytes], deserialize(data))


def _add_token_to_account(ctx: StorageContext, owner: UInt160, token_id: bytes) -> None:
    tokens = _get_account_tokens(ctx, owner)
    if token_id not in tokens:
        tokens.append(token_id)
        put(ctx, PREFIX_ACCOUNT_TOKENS + owner, serialize(tokens))


def _remove_token_from_account(ctx: StorageContext, owner: UInt160, token_id: bytes) -> None:
    tokens = _get_account_tokens(ctx, owner)
    if token_id in tokens:
        tokens.remove(token_id)
        if len(tokens) > 0:
            put(ctx, PREFIX_ACCOUNT_TOKENS + owner, serialize(tokens))
        else:
            delete(ctx, PREFIX_ACCOUNT_TOKENS + owner)


def _add_to_provider_list(ctx: StorageContext, provider: UInt160) -> None:
    data = get(ctx, PREFIX_PROVIDER_LIST)
    if len(data) == 0:
        providers = [provider]
    else:
        providers = cast(List[UInt160], deserialize(data))
        if provider not in providers:
            providers.append(provider)
    put(ctx, PREFIX_PROVIDER_LIST, serialize(providers))


def _mint_internal(ctx: StorageContext, to: UInt160, token_id: bytes, amount: int, model_id: bytes) -> None:
    """Internal mint function."""
    # Update token data
    existing_data = get(ctx, PREFIX_TOKEN_DATA + token_id)
    if len(existing_data) == 0:
        token_data = {
            "name": "Compute: " + model_id.to_str(),
            "model_id": model_id,
            "avg_quality_score": 75,
            "total_mints": 1,
            "created_at": current_index()
        }
        put(ctx, PREFIX_TOKEN_DATA + token_id, serialize(token_data))
    else:
        token_data = cast(dict, deserialize(existing_data))
        token_data["total_mints"] = token_data["total_mints"] + 1
        put(ctx, PREFIX_TOKEN_DATA + token_id, serialize(token_data))
    
    # Update balance
    _increase_balance(ctx, to, token_id, amount)
    
    # Update token supply
    current_token_supply = get(ctx, PREFIX_SUPPLY + token_id)
    if len(current_token_supply) == 0:
        new_token_supply = amount
    else:
        new_token_supply = current_token_supply.to_int() + amount
    put(ctx, PREFIX_SUPPLY + token_id, new_token_supply)
    
    # Update total supply
    current_total = get(ctx, PREFIX_TOTAL_SUPPLY)
    if len(current_total) == 0:
        new_total = amount
    else:
        new_total = current_total.to_int() + amount
    put(ctx, PREFIX_TOTAL_SUPPLY, new_total)
    
    # Fire mint event
    on_transfer(ZERO_ADDRESS, to, amount, token_id)


def _burn_internal(ctx: StorageContext, owner: UInt160, token_id: bytes, amount: int) -> None:
    """Internal burn function."""
    _decrease_balance(ctx, owner, token_id, amount)
    
    current_token_supply = get(ctx, PREFIX_SUPPLY + token_id).to_int()
    put(ctx, PREFIX_SUPPLY + token_id, current_token_supply - amount)
    
    current_total = get(ctx, PREFIX_TOTAL_SUPPLY).to_int()
    put(ctx, PREFIX_TOTAL_SUPPLY, current_total - amount)
    
    on_transfer(owner, ZERO_ADDRESS, amount, token_id)


def _get_gas_reserve(ctx: StorageContext) -> int:
    value = get(ctx, PREFIX_GAS_RESERVE)
    if len(value) == 0:
        return 0
    return value.to_int()


def _get_swap_fee_bps(ctx: StorageContext) -> int:
    value = get(ctx, PREFIX_SWAP_FEE_BPS)
    if len(value) == 0:
        return DEFAULT_SWAP_FEE_BPS
    return value.to_int()


def _is_paused() -> bool:
    ctx = get_read_only_context()
    value = get(ctx, PREFIX_PAUSED)
    if len(value) == 0:
        return False
    return value.to_bool()


def _is_admin(address: UInt160) -> bool:
    ctx = get_read_only_context()
    admin = get(ctx, PREFIX_ADMIN)
    return admin == address


def _is_governance(address: UInt160) -> bool:
    ctx = get_read_only_context()
    governance = get(ctx, PREFIX_GOVERNANCE)
    return governance == address


def _is_oracle(address: UInt160) -> bool:
    ctx = get_read_only_context()
    value = get(ctx, PREFIX_ORACLE + address)
    if len(value) == 0:
        return False
    return value.to_bool()


def _set_oracle(address: UInt160, authorized: bool) -> None:
    ctx = get_context()
    if authorized:
        put(ctx, PREFIX_ORACLE + address, True)
    else:
        delete(ctx, PREFIX_ORACLE + address)


def _is_minter(address: UInt160) -> bool:
    ctx = get_read_only_context()
    value = get(ctx, PREFIX_MINTER + address)
    if len(value) == 0:
        return False
    return value.to_bool()


def _set_minter(address: UInt160, authorized: bool) -> None:
    ctx = get_context()
    if authorized:
        put(ctx, PREFIX_MINTER + address, True)
    else:
        delete(ctx, PREFIX_MINTER + address)


def _is_approved(owner: UInt160, token_id: bytes, spender: UInt160, amount: int) -> bool:
    ctx = get_read_only_context()
    key = PREFIX_APPROVED + owner + token_id + spender
    value = get(ctx, key)
    if len(value) == 0:
        return False
    return value.to_int() >= amount


def _is_reentrancy_locked() -> bool:
    ctx = get_read_only_context()
    value = get(ctx, PREFIX_REENTRANCY)
    if len(value) == 0:
        return False
    return value.to_bool()


def _set_reentrancy_lock(locked: bool) -> None:
    ctx = get_context()
    put(ctx, PREFIX_REENTRANCY, locked)

