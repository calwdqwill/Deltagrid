"""Regression tests for /api/v1/data/* endpoints.

Uses an in-memory SQLite database seeded with canonical symbol data.
Proves that GET /api/v1/data/ohlcv?symbol=BTC&exchange=binance returns
seeded rows when the DB stores the canonical symbol "BTC".
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.config import Settings

_test_settings = Settings(
    database_url="sqlite:///:memory:",
    debug=True,
    secret_key="test-secret-key",
    vault_master_key="test-vault-master-key-" + "x" * 20,
)

with patch("app.config.get_settings", return_value=_test_settings):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.domain.models import Base
    from app.persistence import database as db_module

    _test_engine = create_engine(
        _test_settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    _TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=_test_engine
    )

    db_module.engine = _test_engine
    db_module.SessionLocal = _TestSessionLocal
    Base.metadata.create_all(bind=_test_engine)

    # Avoid external HTTP calls during app lifespan warm-up
    with patch("app.services.scanner_service.ScannerService.fetch_all", return_value=None):
        from app.main import app

from fastapi.testclient import TestClient

client = TestClient(app)


def _seed_canonical_btc() -> None:
    """Seed Instrument + Alias + OHLCV for canonical BTC / binance."""
    session = _TestSessionLocal()
    from app.domain.models import Instrument, InstrumentAlias, DataOhlcv

    instr = Instrument(
        canonical_symbol="BTC",
        base_asset="BTC",
        quote_asset="USDT",
        instrument_type="perp",
        exchange="binance",
    )
    session.add(instr)
    session.flush()

    session.add(
        InstrumentAlias(
            instrument_id=instr.id,
            provider="binance",
            alias="BTCUSDT",
            alias_type="ticker",
            is_primary=True,
        )
    )

    session.add(
        DataOhlcv(
            timestamp=1700000000000,
            symbol="BTC",
            exchange="binance",
            interval="1m",
            open=50000.0,
            high=50100.0,
            low=49900.0,
            close=50050.0,
            volume=100.0,
            quote_volume=5005000.0,
            trades_count=1000,
        )
    )
    session.commit()
    session.close()


def _seed_health_rows() -> None:
    """Seed a fresh OKX stream plus a diagnostic Binance failure."""
    session = _TestSessionLocal()
    from app.domain.models import DataOhlcv, ProviderSyncRun

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    now_ms = int(now.timestamp() * 1000)

    session.merge(
        DataOhlcv(
            timestamp=now_ms - 5 * 60_000,
            symbol="BTC",
            exchange="okx",
            interval="1m",
            open=50000.0,
            high=50100.0,
            low=49900.0,
            close=50050.0,
            volume=100.0,
            quote_volume=5005000.0,
            trades_count=1000,
        )
    )
    session.add(
        ProviderSyncRun(
            provider_name="okx",
            sync_type="ohlcv",
            status="completed",
            start_time=now_ms - 15 * 60_000,
            end_time=now_ms,
            records_fetched=3,
            records_inserted=3,
            created_at=now,
        )
    )
    session.add(
        ProviderSyncRun(
            provider_name="binance",
            sync_type="ohlcv",
            status="partial",
            start_time=now_ms - 15 * 60_000,
            end_time=now_ms,
            records_fetched=0,
            records_inserted=0,
            error_message="HTTP 451 Unavailable For Legal Reasons",
            created_at=now,
        )
    )
    session.commit()
    session.close()


def _seed_sparse_liquidation_rows() -> None:
    """Seed an old liquidation event plus a fresh completed sync run."""
    session = _TestSessionLocal()
    from app.domain.models import DataLiquidation, ProviderSyncRun

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    now_ms = int(now.timestamp() * 1000)

    session.merge(
        DataLiquidation(
            timestamp=now_ms - 240 * 60_000,
            symbol="SOL",
            exchange="okx",
            side="long",
            quantity=0.0,
            price=0.0,
            value_usd=1250.0,
        )
    )
    session.add(
        ProviderSyncRun(
            provider_name="coinglass",
            sync_type="liquidations",
            status="completed",
            start_time=now_ms - 15 * 60_000,
            end_time=now_ms - 5 * 60_000,
            records_fetched=6,
            records_inserted=0,
            created_at=now,
        )
    )
    session.commit()
    session.close()


def _seed_ohlcv_window_rows() -> tuple[int, int]:
    """Seed 150 1m candles to verify latest-anchored chart windows."""
    session = _TestSessionLocal()
    from app.domain.models import DataOhlcv

    base_ts = 1710000000000
    for index in range(150):
        timestamp = base_ts + index * 60_000
        session.merge(
            DataOhlcv(
                timestamp=timestamp,
                symbol="XRP",
                exchange="okx",
                interval="1m",
                open=1.0 + index,
                high=1.1 + index,
                low=0.9 + index,
                close=1.05 + index,
                volume=100.0 + index,
                quote_volume=1000.0 + index,
                trades_count=index,
            )
        )
    session.commit()
    session.close()
    return base_ts + 30 * 60_000, base_ts + 149 * 60_000


def _seed_coverage_rows() -> tuple[int, int]:
    """Seed a complete 24h 1h OHLCV coverage window for ADA / OKX."""
    session = _TestSessionLocal()
    from app.domain.models import DataOhlcv

    base_ts = 1720000000000
    for index in range(24):
        timestamp = base_ts + index * 60 * 60_000
        session.merge(
            DataOhlcv(
                timestamp=timestamp,
                symbol="ADA",
                exchange="okx",
                interval="1h",
                open=0.3 + index,
                high=0.31 + index,
                low=0.29 + index,
                close=0.305 + index,
                volume=1000.0 + index,
                quote_volume=300.0 + index,
                trades_count=100 + index,
            )
        )
    session.commit()
    session.close()
    return base_ts, base_ts + 23 * 60 * 60_000


def _seed_fresh_candidate_rows(symbol: str = "HYPE") -> None:
    """Seed fresh but incomplete 7d candidate rows for provider inventory policy."""
    session = _TestSessionLocal()
    from app.domain.models import (
        BasisPremium,
        DataFundingRate,
        DataLiquidation,
        DataLongShortRatio,
        DataOhlcv,
        DataOpenInterest,
        ProviderSyncRun,
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    now_ms = int(now.timestamp() * 1000)
    fresh_ts = now_ms - 5 * 60_000

    for interval in ("1m", "5m", "1h"):
        session.merge(
            DataOhlcv(
                timestamp=fresh_ts,
                symbol=symbol,
                exchange="okx",
                interval=interval,
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.5,
                volume=100.0,
                quote_volume=1050.0,
                trades_count=50,
            )
        )
    session.merge(
        DataFundingRate(
            timestamp=fresh_ts,
            symbol=symbol,
            exchange="okx",
            funding_rate=0.0001,
            next_funding_time=fresh_ts + 8 * 60 * 60_000,
            interval="8h",
        )
    )
    session.merge(
        DataOpenInterest(
            timestamp=fresh_ts,
            symbol=symbol,
            exchange="okx",
            interval="1h",
            oi_usd=1_000_000.0,
            oi_coins=1000.0,
        )
    )
    session.merge(
        DataLongShortRatio(
            timestamp=fresh_ts,
            symbol=symbol,
            exchange="okx",
            interval="1h",
            long_ratio=0.52,
            short_ratio=0.48,
            long_account_ratio=0.52,
            short_account_ratio=0.48,
        )
    )
    session.merge(
        DataLiquidation(
            timestamp=fresh_ts,
            symbol=symbol,
            exchange="okx",
            side="long",
            quantity=0.0,
            price=0.0,
            value_usd=1000.0,
        )
    )
    session.add(
        BasisPremium(
            timestamp=fresh_ts,
            symbol=symbol,
            exchange="okx",
            spot_price=10.0,
            perp_price=10.1,
            basis_pct=1.0,
            premium_pct=1.0,
        )
    )
    session.add(
        ProviderSyncRun(
            provider_name="coinglass",
            sync_type="liquidations",
            status="completed",
            start_time=fresh_ts - 60_000,
            end_time=fresh_ts,
            records_fetched=1,
            records_inserted=1,
            created_at=now,
        )
    )
    session.commit()
    session.close()


def test_ohlcv_canonical_symbol_returns_data() -> None:
    """Critical regression: canonical BTC must return seeded rows."""
    _seed_canonical_btc()
    response = client.get("/api/v1/data/ohlcv?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["symbol"] == "BTC"
    assert payload["meta"]["symbol"] == "BTC"
    assert payload["meta"]["exchange"] == "binance"


def test_ohlcv_unknown_symbol_returns_empty() -> None:
    response = client.get("/api/v1/data/ohlcv?symbol=UNKNOWN&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []
    assert payload["meta"]["count"] == 0


def test_ohlcv_window_returns_latest_anchored_range() -> None:
    """Window endpoint should return large chart windows without client pagination."""
    expected_start, expected_end = _seed_ohlcv_window_rows()

    response = client.get("/api/v1/data/ohlcv/window?symbol=XRP&exchange=okx&interval=1m&range=2h")
    assert response.status_code == 200
    payload = response.json()

    assert len(payload["data"]) == 120
    assert payload["data"][0]["timestamp"] == expected_start
    assert payload["data"][-1]["timestamp"] == expected_end
    assert payload["meta"]["count"] == 120
    assert payload["meta"]["expected_rows"] == 120
    assert payload["meta"]["limit"] == 20_000
    assert payload["meta"]["window_source"] == "latest_available"


def test_ohlcv_window_rejects_unsupported_interval() -> None:
    response = client.get("/api/v1/data/ohlcv/window?symbol=XRP&exchange=okx&interval=30s&range=2h")
    assert response.status_code == 400


def test_funding_returns_200() -> None:
    """Funding endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/funding?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []


