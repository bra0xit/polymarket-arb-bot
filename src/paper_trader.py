"""
Paper Trading Module for Polymarket Arbitrage

Simulates trades against live market data without executing.
Tracks virtual balance, logs all "trades", calculates P&L.

Usage:
    python src/paper_trader.py --balance 1000 --min-profit 0.02
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
import time


@dataclass
class PaperTrade:
    timestamp: str
    market_id: str
    market_question: str
    action: str  # "BUY_BOTH" or "SELL_BOTH"
    yes_price: float
    no_price: float
    amount_usd: float
    expected_profit: float
    status: str = "SIMULATED"


@dataclass
class PaperPortfolio:
    initial_balance: float
    current_balance: float
    trades: list[PaperTrade] = field(default_factory=list)
    total_profit: float = 0.0
    win_count: int = 0
    loss_count: int = 0
    
    def record_trade(self, trade: PaperTrade):
        self.trades.append(trade)
        self.total_profit += trade.expected_profit
        self.current_balance += trade.expected_profit
        if trade.expected_profit > 0:
            self.win_count += 1
        else:
            self.loss_count += 1
    
    def summary(self) -> dict:
        return {
            "initial_balance": self.initial_balance,
            "current_balance": round(self.current_balance, 2),
            "total_profit": round(self.total_profit, 2),
            "profit_pct": round((self.total_profit / self.initial_balance) * 100, 2),
            "total_trades": len(self.trades),
            "win_rate": round(self.win_count / max(len(self.trades), 1) * 100, 1),
        }


def get_markets_cli(limit: int = 50) -> list[dict]:
    """Fetch markets using Polymarket CLI."""
    try:
        result = subprocess.run(
            ["polymarket", "-o", "json", "markets", "list", 
             "--active", "true", "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        print(f"CLI error: {e}")
    return []


def get_orderbook_cli(token_id: str) -> Optional[dict]:
    """Fetch orderbook for a token using CLI."""
    try:
        result = subprocess.run(
            ["polymarket", "-o", "json", "clob", "book", token_id],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception:
        pass
    return None


def detect_arbitrage(markets: list[dict], min_profit: float = 0.02) -> list[dict]:
    """Detect arbitrage opportunities from market list."""
    opportunities = []
    
    for market in markets:
        try:
            prices = market.get("outcomePrices", [])
            if len(prices) != 2:
                continue
            
            yes_price = float(prices[0])
            no_price = float(prices[1])
            total = yes_price + no_price
            spread = 1.0 - total
            
            if abs(spread) >= min_profit:
                opportunities.append({
                    "market": market,
                    "yes_price": yes_price,
                    "no_price": no_price,
                    "spread": spread,
                    "profit_pct": abs(spread) * 100,
                    "action": "BUY_BOTH" if spread > 0 else "SELL_BOTH"
                })
        except (KeyError, ValueError, TypeError):
            continue
    
    # Sort by profit potential
    opportunities.sort(key=lambda x: x["profit_pct"], reverse=True)
    return opportunities


def simulate_trade(
    opp: dict,
    portfolio: PaperPortfolio,
    trade_size: float = 100.0
) -> PaperTrade:
    """Simulate executing an arbitrage trade."""
    
    market = opp["market"]
    
    # Calculate expected profit
    # For BUY_BOTH: cost = (yes + no) * shares, payout = $1 * shares
    # Profit = payout - cost = spread * trade_size
    expected_profit = opp["spread"] * trade_size
    
    # Apply simulated slippage (0.5% average)
    slippage = 0.005 * trade_size
    expected_profit -= slippage
    
    # Apply fees (0.2% typical)
    fees = 0.002 * trade_size
    expected_profit -= fees
    
    trade = PaperTrade(
        timestamp=datetime.now().isoformat(),
        market_id=market.get("conditionId", market.get("id", "unknown")),
        market_question=market.get("question", "Unknown")[:80],
        action=opp["action"],
        yes_price=opp["yes_price"],
        no_price=opp["no_price"],
        amount_usd=trade_size,
        expected_profit=round(expected_profit, 4)
    )
    
    portfolio.record_trade(trade)
    return trade


def print_opportunity(opp: dict, index: int):
    """Pretty print an arbitrage opportunity."""
    market = opp["market"]
    action_emoji = "🟢" if opp["action"] == "BUY_BOTH" else "🔴"
    
    print(f"\n{action_emoji} #{index}: {market.get('question', 'Unknown')[:60]}...")
    print(f"   YES: ${opp['yes_price']:.3f} | NO: ${opp['no_price']:.3f} | Sum: ${opp['yes_price'] + opp['no_price']:.3f}")
    print(f"   Action: {opp['action']} | Profit: {opp['profit_pct']:.2f}%")


def print_portfolio(portfolio: PaperPortfolio):
    """Print portfolio summary."""
    s = portfolio.summary()
    print("\n" + "="*60)
    print("📊 PAPER TRADING PORTFOLIO")
    print("="*60)
    print(f"  Initial Balance: ${s['initial_balance']:,.2f}")
    print(f"  Current Balance: ${s['current_balance']:,.2f}")
    print(f"  Total Profit:    ${s['total_profit']:,.2f} ({s['profit_pct']:+.2f}%)")
    print(f"  Total Trades:    {s['total_trades']}")
    print(f"  Win Rate:        {s['win_rate']:.1f}%")
    print("="*60)


def save_trades(portfolio: PaperPortfolio, filepath: str = "paper_trades.json"):
    """Save trades to JSON file."""
    data = {
        "summary": portfolio.summary(),
        "trades": [
            {
                "timestamp": t.timestamp,
                "market_id": t.market_id,
                "question": t.market_question,
                "action": t.action,
                "yes_price": t.yes_price,
                "no_price": t.no_price,
                "amount": t.amount_usd,
                "profit": t.expected_profit,
                "status": t.status
            }
            for t in portfolio.trades
        ]
    }
    
    Path(filepath).write_text(json.dumps(data, indent=2))
    print(f"\n💾 Saved to {filepath}")


async def run_paper_trader(
    initial_balance: float = 1000.0,
    min_profit: float = 0.02,
    trade_size: float = 100.0,
    scan_interval: int = 60,
    max_trades: int = 10,
    dry_run: bool = True
):
    """
    Run paper trading loop.
    
    Args:
        initial_balance: Starting virtual balance
        min_profit: Minimum profit threshold (0.02 = 2%)
        trade_size: Amount per trade in USD
        scan_interval: Seconds between scans
        max_trades: Maximum trades before stopping
        dry_run: If True, only detect without simulating trades
    """
    
    portfolio = PaperPortfolio(
        initial_balance=initial_balance,
        current_balance=initial_balance
    )
    
    print("\n" + "="*60)
    print("🎰 POLYMARKET PAPER TRADER")
    print("="*60)
    print(f"  Mode: {'DRY RUN (detection only)' if dry_run else 'PAPER TRADING'}")
    print(f"  Initial Balance: ${initial_balance:,.2f}")
    print(f"  Min Profit: {min_profit*100:.1f}%")
    print(f"  Trade Size: ${trade_size:,.2f}")
    print(f"  Scan Interval: {scan_interval}s")
    print("="*60)
    
    scan_count = 0
    
    try:
        while len(portfolio.trades) < max_trades:
            scan_count += 1
            print(f"\n🔍 Scan #{scan_count} at {datetime.now().strftime('%H:%M:%S')}")
            
            # Fetch markets
            markets = get_markets_cli(limit=100)
            print(f"   Fetched {len(markets)} markets")
            
            if not markets:
                print("   ⚠️ No markets returned (CLI not installed or API error)")
                print("   Install CLI: brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli && brew install polymarket")
                await asyncio.sleep(scan_interval)
                continue
            
            # Detect opportunities
            opportunities = detect_arbitrage(markets, min_profit)
            print(f"   Found {len(opportunities)} opportunities above {min_profit*100:.1f}%")
            
            for i, opp in enumerate(opportunities[:5], 1):
                print_opportunity(opp, i)
                
                if not dry_run and portfolio.current_balance >= trade_size:
                    trade = simulate_trade(opp, portfolio, trade_size)
                    print(f"   📝 Simulated trade: ${trade.amount_usd} → profit ${trade.expected_profit:.2f}")
            
            if not dry_run:
                print_portfolio(portfolio)
            
            print(f"\n⏳ Next scan in {scan_interval}s... (Ctrl+C to stop)")
            await asyncio.sleep(scan_interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopped by user")
    
    # Final summary
    if not dry_run:
        print_portfolio(portfolio)
        save_trades(portfolio)
    
    return portfolio


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Polymarket Paper Trader")
    parser.add_argument("--balance", type=float, default=1000, help="Initial balance")
    parser.add_argument("--min-profit", type=float, default=0.02, help="Min profit threshold")
    parser.add_argument("--trade-size", type=float, default=100, help="Per-trade amount")
    parser.add_argument("--interval", type=int, default=60, help="Scan interval (seconds)")
    parser.add_argument("--max-trades", type=int, default=10, help="Max trades before stopping")
    parser.add_argument("--execute", action="store_true", help="Enable paper trade simulation (default: dry-run)")
    
    args = parser.parse_args()
    
    asyncio.run(run_paper_trader(
        initial_balance=args.balance,
        min_profit=args.min_profit,
        trade_size=args.trade_size,
        scan_interval=args.interval,
        max_trades=args.max_trades,
        dry_run=not args.execute
    ))
