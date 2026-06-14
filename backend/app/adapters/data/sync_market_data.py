"""Production-safe market data sync command.

Fetches recent public market data from the configured primary perp provider and
writes it to the configured database. This is intentionally a small CLI command,
not a background scheduler.
"""

import argparse
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import text

from app.adapters.coingecko_adapter import CoinGeckoAdapter
from app.adapters.data.backfill_orchestrator import BackfillJob, BackfillOrchestrator
from app.adapters.data.base_adapter import BaseDataAdapter
from app.adapters.data.binance_adapter import BinanceAdapter
from app.adapters.data.data_models import FundingRate, Liquidation, OpenInterest
from app.adapters.data.data_writer import DataWriter
from app.adapters.data.okx_adapter import OKX_MAX_CANDLES, OkxAdapter
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
    adapter: BaseDataAdapter,
    writer: DataWriter,
    exchange: str,
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
                exchange=exchange,
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


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in ("usd", "value", "turnover", "amount", "total"):
            parsed = _to_float(value.get(key))
            if parsed is not None:
                return parsed
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _coinglass_timestamp_ms(row: dict[str, Any]) -> int | None:
    for key in ("timestamp", "time", "ts", "t", "date"):
        raw_value = row.get(key)
        if raw_value is None:
            continue
        if isinstance(raw_value, (int, float)):
            timestamp = int(raw_value)
            return timestamp * 1000 if timestamp < 10_000_000_000 else timestamp
        if isinstance(raw_value, str):
            value = raw_value.strip()
            if not value:
                continue
            numeric = _to_float(value)
            if numeric is not None:
                timestamp = int(numeric)
                return timestamp * 1000 if timestamp < 10_000_000_000 else timestamp
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return int(parsed.timestamp() * 1000)
            except ValueError:
                continue
    return None


def _coinglass_liquidation_payload(row: dict[str, Any], exchange: str) -> dict[str, Any]:
    exchange_keys = [
        exchange,
        exchange.lower(),
        exchange.upper(),
        exchange.capitalize(),
        exchange.title(),
        "all",
        "All",
        "total",
        "Total",
    ]
    for key in exchange_keys:
        value = row.get(key)
        if isinstance(value, dict):
            return value
    return row


def _coinglass_liquidation_amount(source: dict[str, Any], side: str) -> float | None:
    if side == "long":
        keys = (
            "aggregated_long_liquidation_usd",
            "longLiquidationUsd",
            "long_liquidation_usd",
            "longLiquidation",
            "long_liquidation",
            "longTurnover",
            "long_turnover",
            "longVolUsd",
            "long_volume_usd",
            "longUsd",
            "long",
        )
    else:
        keys = (
            "aggregated_short_liquidation_usd",
            "shortLiquidationUsd",
            "short_liquidation_usd",
            "shortLiquidation",
            "short_liquidation",
            "shortTurnover",
            "short_turnover",
            "shortVolUsd",
            "short_volume_usd",
            "shortUsd",
            "short",
        )

    for key in keys:
        parsed = _to_float(source.get(key))
        if parsed is not None:
            return parsed
    return None


def _normalize_coinglass_liquidations(
    symbol: str,
    rows: Iterable[dict[str, Any]],
    exchange: str = "binance",
) -> list[Liquidation]:
    normalized: list[Liquidation] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        timestamp_ms = _coinglass_timestamp_ms(row)
        if timestamp_ms is None:
            continue

        payload = _coinglass_liquidation_payload(row, exchange)
        for side in ("long", "short"):
            value_usd = _coinglass_liquidation_amount(payload, side)
            if value_usd is None or value_usd <= 0:
                continue
            normalized.append(
                Liquidation(
                    timestamp_ms=timestamp_ms,
                    symbol=symbol.upper(),
                    exchange=exchange,
                    side=side,
                    quantity=0.0,
                    price=0.0,
                    value_usd=float(value_usd),
                )
            )

    return sorted(normalized, key=lambda item: (item.timestamp_ms, item.side))


async def _sync_coinglass_snapshots(
    writer: DataWriter,
    symbols: Iterable[str],
    timestamp_ms: int,
    exchange_list: str,
) -> tuple[int, int, list[str]]:
    symbol_set = {symbol.upper() for symbol in symbols}
    client = CoinGlassClient()
    try:
        rows = await client.get_funding_rates(exchange_list=exchange_list)
    finally:
        await client.close()

    if not rows:
        return 0, 0, [f"coinglass snapshots {exchange_list}: no data returned"]

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
    logger.info("coinglass snapshots %s fetched=%s inserted=%s", exchange_list, fetched, inserted)
    return fetched, inserted, []


