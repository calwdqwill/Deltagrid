from datetime import datetime
from typing import Optional

from app.adapters.base import RawTicker
from app.adapters.registry import AdapterRegistry
from app.config import get_settings
from app.constants import (
    DEFAULT_EXCHANGES,
    DEFAULT_INSTRUMENTS,
    DataStatus,
    ScannerType,
)
from app.schemas.scanner import ScannerRecord, ScannerMeta, ScannerListResponse
from app.services.cache_service import CacheService
from app.services.coingecko_service import CoinGeckoService
from app.services.perp_dex_service import PerpDEXService
from app.services.spread_calculator import SpreadCalculator
from app.services.signal_classifier import SignalClassifier
from app.services.preference_service import PreferenceService


class ScannerService:
    """Main orchestrator for scanner data.

    Fetches data from multiple sources, normalizes, calculates spreads,
    classifies signals, caches results, and returns records.
    """

    CACHE_KEY = "scanner_records"

    def __init__(
        self,
        cache: CacheService,
        cg_service: CoinGeckoService,
        perp_service: PerpDEXService,
        pref_service: PreferenceService,
    ):
        self.cache = cache
        self.cg_service = cg_service
        self.perp_service = perp_service
        self.pref_service = pref_service
        self.settings = get_settings()

    async def fetch_all(self) -> ScannerListResponse:
        # Try cache first
        cached = await self.cache.get(self.CACHE_KEY)
        if cached:
            return cached

        instrument_ids = list(DEFAULT_INSTRUMENTS.keys())

        # Fetch spot and perp data in parallel
        spot_tickers = await self.cg_service.fetch_spot_prices(instrument_ids)
        perp_tickers = await self.perp_service.fetch_perp_prices(instrument_ids)

        # Determine data status
        is_fallback = all(t.venue_id != "coingecko_aggregated" for t in spot_tickers)
        data_status = DataStatus.FALLBACK if is_fallback else DataStatus.LIVE
        if not spot_tickers:
            data_status = DataStatus.UNAVAILABLE

        # Build venue price maps
        spot_map = self._build_price_map(spot_tickers)
        perp_map = self._build_price_map(perp_tickers)

        # Get preferences for fees
        prefs = await self.pref_service.get_scanner_preferences()
        fee_buy = prefs.fee_buy_pct if prefs else self.settings.default_fee_buy_pct
        fee_sell = prefs.fee_sell_pct if prefs else self.settings.default_fee_sell_pct
        slippage = prefs.slippage_pct if prefs else self.settings.default_slippage_pct

        # Get favorites and pins
        favorites = set(await self.pref_service.get_favorites())
        pinned = set(await self.pref_service.get_pinned())

        records: list[ScannerRecord] = []

        # CEX-CEX pairs
        for inst_id, info in DEFAULT_INSTRUMENTS.items():
            venues = spot_map.get(inst_id, {})
            venue_ids = list(venues.keys())
            for i in range(len(venue_ids)):
                for j in range(i + 1, len(venue_ids)):
                    v1, v2 = venue_ids[i], venue_ids[j]
                    p1, p2 = venues[v1]["price"], venues[v2]["price"]
                    if p1 <= 0 or p2 <= 0:
                        continue
                    # Buy at lower, sell at higher
                    if p1 < p2:
                        buy_v, sell_v, buy_p, sell_p = v1, v2, p1, p2
                    else:
                        buy_v, sell_v, buy_p, sell_p = v2, v1, p2, p1

                    spread = SpreadCalculator.calculate(buy_p, sell_p, fee_buy, fee_sell, slippage)
                    signal = SignalClassifier.classify(spread.net_profit_pct)
                    hint = SignalClassifier.strategy_hint(spread.net_profit_pct, ScannerType.CEX_CEX)

                    rec_id = f"{inst_id}_cex_{buy_v}_{sell_v}"
                    records.append(ScannerRecord(
                        id=rec_id,
                        token_name=info["name"],
                        symbol=info["symbol"],
                        pair=f"{info['symbol']}/USDT",
                        icon_url=info.get("icon_url"),
                        scanner_type=ScannerType.CEX_CEX,
                        buy_venue=DEFAULT_EXCHANGES.get(buy_v, {}).get("name", buy_v),
                        buy_price=buy_p,
                        sell_venue=DEFAULT_EXCHANGES.get(sell_v, {}).get("name", sell_v),
                        sell_price=sell_p,
                        spread_pct=round(spread.gross_spread_pct, 4),
                        net_profit_pct=round(spread.net_profit_pct, 4),
                        volume_24h=venues[buy_v].get("volume"),
                        signal=signal,
                        trend_series=self._generate_trend(spread.gross_spread_pct),
                        data_status=data_status,
                        source_label="coingecko" if not is_fallback else "mock_fallback",
                        updated_at=datetime.utcnow(),
                        is_favorite=rec_id in favorites,
                        is_pinned=rec_id in pinned,
                        strategy_hint=hint,
                    ))

        # Spot-Perp pairs
        for inst_id, info in DEFAULT_INSTRUMENTS.items():
            spot_venues = spot_map.get(inst_id, {})
            perp_venues = perp_map.get(inst_id, {})
            for spot_v, spot_data in spot_venues.items():
                for perp_v, perp_data in perp_venues.items():
                    spot_p = spot_data["price"]
                    perp_p = perp_data["price"]
                    if spot_p <= 0 or perp_p <= 0:
                        continue
                    # Buy spot, sell perp (basis trade)
                    if spot_p < perp_p:
                        buy_v, sell_v, buy_p, sell_p = spot_v, perp_v, spot_p, perp_p
                    else:
                        buy_v, sell_v, buy_p, sell_p = perp_v, spot_v, perp_p, spot_p

                    spread = SpreadCalculator.calculate(buy_p, sell_p, fee_buy, fee_sell, slippage)
                    signal = SignalClassifier.classify(spread.net_profit_pct)
                    hint = SignalClassifier.strategy_hint(spread.net_profit_pct, ScannerType.SPOT_PERP)

                    basis_pct = ((perp_p - spot_p) / spot_p) * 100 if spot_p > 0 else 0

                    rec_id = f"{inst_id}_perp_{spot_v}_{perp_v}"
                    records.append(ScannerRecord(
                        id=rec_id,
                        token_name=info["name"],
                        symbol=info["symbol"],
                        pair=f"{info['symbol']}/USDT",
                        icon_url=info.get("icon_url"),
                        scanner_type=ScannerType.SPOT_PERP,
                        buy_venue=DEFAULT_EXCHANGES.get(buy_v, {}).get("name", buy_v),
                        buy_price=buy_p,
                        sell_venue=DEFAULT_EXCHANGES.get(sell_v, {}).get("name", sell_v),
                        sell_price=sell_p,
                        spread_pct=round(spread.gross_spread_pct, 4),
                        net_profit_pct=round(spread.net_profit_pct, 4),
                        volume_24h=spot_data.get("volume"),
                        signal=signal,
                        trend_series=self._generate_trend(spread.gross_spread_pct),
                        data_status=data_status,
                        source_label="coingecko" if not is_fallback else "mock_fallback",
                        updated_at=datetime.utcnow(),
                        is_favorite=rec_id in favorites,
                        is_pinned=rec_id in pinned,
                        basis_pct=round(basis_pct, 4),
                        funding_rate=perp_data.get("funding_rate"),
                        open_interest=perp_data.get("open_interest"),
                        strategy_hint=hint,
                    ))

        # Sort: pinned first, then by net profit desc
        records.sort(key=lambda r: (-int(r.is_pinned), -r.net_profit_pct))

        status_counts = {}
        for r in records:
            status_counts[r.data_status] = status_counts.get(r.data_status, 0) + 1

        meta = ScannerMeta(
            total=len(records),
            filtered=len(records),
            data_status_counts=status_counts,
            last_updated=datetime.utcnow(),
            sources=["coingecko", "hyperliquid", "aster", "lighter"],
            is_fallback=is_fallback,
        )

        response = ScannerListResponse(records=records, meta=meta)

        # Cache for TTL
        await self.cache.set(
            self.CACHE_KEY,
            response,
            self.settings.cache_ttl_seconds,
        )

        return response

    async def get_by_id(self, record_id: str) -> Optional[ScannerRecord]:
        all_data = await self.fetch_all()
        for rec in all_data.records:
            if rec.id == record_id:
                return rec
        return None

    def _build_price_map(self, tickers: list[RawTicker]) -> dict:
        """Build {instrument_id: {venue_id: {price, volume, ...}}} map."""
        result: dict = {}
        for t in tickers:
            if t.instrument_id not in result:
                result[t.instrument_id] = {}
            result[t.instrument_id][t.venue_id] = {
                "price": t.price,
                "volume": t.volume_24h,
                "funding_rate": t.funding_rate,
                "open_interest": t.open_interest,
            }
        return result

    def _generate_trend(self, base_spread: float, points: int = 10) -> list[float]:
        """Generate a simple sparkline trend around the base spread."""
        import random
        trend = []
        for i in range(points):
            noise = random.uniform(-0.3, 0.3)
            trend.append(round(base_spread + noise, 4))
        return trend
