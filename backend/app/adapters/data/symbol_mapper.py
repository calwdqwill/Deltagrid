"""SymbolMapper — canonical symbol <-> provider-native symbol mapping.

Uses SQLAlchemy ORM models from domain.models for persistence.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import Instrument, InstrumentAlias
from app.persistence.database import SessionLocal

logger = logging.getLogger(__name__)


class SymbolMapper:
    """Maps canonical symbols to provider-native aliases and back."""

    def __init__(self, db_session: Optional[Session] = None):
        self._db = db_session

    def _session(self) -> Session:
        return self._db or SessionLocal()

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
        session = self._session()
        close_session = self._db is None
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
            if close_session:
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
        session = self._session()
        close_session = self._db is None
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
            if close_session:
                session.close()

    def resolve_instrument(
        self,
        canonical: str,
        instrument_type: str = "perp",
        exchange: Optional[str] = None,
    ) -> Optional[Instrument]:
        """Return full Instrument with all aliases."""
        session = self._session()
        close_session = self._db is None
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
            if close_session:
                session.close()

    def list_aliases(
        self,
        canonical: str,
        instrument_type: str = "perp",
    ) -> list[InstrumentAlias]:
        """List all aliases for a canonical symbol."""
        session = self._session()
        close_session = self._db is None
        try:
            return (
                session.query(InstrumentAlias)
                .join(Instrument)
                .filter(Instrument.canonical_symbol == canonical)
                .filter(Instrument.instrument_type == instrument_type)
                .all()
            )
        finally:
            if close_session:
                session.close()

    # -- Seeding -----------------------------------------------------

    def seed_defaults(self) -> None:
        """Seed top perpetuals with cross-provider aliases (idempotent)."""
        session = self._session()
        close_session = self._db is None
        try:
            existing = session.query(Instrument).count()
            if existing > 0:
                logger.info(f"SymbolMapper.seed_defaults: {existing} instruments already seeded, skipping")
                return

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
                    "exchange": "hyperliquid",
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

            for item in defaults:
                instr = Instrument(
                    canonical_symbol=item["canonical"],
                    base_asset=item["base"],
                    quote_asset=item["quote"],
                    instrument_type=item["type"],
                    exchange=item["exchange"],
                )
                session.add(instr)
                session.flush()  # get instr.id

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
            logger.info(f"SymbolMapper.seed_defaults: seeded {len(defaults)} instruments")
        except Exception:
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()
