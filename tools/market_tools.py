"""
Market Tools

SpoonOS tools for analyzing market quality and AI model performance.
"""

from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import random

# SpoonOS SDK imports
try:
    from spoon_ai_sdk import Tool, ToolResult
    from spoon_ai_sdk.tools import BaseTool
except ImportError:
    Tool = object
    ToolResult = dict
    BaseTool = object


class ModelCategory(Enum):
    """Categories of AI models for Q-score calculation."""
    
    LLM = "llm"                    # Large Language Models
    IMAGE_GEN = "image_generation"  # Image Generation
    EMBEDDING = "embedding"         # Embedding Models
    AUDIO = "audio"                # Audio Processing
    MULTIMODAL = "multimodal"      # Multimodal Models


@dataclass
class PerformanceMetrics:
    """Performance metrics for Q-score calculation."""
    
    # Latency metrics (in milliseconds)
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    
    # Throughput metrics
    tokens_per_second: float = 0.0
    requests_per_minute: float = 0.0
    
    # Quality metrics
    accuracy_score: float = 0.0       # 0-1 scale
    benchmark_score: float = 0.0      # Model-specific benchmark
    
    # Availability metrics
    uptime_percentage: float = 0.0    # 0-100
    error_rate: float = 0.0           # 0-1 scale
    
    # Cost metrics
    cost_per_1k_tokens: float = 0.0
    
    # Metadata
    measurement_timestamp: Optional[datetime] = None
    sample_size: int = 0


@dataclass
class QScoreResult:
    """Result of Q-score calculation."""
    
    model_id: str
    q_score: float                    # 0-100 composite score
    category: ModelCategory
    metrics: PerformanceMetrics
    
    # Component scores
    latency_score: float = 0.0        # 0-25 max
    throughput_score: float = 0.0     # 0-25 max
    quality_score: float = 0.0        # 0-25 max
    reliability_score: float = 0.0    # 0-25 max
    
    # Recommendations
    recommendations: list[str] = field(default_factory=list)
    mint_eligible: bool = False


@dataclass
class MarketAnalysis:
    """Market-wide analysis result."""
    
    total_models: int = 0
    avg_q_score: float = 0.0
    top_performers: list[str] = field(default_factory=list)
    market_liquidity: float = 0.0
    price_trend: str = "stable"       # "up", "down", "stable"


