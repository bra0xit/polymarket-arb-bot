#!/usr/bin/env python3
"""
CLI script to scan Polymarket for arbitrage opportunities.

Usage:
    python scripts/scan.py [--min-profit 0.02] [--output json]
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from detection.simple_arb import scan_markets, print_opportunities


async def main():
    parser = argparse.ArgumentParser(description="Scan Polymarket for arbitrage")
    parser.add_argument(
        "--min-profit",
        type=float,
        default=0.02,
        help="Minimum profit threshold (default: 0.02 = 2%%)"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum opportunities to show"
    )
    
    args = parser.parse_args()
    
    print(f"Scanning Polymarket (min profit: {args.min_profit*100:.1f}%)...")
    opportunities = await scan_markets(min_profit=args.min_profit)
    
    if args.limit:
        opportunities = opportunities[:args.limit]
    
    if args.output == "json":
        output = [
            {
                "market_id": opp.market_id,
                "question": opp.market_question,
                "yes_price": opp.yes_price,
                "no_price": opp.no_price,
                "spread": opp.spread,
                "profit_pct": opp.potential_profit_pct,
                "volume_24h": opp.volume_24h,
                "liquidity": opp.liquidity
            }
            for opp in opportunities
        ]
        print(json.dumps(output, indent=2))
    else:
        print_opportunities(opportunities)


if __name__ == "__main__":
    asyncio.run(main())
