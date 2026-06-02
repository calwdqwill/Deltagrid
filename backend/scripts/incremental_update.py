#!/usr/bin/env python3
"""Incremental Update Service для DeltaGrid.

Автоматическое обновление данных каждые N минут.
Забирает только новые данные с момента последнего обновления.

Usage:
    cd backend
    python scripts/incremental_update.py
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone

# Ensure backend/ is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.adapters.data import BinanceAdapter, CoinGlassDataAdapter, GlobalRateLimiter, RetryPolicy
from app.adapters.data.data_writer import DataWriter
from app.adapters.data.symbol_mapper import SymbolMapper
from app.persistence.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SYMBOLS = ["BTC", "ETH", "SOL", "HYPE"]
EXCHANGE = "binance"
INTERVAL = "1m"
INTERVAL_MS = 60_000


async def incremental_update_ohlcv():
    """Обновляет OHLCV 1m данные с Binance."""
    init_db()
    mapper = SymbolMapper()
    mapper.seed_defaults()

    rate_limiter = GlobalRateLimiter()
    adapter = BinanceAdapter(
        rate_limiter=rate_limiter,
        retry_policy=RetryPolicy(max_retries=3, base_delay=1.0),
        symbol_mapper=mapper,
    )
    writer = DataWriter()

    now_ms = int(time.time() * 1000)
    logger.info(f"[Incremental OHLCV] Starting at {datetime.utcnow().isoformat()}")

    for symbol in SYMBOLS:
        last_ts = writer.get_last_timestamp(symbol, EXCHANGE, INTERVAL, table="ohlcv")
        if last_ts is None:
            logger.info(f"  {symbol}: no existing data, skipping (run backfill first)")
            continue

        start_ms = last_ts + INTERVAL_MS
        if start_ms >= now_ms - 300_000:  # данные свежие (< 5 мин)
            logger.info(f"  {symbol}: up to date (last: {last_ts})")
            continue

        run_id = writer.create_sync_run(
            provider_name="binance",
            sync_type="ohlcv",
            symbol=symbol,
            exchange=EXCHANGE,
            interval=INTERVAL,
            start_ms=start_ms,
            end_ms=now_ms,
        )

        try:
            candles = await adapter.fetch_ohlcv(
                symbol=symbol,
                interval=INTERVAL,
                start_ms=start_ms,
                end_ms=now_ms,
                limit=1500,
            )
            if candles:
                inserted = writer.upsert_ohlcv(candles)
                writer.complete_sync_run(
                    run_id=run_id,
                    status="completed",
                    fetched=len(candles),
                    inserted=inserted,
                )
                logger.info(f"  {symbol}: +{inserted} candles ({len(candles)} fetched)")
            else:
                writer.complete_sync_run(
                    run_id=run_id,
                    status="completed",
                    fetched=0,
                    inserted=0,
                )
                logger.info(f"  {symbol}: no new data")
        except Exception as e:
            writer.complete_sync_run(
                run_id=run_id,
                status="failed",
                fetched=0,
                inserted=0,
                error=str(e),
            )
            logger.warning(f"  {symbol}: fetch failed: {e}")

    await adapter.close()


async def incremental_update_coinglass():
    """Обновляет данные CoinGlass (funding, OI, liq, L/S)."""
    init_db()
    mapper = SymbolMapper()
    mapper.seed_defaults()

    rate_limiter = GlobalRateLimiter()
    adapter = CoinGlassDataAdapter(
        rate_limiter=rate_limiter,
        retry_policy=RetryPolicy(max_retries=3, base_delay=1.0),
        symbol_mapper=mapper,
    )
    writer = DataWriter()

    now_ms = int(time.time() * 1000)
    logger.info(f"[Incremental CoinGlass] Starting at {datetime.utcnow().isoformat()}")

    for symbol in SYMBOLS:
        # --- Funding rates ---
        last_funding = writer.get_last_timestamp(symbol, EXCHANGE, "1h", table="funding_rates")
        funding_start = (last_funding + 1) if last_funding else now_ms - (24 * 3600 * 1000)

        if funding_start < now_ms - 3_600_000:  # >= 1 час отставания
            run_id = writer.create_sync_run(
                provider_name="coinglass",
                sync_type="funding",
                symbol=symbol,
                exchange=EXCHANGE,
                interval="1h",
                start_ms=funding_start,
                end_ms=now_ms,
            )
            try:
                rates = await adapter.fetch_funding(symbol, funding_start, now_ms)
                if rates:
                    inserted = writer.upsert_funding(rates)
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=len(rates),
                        inserted=inserted,
                    )
                    logger.info(f"  {symbol} funding: +{inserted}")
                else:
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=0,
                        inserted=0,
                    )
            except Exception as e:
                writer.complete_sync_run(
                    run_id=run_id,
                    status="failed",
                    fetched=0,
                    inserted=0,
                    error=str(e),
                )
                logger.warning(f"  {symbol} funding: failed: {e}")

        # --- Open Interest ---
        last_oi = writer.get_last_timestamp(symbol, EXCHANGE, "1h", table="open_interest")
        oi_start = (last_oi + 1) if last_oi else now_ms - (24 * 3600 * 1000)

        if oi_start < now_ms - 3_600_000:
            run_id = writer.create_sync_run(
                provider_name="coinglass",
                sync_type="oi",
                symbol=symbol,
                exchange=EXCHANGE,
                interval="1h",
                start_ms=oi_start,
                end_ms=now_ms,
            )
            try:
                ois = await adapter.fetch_oi(symbol, interval="1h")
                if ois:
                    inserted = writer.upsert_oi(ois)
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=len(ois),
                        inserted=inserted,
                    )
                    logger.info(f"  {symbol} oi: +{inserted}")
                else:
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=0,
                        inserted=0,
                    )
            except Exception as e:
                writer.complete_sync_run(
                    run_id=run_id,
                    status="failed",
                    fetched=0,
                    inserted=0,
                    error=str(e),
                )
                logger.warning(f"  {symbol} oi: failed: {e}")

        # --- Liquidations ---
        last_liq = writer.get_last_timestamp(symbol, EXCHANGE, "1h", table="liquidations")
        liq_start = (last_liq + 1) if last_liq else now_ms - (24 * 3600 * 1000)

        if liq_start < now_ms - 3_600_000:
            run_id = writer.create_sync_run(
                provider_name="coinglass",
                sync_type="liquidations",
                symbol=symbol,
                exchange=EXCHANGE,
                interval="1h",
                start_ms=liq_start,
                end_ms=now_ms,
            )
            try:
                liqs = await adapter.fetch_liquidations(symbol, liq_start, now_ms)
                if liqs:
                    inserted = writer.upsert_liquidations(liqs)
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=len(liqs),
                        inserted=inserted,
                    )
                    logger.info(f"  {symbol} liquidations: +{inserted}")
                else:
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=0,
                        inserted=0,
                    )
            except Exception as e:
                writer.complete_sync_run(
                    run_id=run_id,
                    status="failed",
                    fetched=0,
                    inserted=0,
                    error=str(e),
                )
                logger.warning(f"  {symbol} liquidations: failed: {e}")

        # --- Long/Short ratio ---
        last_ls = writer.get_last_timestamp(symbol, EXCHANGE, "1h", table="long_short_ratio")
        ls_start = (last_ls + 1) if last_ls else now_ms - (24 * 3600 * 1000)

        if ls_start < now_ms - 3_600_000:
            run_id = writer.create_sync_run(
                provider_name="coinglass",
                sync_type="ls_ratio",
                symbol=symbol,
                exchange=EXCHANGE,
                interval="1h",
                start_ms=ls_start,
                end_ms=now_ms,
            )
            try:
                ratios = await adapter.fetch_long_short_ratio(symbol, "1h", ls_start, now_ms)
                if ratios:
                    inserted = writer.upsert_long_short(ratios)
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=len(ratios),
                        inserted=inserted,
                    )
                    logger.info(f"  {symbol} ls_ratio: +{inserted}")
                else:
                    writer.complete_sync_run(
                        run_id=run_id,
                        status="completed",
                        fetched=0,
                        inserted=0,
                    )
            except Exception as e:
                writer.complete_sync_run(
                    run_id=run_id,
                    status="failed",
                    fetched=0,
                    inserted=0,
                    error=str(e),
                )
                logger.warning(f"  {symbol} ls_ratio: failed: {e}")

    await adapter.close()


async def main():
    print(f"Incremental Update started at {datetime.utcnow().isoformat()}")
    start = time.monotonic()

    await incremental_update_ohlcv()
    await incremental_update_coinglass()

    elapsed = time.monotonic() - start
    print(f"Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
