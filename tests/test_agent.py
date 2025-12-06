"""
Tests for ChattenTraderAgent
"""

import pytest
from agents import ChattenTraderAgent


class TestChattenTraderAgent:
    """Test suite for the Chatten Trader Agent."""
    
    def test_agent_initialization(self):
        """Test basic agent initialization."""
        agent = ChattenTraderAgent(
            name="TestTrader",
            neo_wallet_address="NXjtd..."
        )
        
        assert agent.name == "TestTrader"
        assert agent.neo_wallet_address == "NXjtd..."
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert ChattenTraderAgent.SYSTEM_PROMPT is not None
        assert "Liquidity Manager" in ChattenTraderAgent.SYSTEM_PROMPT
    
    @pytest.mark.asyncio
    async def test_check_balance_not_implemented(self):
        """Test that balance check raises NotImplementedError."""
        agent = ChattenTraderAgent()
        
        with pytest.raises(NotImplementedError):
            await agent.check_token_balance()
    
    @pytest.mark.asyncio
    async def test_analyze_q_score_not_implemented(self):
        """Test that Q-score analysis raises NotImplementedError."""
        agent = ChattenTraderAgent()
        
        with pytest.raises(NotImplementedError):
            await agent.analyze_q_score("model-123")

