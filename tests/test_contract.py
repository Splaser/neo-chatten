"""
Tests for Chatten Compute-Fi Protocol (NEP-11 Divisible + Marketplace)

These tests verify the contract structure and constants.
Full integration tests require a Neo N3 test environment.
"""

import pytest


class TestChattenConstants:
    """Test suite for contract constants."""
    
    def test_token_symbol(self):
        from contracts.chatten_token import TOKEN_SYMBOL
        assert TOKEN_SYMBOL == "COMPUTE"
    
    def test_token_decimals(self):
        from contracts.chatten_token import TOKEN_DECIMALS
        assert TOKEN_DECIMALS == 8
    
    def test_one_token_value(self):
        from contracts.chatten_token import ONE_TOKEN, TOKEN_DECIMALS
        assert ONE_TOKEN == 10 ** TOKEN_DECIMALS
        assert ONE_TOKEN == 100_000_000
    
    def test_one_gas_value(self):
        from contracts.chatten_token import ONE_GAS
        assert ONE_GAS == 100_000_000
    
    def test_quality_score_thresholds(self):
        from contracts.chatten_token import MIN_QUALITY_SCORE, MAX_QUALITY_SCORE
        assert MIN_QUALITY_SCORE == 50
        assert MAX_QUALITY_SCORE == 100
    
    def test_lock_duration_limits(self):
        from contracts.chatten_token import MIN_LOCK_BLOCKS, MAX_LOCK_BLOCKS
        assert MIN_LOCK_BLOCKS == 100
        assert MAX_LOCK_BLOCKS == 2_102_400
    
    def test_swap_fee_defaults(self):
        from contracts.chatten_token import DEFAULT_SWAP_FEE_BPS, MAX_SWAP_FEE_BPS
        assert DEFAULT_SWAP_FEE_BPS == 30  # 0.3%
        assert MAX_SWAP_FEE_BPS == 500  # 5%


class TestStoragePrefixes:
    """Test suite for storage prefix configuration."""
    
    def test_prefixes_are_single_byte(self):
        from contracts.chatten_token import (
            PREFIX_BALANCE,
            PREFIX_SUPPLY,
            PREFIX_TOKEN_DATA,
            PREFIX_ACCOUNT_TOKENS,
            PREFIX_PROVIDER,
            PREFIX_PROVIDER_LIST,
            PREFIX_APPROVED,
            PREFIX_ORACLE,
            PREFIX_MINTER,
            PREFIX_LOCK,
            PREFIX_TOTAL_LOCKED,
            PREFIX_ADMIN,
            PREFIX_PAUSED,
            PREFIX_TOTAL_SUPPLY,
            PREFIX_GOVERNANCE,
            PREFIX_PRICE,
            PREFIX_GAS_RESERVE,
            PREFIX_SWAP_FEE_BPS,
            PREFIX_REENTRANCY,
        )
        
        prefixes = [
            PREFIX_BALANCE,
            PREFIX_SUPPLY,
            PREFIX_TOKEN_DATA,
            PREFIX_ACCOUNT_TOKENS,
            PREFIX_PROVIDER,
            PREFIX_PROVIDER_LIST,
            PREFIX_APPROVED,
            PREFIX_ORACLE,
            PREFIX_MINTER,
            PREFIX_LOCK,
            PREFIX_TOTAL_LOCKED,
            PREFIX_ADMIN,
            PREFIX_PAUSED,
            PREFIX_TOTAL_SUPPLY,
            PREFIX_GOVERNANCE,
            PREFIX_PRICE,
            PREFIX_GAS_RESERVE,
            PREFIX_SWAP_FEE_BPS,
            PREFIX_REENTRANCY,
        ]
        
        for prefix in prefixes:
            assert len(prefix) == 1, f"Prefix {prefix!r} should be single byte"
    
    def test_prefixes_are_unique(self):
        from contracts.chatten_token import (
            PREFIX_BALANCE,
            PREFIX_SUPPLY,
            PREFIX_TOKEN_DATA,
            PREFIX_ACCOUNT_TOKENS,
            PREFIX_PROVIDER,
            PREFIX_PROVIDER_LIST,
            PREFIX_APPROVED,
            PREFIX_ORACLE,
            PREFIX_MINTER,
            PREFIX_LOCK,
            PREFIX_TOTAL_LOCKED,
            PREFIX_ADMIN,
            PREFIX_PAUSED,
            PREFIX_TOTAL_SUPPLY,
            PREFIX_GOVERNANCE,
            PREFIX_PRICE,
            PREFIX_GAS_RESERVE,
            PREFIX_SWAP_FEE_BPS,
            PREFIX_REENTRANCY,
        )
        
        prefixes = [
            PREFIX_BALANCE,
            PREFIX_SUPPLY,
            PREFIX_TOKEN_DATA,
            PREFIX_ACCOUNT_TOKENS,
            PREFIX_PROVIDER,
            PREFIX_PROVIDER_LIST,
            PREFIX_APPROVED,
            PREFIX_ORACLE,
            PREFIX_MINTER,
            PREFIX_LOCK,
            PREFIX_TOTAL_LOCKED,
            PREFIX_ADMIN,
            PREFIX_PAUSED,
            PREFIX_TOTAL_SUPPLY,
            PREFIX_GOVERNANCE,
            PREFIX_PRICE,
            PREFIX_GAS_RESERVE,
            PREFIX_SWAP_FEE_BPS,
            PREFIX_REENTRANCY,
        ]
        
        unique_prefixes = set(prefixes)
        assert len(unique_prefixes) == len(prefixes), "Storage prefixes must be unique"


