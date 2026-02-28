#!/usr/bin/env python3
"""
Spread Monitor for Polymarket

Monitors bid/ask spreads and alerts when they widen above threshold.
This is where real opportunities appear - during volatility or news events.

Usage:
    python src/spread_monitor.py --threshold 2.0 --interval 30
"""

import asyncio
import json
import subprocess
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import argparse
import os
import urllib.request
import urllib.parse

# Telegram config - sends via Clawdbot
TELEGRAM_ENABLED = True


@dataclass
class MarketSpread:
    market_id: str
    question: str
    yes_price: float
    no_price: float
    best_bid: float
    best_ask: float
    spread_pct: float
    volume_24h: float
    liquidity: float


def get_markets(limit: int = 100) -> list[dict]:
    """Fetch active markets via CLI."""
    try:
        result = subprocess.run(
            ["polymarket", "-o", "json", "markets", "list", 
             "--active", "true", "--limit", str(limit)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Error fetching markets: {e}")
    return []


def analyze_spreads(markets: list[dict]) -> list[MarketSpread]:
    """Analyze bid/ask spreads for all markets."""
    spreads = []
    
    for m in markets:
        try:
            prices = json.loads(m.get('outcomePrices', '[]'))
            if len(prices) != 2:
                continue
            
            yes_price = float(prices[0])
            no_price = float(prices[1])
            best_bid = float(m.get('bestBid', 0) or 0)
            best_ask = float(m.get('bestAsk', 0) or 0)
            
            if best_bid > 0 and best_ask > 0:
                spread_pct = (best_ask - best_bid) * 100
            else:
                spread_pct = 0
            
            spreads.append(MarketSpread(
                market_id=m.get('conditionId', m.get('id', '')),
                question=m.get('question', 'Unknown'),
                yes_price=yes_price,
                no_price=no_price,
                best_bid=best_bid,
                best_ask=best_ask,
                spread_pct=spread_pct,
                volume_24h=float(m.get('volume24hr', 0) or 0),
                liquidity=float(m.get('liquidity', 0) or 0)
            ))
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            continue
    
    return spreads


def format_alert(spread: MarketSpread) -> str:
    """Format an alert message."""
    return f"""🚨 WIDE SPREAD ALERT

📊 {spread.question[:60]}...

💰 Spread: {spread.spread_pct:.2f}%
   Bid: ${spread.best_bid:.4f} | Ask: ${spread.best_ask:.4f}
   
📈 YES: ${spread.yes_price:.3f} | NO: ${spread.no_price:.3f}
💧 Liquidity: ${spread.liquidity:,.0f}
📊 24h Volume: ${spread.volume_24h:,.0f}

⏰ {datetime.now().strftime('%H:%M:%S')}"""


def send_telegram_alert(message: str, chat_id: str = "1971982224") -> bool:
    """Send alert via Clawdbot CLI to Telegram."""
    try:
        result = subprocess.run(
            [
                "clawdbot", "message", "send",
                "--channel", "telegram",
                "--target", chat_id,
                "--message", message
            ],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


def save_alert(spread: MarketSpread, filepath: str = "alerts.jsonl"):
    """Append alert to JSONL file."""
    alert = {
        "timestamp": datetime.now().isoformat(),
        "market_id": spread.market_id,
        "question": spread.question,
        "spread_pct": spread.spread_pct,
        "best_bid": spread.best_bid,
        "best_ask": spread.best_ask,
        "yes_price": spread.yes_price,
        "no_price": spread.no_price,
        "volume_24h": spread.volume_24h,
        "liquidity": spread.liquidity
    }
    with open(filepath, "a") as f:
        f.write(json.dumps(alert) + "\n")


async def monitor_spreads(
    threshold: float = 2.0,
    interval: int = 30,
    min_volume: float = 1000,
    min_liquidity: float = 500,
    alert_file: str = "alerts.jsonl",
    verbose: bool = True,
    notify_telegram: bool = False
):
    """
    Continuously monitor spreads and alert on wide ones.
    
    Args:
        threshold: Alert when spread exceeds this % (default 2.0%)
        interval: Seconds between scans
        min_volume: Minimum 24h volume to consider
        min_liquidity: Minimum liquidity to consider
        alert_file: File to save alerts
        verbose: Print all scan results
    """
    
    seen_alerts = set()  # Avoid duplicate alerts
    scan_count = 0
    total_alerts = 0
    
    print("\n" + "="*60)
    print("🔍 POLYMARKET SPREAD MONITOR")
    print("="*60)
    print(f"  Threshold: {threshold}% spread")
    print(f"  Min Volume: ${min_volume:,.0f}")
    print(f"  Min Liquidity: ${min_liquidity:,.0f}")
    print(f"  Scan Interval: {interval}s")
    print(f"  Alerts saved to: {alert_file}")
    print(f"  Telegram alerts: {'ON 📱' if notify_telegram else 'OFF'}")
    print("="*60)
    print("\nMonitoring... (Ctrl+C to stop)\n")
    
    try:
        while True:
            scan_count += 1
            now = datetime.now().strftime('%H:%M:%S')
            
            # Fetch and analyze
            markets = get_markets(limit=150)
            if not markets:
                print(f"[{now}] ⚠️ No markets fetched, retrying...")
                await asyncio.sleep(interval)
                continue
            
            spreads = analyze_spreads(markets)
            
            # Filter by volume/liquidity
            qualified = [
                s for s in spreads 
                if s.volume_24h >= min_volume 
                and s.liquidity >= min_liquidity
                and s.spread_pct > 0
            ]
            
            # Find wide spreads
            wide_spreads = [s for s in qualified if s.spread_pct >= threshold]
            
            if verbose:
                # Show top 5 spreads
                top5 = sorted(qualified, key=lambda x: x.spread_pct, reverse=True)[:5]
                print(f"[{now}] Scan #{scan_count} | {len(qualified)} markets | Top spreads:")
                for s in top5:
                    marker = "🔥" if s.spread_pct >= threshold else "  "
                    print(f"  {marker} {s.spread_pct:.2f}% | {s.question[:40]}...")
                print()
            
            # Process alerts
            for spread in wide_spreads:
                alert_key = f"{spread.market_id}_{int(spread.spread_pct)}"
                
                if alert_key not in seen_alerts:
                    seen_alerts.add(alert_key)
                    total_alerts += 1
                    
                    alert_msg = format_alert(spread)
                    
                    # Print alert
                    print("\n" + "!"*60)
                    print(alert_msg)
                    print("!"*60 + "\n")
                    
                    # Save to file
                    save_alert(spread, alert_file)
                    
                    # Send Telegram notification
                    if notify_telegram:
                        if send_telegram_alert(alert_msg):
                            print("📱 Telegram alert sent!")
                        else:
                            print("⚠️ Telegram alert failed")
            
            # Clean old alerts (reset after 10 minutes)
            if scan_count % 20 == 0:
                seen_alerts.clear()
            
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped after {scan_count} scans, {total_alerts} alerts")
        print(f"Alerts saved to: {alert_file}")


async def quick_scan(threshold: float = 1.0):
    """Run a single scan and show results."""
    print("\n🔍 Quick Spread Scan...")
    
    markets = get_markets(limit=150)
    if not markets:
        print("❌ Failed to fetch markets. Is the CLI installed?")
        print("   Run: brew tap Polymarket/polymarket-cli https://github.com/Polymarket/polymarket-cli && brew install polymarket")
        return
    
    spreads = analyze_spreads(markets)
    
    # Filter and sort
    qualified = [s for s in spreads if s.volume_24h >= 1000 and s.spread_pct > 0]
    qualified.sort(key=lambda x: x.spread_pct, reverse=True)
    
    print(f"\nFound {len(qualified)} markets with >$1k volume\n")
    print("TOP 15 BY SPREAD:")
    print("="*70)
    
    for i, s in enumerate(qualified[:15], 1):
        alert = "🔥" if s.spread_pct >= threshold else "  "
        print(f"{i:2}. {alert} {s.spread_pct:5.2f}% | ${s.volume_24h:>10,.0f} vol | {s.question[:40]}...")
    
    print("="*70)
    
    # Stats
    if qualified:
        avg_spread = sum(s.spread_pct for s in qualified) / len(qualified)
        max_spread = max(s.spread_pct for s in qualified)
        above_threshold = len([s for s in qualified if s.spread_pct >= threshold])
        
        print(f"\nSTATS:")
        print(f"  Avg spread: {avg_spread:.3f}%")
        print(f"  Max spread: {max_spread:.3f}%")
        print(f"  Above {threshold}% threshold: {above_threshold} markets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Polymarket Spread Monitor")
    parser.add_argument("--threshold", type=float, default=2.0,
                       help="Alert threshold in %% (default: 2.0)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Scan interval in seconds (default: 30)")
    parser.add_argument("--min-volume", type=float, default=1000,
                       help="Min 24h volume (default: 1000)")
    parser.add_argument("--min-liquidity", type=float, default=500,
                       help="Min liquidity (default: 500)")
    parser.add_argument("--quick", action="store_true",
                       help="Run single scan and exit")
    parser.add_argument("--quiet", action="store_true",
                       help="Only show alerts, not every scan")
    parser.add_argument("--notify", action="store_true",
                       help="Send Telegram notifications on alerts")
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_scan(args.threshold))
    else:
        asyncio.run(monitor_spreads(
            threshold=args.threshold,
            interval=args.interval,
            min_volume=args.min_volume,
            min_liquidity=args.min_liquidity,
            verbose=not args.quiet,
            notify_telegram=args.notify
        ))