def test_open_interest_returns_200() -> None:
    """Open-interest endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/open-interest?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []


def test_long_short_ratio_returns_200() -> None:
    """Long/short ratio endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/long-short-ratio?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []


def test_basis_premium_returns_200() -> None:
    """Basis endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/basis-premium?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []


def test_liquidations_returns_200() -> None:
    """Liquidations endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/liquidations?symbol=BTC&exchange=binance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == []


def test_health_returns_200() -> None:
    """Data health endpoint must summarize row counts."""
    response = client.get("/api/v1/data/health")
    assert response.status_code == 200
    payload = response.json()
    assert "row_counts" in payload["data"]
    assert "data_quality" in payload["data"]
    assert "freshness" in payload["data"]
    assert "coverage" in payload["data"]
    assert "universe" in payload["data"]
    assert "sync_health_by_type" in payload["data"]
    assert "sync_diagnostics" in payload["data"]


def test_coverage_reports_regular_window_counts() -> None:
    """Coverage endpoint should expose row counts versus expected cadence."""
    expected_start, expected_end = _seed_coverage_rows()

    response = client.get("/api/v1/data/coverage?symbols=ADA&exchange=okx&range=24h")
    assert response.status_code == 200
    data = response.json()["data"]

    ada_1h = next(
        row
        for row in data["rows"]
        if row["symbol"] == "ADA"
        and row["exchange"] == "okx"
        and row["stream"] == "ohlcv"
        and row["interval"] == "1h"
    )
    assert ada_1h["status"] == "covered"
    assert ada_1h["rows"] == 24
    assert ada_1h["expected_rows"] == 24
    assert ada_1h["coverage_pct"] == 100.0
    assert ada_1h["window_start"] == expected_start
    assert ada_1h["window_end"] == expected_end
    assert data["summary"]["total"] == len(data["rows"])
    assert data["summary"]["covered"] >= 1