class TestNEP11Methods:
    """Test suite for NEP-11 standard methods."""
    
    def test_symbol_returns_string(self):
        from contracts.chatten_token import symbol
        result = symbol()
        assert isinstance(result, str)
        assert result == "COMPUTE"
    
    def test_decimals_returns_int(self):
        from contracts.chatten_token import decimals
        result = decimals()
        assert isinstance(result, int)
        assert result == 8


class TestZeroAddress:
    """Test suite for zero address constant."""
    
    def test_zero_address_length(self):
        from contracts.chatten_token import ZERO_ADDRESS
        assert len(ZERO_ADDRESS) == 20
    
    def test_zero_address_is_all_zeros(self):
        from contracts.chatten_token import ZERO_ADDRESS
        assert ZERO_ADDRESS == b'\x00' * 20


class TestContractFunctions:
    """Test suite verifying contract functions exist."""
    
    def test_nep11_methods_exist(self):
        from contracts import chatten_token
        
        nep11_methods = [
            'symbol',
            'decimals',
            'totalSupply',
            'balanceOf',
            'tokensOf',
            'ownerOf',
            'transfer',
            'properties',
        ]
        
        for method in nep11_methods:
            assert hasattr(chatten_token, method), f"Missing NEP-11 method: {method}"
    
    def test_divisible_methods_exist(self):
        from contracts import chatten_token
        
        divisible_methods = [
            'balanceOfToken',
            'tokenSupply',
            'approve',
            'allowance',
        ]
        
        for method in divisible_methods:
            assert hasattr(chatten_token, method), f"Missing divisible method: {method}"
    
    def test_pricing_methods_exist(self):
        """Verify pricing engine methods exist."""
        from contracts import chatten_token
        
        pricing_methods = [
            'get_current_price',
            'get_price_by_token_id',
            'update_price_oracle',
            'set_price_floor',
            'get_price_info',
        ]
        
        for method in pricing_methods:
            assert hasattr(chatten_token, method), f"Missing pricing method: {method}"
    
    def test_swap_methods_exist(self):
        """Verify DEX swap methods exist."""
        from contracts import chatten_token
        
        swap_methods = [
            'buy_compute',
            'sell_compute',
            'get_buy_quote',
            'get_sell_quote',
            'get_gas_reserve',
            'get_swap_fee_bps',
            'set_swap_fee',
        ]
        
        for method in swap_methods:
            assert hasattr(chatten_token, method), f"Missing swap method: {method}"
    
    def test_nep17_receiver_exists(self):
        """Verify NEP-17 payment receiver exists."""
        from contracts import chatten_token
        assert hasattr(chatten_token, 'onNEP17Payment'), "Missing onNEP17Payment"
    
    def test_provider_methods_exist(self):
        from contracts import chatten_token
        
        provider_methods = [
            'register_provider',
            'mint_rewards',
            'update_provider_reputation',
            'get_provider',
        ]
        
        for method in provider_methods:
            assert hasattr(chatten_token, method), f"Missing provider method: {method}"
    
    def test_microfinance_methods_exist(self):
        from contracts import chatten_token
        
        lock_methods = [
            'lock',
            'unlock',
            'lockedBalanceOf',
            'availableBalanceOf',
        ]
        
        for method in lock_methods:
            assert hasattr(chatten_token, method), f"Missing lock method: {method}"
    
    def test_admin_methods_exist(self):
        from contracts import chatten_token
        
        admin_methods = [
            'pause',
            'resume',
            'isPaused',
            'update_admin',
            'set_governance',
            'set_oracle',
            'set_minter',
            'get_admin',
            'is_oracle',
            'is_minter',
            'withdraw_gas',
        ]
        
        for method in admin_methods:
            assert hasattr(chatten_token, method), f"Missing admin method: {method}"
    
    def test_mint_burn_methods_exist(self):
        from contracts import chatten_token
        
        mint_methods = ['mint', 'burn']
        
        for method in mint_methods:
            assert hasattr(chatten_token, method), f"Missing mint/burn method: {method}"


