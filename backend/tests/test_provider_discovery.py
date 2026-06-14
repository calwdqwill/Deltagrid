"""Regression tests for provider discovery report helpers."""

from app.adapters.data.discover_provider_universe import (
    build_report,
    build_symbol_readiness,
    parse_symbols,
    render_markdown_report,
)


def _available(reason: str = "ok") -> dict:
    return {"status": "available", "available": True, "reason": reason, "details": {}}


def _missing(reason: str = "missing") -> dict:
    return {"status": "missing", "available": False, "reason": reason, "details": {}}


def _okx_row(*, ready: bool = True) -> dict:
    status_row = _available() if ready else _missing()
    return {
        "alias": "TEST-USDT-SWAP",
        "instrument": status_row,
        "ohlcv": status_row,
        "funding": status_row,
        "open_interest": status_row,
        "long_short_ratio": status_row,
    }


def _coinglass_row(*, ready: bool = True) -> dict:
    status_row = _available() if ready else _missing()
    return {
        "alias": "TEST",
        "market_row": status_row,
        "funding_snapshot": status_row,
        "open_interest_snapshot": status_row,
        "liquidations": status_row,
    }


def _coingecko_row(*, ready: bool = True) -> dict:
    return {
        "alias": "test-token",
        "spot_price": _available() if ready else _missing(),
    }


def _binance_row(*, ready: bool = False) -> dict:
    return {
        "alias": "TESTUSDT",
        "instrument": _available() if ready else _missing(),
    }


def test_parse_symbols_deduplicates_and_normalizes() -> None:
    assert parse_symbols(" btc, ETH,btc ,, sol ") == ("BTC", "ETH", "SOL")


def test_build_symbol_readiness_requires_core_enrichment_and_spot() -> None:
    readiness = build_symbol_readiness(
        "TEST",
        _okx_row(ready=True),
        _coinglass_row(ready=True),
        _coingecko_row(ready=True),
        _binance_row(ready=False),
    )

    assert readiness["okx_core_ready"] is True
    assert readiness["coinglass_enrichment_ready"] is True
    assert readiness["coingecko_spot_ready"] is True
    assert readiness["next_action"] == "eligible_for_24h_sync_dry_run"


def test_build_symbol_readiness_blocks_incomplete_okx_core() -> None:
    readiness = build_symbol_readiness(
        "TEST",
        _okx_row(ready=False),
        _coinglass_row(ready=True),
        _coingecko_row(ready=True),
        _binance_row(ready=True),
    )

    assert readiness["okx_core_ready"] is False
    assert readiness["next_action"] == "do_not_expand_sync_yet"
    assert "OKX core streams are incomplete" in readiness["blocking_reasons"]


def test_render_markdown_report_includes_next_action() -> None:
    report = build_report(
        ("TEST",),
        {
            "provider": {"status": "healthy", "http_status": 200, "reason": "ok"},
            "symbols": {"TEST": _okx_row(ready=True)},
        },
        {
            "provider": {"status": "healthy", "http_status": 200, "reason": "ok"},
            "symbols": {"TEST": _coinglass_row(ready=True)},
        },
        {
            "provider": {"status": "healthy", "http_status": 200, "reason": "ok"},
            "symbols": {"TEST": _coingecko_row(ready=True)},
        },
        {
            "provider": {"status": "blocked_http_451", "http_status": 451, "reason": "blocked"},
            "symbols": {"TEST": _binance_row(ready=False)},
        },
    )

    markdown = render_markdown_report(report)

    assert "Provider discovery v1" in markdown
    assert "eligible_for_24h_sync_dry_run" in markdown
    assert "`TEST`" in markdown