async def _sync_coingecko_basis(
    writer: DataWriter,
    symbols: Iterable[str],
    timestamp_ms: int,
    perp_exchange: str,
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
        perp_price = writer.get_latest_ohlcv_close(symbol, perp_exchange, "1m")
        if not spot_price or not perp_price:
            errors.append(f"coingecko basis {symbol}: missing spot or perp price")
            continue
        basis_pct = ((perp_price - spot_price) / spot_price) * 100
        basis_rows.append(
            {
                "symbol": symbol,
                "exchange": perp_exchange,
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
    adapter: BaseDataAdapter,
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
    adapter: BaseDataAdapter,
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
    adapter: BaseDataAdapter,
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


async def _sync_liquidations(
    writer: DataWriter,
    symbols: Iterable[str],
    start_ms: int,
    end_ms: int,
    interval: str,
    exchange: str,
    exchange_list: str,
) -> tuple[int, int, list[str]]:
    fetched = 0
    inserted = 0
    errors: list[str] = []
    mapper = SymbolMapper()
    client = CoinGlassClient()

    try:
        for symbol in symbols:
            try:
                provider_symbol = mapper.to_provider(symbol, "coinglass")
            except Exception:
                provider_symbol = symbol.upper()

            try:
                rows = await client.get_liquidation_aggregated_history(
                    symbol=provider_symbol,
                    exchange_list=exchange_list,
                    interval=interval,
                    start_time=start_ms,
                    end_time=end_ms,
                )
                if not rows:
                    message = f"liquidations {symbol}: no CoinGlass data returned"
                    errors.append(message)
                    logger.warning(message)
                    continue

                liquidations = _normalize_coinglass_liquidations(symbol, rows, exchange=exchange)
                fetched += len(rows)
                inserted += writer.upsert_liquidations(liquidations)
                logger.info(
                    "liquidations %s %s fetched=%s normalized=%s",
                    symbol,
                    interval,
                    len(rows),
                    len(liquidations),
                )
            except Exception as exc:
                message = f"liquidations {symbol}: {exc}"
                errors.append(message)
                logger.exception(message)
    finally:
        await client.close()

    return fetched, inserted, errors


def _create_primary_adapter(provider: str, rate_limiter: GlobalRateLimiter, use_mock: bool) -> BaseDataAdapter:
    normalized = provider.strip().lower()
    if normalized == "binance":
        return BinanceAdapter(rate_limiter=rate_limiter, use_mock=use_mock)
    if normalized == "okx":
        if use_mock:
            logger.warning("--use-mock is only supported by BinanceAdapter; using live OKX public API")
        return OkxAdapter(rate_limiter=rate_limiter)
    raise ValueError(f"Unsupported primary perp provider: {provider}")


def _coinglass_exchange_list(provider: str) -> str:
    mapping = {
        "binance": "Binance",
        "okx": "OKX",
    }
    return mapping.get(provider.lower(), provider.upper())


async def run(args: argparse.Namespace) -> int:
    symbols = _csv(args.symbols)
    intervals = _csv_lower(args.ohlcv_intervals)
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - int(args.lookback_hours * 60 * 60 * 1000)
    primary_provider = args.primary_perp_provider.strip().lower()
    chunk_size = args.chunk_size
    if primary_provider == "okx" and chunk_size > OKX_MAX_CANDLES:
        logger.info("Reducing OKX OHLCV chunk size from %s to %s", chunk_size, OKX_MAX_CANDLES)
        chunk_size = OKX_MAX_CANDLES

    writer = DataWriter()
    adapter = _create_primary_adapter(
        primary_provider,
        rate_limiter=GlobalRateLimiter(),
        use_mock=args.use_mock,
    )

    try:
        total_fetched = 0
        total_inserted = 0
        all_errors: list[str] = []

        fetched, inserted, errors = await _sync_ohlcv(
            adapter,
            writer,
            primary_provider,
            symbols,
            intervals,
            start_ms,
            now_ms,
            chunk_size,
        )
        total_fetched += fetched
        total_inserted += inserted
        all_errors.extend(errors)
        _record_sync_run(
            writer,
            primary_provider,
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
                primary_provider,
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
                primary_provider,
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
                primary_provider,
                "long_short_ratio",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_liquidations:
            fetched, inserted, errors = await _sync_liquidations(
                writer,
                symbols,
                start_ms,
                now_ms,
                args.liquidation_interval,
                primary_provider,
                _coinglass_exchange_list(primary_provider),
            )
            total_fetched += fetched
            total_inserted += inserted
            all_errors.extend(errors)
            _record_sync_run(
                writer,
                "coinglass",
                "liquidations",
                "completed" if not errors else "partial",
                start_ms,
                now_ms,
                fetched,
                inserted,
                "; ".join(errors) if errors else None,
            )

        if args.include_coinglass:
            fetched, inserted, errors = await _sync_coinglass_snapshots(
                writer,
                symbols,
                now_ms,
                _coinglass_exchange_list(primary_provider),
            )
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
            fetched, inserted, errors = await _sync_coingecko_basis(
                writer,
                symbols,
                now_ms,
                primary_provider,
            )
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
    parser = argparse.ArgumentParser(description="Sync recent market data into DeltaGrid DB.")
    parser.add_argument("--symbols", default="BTC,ETH,SOL", help="Comma-separated canonical symbols.")
    parser.add_argument("--ohlcv-intervals", default="1m,5m,1h", help="Comma-separated OHLCV intervals.")
    parser.add_argument("--lookback-hours", type=float, default=24.0, help="Historical window to fetch.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="OHLCV candles per request.")
    parser.add_argument("--derived-interval", default="1h", help="Interval for OI and long/short endpoints.")
    parser.add_argument(
        "--primary-perp-provider",
        choices=("okx", "binance"),
        default="okx",
        help="Primary CEX perp provider for OHLCV, funding, OI, long/short and basis.",
    )
    parser.add_argument("--include-funding", action="store_true", help="Fetch funding-rate history.")
    parser.add_argument("--include-open-interest", action="store_true", help="Fetch open-interest history.")
    parser.add_argument("--include-long-short", action="store_true", help="Fetch long/short account ratio.")
    parser.add_argument("--include-liquidations", action="store_true", help="Fetch CoinGlass aggregated liquidation history.")
    parser.add_argument("--liquidation-interval", default="1h", help="Interval for CoinGlass liquidation history.")
    parser.add_argument("--include-coinglass", action="store_true", help="Fetch CoinGlass v4 funding/OI snapshots.")
    parser.add_argument("--include-coingecko-basis", action="store_true", help="Write CoinGecko spot vs primary perp basis snapshots.")
    parser.add_argument("--use-mock", action="store_true", help="Use deterministic mock OHLCV for Binance diagnostic runs.")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    raise SystemExit(asyncio.run(run(parse_args())))


if __name__ == "__main__":
    main()
