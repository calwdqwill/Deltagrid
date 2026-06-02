#!/usr/bin/env python3
"""CLI для проверки качества данных.

Usage:
    cd backend
    python scripts/check_quality.py
    python scripts/check_quality.py --symbol BTC
"""

import argparse
import os
import sys

# Ensure backend/ is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.persistence.database import SessionLocal
from app.backtest.quality_monitor import DataQualityMonitor


def main():
    parser = argparse.ArgumentParser(description="Check data quality")
    parser.add_argument(
        "--symbol", help="Check specific symbol (BTC/ETH/SOL/HYPE)"
    )
    args = parser.parse_args()

    db = SessionLocal()
    monitor = DataQualityMonitor(db)

    if args.symbol:
        score = monitor.get_quality_score(args.symbol, "binance")
        gaps = monitor.check_ohlcv_gaps(args.symbol, "binance")
        print(f"Quality Report for {args.symbol}")
        print(f"  Score: {score}/100")
        print(f"  Gaps: {len(gaps)}")
        for g in gaps[:5]:
            print(f"    - {g.duration_min} min gap at {g.start_ms}")
    else:
        reports = monitor.run_all_checks()
        print("Quality Report for all symbols:")
        print("-" * 50)
        for r in reports:
            status = "OK" if r.is_backtest_ready() else "FAIL"
            print(
                f"  {r.symbol:6} | Score: {r.overall_score:3}/100 | {status}"
            )
            if r.warnings:
                for w in r.warnings:
                    print(f"    WARNING: {w}")

    db.close()


if __name__ == "__main__":
    main()