class QScoreAnalyzerTool(BaseTool):
    """
    SpoonOS Tool for analyzing AI model Quality Scores (Q-score).
    
    The Q-score is a composite metric (0-100) that determines the fair
    market value of Compute Tokens based on real-time performance data.
    
    Scoring Components (25 points each):
    1. Latency: Response time efficiency
    2. Throughput: Processing capacity
    3. Quality: Accuracy and benchmark performance
    4. Reliability: Uptime and error rates
    """
    
    name: str = "q_score_analyzer"
    description: str = """
    Analyze AI model performance and calculate Quality Scores (Q-score).
    Use this tool to:
    - Calculate Q-score for a specific model
    - Compare Q-scores between models
    - Get market-wide quality analysis
    - Determine token minting eligibility
    """
    
    # Q-score thresholds
    MIN_SCORE_FOR_MINT = 50
    EXCELLENT_THRESHOLD = 80
    GOOD_THRESHOLD = 60
    
    # Weight factors for score components
    LATENCY_WEIGHT = 0.25
    THROUGHPUT_WEIGHT = 0.25
    QUALITY_WEIGHT = 0.25
    RELIABILITY_WEIGHT = 0.25
    
    def __init__(self) -> None:
        """Initialize the Q-score Analyzer Tool."""
        super().__init__()
        self._metrics_cache: dict[str, PerformanceMetrics] = {}
        self._recent_scores: dict[str, QScoreResult] = {}
    
    # =========================================================================
    # Q-SCORE CALCULATION
    # =========================================================================
    
    async def calculate_q_score(
        self,
        model_id: str,
        metrics: Optional[PerformanceMetrics] = None,
        category: ModelCategory = ModelCategory.LLM
    ) -> QScoreResult:
        """
        Calculate the Q-score for an AI model.
        
        Args:
            model_id: Unique identifier of the model
            metrics: Pre-collected performance metrics (if available)
            category: Model category for scoring context
            
        Returns:
            QScoreResult: Complete Q-score analysis
        """
        # TODO: Implement Q-score calculation
        # 1. Fetch metrics from oracle if not provided
        # 2. Calculate component scores
        # 3. Apply weights and normalize
        # 4. Generate recommendations
        
        if metrics is None:
            metrics = await self._fetch_metrics(model_id)
        
        latency_score = self._calculate_latency_score(metrics)
        throughput_score = self._calculate_throughput_score(metrics)
        quality_score = self._calculate_quality_score(metrics)
        reliability_score = self._calculate_reliability_score(metrics)
        
        q_score = (
            latency_score * self.LATENCY_WEIGHT +
            throughput_score * self.THROUGHPUT_WEIGHT +
            quality_score * self.QUALITY_WEIGHT +
            reliability_score * self.RELIABILITY_WEIGHT
        ) * 100
        
        mint_eligible = q_score >= self.MIN_SCORE_FOR_MINT
        
        recommendations = self._generate_recommendations(
            q_score, latency_score, throughput_score,
            quality_score, reliability_score
        )
        
        result = QScoreResult(
            model_id=model_id,
            q_score=q_score,
            category=category,
            metrics=metrics,
            latency_score=latency_score * 25,
            throughput_score=throughput_score * 25,
            quality_score=quality_score * 25,
            reliability_score=reliability_score * 25,
            recommendations=recommendations,
            mint_eligible=mint_eligible
        )
        
        # Cache for market-wide aggregation
        self._metrics_cache[model_id] = metrics
        self._recent_scores[model_id] = result
        
        return result
    
    async def compare_models(
        self,
        model_ids: list[str]
    ) -> list[QScoreResult]:
        """
        Compare Q-scores across multiple models.
        
        Args:
            model_ids: List of model identifiers to compare
            
        Returns:
            list: Sorted list of QScoreResults (highest first)
        """
        # TODO: Implement model comparison
        results = []
        for model_id in model_ids:
            result = await self.calculate_q_score(model_id)
            results.append(result)
        
        return sorted(results, key=lambda x: x.q_score, reverse=True)
    
    async def get_market_analysis(self) -> MarketAnalysis:
        """
        Get market-wide Q-score analysis.
        
        Returns:
            MarketAnalysis: Overview of market quality metrics
        """
        if not self._recent_scores:
            return MarketAnalysis()
        
        scores = list(self._recent_scores.values())
        total_models = len(scores)
        avg_q_score = sum(r.q_score for r in scores) / total_models
        
        # Top performers by q_score
        sorted_scores = sorted(scores, key=lambda r: r.q_score, reverse=True)
        top_performers = [r.model_id for r in sorted_scores[:3]]
        
        # Simple pseudo-liquidity metric based on sample sizes
        market_liquidity = sum(r.metrics.sample_size for r in scores)
        
        # Trend heuristic: classify based on average score
        if avg_q_score >= self.EXCELLENT_THRESHOLD:
            price_trend = "up"
        elif avg_q_score >= self.GOOD_THRESHOLD:
            price_trend = "stable"
        else:
            price_trend = "down"
        
        return MarketAnalysis(
            total_models=total_models,
            avg_q_score=round(avg_q_score, 2),
            top_performers=top_performers,
            market_liquidity=market_liquidity,
            price_trend=price_trend,
        )
    
    # =========================================================================
    # SCORE CALCULATION HELPERS
    # =========================================================================
    
    def _calculate_latency_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate latency component score (0-1).
        
        Lower latency = higher score.
        """
        latency = metrics.avg_latency_ms or 0.0
        p95 = metrics.p95_latency_ms or latency
        
        # Fast paths first
        if latency <= 50 and p95 <= 100:
            return 1.0
        if latency <= 100 and p95 <= 200:
            return 0.85
        if latency <= 200 and p95 <= 400:
            return 0.7
        if latency <= 400 and p95 <= 800:
            return 0.5
        if latency <= 800 and p95 <= 1500:
            return 0.35
        return 0.2
    
    def _calculate_throughput_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate throughput component score (0-1).
        
        Higher throughput = higher score.
        """
        tps = metrics.tokens_per_second or 0.0
        rpm = metrics.requests_per_minute or 0.0
        
        # Normalize tokens/second to a 0-1 scale with gentle curve
        if tps >= 2000 or rpm >= 2000:
            return 1.0
        if tps >= 1000 or rpm >= 1000:
            return 0.85
        if tps >= 500 or rpm >= 500:
            return 0.7
        if tps >= 200 or rpm >= 200:
            return 0.5
        if tps >= 50 or rpm >= 50:
            return 0.35
        return 0.2
    
    def _calculate_quality_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate quality component score (0-1).
        
        Based on accuracy and benchmark performance.
        """
        # Simple average of accuracy & benchmark, both expected on 0-1 scale
        accuracy = metrics.accuracy_score or 0.0
        benchmark = metrics.benchmark_score or accuracy
        
        raw = (accuracy + benchmark) / 2
        return self._clamp(raw, 0.0, 1.0)
    
    def _calculate_reliability_score(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate reliability component score (0-1).
        
        Based on uptime and error rates.
        """
        uptime = metrics.uptime_percentage / 100 if metrics.uptime_percentage else 0.0
        error_rate = metrics.error_rate or 0.0
        
        if error_rate < 0:
            error_rate = 0.0
        
        # Reliability rewards high uptime and low error rate
        reliability = uptime * 0.9 + (1 - min(error_rate, 1.0)) * 0.1
        return self._clamp(reliability, 0.0, 1.0)

    def _clamp(self, value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
        """Clamp a value between bounds."""
        return max(min_value, min(max_value, value))
    
    def _generate_recommendations(
        self,
        q_score: float,
        latency: float,
        throughput: float,
        quality: float,
        reliability: float
    ) -> list[str]:
        """
        Generate improvement recommendations based on scores.
        """
        recommendations = []
        
        if latency < 0.5:
            recommendations.append("Consider optimizing inference latency")
        if throughput < 0.5:
            recommendations.append("Throughput could be improved with batching")
        if quality < 0.5:
            recommendations.append("Model accuracy needs improvement")
        if reliability < 0.5:
            recommendations.append("Improve uptime and reduce error rates")
        
        if q_score >= self.EXCELLENT_THRESHOLD:
            recommendations.append("Excellent performance - eligible for premium rates")
        elif q_score >= self.MIN_SCORE_FOR_MINT:
            recommendations.append("Good performance - eligible for token minting")
        else:
            recommendations.append("Below threshold - improvements needed before minting")
        
        return recommendations
    
    async def _fetch_metrics(self, model_id: str) -> PerformanceMetrics:
        """
        Fetch performance metrics from oracle or cache.
        
        Args:
            model_id: Model to fetch metrics for
            
        Returns:
            PerformanceMetrics: Current metrics
        """
        # In a real deployment this would query an oracle. For the demo we
        # generate deterministic pseudo-metrics so the numbers are stable
        # between runs without needing network access.
        if model_id in self._metrics_cache:
            return self._metrics_cache[model_id]
        
        seed = int.from_bytes(hashlib.sha256(model_id.encode()).digest()[:8], "big")
        rng = random.Random(seed)
        
        metrics = PerformanceMetrics(
            avg_latency_ms=round(60 + rng.random() * 500, 2),
            p95_latency_ms=round(100 + rng.random() * 600, 2),
            p99_latency_ms=round(150 + rng.random() * 800, 2),
            tokens_per_second=round(50 + rng.random() * 2500, 2),
            requests_per_minute=round(30 + rng.random() * 2500, 2),
            accuracy_score=round(0.65 + rng.random() * 0.3, 3),
            benchmark_score=round(0.6 + rng.random() * 0.35, 3),
            uptime_percentage=round(96 + rng.random() * 4, 3),
            error_rate=round(rng.random() * 0.05, 4),
            cost_per_1k_tokens=round(0.0005 + rng.random() * 0.002, 6),
            measurement_timestamp=datetime.utcnow(),
            sample_size=rng.randint(100, 1000),
        )
        
        self._metrics_cache[model_id] = metrics
        return metrics
    
    # =========================================================================
    # TOOL INTERFACE (SpoonOS)
    # =========================================================================
    
    async def run(self, **kwargs: Any) -> ToolResult:
        """SpoonOS tool execution entry point."""
        action = kwargs.get("action", "calculate")
        
        if action == "calculate":
            model_id = kwargs.get("model_id", "")
            result = await self.calculate_q_score(model_id)
            return {
                "model_id": result.model_id,
                "q_score": result.q_score,
                "mint_eligible": result.mint_eligible,
                "recommendations": result.recommendations
            }
        
        elif action == "compare":
            model_ids = kwargs.get("model_ids", [])
            results = await self.compare_models(model_ids)
            return {
                "rankings": [
                    {"model_id": r.model_id, "q_score": r.q_score}
                    for r in results
                ]
            }
        
        elif action == "market":
            analysis = await self.get_market_analysis()
            return {
                "total_models": analysis.total_models,
                "avg_q_score": analysis.avg_q_score,
                "trend": analysis.price_trend
            }
        
        return {"error": "Unknown action"}

