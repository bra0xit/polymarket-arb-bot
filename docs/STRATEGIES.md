# Polymarket Trading Strategies

Compiled from [@Argona0x](https://x.com/Argona0x/status/2002391129870803306) - practical breakdown of how traders are making $10k-200k/month.

## 1. Simple Arbitrage Bots

**Concept:** Buy YES + NO when combined price < $1

**Example:**
- YES at 48¢ + NO at 49¢ = 97¢ total
- Lock $0.03 profit per $1 no matter who wins

**Real Results:**
- Trader "distinct-baguette": $242k in 1.5 months

**Implementation:**
- Target 15-min crypto markets (prices move fast)
- Python script polls API every 1-3 seconds
- Execute when sum < 99¢

## 2. Statistical Arbitrage

**Concept:** Find correlated markets that drift apart

**Example:**
- "Trump wins" vs "GOP senate control" should move together
- When spread hits 4-7%: short expensive, long cheap
- Close when they converge

**Real Results:**
- Trader "sharky6999": $480k

**Implementation:**
- Scan 100+ markets per minute
- Track correlation coefficients
- Alert on divergence

## 3. AI Probability Models

**Concept:** Train ML models to estimate real odds from news/social data

**Example:**
- Your model says 60% YES but market at 50¢ → buy

**Real Results:**
- Trader "ilovecircle": $2.2M in 2 months with 74% accuracy

**Implementation:**
- Ensemble of 10 AI models
- Retrain weekly
- Sources: news feeds, Twitter sentiment, polling data

## 4. Spread Farming (Market Making)

**Concept:** Buy at bid, sell at ask, repeat

**Example:**
- Buy at 5¢, sell at 6¢, pocket 1¢
- Or hedge across platforms (short Polymarket, long Binance)

**Real Results:**
- Trader "cry.eth2": $194k with 1M trades

**Implementation:**
- High-frequency loop via CLOB API
- Requires capital for both sides
- Focus on liquid markets

## 5. Copy-Trading Automation

**Concept:** Mirror successful whale traders automatically

**Implementation:**
- Scan whale profiles
- Execute proportional trades
- Focus on near-resolved markets (higher confidence)

**Real Results:**
- One bot: $80k in 2 weeks

## Tech Stack

### Core Libraries
```python
# API calls
import requests

# Blockchain interactions
from web3 import Web3

# Data processing
import pandas as pd
import numpy as np
```

### Polymarket APIs
| API | Purpose |
|-----|---------|
| Gamma Markets API | Prices, volumes, market info |
| CLOB API | Place/cancel orders |
| Data API | Track positions, history |

### Infrastructure
- VPS for 24/7 operation (DigitalOcean, AWS, etc.)
- Redis for caching/state
- PostgreSQL for historical data
- Prometheus + Grafana for monitoring

## Getting Started

### Phase 1: Simple Arbitrage Bot
1. Build basic YES+NO < $1 detector
2. Fund with $100-$1k for testing
3. Target high-volume markets (politics/crypto)
4. Expect 50-70% win rate, focus on positive EV

### Phase 2: Add Statistical Arb
1. Build correlation tracker
2. Identify logical dependencies
3. Test with paper trading first

### Phase 3: ML Enhancement
1. Add news/sentiment feeds
2. Train probability models
3. Ensemble for robustness

## Risk Warnings

⚠️ **Execution Risk:** Orders may not fill at expected prices
⚠️ **Liquidity Risk:** Large orders move the market
⚠️ **Platform Risk:** API downtime, settlement issues
⚠️ **Regulatory Risk:** Prediction markets have legal grey areas

## Trader Leaderboard (Referenced)

| Trader | Strategy | Profit | Timeframe |
|--------|----------|--------|-----------|
| ilovecircle | AI models | $2.2M | 2 months |
| sharky6999 | Stat arb | $480k | - |
| distinct-baguette | Simple arb | $242k | 1.5 months |
| cry.eth2 | Spread farming | $194k | 1M trades |
| Copy bot | Copy trading | $80k | 2 weeks |

---

*Source: [@Argona0x](https://x.com/Argona0x/status/2002391129870803306)*
