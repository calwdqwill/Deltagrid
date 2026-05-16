"""RWA asset service — CRUD and provider orchestration."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import RwaAsset, RwaAssetSnapshot
from app.services.cache_service import InMemoryCacheService

logger = logging.getLogger(__name__)


class RwaAssetService:
    """Manage RWA assets and their snapshots."""

    DEFAULT_ASSETS = [
        {
            "symbol": "XAUT",
            "name": "Tether Gold",
            "category": "tokenized_gold",
            "issuer": "Tether",
            "blockchain": "Ethereum",
            "contract_address": "0x4922a015c4407F87432B179bb209e125432E4a2A",
            "decimals": 6,
        },
        {
            "symbol": "PAXG",
            "name": "PAX Gold",
            "category": "tokenized_gold",
            "issuer": "Paxos",
            "blockchain": "Ethereum",
            "contract_address": "0x45804880De22913dAFE09f4980848ECE6EcbAf78",
            "decimals": 18,
        },
        {
            "symbol": "BUIDL",
            "name": "BlackRock USD Institutional Digital Liquidity Fund",
            "category": "tokenized_treasury",
            "issuer": "BlackRock",
            "blockchain": "Ethereum",
            "contract_address": "0x7712c34205737192402172409a8F7ccef8a2D62c",
            "decimals": 6,
        },
        {
            "symbol": "USDY",
            "name": "Ondo US Dollar Yield",
            "category": "tokenized_treasury",
            "issuer": "Ondo Finance",
            "blockchain": "Ethereum",
            "contract_address": "0x96F6efF8528f5600C9a4398dbfd09C6CdfDa45e1",
            "decimals": 18,
        },
        {
            "symbol": "CFG",
            "name": "Centrifuge",
            "category": "tokenized_credit",
            "issuer": "Centrifuge",
            "blockchain": "Ethereum",
            "contract_address": "0xc221b7E65FfC80DE234bbB6667aBD1a2369ba8E3",
            "decimals": 18,
        },
    ]

    def __init__(self, db: Session, cache: Optional[InMemoryCacheService] = None):
        self.db = db
        self.cache = cache or InMemoryCacheService()

    @classmethod
    def seed_assets(cls, db: Session) -> None:
        """Seed default RWA assets if table is empty."""
        existing = db.query(RwaAsset).count()
        if existing > 0:
            return
        for item in cls.DEFAULT_ASSETS:
            asset = RwaAsset(**item)
            db.add(asset)
        db.commit()

    async def list_assets(self, category: Optional[str] = None, active_only: bool = True) -> list[dict]:
        """List RWA assets with optional filtering."""
        cache_key = f"rwa_assets:{category or 'all'}:{active_only}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        query = self.db.query(RwaAsset)
        if active_only:
            query = query.filter(RwaAsset.is_active == True)
        if category:
            query = query.filter(RwaAsset.category == category)

        rows = query.order_by(RwaAsset.symbol).all()
        result = [
            {
                "id": r.id,
                "symbol": r.symbol,
                "name": r.name,
                "category": r.category,
                "asset_class": r.asset_class,
                "issuer": r.issuer,
                "blockchain": r.blockchain,
                "contract_address": r.contract_address,
                "decimals": r.decimals,
                "is_active": r.is_active,
                "is_executable": r.is_executable,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
        await self.cache.set(cache_key, result, ttl_seconds=300)
        return result

    async def get_asset_with_latest_snapshot(self, asset_id: str) -> Optional[dict]:
        """Get single asset plus its latest snapshot."""
        cache_key = f"rwa_asset:{asset_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        asset = self.db.query(RwaAsset).filter(RwaAsset.id == asset_id).first()
        if not asset:
            return None

        latest_snap = (
            self.db.query(RwaAssetSnapshot)
            .filter(RwaAssetSnapshot.asset_id == asset_id)
            .order_by(RwaAssetSnapshot.fetched_at.desc())
            .first()
        )

        result = {
            "id": asset.id,
            "symbol": asset.symbol,
            "name": asset.name,
            "category": asset.category,
            "asset_class": asset.asset_class,
            "issuer": asset.issuer,
            "blockchain": asset.blockchain,
            "contract_address": asset.contract_address,
            "decimals": asset.decimals,
            "is_active": asset.is_active,
            "is_executable": asset.is_executable,
            "latest_snapshot": self._snapshot_to_dict(latest_snap) if latest_snap else None,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }
        await self.cache.set(cache_key, result, ttl_seconds=300)
        return result

    async def get_snapshots(self, asset_id: str, limit: int = 30) -> list[dict]:
        """Get historical snapshots for an asset."""
        rows = (
            self.db.query(RwaAssetSnapshot)
            .filter(RwaAssetSnapshot.asset_id == asset_id)
            .order_by(RwaAssetSnapshot.fetched_at.desc())
            .limit(limit)
            .all()
        )
        return [self._snapshot_to_dict(r) for r in rows]

    async def get_categories(self) -> list[dict]:
        """Return distinct categories with counts."""
        cache_key = "rwa_categories"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        from sqlalchemy import func

        rows = (
            self.db.query(RwaAsset.category, func.count(RwaAsset.id))
            .filter(RwaAsset.is_active == True)
            .group_by(RwaAsset.category)
            .all()
        )
        result = [{"category": cat, "count": cnt} for cat, cnt in rows]
        await self.cache.set(cache_key, result, ttl_seconds=300)
        return result

    @staticmethod
    def _snapshot_to_dict(s: RwaAssetSnapshot) -> dict:
        return {
            "id": s.id,
            "asset_id": s.asset_id,
            "source": s.source,
            "source_quality": s.source_quality,
            "price_usd": float(s.price_usd) if s.price_usd is not None else None,
            "nav_usd": float(s.nav_usd) if s.nav_usd is not None else None,
            "market_cap_usd": float(s.market_cap_usd) if s.market_cap_usd is not None else None,
            "total_supply": float(s.total_supply) if s.total_supply is not None else None,
            "volume_24h_usd": float(s.volume_24h_usd) if s.volume_24h_usd is not None else None,
            "yield_apr": float(s.yield_apr) if s.yield_apr is not None else None,
            "premium_discount_pct": float(s.premium_discount_pct) if s.premium_discount_pct is not None else None,
            "fetched_at": s.fetched_at.isoformat() if s.fetched_at else None,
            "next_expected_update_at": s.next_expected_update_at.isoformat() if s.next_expected_update_at else None,
        }
