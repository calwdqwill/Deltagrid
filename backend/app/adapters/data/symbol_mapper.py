"""SymbolMapper — canonical symbol <-> provider-native symbol mapping.

Uses SQLAlchemy for persistence. Integrates with app.domain.models.
"""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.models import Base, Instrument, InstrumentAlias
from app.persistence.database_url import is_sqlite_database_url, to_sync_database_url


# ------------------------------------------------------------------
# SymbolMapper
# ------------------------------------------------------------------

class SymbolMapper:
    """Maps canonical symbols to provider-native aliases and back."""

    def __init__(self, db_url: Optional[str] = None):
        from app.config import get_settings

        if db_url is None:
            db_url = get_settings().database_url
        self.db_url = to_sync_database_url(db_url)
        self.engine = create_engine(self.db_url, echo=False, **self._engine_kwargs())
        if is_sqlite_database_url(self.db_url):
            Base.metadata.create_all(self.engine, checkfirst=True)
        self.Session = sessionmaker(bind=self.engine)

    def _engine_kwargs(self) -> dict:
        if is_sqlite_database_url(self.db_url):
            return {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            }
        return {"pool_pre_ping": True}

    # -- Public API --------------------------------------------------

    def to_provider(
        self,
        canonical: str,
        provider: str,
        alias_type: str = "ticker",
        instrument_type: str = "perp",
        exchange: Optional[str] = None,
    ) -> str:
        """Canonical symbol -> provider-native alias.

        Example: to_provider("BTC", "binance") -> "BTCUSDT"
        """
        session = self.Session()
        try:
            alias = (
                session.query(InstrumentAlias)
                .join(Instrument)
                .filter(Instrument.canonical_symbol == canonical)
                .filter(InstrumentAlias.provider == provider)
                .filter(InstrumentAlias.alias_type == alias_type)
                .filter(InstrumentAlias.is_primary == True)
            )

            if exchange:
                alias = alias.filter(Instrument.exchange == exchange)
            if instrument_type:
                alias = alias.filter(Instrument.instrument_type == instrument_type)

            row = alias.first()
            if row:
                return row.alias

            # Fallback: any alias for this provider
            row = (
                session.query(InstrumentAlias)
                .join(Instrument)
                .filter(Instrument.canonical_symbol == canonical)
                .filter(InstrumentAlias.provider == provider)
                .filter(InstrumentAlias.alias_type == alias_type)
                .first()
            )
            if row:
                return row.alias

            raise ValueError(
                f"No alias found for {canonical} -> {provider} ({alias_type})"
            )
        finally:
            session.close()

    def from_provider(
        self,
        alias: str,
        provider: str,
        alias_type: str = "ticker",
    ) -> str:
        """Provider-native alias -> canonical symbol.

        Example: from_provider("BTCUSDT", "binance") -> "BTC"
        """
        session = self.Session()
        try:
            row = (
                session.query(Instrument)
                .join(InstrumentAlias)
                .filter(InstrumentAlias.alias == alias)
                .filter(InstrumentAlias.provider == provider)
                .filter(InstrumentAlias.alias_type == alias_type)
                .first()
            )
            if row:
                return row.canonical_symbol
            raise ValueError(f"No canonical symbol found for {provider}:{alias}")
        finally:
            session.close()

    def resolve_instrument(
        self,
        canonical: str,
        instrument_type: str = "perp",
        exchange: Optional[str] = None,
    ) -> Optional[Instrument]:
        """Return full Instrument with all aliases."""
        session = self.Session()
        try:
            query = (
                session.query(Instrument)
                .filter(Instrument.canonical_symbol == canonical)
                .filter(Instrument.instrument_type == instrument_type)
            )
            if exchange:
                query = query.filter(Instrument.exchange == exchange)
            return query.first()
        finally:
            session.close()

    def list_aliases(
        self,
        canonical: str,
        instrument_type: str = "perp",
    ) -> list[InstrumentAlias]:
        """List all aliases for a canonical symbol."""
        session = self.Session()
        try:
            return (
                session.query(InstrumentAlias)
                .join(Instrument)
                .filter(Instrument.canonical_symbol == canonical)
                .filter(Instrument.instrument_type == instrument_type)
                .all()
            )
        finally:
            session.close()

    # -- Seeding -----------------------------------------------------

    def seed_defaults(self) -> None:
        """Seed top perpetuals with cross-provider aliases."""
        from datetime import datetime

        defaults = [
            {
                "canonical": "BTC",
                "base": "BTC",
                "quote": "USDT",
                "type": "perp",
                "exchange": "binance",
                "aliases": [
                    ("binance", "BTCUSDT", "ticker", True),
                    ("coinglass", "BTC", "ticker", True),
                    ("coingecko", "bitcoin", "cg_id", True),
                    ("coingecko", "btc", "cg_symbol", False),
                    ("bybit", "BTCUSDT", "ticker", True),
                    ("okx", "BTC-USDT-SWAP", "ticker", True),
                    ("hyperliquid", "BTC", "ticker", True),
                ],
            },
            {
                "canonical": "ETH",
                "base": "ETH",
                "quote": "USDT",
                "type": "perp",
                "exchange": "binance",
                "aliases": [
                    ("binance", "ETHUSDT", "ticker", True),
                    ("coinglass", "ETH", "ticker", True),
                    ("coingecko", "ethereum", "cg_id", True),
                    ("coingecko", "eth", "cg_symbol", False),
                    ("bybit", "ETHUSDT", "ticker", True),
                    ("okx", "ETH-USDT-SWAP", "ticker", True),
                    ("hyperliquid", "ETH", "ticker", True),
                ],
            },
            {
                "canonical": "SOL",
                "base": "SOL",
                "quote": "USDT",
                "type": "perp",
                "exchange": "binance",
                "aliases": [
                    ("binance", "SOLUSDT", "ticker", True),
                    ("coinglass", "SOL", "ticker", True),
                    ("coingecko", "solana", "cg_id", True),
                    ("coingecko", "sol", "cg_symbol", False),
                    ("bybit", "SOLUSDT", "ticker", True),
                    ("okx", "SOL-USDT-SWAP", "ticker", True),
                    ("hyperliquid", "SOL", "ticker", True),
                ],
            },
            {
                "canonical": "HYPE",
                "base": "HYPE",
                "quote": "USDT",
                "type": "perp",
                "exchange": "binance",
                "aliases": [
                    ("binance", "HYPEUSDT", "ticker", True),
                    ("coinglass", "HYPE", "ticker", True),
                    ("coingecko", "hyperliquid", "cg_id", True),
                    ("coingecko", "hype", "cg_symbol", False),
                    ("bybit", "HYPEUSDT", "ticker", True),
                    ("okx", "HYPE-USDT-SWAP", "ticker", True),
                    ("hyperliquid", "HYPE", "ticker", True),
                ],
            },
        ]

        session = self.Session()
        try:
            for item in defaults:
                instr = Instrument(
                    canonical_symbol=item["canonical"],
                    base_asset=item["base"],
                    quote_asset=item["quote"],
                    instrument_type=item["type"],
                    exchange=item["exchange"],
                )
                session.add(instr)
                session.flush()

                for provider, alias, alias_type, is_primary in item["aliases"]:
                    session.add(
                        InstrumentAlias(
                            instrument_id=instr.id,
                            provider=provider,
                            alias=alias,
                            alias_type=alias_type,
                            is_primary=is_primary,
                        )
                    )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
