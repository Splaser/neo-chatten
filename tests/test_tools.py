"""
Tests for SpoonOS Tools
"""

import pytest
from tools import NeoBridgeTool, TokenBalanceTool, QScoreAnalyzerTool
from tools.neo_bridge import NeoConfig, TransactionResult
from tools.market_tools import PerformanceMetrics, QScoreResult, ModelCategory


class TestNeoBridgeTool:
    """Test suite for the Neo Bridge Tool."""
    
    def test_initialization(self):
        """Test tool initialization with default config."""
        tool = NeoBridgeTool()
        
        assert tool.name == "neo_bridge"
        assert tool.config is not None
        assert tool.config.rpc_url == "https://mainnet1.neo.coz.io:443"
    
    def test_custom_config(self):
        """Test tool initialization with custom config."""
        config = NeoConfig(
            rpc_url="https://testnet1.neo.coz.io:443",
            network_magic=894710606
        )
        tool = NeoBridgeTool(config=config)
        
        assert tool.config.rpc_url == "https://testnet1.neo.coz.io:443"
        assert tool.config.network_magic == 894710606
    
    def test_not_connected_initially(self):
        """Test that tool is not connected on init."""
        tool = NeoBridgeTool()
        assert not tool.is_connected()


class TestTokenBalanceTool:
    """Test suite for the Token Balance Tool."""
    
    def test_initialization(self):
        """Test tool initialization."""
        tool = TokenBalanceTool(
            contract_hash="0x1234567890abcdef"
        )
        
        assert tool.name == "token_balance"
        assert tool.contract_hash == "0x1234567890abcdef"


class TestQScoreAnalyzerTool:
    """Test suite for the Q-Score Analyzer Tool."""
    
    def test_initialization(self):
        """Test tool initialization."""
        tool = QScoreAnalyzerTool()
        
        assert tool.name == "q_score_analyzer"
        assert tool.MIN_SCORE_FOR_MINT == 50
    
    def test_thresholds(self):
        """Test Q-score thresholds."""
        tool = QScoreAnalyzerTool()
        
        assert tool.EXCELLENT_THRESHOLD == 80
        assert tool.GOOD_THRESHOLD == 60
        assert tool.MIN_SCORE_FOR_MINT == 50
    
    def test_performance_metrics_dataclass(self):
        """Test PerformanceMetrics dataclass."""
        metrics = PerformanceMetrics(
            avg_latency_ms=50.0,
            tokens_per_second=1000.0,
            accuracy_score=0.95,
            uptime_percentage=99.9
        )
        
        assert metrics.avg_latency_ms == 50.0
        assert metrics.tokens_per_second == 1000.0
        assert metrics.accuracy_score == 0.95
        assert metrics.uptime_percentage == 99.9
    
    def test_model_categories(self):
        """Test model category enum."""
        assert ModelCategory.LLM.value == "llm"
        assert ModelCategory.IMAGE_GEN.value == "image_generation"
        assert ModelCategory.EMBEDDING.value == "embedding"

