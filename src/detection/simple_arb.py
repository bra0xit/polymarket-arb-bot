"""
Simple Arbitrage Detection for Polymarket

Detects basic arbitrage opportunities:
1. YES + NO < $1.00 (buy both, guaranteed profit)
2. YES + NO > $1.00 (sell both if you hold, or short)
3. Multi-outcome sum != $1.00
"""

import asyncio
import aiohttp
from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class ArbitrageOpportunity:
    market_id: str
    market_question: str
    yes_price: float
    no_price: float
    spread: float  # 1.0 - (yes + no), positive = buy opportunity
    potential_profit_pct: float
    volume_24h: float
    liquidity: float


POLYMARKET_API = "https://clob.polymarket.com"
MIN_PROFIT_THRESHOLD = 0.02  # 2% minimum to account for fees/slippage


async def fetch_markets(session: aiohttp.ClientSession) -> list[dict]:
    """Fetch active markets from Polymarket CLOB API."""
    url = f"{POLYMARKET_API}/markets"
    async with session.get(url) as resp:
        if resp.status == 200:
            return await resp.json()
    return []


async def fetch_orderbook(session: aiohttp.ClientSession, token_id: str) -> dict:
    """Fetch orderbook for a specific token."""
    url = f"{POLYMARKET_API}/book"
    params = {"token_id": token_id}
    async with session.get(url, params=params) as resp:
        if resp.status == 200:
            return await resp.json()
    return {}


def calculate_vwap(orders: list[dict], max_amount: float = 1000) -> Optional[float]:
    """Calculate volume-weighted average price up to max_amount."""
    if not orders:
        return None
    
    total_cost = 0.0
    total_volume = 0.0
    
    for order in orders:
        price = float(order.get("price", 0))
        size = float(order.get("size", 0))
        
        remaining = max_amount - total_volume
        if remaining <= 0:
            break
            
        fill_size = min(size, remaining)
        total_cost += price * fill_size
        total_volume += fill_size
    
    return total_cost / total_volume if total_volume > 0 else None


def detect_simple_arbitrage(
    yes_price: float,
    no_price: float,
    threshold: float = MIN_PROFIT_THRESHOLD
) -> tuple[bool, float]:
    """
    Detect if simple YES/NO arbitrage exists.
    
    Returns (is_arbitrage, spread) where:
    - Positive spread = buy opportunity (sum < $1)
    - Negative spread = sell opportunity (sum > $1)
    """
    total = yes_price + no_price
    spread = 1.0 - total
    
    is_arb = abs(spread) >= threshold
    return is_arb, spread


async def scan_markets(min_profit: float = MIN_PROFIT_THRESHOLD) -> list[ArbitrageOpportunity]:
    """Scan all markets for arbitrage opportunities."""
    opportunities = []
    
    async with aiohttp.ClientSession() as session:
        markets = await fetch_markets(session)
        
        for market in markets:
            try:
                # Get YES and NO token prices
                tokens = market.get("tokens", [])
                if len(tokens) != 2:
                    continue  # Skip non-binary markets for now
                
                yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), None)
                no_token = next((t for t in tokens if t.get("outcome") == "No"), None)
                
                if not yes_token or not no_token:
                    continue
                
                yes_price = float(yes_token.get("price", 0))
                no_price = float(no_token.get("price", 0))
                
                is_arb, spread = detect_simple_arbitrage(yes_price, no_price, min_profit)
                
                if is_arb:
                    opp = ArbitrageOpportunity(
                        market_id=market.get("condition_id", ""),
                        market_question=market.get("question", "Unknown"),
                        yes_price=yes_price,
                        no_price=no_price,
                        spread=spread,
                        potential_profit_pct=abs(spread) * 100,
                        volume_24h=float(market.get("volume_24hr", 0)),
                        liquidity=float(market.get("liquidity", 0))
                    )
                    opportunities.append(opp)
                    
            except (KeyError, ValueError, TypeError) as e:
                continue  # Skip malformed markets
    
    # Sort by profit potential
    opportunities.sort(key=lambda x: x.potential_profit_pct, reverse=True)
    return opportunities


def print_opportunities(opportunities: list[ArbitrageOpportunity]):
    """Pretty print arbitrage opportunities."""
    if not opportunities:
        print("No arbitrage opportunities found above threshold.")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(opportunities)} arbitrage opportunities")
    print(f"{'='*80}\n")
    
    for i, opp in enumerate(opportunities, 1):
        action = "BUY BOTH" if opp.spread > 0 else "SELL BOTH"
        print(f"{i}. {opp.market_question[:60]}...")
        print(f"   YES: ${opp.yes_price:.3f} | NO: ${opp.no_price:.3f} | Sum: ${opp.yes_price + opp.no_price:.3f}")
        print(f"   Action: {action} | Profit: {opp.potential_profit_pct:.2f}%")
        print(f"   24h Volume: ${opp.volume_24h:,.0f} | Liquidity: ${opp.liquidity:,.0f}")
        print()


async def main():
    print("Scanning Polymarket for arbitrage opportunities...")
    opportunities = await scan_markets()
    print_opportunities(opportunities)


if __name__ == "__main__":
    asyncio.run(main())