def test_coverage_rejects_unsupported_range() -> None:
    response = client.get("/api/v1/data/coverage?symbols=ADA&exchange=okx&range=30d")
    assert response.status_code == 400


def test_universe_reports_not_ready_symbol_policy() -> None:
    """Universe endpoint should classify symbols without persisted coverage as not ready."""
    response = client.get("/api/v1/data/universe?symbols=UNI&exchange=okx")
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["scope"]["symbols"] == ["UNI"]
    assert data["summary"]["total"] == 1
    assert data["summary"]["not_ready"] == 1
    assert data["policy"]["ui_universe"] == []
    assert data["policy"]["deferred_symbols"] == ["UNI"]

    uni = data["symbols"][0]
    assert uni["symbol"] == "UNI"
    assert uni["status"] == "not_ready"
    assert uni["ui_visible"] is False
    assert uni["chart_ready"] is False
    assert len(uni["missing_streams_7d"]) > 0


def test_provider_inventory_defaults_to_expansion_candidates() -> None:
    """Provider inventory should expose a read-only candidate list for universe expansion."""
    response = client.get("/api/v1/data/provider-inventory")
    assert response.status_code == 200
    payload = response.json()
    data = payload["data"]

    assert payload["meta"]["read_only"] is True
    assert data["scope"]["inventory_mode"] == "persisted_data_only"
    assert data["scope"]["external_provider_calls"] is False
    assert data["scope"]["symbols"][:4] == ["BTC", "ETH", "SOL", "HYPE"]
    assert data["summary"]["total"] == len(data["scope"]["symbols"])
    assert "promotion_candidates" in data["policy"]
    assert "chart_ready_candidates" in data["policy"]
    assert "chart_ready_candidates" in data["summary"]
    assert "coverage_blockers" in data["summary"]
    assert "freshness_blockers" in data["summary"]
    assert "promotion_blockers" in data["summary"]
    assert all("next_action" in row for row in data["symbols"])
    assert all("promotion_blockers" in row for row in data["symbols"])


def test_provider_inventory_defers_symbol_without_coverage() -> None:
    """Symbols without persisted streams must stay out of UI promotion candidates."""
    response = client.get("/api/v1/data/provider-inventory?symbols=UNI&exchange=okx")
    assert response.status_code == 200
    data = response.json()["data"]

    uni = data["symbols"][0]
    assert data["scope"]["symbols"] == ["UNI"]
    assert data["policy"]["promotion_candidates"] == []
    assert data["policy"]["deferred_symbols"] == ["UNI"]
    assert uni["promotion_candidate"] is False
    assert uni["next_action"] == "backfill_required"
    assert uni["freshness_tracked"] is True
    assert len(uni["missing_streams_7d"]) > 0
    assert len(uni["coverage_blockers_7d"]) > 0
    assert len(uni["freshness_blockers"]) > 0
    assert len(uni["promotion_blockers"]) == (
        len(uni["coverage_blockers_7d"]) + len(uni["freshness_blockers"])
    )


