"""CLI runner for backtests.

Usage:
    python scripts/run_backtest.py \
        --strategy funding_mean_reversion \
        --symbol BTC \
        --exchange binance \
        --days 30 \
        --output results.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path so imports work when running standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.backtest.config import BacktestConfig
from app.backtest.engine import BacktestEngine
from app.persistence.database import SessionLocal


def parse_args():
    parser = argparse.ArgumentParser(description="Run backtest")
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        choices=[
            "funding_mean_reversion",
            "basis_compression",
            "liquidation_cascade_fade",
        ],
        help="Strategy to run",
    )
    parser.add_argument("--symbol", type=str, required=True, help="Symbol (BTC, ETH, SOL, HYPE)")
    parser.add_argument("--exchange", type=str, default="binance", help="Exchange")
    parser.add_argument("--days", type=int, default=30, help="Backtest last N days")
    parser.add_argument("--output", type=str, default=None, help="Output JSON file path")
    parser.add_argument("--position-size", type=float, default=10_000, help="Position size in USD")
    parser.add_argument("--leverage", type=float, default=1.0, help="Leverage")
    parser.add_argument("--fee-type", type=str, default="taker", choices=["maker", "taker"])
    parser.add_argument("--no-slippage", action="store_true", help="Disable slippage")
    parser.add_argument("--params", type=str, default="{}", help='JSON dict of strategy params, e.g. \'{"price_move_threshold":0.015}\'')
    return parser.parse_args()


def main():
    args = parse_args()

    # Compute time range: last N days from now
    now = datetime.now(timezone.utc)
    end_ms = int(now.timestamp() * 1000)
    start_ms = int((now.timestamp() - args.days * 86400) * 1000)

    import json
    params = json.loads(args.params) if args.params else {}

    config = BacktestConfig(
        strategy_type=args.strategy,
        symbol=args.symbol.upper(),
        exchange=args.exchange.lower(),
        start_ms=start_ms,
        end_ms=end_ms,
        position_size_usd=args.position_size,
        leverage=args.leverage,
        fee_type=args.fee_type,
        use_slippage=not args.no_slippage,
        params=params,
    )

    db = SessionLocal()
    try:
        engine = BacktestEngine(db, config)
        result = engine.run()
        print(result.summary())

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            print(f"\nResults saved to: {output_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
