"""Production-safe market data sync command.

Fetches recent Binance USD-M public market data and writes it to the configured
database. This is intentionally a small CLI command, not a background scheduler.
"""

import argparse
import asyncio
import logging
import time
import uuid
from typing import Iterable

from sqlalchemy import text

from app.adapters.data.backfill_orchestrator import BackfillJob, BackfillOrchestrator
from app.adapters.data.binance_adapter import BinanceAdapter
from app.adapters.data.data_writer import DataWriter
from app.adapters.data.rate_limiter import GlobalRateLimiter

logger = logging.getLogger("sync_market_data")


def _csv(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def _csv_lower(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _record_sync_run(
    writer: DataWriter,
    sync_type: str,
    status: str,
    start_ms: int,
    end_ms: int,
    fetched: int,
    inserted: int,
    error: str | None = None,
) -> None:
    stmt = text("""
        INSERT INTO provider_sync_runs (
            id, provider_name, sync_type, status, start_time, end_time,
            records_fetched, records_inserted, error_message
        )
        VALUES (
            :id, 'binance', :sync_type, :status, :start_time, :end_time,
            :records_fetched, :records_inserted, :error_message
        )
    """)
    with writer.engine.connect() as conn:
        conn.execute(
            stmt,
            {
                "id": str(uuid.uuid4()),
                "sync_type": sync_type,
                "status": status,
                "start_time": start_ms,
                "end_time": end_ms,
                "records_fetched": fetched,
                "records_inserted": inserted,
                "error_message": error,
            },
        )
        conn.commit()


async def _sync_ohlcv(
    adapter: BinanceAdapter,
    writer: DataWriter,
    symbols: Iterable[str],
    intervals: Iterable[str],
    start_ms: int,
    end_ms: int,
    chunk_size: int,
) -> tuple[int, int, list[str]]:
    orchestrator = BackfillOrchestrator(writer=writer)
    fetched = 0
    inserted = 0
    errors: list[str] = []

    for symbol in symbols:
        for interval in intervals:
            job = BackfillJob(
                symbol=symbol,
                exchange="binance",
                data_type="ohlcv",
                interval=interval,
                start_ms=start_ms,
                end_ms=end_ms,
                chunk_size=chunk_size,
            )
            try:
                result = await orchestrator.backfill_ohlcv(adapter, job)
                fetched += result.total_fetched
                inserted += result.total_inserted
                logger.info(
                    "ohlcv %s %s fetched=%s inserted=%s gaps=%s",
                    symbol,
                    interval,
                    result.total_fetched,
                    result.total_inserted,
                    len(result.gaps),
                )
            except Exception as exc:
                message = f"ohlcv {symbol} {interval}: {exc}"
                errors.append(message)
                logger.exception(message)

    return fetched, inserted, errors


async def _sync_funding(
    adapter: BinanceAdapter,
    writer: DataWriter,
    symbols: Iterable[str],
    start_ms: int,
    end_ms: int,
) -> tuple[int, int, list[str]]:
    fetched = 0
    inserted = 0
    errors: list[str] = []

    for symbol in symbols:
        try:
            rows = await adapter.fetch_funding(symbol, start_ms, end_ms)
            fetched += len(rows)
            inserted += writer.upsert_funding(rows)
            logger.info("funding %s fetched=%s", symbol, len(rows))
        except Exception as exc:
            message = f"funding {symbol}: {exc}"
            errors.append(message)
            logger.exception(message)

    return fetched, inserted, errors


async def _sync_oi(
    adapter: BinanceAdapter,
    writer: DataWriter,
    symbols: Iterable[str],
    interval: str,
) -> tuple[int, int, list[str]]:
    fetched = 0
    inserted = 0
    errors: list[str] = []

    for symbol in symbols:
        try:
            rows = await adapter.fetch_oi(symbol, interval=interval)
            fetched += len(rows)
            inserted += writer.upsert_oi(rows)
            logger.info("open_interest %s %s fetched=%s", symbol, interval, len(rows))
        except Exception as exc:
            message = f"open_interest {symbol}: {exc}"
            errors.append(message)
            logger.exception(message)

    return fetched, inserted, errors


async def _sync_long_short(
    adapter: BinanceAdapter,
    writer: DataWriter,
    symbols: Iterable[str],
    interval: str,
    start_ms: int,
    end_ms: int,
) -> tuple[int, int, list[str]]:
    fetched = 0
    inserted = 0
    errors: list[str] = []

    for symbol in symbols:
        try:
            rows = await adapter.fetch_long_short_ratio(symbol, interval, start_ms, end_ms)
            fetched += len(rows)
            inserted += writer.upsert_long_short(rows)
            logger.info("long_short_ratio %s %s fetched=%s", symbol, interval, len(rows))
        except Exception as exc:
            message = f"long_short_ratio {symbol}: {exc}"
            errors.append(message)
            logger.exception(message)

    return fetched, inserted, errors


async def run(args: argparse.Namespace) -> int:
    symbols = _csv(args.symbols)
    intervals = _csv_lower(args.ohlcv_intervals)
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - int(args.lookback_hours * 60 * 60 * 1000)

    writer = DataWriter()
    adapter = BinanceAdapter(rate_limiter=GlobalRateLimiter(), use_mock=args.use_mock)

    try:
        total_fetched = 0
        total_inserted = 0
        all_errors: list[str] = []

        fetched, inserted, errors = await _sync_ohlcv(
            adapter,
            writer,
            symbols,
            intervals,
            start_ms,
            now_ms,
            args.chunk_size,
        )
        total_fetched += fetched
        total_inserted += inserted
        all_errors.extend(errors)
        _record_sync_run(
            writer,
            "ohlcv",
            "completed" if not errors else "partial",
            start_ms,
            now_ms,
            fetched,
            inserted,
            "; ".join(errors) if errors else None,
        )

        if args.include_funding:
            fetched, inserted, errors = await _sync_funding(adapter, writer, symbols, start_ms, now_ms)
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "funding_rates",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_open_interest:
            fetched, inserted, errors = await _sync_oi(adapter, writer, symbols, args.derived_interval)
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "open_interest",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_long_short:
            fetched, inserted, errors = await _sync_long_short(
                adapter,
                writer,
                symbols,
                args.derived_interval,
                start_ms,
                now_ms,
            )
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "long_short_ratio",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        logger.info("sync complete fetched=%s inserted=%s errors=%s", total_fetched, total_inserted, len(all_errors))
        return 1 if all_errors and total_inserted == 0 else 0
    finally:
        await adapter.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync recent Binance market data into DeltaGrid DB.")
    parser.add_argument("--symbols", default="BTC,ETH,SOL", help="Comma-separated canonical symbols.")
    parser.add_argument("--ohlcv-intervals", default="1m,5m,1h", help="Comma-separated OHLCV intervals.")
    parser.add_argument("--lookback-hours", type=float, default=24.0, help="Historical window to fetch.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="OHLCV candles per request.")
    parser.add_argument("--derived-interval", default="1h", help="Interval for OI and long/short endpoints.")
    parser.add_argument("--include-funding", action="store_true", help="Fetch funding-rate history.")
    parser.add_argument("--include-open-interest", action="store_true", help="Fetch open-interest history.")
    parser.add_argument("--include-long-short", action="store_true", help="Fetch long/short account ratio.")
    parser.add_argument("--use-mock", action="store_true", help="Use deterministic mock OHLCV instead of Binance.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
