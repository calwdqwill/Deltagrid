"""BackfillOrchestrator — chunked backfill with gap tracking.

Algorithm:
1. Split time range into chunks of N candles.
2. Fetch each chunk via adapter.
3. Write to storage via writer.
4. Track gaps and retry/fallback.
5. Log job status via ProviderSyncRun.
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from .base_adapter import BaseDataAdapter, FallbackChain
from .data_models import BackfillResult, OHLCVCandle
from .data_writer import DataWriter

logger = logging.getLogger(__name__)


@dataclass
class BackfillJob:
    symbol: str          # canonical symbol
    exchange: str
    data_type: str       # "ohlcv", "funding", "oi", ...
    interval: str
    start_ms: int
    end_ms: int
    chunk_size: int = 1500


class BackfillOrchestrator:
    """Orchestrates chunked backfill for historical market data."""

    def __init__(
        self,
        writer: DataWriter,
        fallback_chain: Optional[FallbackChain] = None,
    ):
        self.writer = writer
        self.fallback_chain = fallback_chain

    async def backfill_ohlcv(
        self,
        adapter: BaseDataAdapter,
        job: BackfillJob,
    ) -> BackfillResult:
        """Backfill OHLCV with chunked fetching."""
        run_id = self.writer.create_sync_run(
            provider_name=adapter.source_name,
            sync_type="ohlcv",
            symbol=job.symbol,
            exchange=job.exchange,
            interval=job.interval,
            start_ms=job.start_ms,
            end_ms=job.end_ms,
        )

        logger.info(
            f"[Backfill] Starting job {run_id}: {job.symbol} {job.interval} "
            f"from {job.start_ms} to {job.end_ms}"
        )

        total_fetched = 0
        total_inserted = 0
        gaps: list[tuple[int, int]] = []
        api_requests = 0

        interval_ms = self._interval_to_ms(job.interval)
        current_start = job.start_ms

        try:
            while current_start < job.end_ms:
                chunk_end = min(
                    current_start + (job.chunk_size * interval_ms),
                    job.end_ms,
                )

                candles: list[OHLCVCandle] = []
                try:
                    candles = await adapter.fetch_ohlcv(
                        symbol=job.symbol,
                        interval=job.interval,
                        start_ms=current_start,
                        end_ms=chunk_end,
                        limit=job.chunk_size,
                    )
                    api_requests += 1
                except Exception as e:
                    logger.warning(f"[Backfill] Primary adapter failed: {e}")
                    if self.fallback_chain:
                        try:
                            candles = await self.fallback_chain.fetch_ohlcv(
                                symbol=job.symbol,
                                interval=job.interval,
                                start_ms=current_start,
                                end_ms=chunk_end,
                                limit=job.chunk_size,
                            )
                            logger.info("[Backfill] Fallback adapter succeeded")
                        except Exception as fe:
                            logger.error(f"[Backfill] Fallback also failed: {fe}")

                if candles:
                    inserted = self.writer.upsert_ohlcv(candles)
                    total_inserted += inserted
                    total_fetched += len(candles)

                    # Advance: last candle timestamp + 1 interval
                    last_ts = candles[-1].timestamp_ms
                    current_start = last_ts + interval_ms

                    # Detect gap: if we got fewer candles than expected
                    expected = (chunk_end - current_start) // interval_ms
                    if len(candles) < expected * 0.9:
                        logger.warning(
                            f"[Backfill] Potential gap: got {len(candles)}, expected ~{expected}"
                        )
                else:
                    # No data for this chunk -> definite gap
                    gaps.append((current_start, chunk_end))
                    logger.warning(
                        f"[Backfill] Gap detected: {current_start} -> {chunk_end}"
                    )
                    current_start = chunk_end

                # Small yield to prevent event loop blocking
                await asyncio.sleep(0)

            status = "completed" if not gaps else "partial"
            self.writer.complete_sync_run(
                run_id=run_id,
                status=status,
                fetched=total_fetched,
                inserted=total_inserted,
                api_requests=api_requests,
            )
            logger.info(
                f"[Backfill] Job {run_id} {status}: fetched={total_fetched}, "
                f"inserted={total_inserted}, gaps={len(gaps)}"
            )

            return BackfillResult(
                total_fetched=total_fetched,
                total_inserted=total_inserted,
                gaps=gaps,
            )

        except Exception as e:
            logger.exception(f"[Backfill] Job {run_id} failed: {e}")
            self.writer.complete_sync_run(
                run_id=run_id,
                status="failed",
                fetched=total_fetched,
                inserted=total_inserted,
                api_requests=api_requests,
                error=str(e),
            )
            raise

    async def incremental_update(
        self,
        adapter: BaseDataAdapter,
        symbol: str,
        exchange: str,
        interval: str,
        lookback_days: int = 1,
    ) -> BackfillResult:
        """Incremental update: fetch only missing data since last candle."""
        last_ts = self.writer.get_last_timestamp(symbol, exchange, interval)
        now_ms = int(time.time() * 1000)

        if last_ts:
            start_ms = last_ts + self._interval_to_ms(interval)
        else:
            # No data -> backfill lookback period
            start_ms = now_ms - (lookback_days * 24 * 3600 * 1000)

        if start_ms >= now_ms:
            logger.info(f"[Incremental] {symbol} is up to date")
            return BackfillResult()

        job = BackfillJob(
            symbol=symbol,
            exchange=exchange,
            data_type="ohlcv",
            interval=interval,
            start_ms=start_ms,
            end_ms=now_ms,
        )
        return await self.backfill_ohlcv(adapter, job)

    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        mapping = {
            "1m": 60_000,
            "3m": 180_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "2h": 7_200_000,
            "4h": 14_400_000,
            "6h": 21_600_000,
            "8h": 28_800_000,
            "12h": 43_200_000,
            "1d": 86_400_000,
        }
        return mapping.get(interval, 60_000)
