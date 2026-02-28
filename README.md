# Polymarket Arbitrage Bot 🎰

A testing/learning project for Polymarket arbitrage based on:
- [@RohOnChain's deep dive](https://x.com/RohOnChain/status/2017314080395296995) on the math behind $40M in extracted arbitrage profits
- [@karpathy's thoughts](https://x.com/karpathy/status/2026360908398862478) on CLI-first tooling for AI agents

## Core Concepts

### The Math (from RohOnChain)

1. **Marginal Polytope Problem** - Why simple "YES + NO = $1" checks fail for multi-condition markets
2. **Bregman Projection** - Information-theoretic optimal arbitrage calculation
3. **Frank-Wolfe Algorithm** - Making the math computationally tractable
4. **Execution Under Non-Atomic Constraints** - Why order books change everything

### Key Stats from Research
- 17,218 conditions examined (Apr 2024 - Apr 2025)
- 7,051 conditions showed single-market arbitrage (41%)
- $39.7M total extracted
- Top trader: $2,009,632 from 4,049 trades (~$496/trade avg)

## Architecture

```
polymarket-arb-bot/
├── src/
│   ├── detection/       # Arbitrage detection (simple + combinatorial)
│   ├── projection/      # Bregman projection implementation
│   ├── execution/       # Order execution with slippage estimation
│   └── monitoring/      # Real-time dashboards
├── scripts/             # CLI tools and utilities
├── tests/               # Unit and integration tests
└── docs/                # Math breakdowns and strategy docs
```

## Getting Started

```bash
# Install Polymarket CLI (by @SuhailKakar)
# https://github.com/SuhailKakar/polymarket-cli

# Clone this repo
git clone https://github.com/bra0xit/polymarket-arb-bot
cd polymarket-arb-bot

# Install dependencies
pip install -r requirements.txt  # or npm install

# Run detection
python src/detection/simple_arb.py
```

## Types of Arbitrage

### 1. Single Condition (Simple)
- Check if YES + NO < $1.00 or > $1.00
- Most common, easiest to detect
- Often quickly arbitraged away

### 2. Market Rebalancing
- Multi-outcome markets where sum of all options ≠ $1.00
- Buy all YES tokens if sum < $1.00
- Buy all NO tokens if sum > $1.00

### 3. Combinatorial (Cross-Market)
- Exploits logical dependencies between markets
- E.g., "Trump wins PA" implies "Republican wins PA by 5+ points" is impossible
- Requires integer programming to detect efficiently

## Resources

- [Research Paper](https://arxiv.org/abs/2508.03474v1) - "Unravelling the Probabilistic Forest: Arbitrage in Prediction Markets"
- [Theory Foundation](https://arxiv.org/abs/1606.02825v2) - "Arbitrage-Free Combinatorial Market Making via Integer Programming"
- [Polymarket API Docs](https://docs.polymarket.com/)
- [Polymarket CLI](https://github.com/SuhailKakar/polymarket-cli)

## Disclaimer

⚠️ **Educational/Testing Only** - This is a learning project. Not financial advice. Prediction market trading involves significant risk.

## License

MIT
