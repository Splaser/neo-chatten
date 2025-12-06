# Chatten 🤖⛓️

> Decentralized Exchange for AI Compute Tokens on Neo N3

Chatten enables AI agents to buy and sell model compute capacity based on real-time performance metrics, powered by the Neo N3 blockchain and SpoonOS agent framework.

## 🏗️ Architecture

```
chatten/
├── agents/                    # SpoonOS Agent Implementations
│   ├── __init__.py
│   └── chatten_trader.py      # Liquidity Manager Agent
├── contracts/                 # Neo N3 Smart Contracts
│   ├── __init__.py
│   └── chatten_token.py       # NEP-11 Compute Token Contract
├── tools/                     # SpoonOS Tools (Agent-Blockchain Bridge)
│   ├── __init__.py
│   ├── neo_bridge.py          # Core Neo N3 RPC Bridge
│   ├── token_tools.py         # Token Balance & Transfer Tools
│   └── market_tools.py        # Q-Score Analysis Tools
├── main.py                    # Application Entry Point
├── pyproject.toml             # Project Configuration
└── .env.example               # Environment Template
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Neo N3 wallet (TestNet for development)

### Installation

```bash
# Clone the repository
git clone https://github.com/chatten/neo-chatten.git
cd neo-chatten

# Create virtual environment and install dependencies
uv sync

# Or with pip
pip install -e ".[dev]"
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required environment variables:
- `NEO_PRIVATE_KEY` - Your Neo N3 wallet private key
- `OPENAI_API_KEY` - OpenAI API key for agent LLM
- `SPOON_API_KEY` - SpoonOS API key (optional)

### Running

```bash
# Run the Chatten agent
python main.py

# Or via the installed command
chatten
```

## 📦 Components

### ChattenTraderAgent

The core AI agent that manages liquidity and executes trades:

```python
from agents import ChattenTraderAgent

agent = ChattenTraderAgent(
    name="MyTrader",
    neo_wallet_address="NXjtd..."
)

# Check token balance
balance = await agent.check_token_balance()

# Analyze model quality
q_score = await agent.analyze_q_score("model-123")
```

### Chatten Token Contract (NEP-11)

Semi-fungible token representing AI compute capacity:

- **Symbol**: `COMPUTE`
- **Decimals**: 8
- **Standard**: NEP-11 (Semi-Fungible)

Key functions:
- `mint(to, model_id, q_score, compute_units)` - Mint tokens based on performance
- `transfer(to, token_id, data)` - Transfer token ownership
- `properties(token_id)` - Get token metadata

### SpoonOS Tools

Bridge between agents and the blockchain:

| Tool | Purpose |
|------|---------|
| `NeoBridgeTool` | Core RPC communication & signing |
| `TokenBalanceTool` | Query token balances & ownership |
| `TokenTransferTool` | Execute token transfers |
| `QScoreAnalyzerTool` | Calculate AI model Q-scores |

## 📊 Q-Score System

The Quality Score (Q-score) is a composite metric (0-100) that determines token value:

| Component | Weight | Measures |
|-----------|--------|----------|
| Latency | 25% | Response time efficiency |
| Throughput | 25% | Processing capacity |
| Quality | 25% | Accuracy & benchmarks |
| Reliability | 25% | Uptime & error rates |

**Minting Threshold**: Models must achieve Q-score ≥ 50 to mint tokens.

## 🛠️ Development

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Linting

```bash
# Run ruff linter
ruff check .

# Format with black
black .

# Type checking
mypy .
```

### Contract Compilation

```bash
# Compile smart contract with neo3-boa
neo3-boa compile contracts/chatten_token.py
```

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! Please read our contributing guidelines first.

---

Built with ❤️ using [Neo N3](https://neo.org) and [SpoonOS](https://spoonos.ai)
