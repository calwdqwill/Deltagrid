"""DataWriter — ORM-based persistence for normalized market data.

Uses SQLAlchemy 2.0 SQLite UPSERT (INSERT ... ON CONFLICT DO UPDATE).
"""

import logging
import time
from typing import Optional

from sqlalchemy import insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.domain.models import (
    BacktestConfig,
    BacktestEquity,
    BacktestResult,
    BacktestTrade,
    BasisPremium,
    DataQualityLog,
    ExchangeFee,
    FundingRate,
    Instrument,
    InstrumentAlias,
    Liquidation,
    LongShortRatio,
    OHLCV,
    OpenInterest,
    ProviderSyncRun,
)
from app.persistence.database import SessionLocal
from .data_models import (
    FundingRate as FundingRatePydantic,
    Liquidation as LiquidationPydantic,
    LongShortRatio as LongShortRatioPydantic,
    OHLCVCandle,
    OpenInterest as OpenInterestPydantic,
)

logger = logging.getLogger(__name__)


class DataWriter:
    """ORM writer with UPSERT support for time-series data."""

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _session(self) -> Session:
        return self._db or SessionLocal()

    # -- UPSERT helpers ------------------------------------------------

    def upsert_ohlcv(self, candles: list[OHLCVCandle]) -> int:
        if not candles:
            return 0
        session = self._session()
        close_session = self._db is None
        try:
            values = [
                {
                    "timestamp": c.timestamp_ms,
                    "symbol": c.symbol,
                    "exchange": c.exchange,
                    "interval": c.interval,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                    "quote_volume": c.quote_volume,
                    "trades_count": c.trades_count,
                }
                for c in candles
            ]
            stmt = sqlite_insert(OHLCV).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "symbol", "exchange", "interval"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                    "quote_volume": stmt.excluded.quote_volume,
                    "trades_count": stmt.excluded.trades_count,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def upsert_funding(self, rates: list[FundingRatePydantic]) -> int:
        if not rates:
            return 0
        session = self._session()
        close_session = self._db is None
        try:
            values = [
                {
                    "timestamp": r.timestamp_ms,
                    "symbol": r.symbol,
                    "exchange": r.exchange,
                    "funding_rate": r.funding_rate,
                    "next_funding_time": r.next_funding_time_ms,
                    "interval_hours": self._interval_to_hours(r.interval),
                }
                for r in rates
            ]
            stmt = sqlite_insert(FundingRate).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "symbol", "exchange"],
                set_={
                    "funding_rate": stmt.excluded.funding_rate,
                    "next_funding_time": stmt.excluded.next_funding_time,
                    "interval_hours": stmt.excluded.interval_hours,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def upsert_oi(self, ois: list[OpenInterestPydantic]) -> int:
        if not ois:
            return 0
        session = self._session()
        close_session = self._db is None
        try:
            values = [
                {
                    "timestamp": o.timestamp_ms,
                    "symbol": o.symbol,
                    "exchange": o.exchange,
                    "interval": o.interval,
                    "oi_usd": o.oi_usd,
                    "oi_coins": o.oi_coins,
                }
                for o in ois
            ]
            stmt = sqlite_insert(OpenInterest).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "symbol", "exchange", "interval"],
                set_={
                    "oi_usd": stmt.excluded.oi_usd,
                    "oi_coins": stmt.excluded.oi_coins,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def upsert_liquidations(self, liqs: list[LiquidationPydantic]) -> int:
        if not liqs:
            return 0
        session = self._session()
        close_session = self._db is None
        try:
            values = [
                {
                    "timestamp": l.timestamp_ms,
                    "symbol": l.symbol,
                    "exchange": l.exchange,
                    "side": l.side,
                    "quantity": l.quantity,
                    "price": l.price,
                    "value_usd": l.value_usd,
                }
                for l in liqs
            ]
            stmt = sqlite_insert(Liquidation).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "symbol", "exchange", "side"],
                set_={
                    "quantity": stmt.excluded.quantity,
                    "price": stmt.excluded.price,
                    "value_usd": stmt.excluded.value_usd,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def upsert_long_short(self, ratios: list[LongShortRatioPydantic]) -> int:
        if not ratios:
            return 0
        session = self._session()
        close_session = self._db is None
        try:
            values = [
                {
                    "timestamp": r.timestamp_ms,
                    "symbol": r.symbol,
                    "exchange": r.exchange,
                    "interval": r.interval,
                    "long_ratio": r.long_ratio,
                    "short_ratio": r.short_ratio,
                    "long_account_ratio": r.long_account_ratio,
                    "short_account_ratio": r.short_account_ratio,
                }
                for r in ratios
            ]
            stmt = sqlite_insert(LongShortRatio).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["timestamp", "symbol", "exchange", "interval"],
                set_={
                    "long_ratio": stmt.excluded.long_ratio,
                    "short_ratio": stmt.excluded.short_ratio,
                    "long_account_ratio": stmt.excluded.long_account_ratio,
                    "short_account_ratio": stmt.excluded.short_account_ratio,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    # -- Provider sync run tracking ------------------------------------

    def create_sync_run(
        self,
        provider_name: str,
        sync_type: str,
        symbol: Optional[str],
        exchange: Optional[str],
        interval: Optional[str],
        start_ms: int,
        end_ms: int,
    ) -> str:
        import uuid
        from datetime import datetime

        run_id = str(uuid.uuid4())
        session = self._session()
        close_session = self._db is None
        try:
            run = ProviderSyncRun(
                id=run_id,
                provider_name=provider_name,
                sync_type=sync_type,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start_time=start_ms,
                end_time=end_ms,
                status="running",
                started_at=datetime.utcnow(),
            )
            session.add(run)
            session.commit()
            return run_id
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def complete_sync_run(
        self,
        run_id: str,
        status: str,
        fetched: int,
        inserted: int,
        updated: int = 0,
        api_requests: int = 0,
        error: Optional[str] = None,
    ) -> None:
        from datetime import datetime

        session = self._session()
        close_session = self._db is None
        try:
            run = session.query(ProviderSyncRun).filter(ProviderSyncRun.id == run_id).first()
            if run:
                run.status = status
                run.records_fetched = fetched
                run.records_inserted = inserted
                run.records_updated = updated
                run.api_requests_count = api_requests
                run.error_message = error
                run.completed_at = datetime.utcnow()
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def log_data_quality(
        self,
        table_name: str,
        check_type: str,
        severity: str = "info",
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        interval: Optional[str] = None,
        expected_count: Optional[int] = None,
        actual_count: Optional[int] = None,
        gap_start: Optional[int] = None,
        gap_end: Optional[int] = None,
        details_json: Optional[str] = None,
    ) -> None:
        session = self._session()
        close_session = self._db is None
        try:
            log = DataQualityLog(
                table_name=table_name,
                check_type=check_type,
                severity=severity,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                expected_count=expected_count,
                actual_count=actual_count,
                gap_start=gap_start,
                gap_end=gap_end,
                details_json=details_json,
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    # -- Query helpers -------------------------------------------------

    def get_last_timestamp(
        self,
        symbol: str,
        exchange: str,
        interval: str,
        table: str = "ohlcv",
    ) -> Optional[int]:
        session = self._session()
        close_session = self._db is None
        try:
            model = {
                "ohlcv": OHLCV,
                "funding_rates": FundingRate,
                "open_interest": OpenInterest,
                "liquidations": Liquidation,
                "long_short_ratio": LongShortRatio,
            }.get(table)
            if not model:
                return None
            result = (
                session.query(model.timestamp)
                .filter_by(symbol=symbol, exchange=exchange)
                .order_by(model.timestamp.desc())
                .first()
            )
            return result[0] if result else None
        finally:
            if close_session:
                session.close()

    def count_rows(self, table: str = "ohlcv") -> int:
        session = self._session()
        close_session = self._db is None
        try:
            model = {
                "ohlcv": OHLCV,
                "funding_rates": FundingRate,
                "open_interest": OpenInterest,
                "liquidations": Liquidation,
                "long_short_ratio": LongShortRatio,
                "provider_sync_runs": ProviderSyncRun,
            }.get(table)
            if not model:
                return 0
            return session.query(model).count()
        finally:
            if close_session:
                session.close()

    # -- Utils ---------------------------------------------------------

    @staticmethod
    def _interval_to_hours(interval: str) -> int:
        mapping = {
            "1h": 1,
            "8h": 8,
        }
        return mapping.get(interval, 8)
