"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                     CHATTEN COMPUTE-FI PROTOCOL                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  A Hyperledger-style Compute Finance Protocol on Neo N3                     ║
║                                                                              ║
║  BASE ASSET: COMPUTE (NEP-11 SFT)  │  QUOTE ASSET: $GAS                     ║
║                                                                              ║
║  Features:                                                                   ║
║  • NEP-11 Divisible Semi-Fungible Token                                     ║
║  • Built-in DEX with GAS trading pairs                                      ║
║  • Oracle-driven dynamic pricing                                             ║
║  • Provider Registry for compute suppliers                                   ║
║  • Microfinance primitives (collateral locking)                             ║
║  • A2A Payment callbacks for Pay-and-Execute                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from .chatten_token import (
    # ─────────────────────────────────────────────────────────────────────────
    # Constants
    # ─────────────────────────────────────────────────────────────────────────
    TOKEN_SYMBOL,
    TOKEN_DECIMALS,
    TOKEN_NAME,
    ONE_TOKEN,
    ONE_GAS,
    MIN_QUALITY_SCORE,
    MAX_QUALITY_SCORE,
    MIN_LOCK_BLOCKS,
    MAX_LOCK_BLOCKS,
    DEFAULT_SWAP_FEE_BPS,
    ZERO_ADDRESS,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Storage Prefixes
    # ─────────────────────────────────────────────────────────────────────────
    PREFIX_BALANCE,
    PREFIX_SUPPLY,
    PREFIX_TOKEN_DATA,
    PREFIX_PROVIDER,
    PREFIX_LOCK,
    PREFIX_ADMIN,
    PREFIX_PAUSED,
    PREFIX_PRICE,
    PREFIX_GAS_RESERVE,
    
    # ─────────────────────────────────────────────────────────────────────────
    # NEP-11 Standard Methods
    # ─────────────────────────────────────────────────────────────────────────
    symbol,
    decimals,
    totalSupply,
    balanceOf,
    balanceOfToken,
    tokensOf,
    ownerOf,
    properties,
    tokenSupply,
    transfer,
    approve,
    allowance,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Pricing Engine (Hyperledger)
    # ─────────────────────────────────────────────────────────────────────────
    get_current_price,
    get_price_by_token_id,
    update_price_oracle,
    set_price_floor,
    get_price_info,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Swap Mechanism (DEX)
    # ─────────────────────────────────────────────────────────────────────────
    buy_compute,
    sell_compute,
    get_buy_quote,
    get_sell_quote,
    get_gas_reserve,
    get_swap_fee_bps,
    set_swap_fee,
    onNEP17Payment,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Provider Registry
    # ─────────────────────────────────────────────────────────────────────────
    register_provider,
    mint_rewards,
    update_provider_reputation,
    get_provider,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Minting & Burning
    # ─────────────────────────────────────────────────────────────────────────
    mint,
    burn,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Microfinance
    # ─────────────────────────────────────────────────────────────────────────
    lock,
    unlock,
    lockedBalanceOf,
    availableBalanceOf,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Admin/Governance
    # ─────────────────────────────────────────────────────────────────────────
    pause,
    resume,
    isPaused,
    update_admin,
    set_governance,
    set_oracle,
    set_minter,
    get_admin,
    is_oracle,
    is_minter,
    withdraw_gas,
    
    # ─────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ─────────────────────────────────────────────────────────────────────────
    onNEP11Payment,
)

__all__ = [
    # Constants
    "TOKEN_SYMBOL",
    "TOKEN_DECIMALS", 
    "TOKEN_NAME",
    "ONE_TOKEN",
    "ONE_GAS",
    "MIN_QUALITY_SCORE",
    "MAX_QUALITY_SCORE",
    "MIN_LOCK_BLOCKS",
    "MAX_LOCK_BLOCKS",
    "DEFAULT_SWAP_FEE_BPS",
    "ZERO_ADDRESS",
    
    # NEP-11 Methods
    "symbol",
    "decimals",
    "totalSupply",
    "balanceOf",
    "balanceOfToken",
    "tokensOf",
    "ownerOf",
    "properties",
    "tokenSupply",
    "transfer",
    "approve",
    "allowance",
    
    # Pricing Engine
    "get_current_price",
    "get_price_by_token_id",
    "update_price_oracle",
    "set_price_floor",
    "get_price_info",
    
    # Swap Mechanism
    "buy_compute",
    "sell_compute",
    "get_buy_quote",
    "get_sell_quote",
    "get_gas_reserve",
    "get_swap_fee_bps",
    "set_swap_fee",
    "onNEP17Payment",
    
    # Provider Registry
    "register_provider",
    "mint_rewards",
    "update_provider_reputation",
    "get_provider",
    
    # Minting
    "mint",
    "burn",
    
    # Microfinance
    "lock",
    "unlock",
    "lockedBalanceOf",
    "availableBalanceOf",
    
    # Admin
    "pause",
    "resume",
    "isPaused",
    "update_admin",
    "set_governance",
    "set_oracle",
    "set_minter",
    "get_admin",
    "is_oracle",
    "is_minter",
    "withdraw_gas",
    
    # Callbacks
    "onNEP11Payment",
]
