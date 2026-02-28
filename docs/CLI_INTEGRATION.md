# Polymarket CLI Integration

Official CLI: https://github.com/Polymarket/polymarket-cli

Rust CLI for Polymarket. Browse markets, place orders, manage positions — from terminal or as JSON API for scripts/agents.

## Install

```bash
# Homebrew (macOS/Linux)
brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli
brew install polymarket

# Shell script
curl -sSL https://raw.githubusercontent.com/Polymarket/polymarket-cli/main/install.sh | sh

# From source
git clone https://github.com/Polymarket/polymarket-cli
cd polymarket-cli
cargo install --path .
```

## Key Commands for Arbitrage

### Read-Only (No Wallet Needed)

```bash
# List markets
polymarket markets list --limit 10
polymarket markets list --active true --order volume_num

# Search
polymarket markets search "bitcoin" --limit 5

# Get specific market
polymarket markets get will-trump-win-the-2024-election

# Order book
polymarket clob book <token_id>
polymarket clob books "TOKEN1,TOKEN2"

# Prices
polymarket clob price <token_id> --side buy
polymarket clob midpoint <token_id>
polymarket clob spread <token_id>

# Batch price queries
polymarket clob batch-prices "TOKEN1,TOKEN2" --side buy
polymarket clob midpoints "TOKEN1,TOKEN2"
polymarket clob spreads "TOKEN1,TOKEN2"

# Price history
polymarket clob price-history <token_id> --interval 1d --fidelity 30

# Market metadata
polymarket clob tick-size <token_id>
polymarket clob fee-rate <token_id>
```

### Trading (Wallet Required)

```bash
# Setup wallet
polymarket setup
# Or manually:
polymarket wallet create
polymarket approve set  # needs MATIC for gas

# Place limit order
polymarket clob create-order \
  --token <token_id> \
  --side buy --price 0.50 --size 10

# Place market order
polymarket clob market-order \
  --token <token_id> \
  --side buy --amount 5

# Multiple orders at once
polymarket clob post-orders \
  --tokens "TOKEN1,TOKEN2" \
  --side buy \
  --prices "0.40,0.60" \
  --sizes "10,10"

# Cancel orders
polymarket clob cancel ORDER_ID
polymarket clob cancel-all

# Check balances
polymarket clob balance --asset-type collateral
polymarket clob balance --asset-type conditional --token <token_id>
```

### On-Chain Operations

```bash
# Split USDC into YES/NO tokens
polymarket ctf split --condition 0xCONDITION... --amount 10

# Merge tokens back to USDC
polymarket ctf merge --condition 0xCONDITION... --amount 10

# Redeem winning tokens
polymarket ctf redeem --condition 0xCONDITION...
```

## JSON Output for Scripts

Every command supports `--output json` (or `-o json`):

```bash
# Get market data as JSON
polymarket -o json markets list --limit 10

# Pipe to jq
polymarket -o json clob book <token_id> | jq '.bids[0]'
```

## Python Integration

```python
import subprocess
import json

def get_markets(limit=10):
    result = subprocess.run(
        ["polymarket", "-o", "json", "markets", "list", "--limit", str(limit)],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def get_orderbook(token_id):
    result = subprocess.run(
        ["polymarket", "-o", "json", "clob", "book", token_id],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

def place_order(token_id, side, price, size):
    result = subprocess.run(
        [
            "polymarket", "-o", "json", "clob", "create-order",
            "--token", token_id,
            "--side", side,
            "--price", str(price),
            "--size", str(size)
        ],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

## Arbitrage Detection with CLI

```bash
#!/bin/bash
# Simple arbitrage scanner using CLI

# Get all active markets
markets=$(polymarket -o json markets list --active true --limit 100)

# For each market, check if YES + NO < 1.0
echo "$markets" | jq -c '.[]' | while read market; do
    yes_price=$(echo "$market" | jq -r '.outcomePrices[0]')
    no_price=$(echo "$market" | jq -r '.outcomePrices[1]')
    sum=$(echo "$yes_price + $no_price" | bc)
    
    if (( $(echo "$sum < 0.98" | bc -l) )); then
        question=$(echo "$market" | jq -r '.question')
        echo "ARBITRAGE: $question"
        echo "  YES: $yes_price, NO: $no_price, Sum: $sum"
    fi
done
```

## Interactive Shell

```bash
polymarket shell
# polymarket> markets list --limit 3
# polymarket> clob book <token_id>
# polymarket> exit
```

## Configuration

Config file: `~/.config/polymarket/config.json`

```json
{
  "private_key": "0x...",
  "chain_id": 137,
  "signature_type": "proxy"
}
```

## Useful Leaderboard Commands

```bash
# Top traders by PnL
polymarket data leaderboard --period month --order-by pnl --limit 10

# Check any wallet's positions
polymarket data positions 0xWALLET_ADDRESS
polymarket data value 0xWALLET_ADDRESS
polymarket data trades 0xWALLET_ADDRESS --limit 50
```
