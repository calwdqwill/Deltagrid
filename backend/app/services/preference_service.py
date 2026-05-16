import json
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import Favorite, PinnedInstrument, Preference
from app.persistence.database import SessionLocal
from app.schemas.preferences import ScannerPreferences
from app.services.cache_service import CacheService


class PreferenceService:
    """CRUD service for user preferences, favorites, and pinned instruments.

    Phase 1: No user auth, so uses a single global user context (user_id=None).
    Phase 2+: Accepts optional user_id for authenticated users.
    Phase 4: Added cache invalidation and explicit session lifecycle.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        user_id: Optional[str] = None,
        cache: Optional[CacheService] = None,
    ):
        self._owns_session = db is None
        self.db = db or SessionLocal()
        self.user_id = user_id
        self.cache = cache
        self._ensure_defaults()

    def close(self) -> None:
        """Close the underlying DB session if we own it."""
        if self._owns_session and self.db:
            self.db.close()
            self.db = None

    def _invalidate_cache(self) -> None:
        """Invalidate scanner cache after preference mutations."""
        if self.cache:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.cache.delete("scanner_records"))
            except RuntimeError:
                pass

    def _ensure_defaults(self) -> None:
        """Ensure default preferences exist for the current user context."""
        defaults = [
            ("language", "en"),
            ("min_spread_pct", "0.1"),
            ("refresh_interval_sec", "60"),
            ("slippage_pct", "0.0"),
            ("fee_buy_pct", "0.1"),
            ("fee_sell_pct", "0.1"),
            ("positive_net_only", "false"),
            ("selected_types", json.dumps(["cex-cex", "dex-cex", "spot-perp"])),
        ]
        for key, value in defaults:
            query = self.db.query(Preference).filter(
                Preference.key == key,
                Preference.user_id == self.user_id,
            )
            existing = query.first()
            if not existing:
                self.db.add(Preference(key=key, value=value, user_id=self.user_id))
        self.db.commit()

    def _pref_query(self):
        """Base query scoped to current user_id."""
        return self.db.query(Preference).filter(Preference.user_id == self.user_id)

    def _fav_query(self):
        return self.db.query(Favorite).filter(Favorite.user_id == self.user_id)

    def _pinned_query(self):
        return self.db.query(PinnedInstrument).filter(PinnedInstrument.user_id == self.user_id)

    async def get_scanner_preferences(self) -> ScannerPreferences:
        """Load all scanner preferences from DB."""
        prefs = {}
        for p in self._pref_query().all():
            prefs[p.key] = p.value

        selected_types = prefs.get("selected_types", '["cex-cex", "dex-cex", "spot-perp"]')
        try:
            selected_types = json.loads(selected_types)
        except json.JSONDecodeError:
            selected_types = ["cex-cex", "dex-cex", "spot-perp"]

        return ScannerPreferences(
            language=prefs.get("language", "en"),
            min_spread_pct=float(prefs.get("min_spread_pct", "0.1")),
            min_volume_24h=float(prefs["min_volume_24h"]) if prefs.get("min_volume_24h") else None,
            refresh_interval_sec=int(prefs.get("refresh_interval_sec", "60")),
            slippage_pct=float(prefs.get("slippage_pct", "0.0")),
            fee_buy_pct=float(prefs.get("fee_buy_pct", "0.1")),
            fee_sell_pct=float(prefs.get("fee_sell_pct", "0.1")),
            positive_net_only=prefs.get("positive_net_only", "false").lower() == "true",
            selected_types=selected_types,
        )

    async def update_preferences(self, prefs: ScannerPreferences) -> ScannerPreferences:
        """Update preferences in DB."""
        updates = {
            "language": prefs.language,
            "min_spread_pct": str(prefs.min_spread_pct),
            "min_volume_24h": str(prefs.min_volume_24h) if prefs.min_volume_24h else None,
            "refresh_interval_sec": str(prefs.refresh_interval_sec),
            "slippage_pct": str(prefs.slippage_pct),
            "fee_buy_pct": str(prefs.fee_buy_pct),
            "fee_sell_pct": str(prefs.fee_sell_pct),
            "positive_net_only": "true" if prefs.positive_net_only else "false",
            "selected_types": json.dumps(prefs.selected_types),
        }
        for key, value in updates.items():
            if value is None:
                continue
            existing = self._pref_query().filter(Preference.key == key).first()
            if existing:
                existing.value = value
            else:
                self.db.add(Preference(key=key, value=value, user_id=self.user_id))
        self.db.commit()
        self._invalidate_cache()
        return prefs

    async def get_favorites(self) -> list[str]:
        """Get list of favorite instrument IDs."""
        rows = self._fav_query().all()
        return [r.instrument_id for r in rows]

    async def toggle_favorite(self, instrument_id: str) -> bool:
        """Toggle favorite status. Returns new state."""
        existing = self._fav_query().filter(Favorite.instrument_id == instrument_id).first()
        if existing:
            self.db.delete(existing)
            self.db.commit()
            self._invalidate_cache()
            return False
        self.db.add(Favorite(instrument_id=instrument_id, user_id=self.user_id))
        self.db.commit()
        self._invalidate_cache()
        return True

    async def get_pinned(self) -> list[str]:
        """Get list of pinned instrument IDs."""
        rows = self._pinned_query().all()
        return [r.instrument_id for r in rows]

    async def toggle_pinned(self, instrument_id: str) -> bool:
        """Toggle pinned status. Returns new state."""
        existing = (
            self._pinned_query()
            .filter(PinnedInstrument.instrument_id == instrument_id)
            .first()
        )
        if existing:
            self.db.delete(existing)
            self.db.commit()
            self._invalidate_cache()
            return False
        self.db.add(PinnedInstrument(instrument_id=instrument_id, user_id=self.user_id))
        self.db.commit()
        self._invalidate_cache()
        return True