def test_provider_inventory_tracks_candidate_freshness_scope() -> None:
    """Fresh candidate rows should move inventory to history completion gate."""
    _seed_fresh_candidate_rows("HYPE")
    response = client.get("/api/v1/data/provider-inventory?symbols=HYPE&exchange=okx")
    assert response.status_code == 200
    data = response.json()["data"]

    hype = data["symbols"][0]
    assert data["scope"]["freshness_scope"] == "requested_symbols"
    assert hype["symbol"] == "HYPE"
    assert hype["freshness_tracked"] is True
    assert hype["freshness"]["worst_status"] == "fresh"
    assert hype["status"] == "partial_history"
    assert hype["promotion_candidate"] is False
    assert hype["next_action"] == "history_completion_required"
    assert len(hype["partial_streams_7d"]) > 0
    assert hype["missing_streams_7d"] == []
    assert len(hype["coverage_blockers_7d"]) > 0
    assert hype["freshness_blockers"] == []
    assert hype["promotion_blockers"] == hype["coverage_blockers_7d"]
    coverage_blocker = hype["promotion_blockers"][0]
    assert coverage_blocker["blocker_type"] == "coverage"
    assert coverage_blocker["range"] == "7d"
    assert coverage_blocker["status"] == "partial"
    assert coverage_blocker["stream"] in {"ohlcv", "funding_rates", "open_interest", "long_short_ratio"}
    assert isinstance(data["policy"]["chart_ready_candidates"], list)
    assert data["summary"]["chart_ready_candidates"] >= 0
    assert data["summary"]["coverage_blockers"] >= len(hype["coverage_blockers_7d"])


def test_health_reports_freshness_and_sync_diagnostics() -> None:
    """Data health must expose stream freshness, sync type split and error classes."""
    _seed_health_rows()
    response = client.get("/api/v1/data/health")
    assert response.status_code == 200
    data = response.json()["data"]

    freshness_rows = data["freshness"]["streams"]
    btc_1m = next(
        row
        for row in freshness_rows
        if row["symbol"] == "BTC"
        and row["exchange"] == "okx"
        and row["stream"] == "ohlcv"
        and row["interval"] == "1m"
    )
    assert btc_1m["status"] == "fresh"
    assert btc_1m["age_minutes"] <= 30

    assert data["sync_health_by_type"]["okx"]["ohlcv"]["status"] == "healthy"
    assert data["sync_health_by_type"]["binance"]["ohlcv"]["status"] == "degraded"
    assert data["sync_diagnostics"]["recent_error_classes"]["http_451"] >= 1


def test_sparse_liquidations_use_sync_freshness() -> None:
    """Sparse liquidation streams should not go stale when sync runs are fresh."""
    _seed_sparse_liquidation_rows()
    response = client.get("/api/v1/data/health")
    assert response.status_code == 200
    data = response.json()["data"]

    sol_liquidations = next(
        row
        for row in data["freshness"]["streams"]
        if row["symbol"] == "SOL"
        and row["exchange"] == "okx"
        and row["stream"] == "liquidations"
        and row["interval"] == "1h"
    )

    assert sol_liquidations["status"] == "fresh"
    assert sol_liquidations["freshness_mode"] == "sparse_event"
    assert sol_liquidations["age_minutes"] > sol_liquidations["stale_after_minutes"]
    assert sol_liquidations["sync_provider"] == "coinglass"
    assert sol_liquidations["sync_type"] == "liquidations"
    assert sol_liquidations["sync_age_minutes"] <= 30
    assert "no recent liquidation events" in sol_liquidations["reason"]


def test_readiness_reports_missing_migration_state() -> None:
    """Readiness must fail when the DB is reachable but Alembic state is absent."""
    response = client.get("/api/v1/health/readiness")
    assert response.status_code == 503
    payload = response.json()
    assert payload["data"]["status"] == "not_ready"
    assert payload["data"]["checks"]["database"]["ok"] is True
    assert payload["data"]["checks"]["migrations"]["ok"] is False


def test_production_validation_blocks_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    """SQLite fallback must not be accepted in production-like runtime."""
    from app import main as main_module

    production_settings = Settings(
        database_url="sqlite:///:memory:",
        debug=False,
        secret_key="x" * 32,
        vault_master_key="y" * 32,
        cors_origins="https://example.com",
    )
    monkeypatch.setattr(main_module, "settings", production_settings)

    with pytest.raises(RuntimeError, match="SQLite DATABASE_URL"):
        main_module._validate_production_settings()
