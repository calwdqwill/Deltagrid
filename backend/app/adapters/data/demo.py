"""Demo script for the DeltaGrid data layer (real DB integration).

Runs a mock backfill of 1m OHLCV for BTC and ETH into the real deltagrid.db,
demonstrating SymbolMapper, BinanceAdapter, DataWriter, and BackfillOrchestrator.
"""

import asyncio
import logging
import time

from app.adapters.data.backfill_orchestrator import BackfillJob, BackfillOrchestrator
from app.adapters.data.base_adapter import DataAdapterRegistry, FallbackChain
from app.adapters.data.binance_adapter import BinanceAdapter
from app.adapters.data.rate_limiter import GlobalRateLimiter
from app.adapters.data.data_writer import DataWriter
from app.adapters.data.symbol_mapper import SymbolMapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("demo")


async def main():
    logger.info("=" * 60)
    logger.info("DeltaGrid Data Layer — Real DB Demo")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # 1. Symbol Mapping (reads from real deltagrid.db)
    # ------------------------------------------------------------------
    logger.info("\n[1] Symbol Mapping from deltagrid.db")
    mapper = SymbolMapper()

    btc_binance = mapper.to_provider("BTC", "binance")
    eth_binance = mapper.to_provider("ETH", "binance")
    btc_okx = mapper.to_provider("BTC", "okx")
    logger.info(f"  BTC -> binance: {btc_binance}")
    logger.info(f"  ETH -> binance: {eth_binance}")
    logger.info(f"  BTC -> okx:     {btc_okx}")

    canonical = mapper.from_provider("BTCUSDT", "binance")
    logger.info(f"  BTCUSDT (binance) -> canonical: {canonical}")

    aliases = mapper.list_aliases("BTC")
    logger.info(f"  BTC aliases count: {len(aliases)}")

    # ------------------------------------------------------------------
    # 2. Rate Limiter & Adapter Setup (MOCK mode — no real API calls)
    # ------------------------------------------------------------------
    logger.info("\n[2] Adapter Setup (MOCK mode)")
    limiter = GlobalRateLimiter()
    adapter = BinanceAdapter(rate_limiter=limiter, use_mock=True)

    registry = DataAdapterRegistry()
    registry.register("binance", adapter)

    health = await registry.health_check_all()
    for name, status in health.items():
        logger.info(f"  {name}: healthy={status.is_healthy}, cb={status.circuit_breaker_state}")

    # ------------------------------------------------------------------
    # 3. DataWriter (writes to real deltagrid.db)
    # ------------------------------------------------------------------
    logger.info("\n[3] DataWriter connected to deltagrid.db")
    writer = DataWriter()
    logger.info("  Tables initialized (IF NOT EXISTS)")

    # ------------------------------------------------------------------
    # 4. Backfill: 1 hour of 1m OHLCV for BTC
    # ------------------------------------------------------------------
    logger.info("\n[4] Backfill: 1 hour of 1m BTC")
    now_ms = int(time.time() * 1000)
    one_hour_ago = now_ms - (60 * 60 * 1000)

    orchestrator = BackfillOrchestrator(writer=writer)
    job = BackfillJob(
        symbol="BTC",
        exchange="binance",
        data_type="ohlcv",
        interval="1m",
        start_ms=one_hour_ago,
        end_ms=now_ms,
        chunk_size=100,
    )

    t0 = time.monotonic()
    result = await orchestrator.backfill_ohlcv(adapter, job)
    elapsed = time.monotonic() - t0

    logger.info(f"  Fetched: {result.total_fetched}")
    logger.info(f"  Inserted: {result.total_inserted}")
    logger.info(f"  Gaps: {len(result.gaps)}")
    logger.info(f"  Elapsed: {elapsed:.3f}s")
    logger.info(f"  DB rows (ohlcv): {writer.count_rows('ohlcv')}")

    # ------------------------------------------------------------------
    # 5. Backfill: 1 hour of 1m ETH
    # ------------------------------------------------------------------
    logger.info("\n[5] Backfill: 1 hour of 1m ETH")
    job2 = BackfillJob(
        symbol="ETH",
        exchange="binance",
        data_type="ohlcv",
        interval="1m",
        start_ms=one_hour_ago,
        end_ms=now_ms,
        chunk_size=100,
    )

    result2 = await orchestrator.backfill_ohlcv(adapter, job2)
    logger.info(f"  Fetched: {result2.total_fetched}")
    logger.info(f"  Inserted: {result2.total_inserted}")
    logger.info(f"  DB rows (ohlcv): {writer.count_rows('ohlcv')}")

    # ------------------------------------------------------------------
    # 6. Incremental Update (should be minimal — data is fresh)
    # ------------------------------------------------------------------
    logger.info("\n[6] Incremental Update BTC")
    inc_result = await orchestrator.incremental_update(
        adapter, symbol="BTC", exchange="binance", interval="1m"
    )
    logger.info(f"  Fetched: {inc_result.total_fetched} (expected 0-1 — data is fresh)")

    # ------------------------------------------------------------------
    # 7. Fallback Chain Demo
    # ------------------------------------------------------------------
    logger.info("\n[7] Fallback Chain Demo")
    fallback = FallbackChain([adapter])
    fb_candles = await fallback.fetch_ohlcv(
        symbol="BTC", interval="1m",
        start_ms=one_hour_ago, end_ms=one_hour_ago + 60_000 * 10,
    )
    logger.info(f"  Fallback returned {len(fb_candles)} candles")

    # ------------------------------------------------------------------
    # 8. Summary
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("Demo Complete")
    logger.info("=" * 60)
    logger.info(f"Total DB rows (ohlcv):          {writer.count_rows('ohlcv')}")
    logger.info(f"Total DB rows (jobs):           {writer.count_rows('backfill_jobs')}")
    logger.info(f"Total DB rows (funding_rates):  {writer.count_rows('funding_rates')}")
    logger.info(f"Total DB rows (open_interest):  {writer.count_rows('open_interest')}")

    await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
