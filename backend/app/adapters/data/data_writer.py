"""DataWriter — persistence layer for normalized market data.

Implements UPSERT via INSERT ... ON CONFLICT DO UPDATE.
Works with the project's configured database via SQLAlchemy.
"""

import logging
import uuid
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.domain.models import Base
from app.persistence.database_url import is_sqlite_database_url, to_sync_database_url

from .data_models import (
    FundingRate,
    Liquidation,
    LongShortRatio,
    OHLCVCandle,
    OpenInterest,
)

logger = logging.getLogger(__name__)


class DataWriter:
    """PostgreSQL/SQLite writer with UPSERT support for time-series data.

    Uses the project's configured database via app.config.
    """

    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            db_url = get_settings().database_url
        self.db_url = to_sync_database_url(db_url)
        self.engine = create_engine(self.db_url, echo=False, **self._engine_kwargs())
        self.Session = sessionmaker(bind=self.engine)
        self._init_tables()

    def _engine_kwargs(self) -> dict:
        if is_sqlite_database_url(self.db_url):
            return {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        return {"pool_pre_ping": True}

    def _init_tables(self) -> None:
        """Create SQLite fallback tables; PostgreSQL is managed by Alembic."""
        if is_sqlite_database_url(self.db_url):
            Base.metadata.create_all(self.engine, checkfirst=True)

    # -- UPSERT methods ----------------------------------------------

    def upsert_ohlcv(self, candles: list[OHLCVCandle]) -> int:
        if not candles:
            return 0

        stmt = text("""
            INSERT INTO ohlcv (timestamp, symbol, exchange, interval, open, high, low, close, volume, quote_volume, trades_count)
            VALUES (:ts, :sym, :ex, :iv, :o, :h, :l, :c, :v, :qv, :tc)
            ON CONFLICT(timestamp, symbol, exchange, interval) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume,
                quote_volume=excluded.quote_volume,
                trades_count=excluded.trades_count
        """)

        with self.engine.connect() as conn:
            params = [
                {
                    "ts": c.timestamp_ms,
                    "sym": c.symbol,
                    "ex": c.exchange,
                    "iv": c.interval,
                    "o": c.open,
                    "h": c.high,
                    "l": c.low,
                    "c": c.close,
                    "v": c.volume,
                    "qv": c.quote_volume,
                    "tc": c.trades_count,
                }
                for c in candles
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    def upsert_funding(self, rates: list[FundingRate]) -> int:
        if not rates:
            return 0
        stmt = text("""
            INSERT INTO funding_rates (timestamp, symbol, exchange, funding_rate, next_funding_time, interval)
            VALUES (:ts, :sym, :ex, :fr, :nft, :iv)
            ON CONFLICT(timestamp, symbol, exchange) DO UPDATE SET
                funding_rate=excluded.funding_rate,
                next_funding_time=excluded.next_funding_time,
                interval=excluded.interval
        """)
        with self.engine.connect() as conn:
            params = [
                {
                    "ts": r.timestamp_ms,
                    "sym": r.symbol,
                    "ex": r.exchange,
                    "fr": r.funding_rate,
                    "nft": r.next_funding_time_ms,
                    "iv": r.interval,
                }
                for r in rates
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    def upsert_oi(self, ois: list[OpenInterest]) -> int:
        if not ois:
            return 0
        stmt = text("""
            INSERT INTO open_interest (timestamp, symbol, exchange, interval, oi_usd, oi_coins)
            VALUES (:ts, :sym, :ex, :iv, :oi_usd, :oi_coins)
            ON CONFLICT(timestamp, symbol, exchange, interval) DO UPDATE SET
                oi_usd=excluded.oi_usd,
                oi_coins=excluded.oi_coins
        """)
        with self.engine.connect() as conn:
            params = [
                {
                    "ts": o.timestamp_ms,
                    "sym": o.symbol,
                    "ex": o.exchange,
                    "iv": o.interval,
                    "oi_usd": o.oi_usd,
                    "oi_coins": o.oi_coins,
                }
                for o in ois
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    def upsert_liquidations(self, liqs: list[Liquidation]) -> int:
        if not liqs:
            return 0
        stmt = text("""
            INSERT INTO liquidations (timestamp, symbol, exchange, side, quantity, price, value_usd)
            VALUES (:ts, :sym, :ex, :side, :qty, :price, :val)
            ON CONFLICT(timestamp, symbol, exchange, side) DO UPDATE SET
                quantity=excluded.quantity,
                price=excluded.price,
                value_usd=excluded.value_usd
        """)
        with self.engine.connect() as conn:
            params = [
                {
                    "ts": l.timestamp_ms,
                    "sym": l.symbol,
                    "ex": l.exchange,
                    "side": l.side,
                    "qty": l.quantity,
                    "price": l.price,
                    "val": l.value_usd,
                }
                for l in liqs
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    def upsert_long_short(self, ratios: list[LongShortRatio]) -> int:
        if not ratios:
            return 0
        stmt = text("""
            INSERT INTO long_short_ratio (timestamp, symbol, exchange, interval, long_ratio, short_ratio, long_account_ratio, short_account_ratio)
            VALUES (:ts, :sym, :ex, :iv, :lr, :sr, :lar, :sar)
            ON CONFLICT(timestamp, symbol, exchange, interval) DO UPDATE SET
                long_ratio=excluded.long_ratio,
                short_ratio=excluded.short_ratio,
                long_account_ratio=excluded.long_account_ratio,
                short_account_ratio=excluded.short_account_ratio
        """)
        with self.engine.connect() as conn:
            params = [
                {
                    "ts": r.timestamp_ms,
                    "sym": r.symbol,
                    "ex": r.exchange,
                    "iv": r.interval,
                    "lr": r.long_ratio,
                    "sr": r.short_ratio,
                    "lar": r.long_account_ratio,
                    "sar": r.short_account_ratio,
                }
                for r in ratios
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    def insert_basis_premium(self, rows: list[dict]) -> int:
        if not rows:
            return 0
        stmt = text("""
            INSERT INTO basis_premium (
                id, symbol, exchange, spot_price, perp_price, basis_pct, premium_pct, timestamp
            )
            VALUES (
                :id, :symbol, :exchange, :spot_price, :perp_price, :basis_pct, :premium_pct, :timestamp
            )
        """)
        with self.engine.connect() as conn:
            params = [
                {
                    "id": str(uuid.uuid4()),
                    "symbol": row["symbol"],
                    "exchange": row["exchange"],
                    "spot_price": row.get("spot_price"),
                    "perp_price": row.get("perp_price"),
                    "basis_pct": row.get("basis_pct"),
                    "premium_pct": row.get("premium_pct"),
                    "timestamp": row["timestamp"],
                }
                for row in rows
            ]
            result = conn.execute(stmt, params)
            conn.commit()
            return result.rowcount

    # -- Job tracking ------------------------------------------------

    def create_job(self, job_id: str, symbol: str, exchange: str, data_type: str,
                   interval: str, start_ms: int, end_ms: int) -> None:
        stmt = text("""
            INSERT INTO backfill_jobs (id, symbol, exchange, data_type, interval, start_time, end_time, status, started_at)
            VALUES (:id, :sym, :ex, :dt, :iv, :st, :et, 'running', :now)
        """)
        with self.engine.connect() as conn:
            import time
            conn.execute(stmt, {
                "id": job_id, "sym": symbol, "ex": exchange, "dt": data_type,
                "iv": interval, "st": start_ms, "et": end_ms, "now": int(time.time()),
            })
            conn.commit()

    def complete_job(self, job_id: str, status: str, fetched: int, inserted: int,
                     error: Optional[str] = None) -> None:
        stmt = text("""
            UPDATE backfill_jobs
            SET status=:status, records_fetched=:fetched, records_inserted=:inserted,
                error_message=:err, completed_at=:now
            WHERE id=:id
        """)
        with self.engine.connect() as conn:
            import time
            conn.execute(stmt, {
                "id": job_id, "status": status, "fetched": fetched,
                "inserted": inserted, "err": error, "now": int(time.time()),
            })
            conn.commit()

    # -- Query helpers -----------------------------------------------

    def get_last_timestamp(self, symbol: str, exchange: str, interval: str,
                           table: str = "ohlcv") -> Optional[int]:
        stmt = text(f"""
            SELECT MAX(timestamp) FROM {table}
            WHERE symbol=:sym AND exchange=:ex AND interval=:iv
        """)
        with self.engine.connect() as conn:
            result = conn.execute(stmt, {"sym": symbol, "ex": exchange, "iv": interval})
            row = result.fetchone()
            return row[0] if row and row[0] else None

    def get_latest_ohlcv_close(self, symbol: str, exchange: str, interval: str) -> Optional[float]:
        stmt = text("""
            SELECT close FROM ohlcv
            WHERE symbol=:sym AND exchange=:ex AND interval=:iv
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        with self.engine.connect() as conn:
            result = conn.execute(stmt, {"sym": symbol, "ex": exchange, "iv": interval})
            row = result.fetchone()
            return float(row[0]) if row and row[0] is not None else None

    def count_rows(self, table: str = "ohlcv") -> int:
        stmt = text(f"SELECT COUNT(*) FROM {table}")
        with self.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.scalar() or 0
