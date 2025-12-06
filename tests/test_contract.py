"""
Tests for Chatten Token Contract
"""

import pytest
from contracts.chatten_token import (
    symbol,
    decimals,
    totalSupply,
    TOKEN_SYMBOL,
    TOKEN_DECIMALS,
    MIN_Q_SCORE_FOR_MINT,
)


class TestChattenTokenContract:
    """Test suite for the Chatten Token Contract."""
    
    def test_symbol(self):
        """Test token symbol."""
        assert symbol() == "COMPUTE"
        assert symbol() == TOKEN_SYMBOL
    
    def test_decimals(self):
        """Test token decimals."""
        assert decimals() == 8
        assert decimals() == TOKEN_DECIMALS
    
    def test_total_supply_initial(self):
        """Test initial total supply is zero."""
        assert totalSupply() == 0
    
    def test_min_q_score_threshold(self):
        """Test minimum Q-score threshold for minting."""
        assert MIN_Q_SCORE_FOR_MINT == 50