class TestPricingLogic:
    """Test pricing calculation logic."""
    
    def test_buy_quote_calculation(self):
        """Test the buy quote formula: compute = (gas - fee) / price."""
        from contracts.chatten_token import ONE_TOKEN, ONE_GAS, DEFAULT_SWAP_FEE_BPS
        
        # Simulate: 1 GAS input, price = 0.5 GAS per COMPUTE
        gas_amount = ONE_GAS  # 1.0 GAS
        price = ONE_GAS // 2   # 0.5 GAS per COMPUTE
        
        # Fee calculation: 0.3%
        fee = (gas_amount * DEFAULT_SWAP_FEE_BPS) // 10000
        net_gas = gas_amount - fee
        
        # Expected output
        expected_compute = (net_gas * ONE_TOKEN) // price
        
        # Should get ~1.994 COMPUTE (accounting for 0.3% fee)
        assert expected_compute > ONE_TOKEN * 19 // 10  # > 1.9 COMPUTE
        assert expected_compute < ONE_TOKEN * 2  # < 2.0 COMPUTE
    
    def test_sell_quote_calculation(self):
        """Test the sell quote formula: gas = (compute * price) - fee."""
        from contracts.chatten_token import ONE_TOKEN, ONE_GAS, DEFAULT_SWAP_FEE_BPS
        
        # Simulate: 2 COMPUTE input, price = 0.5 GAS per COMPUTE
        compute_amount = 2 * ONE_TOKEN  # 2.0 COMPUTE
        price = ONE_GAS // 2  # 0.5 GAS per COMPUTE
        
        # Gross output
        gross_gas = (compute_amount * price) // ONE_TOKEN  # 1.0 GAS
        
        # Fee calculation
        fee = (gross_gas * DEFAULT_SWAP_FEE_BPS) // 10000
        net_gas = gross_gas - fee
        
        # Should get ~0.997 GAS (accounting for 0.3% fee)
        assert net_gas > ONE_GAS * 99 // 100  # > 0.99 GAS
        assert net_gas < ONE_GAS  # < 1.0 GAS


class TestSwapFeeConfiguration:
    """Test swap fee configuration."""
    
    def test_default_fee_is_30_bps(self):
        """Default fee should be 0.3% (30 basis points)."""
        from contracts.chatten_token import DEFAULT_SWAP_FEE_BPS
        assert DEFAULT_SWAP_FEE_BPS == 30
    
    def test_max_fee_is_500_bps(self):
        """Maximum fee should be 5% (500 basis points)."""
        from contracts.chatten_token import MAX_SWAP_FEE_BPS
        assert MAX_SWAP_FEE_BPS == 500
    
    def test_fee_percentage_calculation(self):
        """Verify fee percentage is correct."""
        from contracts.chatten_token import DEFAULT_SWAP_FEE_BPS
        
        # 30 basis points = 0.3%
        amount = 10000
        fee = (amount * DEFAULT_SWAP_FEE_BPS) // 10000
        
        assert fee == 30  # 0.3% of 10000
