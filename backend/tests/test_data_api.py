"""Regression tests for /api/v1/data/* endpoints.

Uses an in-memory SQLite database seeded with canonical symbol data.
Proves that GET /api/v1/data/ohlcv?symbol=BTC&exchange=binance returns
seeded rows when the DB stores the canonical symbol "BTC".
"""

from unittest.mock import patch

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


def test_funding_returns_200() -> None:
    """Funding endpoint must be reachable even when table is empty."""
    response = client.get("/api/v1/data/funding?symbol=BTC&exchange=binance")
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
