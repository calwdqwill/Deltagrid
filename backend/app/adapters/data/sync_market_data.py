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

from app.adapters.coingecko_adapter import CoinGeckoAdapter
from app.adapters.data.backfill_orchestrator import BackfillJob, BackfillOrchestrator
from app.adapters.data.binance_adapter import BinanceAdapter
from app.adapters.data.data_writer import DataWriter
from app.adapters.data.data_models import FundingRate, OpenInterest
from app.adapters.data.rate_limiter import GlobalRateLimiter
from app.adapters.data.symbol_mapper import SymbolMapper
from app.services.providers.coinglass_client import CoinGlassClient

logger = logging.getLogger("sync_market_data")


def _csv(value: str) -> list[str]:
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def _csv_lower(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _record_sync_run(
    writer: DataWriter,
    provider_name: str,
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
            :id, :provider_name, :sync_type, :status, :start_time, :end_time,
            :records_fetched, :records_inserted, :error_message
        )
    """)
    with writer.engine.connect() as conn:
        conn.execute(
            stmt,
            {
                "id": str(uuid.uuid4()),
                "provider_name": provider_name,
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


def _coinglass_rate_to_decimal(raw_value) -> float:
    """CoinGlass v4 market endpoint returns funding as percent-like values."""
    if raw_value is None:
        return 0.0
    return float(raw_value) / 100


async def _sync_coinglass_snapshots(
    writer: DataWriter,
    symbols: Iterable[str],
    timestamp_ms: int,
) -> tuple[int, int, list[str]]:
    symbol_set = {symbol.upper() for symbol in symbols}
    client = CoinGlassClient()
    try:
        rows = await client.get_funding_rates()
    finally:
        await client.close()

    if not rows:
        return 0, 0, ["coinglass snapshots: no data returned"]

    filtered = [
        row
        for row in rows
        if str(row.get("symbol", "")).upper() in symbol_set
    ]
    funding_rows: list[FundingRate] = []
    oi_rows: list[OpenInterest] = []

    for row in filtered:
        symbol = str(row.get("symbol", "")).upper()
        funding_raw = (
            row.get("avg_funding_rate_by_oi")
            or row.get("avg_funding_rate_by_vol")
            or row.get("fundingRate")
            or row.get("funding_rate")
        )
        funding_rows.append(
            FundingRate(
                timestamp_ms=timestamp_ms,
                symbol=symbol,
                exchange="coinglass",
                funding_rate=_coinglass_rate_to_decimal(funding_raw),
                next_funding_time_ms=None,
                interval="8h",
            )
        )
        oi_rows.append(
            OpenInterest(
                timestamp_ms=timestamp_ms,
                symbol=symbol,
                exchange="coinglass",
                interval="snapshot",
                oi_usd=float(row.get("open_interest_usd") or 0),
                oi_coins=float(row.get("open_interest_quantity") or 0),
            )
        )

    inserted = writer.upsert_funding(funding_rows)
    inserted += writer.upsert_oi(oi_rows)
    fetched = len(filtered) * 2
    logger.info("coinglass snapshots fetched=%s inserted=%s", fetched, inserted)
    return fetched, inserted, []


async def _sync_coingecko_basis(
    writer: DataWriter,
    symbols: Iterable[str],
    timestamp_ms: int,
) -> tuple[int, int, list[str]]:
    mapper = SymbolMapper()
    cg_ids_by_symbol: dict[str, str] = {}
    errors: list[str] = []

    for symbol in symbols:
        try:
            cg_ids_by_symbol[symbol] = mapper.to_provider(
                symbol,
                "coingecko",
                alias_type="cg_id",
            )
        except Exception as exc:
            errors.append(f"coingecko basis {symbol}: {exc}")

    if not cg_ids_by_symbol:
        return 0, 0, errors or ["coingecko basis: no mapped symbols"]

    adapter = CoinGeckoAdapter()
    try:
        tickers = await adapter.fetch_tickers(list(cg_ids_by_symbol.values()))
    finally:
        await adapter.client.aclose()

    spot_by_cg_id = {
        ticker.instrument_id: ticker.price
        for ticker in tickers
        if ticker.venue_id == "coingecko_aggregated" and ticker.price
    }
    basis_rows = []

    for symbol, cg_id in cg_ids_by_symbol.items():
        spot_price = spot_by_cg_id.get(cg_id)
        perp_price = writer.get_latest_ohlcv_close(symbol, "binance", "1m")
        if not spot_price or not perp_price:
            errors.append(f"coingecko basis {symbol}: missing spot or perp price")
            continue
        basis_pct = ((perp_price - spot_price) / spot_price) * 100
        basis_rows.append(
            {
                "symbol": symbol,
                "exchange": "binance",
                "spot_price": float(spot_price),
                "perp_price": float(perp_price),
                "basis_pct": basis_pct,
                "premium_pct": basis_pct,
                "timestamp": timestamp_ms,
            }
        )

    inserted = writer.insert_basis_premium(basis_rows)
    logger.info("coingecko basis fetched=%s inserted=%s errors=%s", len(basis_rows), inserted, len(errors))
    return len(basis_rows), inserted, errors


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
            "binance",
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
                "binance",
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
                "binance",
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
                "binance",
                "long_short_ratio",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_coinglass:
            fetched, inserted, errors = await _sync_coinglass_snapshots(writer, symbols, now_ms)
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "coinglass",
                "snapshots",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_coingecko_basis:
            fetched, inserted, errors = await _sync_coingecko_basis(writer, symbols, now_ms)
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "coingecko",
                "basis_premium",
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
    parser.add_argument("--include-coinglass", action="store_true", help="Fetch CoinGlass v4 funding/OI snapshots.")
    parser.add_argument("--include-coingecko-basis", action="store_true", help="Write CoinGecko spot vs Binance perp basis snapshots.")
    parser.add_argument("--use-mock", action="store_true", help="Use deterministic mock OHLCV instead of Binance.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
