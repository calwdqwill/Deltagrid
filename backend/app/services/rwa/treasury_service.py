"""Treasury intelligence service — company and platform data."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import TreasuryEntity, TreasurySnapshot, TokenizationPlatform
from app.services.cache_service import InMemoryCacheService

logger = logging.getLogger(__name__)


class TreasuryService:
    """Manage treasury entities, snapshots, and tokenization platforms."""

    DEFAULT_ENTITIES = [
        {
            "entity_type": "public_company",
            "name": "MicroStrategy",
            "ticker": "MSTR",
            "sector": "Software / Bitcoin Treasury",
            "description": "Business intelligence firm with large Bitcoin treasury holdings.",
            "website_url": "https://www.microstrategy.com",
        },
        {
            "entity_type": "public_company",
            "name": "Marathon Digital Holdings",
            "ticker": "MARA",
            "sector": "Bitcoin Mining",
            "description": "Bitcoin mining company with significant BTC holdings.",
            "website_url": "https://www.marathondh.com",
        },
        {
            "entity_type": "public_company",
            "name": "Tesla",
            "ticker": "TSLA",
            "sector": "Automotive / Energy",
            "description": "Electric vehicle manufacturer with Bitcoin treasury exposure.",
            "website_url": "https://www.tesla.com",
        },
        {
            "entity_type": "public_company",
            "name": "Block (Square)",
            "ticker": "SQ",
            "sector": "Fintech",
            "description": "Financial services company led by Jack Dorsey with BTC holdings.",
            "website_url": "https://block.xyz",
        },
    ]

    DEFAULT_PLATFORMS = [
        {
            "name": "Centrifuge",
            "category": "credit",
            "description": "Decentralized asset financing protocol for real-world assets.",
            "website_url": "https://centrifuge.io",
            "blockchain": "Ethereum / Centrifuge Chain",
            "governance_token": "CFG",
        },
        {
            "name": "Figure",
            "category": "credit",
            "description": "Fintech company focusing on home equity and blockchain-based lending.",
            "website_url": "https://www.figure.com",
            "blockchain": "Provenance Blockchain",
            "governance_token": "HASH",
        },
        {
            "name": "Maple Finance",
            "category": "credit",
            "description": "Institutional capital marketplace powered by blockchain.",
            "website_url": "https://maple.finance",
            "blockchain": "Ethereum",
            "governance_token": "MPL",
        },
    ]

    def __init__(self, db: Session, cache: Optional[InMemoryCacheService] = None):
        self.db = db
        self.cache = cache or InMemoryCacheService()

    @classmethod
    def seed_entities(cls, db: Session) -> None:
        """Seed default treasury entities if table is empty."""
        existing = db.query(TreasuryEntity).count()
        if existing > 0:
            return
        for item in cls.DEFAULT_ENTITIES:
            entity = TreasuryEntity(**item)
            db.add(entity)
        db.commit()

    @classmethod
    def seed_platforms(cls, db: Session) -> None:
        """Seed default tokenization platforms if table is empty."""
        existing = db.query(TokenizationPlatform).count()
        if existing > 0:
            return
        for item in cls.DEFAULT_PLATFORMS:
            platform = TokenizationPlatform(**item)
            db.add(platform)
        db.commit()

    async def list_entities(self, entity_type: Optional[str] = None, active_only: bool = True) -> list[dict]:
        """List treasury entities."""
        cache_key = f"treasury_entities:{entity_type or 'all'}:{active_only}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        query = self.db.query(TreasuryEntity)
        if active_only:
            query = query.filter(TreasuryEntity.is_active == True)
        if entity_type:
            query = query.filter(TreasuryEntity.entity_type == entity_type)

        rows = query.order_by(TreasuryEntity.name).all()
        result = [
            {
                "id": r.id,
                "entity_type": r.entity_type,
                "name": r.name,
                "ticker": r.ticker,
                "sector": r.sector,
                "description": r.description,
                "website_url": r.website_url,
                "is_active": r.is_active,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
        await self.cache.set(cache_key, result, ttl_seconds=3600)
        return result

    async def get_entity_with_latest_snapshot(self, entity_id: str) -> Optional[dict]:
        """Get single entity plus its latest snapshot."""
        cache_key = f"treasury_entity:{entity_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        entity = self.db.query(TreasuryEntity).filter(TreasuryEntity.id == entity_id).first()
        if not entity:
            return None

        latest_snap = (
            self.db.query(TreasurySnapshot)
            .filter(TreasurySnapshot.entity_id == entity_id)
            .order_by(TreasurySnapshot.report_date.desc())
            .first()
        )

        result = {
            "id": entity.id,
            "entity_type": entity.entity_type,
            "name": entity.name,
            "ticker": entity.ticker,
            "sector": entity.sector,
            "description": entity.description,
            "website_url": entity.website_url,
            "is_active": entity.is_active,
            "latest_snapshot": self._snapshot_to_dict(latest_snap) if latest_snap else None,
            "created_at": entity.created_at.isoformat() if entity.created_at else None,
            "updated_at": entity.updated_at.isoformat() if entity.updated_at else None,
        }
        await self.cache.set(cache_key, result, ttl_seconds=3600)
        return result

    async def get_snapshots(self, entity_id: str, limit: int = 30) -> list[dict]:
        """Get historical snapshots for an entity."""
        rows = (
            self.db.query(TreasurySnapshot)
            .filter(TreasurySnapshot.entity_id == entity_id)
            .order_by(TreasurySnapshot.report_date.desc())
            .limit(limit)
            .all()
        )
        return [self._snapshot_to_dict(r) for r in rows]

    async def get_btc_holdings_leaderboard(self, limit: int = 50) -> list[dict]:
        """Aggregate BTC holdings across entities using latest snapshot."""
        cache_key = f"btc_leaderboard:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        from sqlalchemy import func

        subq = (
            self.db.query(
                TreasurySnapshot.entity_id,
                func.max(TreasurySnapshot.report_date).label("max_date")
            )
            .group_by(TreasurySnapshot.entity_id)
            .subquery()
        )

        rows = (
            self.db.query(TreasuryEntity, TreasurySnapshot)
            .join(TreasurySnapshot, TreasuryEntity.id == TreasurySnapshot.entity_id)
            .join(subq, (TreasurySnapshot.entity_id == subq.c.entity_id) & (TreasurySnapshot.report_date == subq.c.max_date))
            .filter(TreasuryEntity.is_active == True)
            .order_by(TreasurySnapshot.btc_holdings.desc())
            .limit(limit)
            .all()
        )

        result = []
        for entity, snap in rows:
            result.append({
                "entity_id": entity.id,
                "name": entity.name,
                "ticker": entity.ticker,
                "btc_holdings": float(snap.btc_holdings) if snap.btc_holdings is not None else None,
                "btc_value_usd": float(snap.btc_value_usd) if snap.btc_value_usd is not None else None,
                "btc_per_share": float(snap.btc_per_share) if snap.btc_per_share is not None else None,
                "report_date": snap.report_date.isoformat() if snap.report_date else None,
                "source": snap.source,
                "source_quality": snap.source_quality,
            })

        await self.cache.set(cache_key, result, ttl_seconds=3600)
        return result

    async def list_platforms(self, active_only: bool = True) -> list[dict]:
        """List tokenization platforms."""
        cache_key = f"tokenization_platforms:{active_only}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        query = self.db.query(TokenizationPlatform)
        if active_only:
            query = query.filter(TokenizationPlatform.is_active == True)

        rows = query.order_by(TokenizationPlatform.name).all()
        result = [
            {
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "description": r.description,
                "website_url": r.website_url,
                "tvl_usd": float(r.tvl_usd) if r.tvl_usd is not None else None,
                "active_pools": r.active_pools,
                "blockchain": r.blockchain,
                "governance_token": r.governance_token,
                "is_active": r.is_active,
                "last_updated_at": r.last_updated_at.isoformat() if r.last_updated_at else None,
            }
            for r in rows
        ]
        await self.cache.set(cache_key, result, ttl_seconds=3600)
        return result

    @staticmethod
    def _snapshot_to_dict(s: TreasurySnapshot) -> dict:
        return {
            "id": s.id,
            "entity_id": s.entity_id,
            "source": s.source,
            "source_quality": s.source_quality,
            "btc_holdings": float(s.btc_holdings) if s.btc_holdings is not None else None,
            "btc_value_usd": float(s.btc_value_usd) if s.btc_value_usd is not None else None,
            "total_treasury_usd": float(s.total_treasury_usd) if s.total_treasury_usd is not None else None,
            "shares_outstanding": float(s.shares_outstanding) if s.shares_outstanding is not None else None,
            "btc_per_share": float(s.btc_per_share) if s.btc_per_share is not None else None,
            "report_date": s.report_date.isoformat() if s.report_date else None,
            "fetched_at": s.fetched_at.isoformat() if s.fetched_at else None,
            "next_expected_update_at": s.next_expected_update_at.isoformat() if s.next_expected_update_at else None,
        }
