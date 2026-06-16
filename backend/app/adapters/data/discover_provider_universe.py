"""Read-only provider discovery for candidate perp universe expansion."""

import argparse
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

DEFAULT_SYMBOLS = (
    "BTC",
    "ETH",
    "SOL",
    "HYPE",
    "XRP",
    "DOGE",
    "BNB",
    "ADA",
    "LINK",
    "AVAX",
    "SUI",
    "TON",
    "TRX",
    "DOT",
    "LTC",
    "BCH",
    "AAVE",
    "UNI",
    "APT",
    "ARB",
)

COINGECKO_IDS_BY_SYMBOL = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "HYPE": "hyperliquid",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "LINK": "chainlink",
    "AVAX": "avalanche-2",
    "SUI": "sui",
    "TON": "the-open-network",
    "TRX": "tron",
    "DOT": "polkadot",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "AAVE": "aave",
    "UNI": "uniswap",
    "APT": "aptos",
    "ARB": "arbitrum",
}

OKX_BASE_URL = "https://www.okx.com"
COINGLASS_BASE_URL = "https://open-api-v4.coinglass.com"
COINGECKO_DEMO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
BINANCE_FAPI_BASE_URL = "https://fapi.binance.com"
AVAILABLE_STATUSES = {"available", "available_empty", "available_instrument"}


def parse_symbols(value: Optional[str]) -> tuple[str, ...]:
    if not value or not value.strip():
        return DEFAULT_SYMBOLS
    parsed = tuple(dict.fromkeys(item.strip().upper() for item in value.split(",") if item.strip()))
    if not parsed:
        raise ValueError("symbols must contain at least one symbol")
    return parsed


def load_env_file(path: Optional[str]) -> None:
    if not path:
        return

    env_path = Path(path)
    if not env_path.exists():
        raise FileNotFoundError(f"env file does not exist: {env_path}")

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def status_is_available(status_value: str) -> bool:
    return status_value in AVAILABLE_STATUSES


def _stream(status_value: str, reason: str, **details: Any) -> dict[str, Any]:
    return {
        "status": status_value,
        "available": status_is_available(status_value),
        "reason": reason,
        "details": details,
    }


def _http_error_status(status_code: Optional[int]) -> str:
    if status_code == 451:
        return "blocked_http_451"
    if status_code in (401, 403):
        return "auth_failed"
    if status_code == 429:
        return "rate_limited"
    return "http_error"


async def _request_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, Any]] = None,
    retries: int = 2,
    retry_backoff_seconds: float = 1.0,
) -> dict[str, Any]:
    last_error: Optional[dict[str, Any]] = None
    for attempt in range(retries + 1):
        try:
            response = await client.get(url, headers=headers, params=params)
        except Exception as exc:
            last_error = {
                "ok": False,
                "status": "network_error",
                "http_status": None,
                "error": str(exc),
                "payload": None,
            }
            if attempt < retries:
                await asyncio.sleep(retry_backoff_seconds * (attempt + 1))
                continue
            return last_error

        try:
            payload = response.json()
        except ValueError:
            payload = None

        if response.status_code == 429 and attempt < retries:
            retry_after = response.headers.get("Retry-After")
            sleep_seconds = float(retry_after) if retry_after and retry_after.isdigit() else retry_backoff_seconds * (attempt + 1)
            await asyncio.sleep(sleep_seconds)
            continue

        if response.status_code >= 400:
            return {
                "ok": False,
                "status": _http_error_status(response.status_code),
                "http_status": response.status_code,
                "error": response.text[:180],
                "payload": payload,
            }

        return {
            "ok": True,
            "status": "ok",
            "http_status": response.status_code,
            "error": None,
            "payload": payload,
        }

    return last_error or {
        "ok": False,
        "status": "unknown_error",
        "http_status": None,
        "error": "request failed without response",
        "payload": None,
    }


def _extract_provider_data(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return None
    if payload.get("success") is True or payload.get("code") in ("0", 0):
        return payload.get("data")
    if "data" in payload and payload.get("status") not in ("error", "fail"):
        return payload.get("data")
    return None


def _okx_stream_status(result: dict[str, Any], data_label: str) -> dict[str, Any]:
    if not result["ok"]:
        return _stream(result["status"], f"{data_label} request failed", http_status=result["http_status"])

    payload = result["payload"]
    if not isinstance(payload, dict):
        return _stream("invalid_response", f"{data_label} response is not a JSON object")
    if payload.get("code") != "0":
        return _stream("provider_error", payload.get("msg") or f"OKX code {payload.get('code')}")

    rows = payload.get("data")
    if isinstance(rows, list) and rows:
        return _stream("available", f"{data_label} returned rows", rows=len(rows))
    if isinstance(rows, list):
        return _stream("missing_empty", f"{data_label} returned an empty data list", rows=0)
    return _stream("invalid_response", f"{data_label} data field is not a list")


async def discover_okx(client: httpx.AsyncClient, symbols: tuple[str, ...]) -> dict[str, Any]:
    instruments_result = await _request_json(
        client,
        f"{OKX_BASE_URL}/api/v5/public/instruments",
        params={"instType": "SWAP"},
    )
    provider_status = {
        "status": "healthy" if instruments_result["ok"] else instruments_result["status"],
        "http_status": instruments_result["http_status"],
        "reason": "OKX instruments endpoint reachable" if instruments_result["ok"] else instruments_result["error"],
    }

    payload = instruments_result["payload"] if instruments_result["ok"] else None
    raw_instruments = payload.get("data", []) if isinstance(payload, dict) else []
    instruments_by_id = {
        item.get("instId"): item
        for item in raw_instruments
        if isinstance(item, dict)
        and item.get("instId")
        and item.get("instType") == "SWAP"
        and item.get("settleCcy") == "USDT"
    }

    semaphore = asyncio.Semaphore(2)

    async def probe(symbol: str) -> tuple[str, dict[str, Any]]:
        inst_id = f"{symbol}-USDT-SWAP"
        instrument = instruments_by_id.get(inst_id)
        if not instrument:
            return symbol, {
                "alias": inst_id,
                "instrument": _stream("missing_instrument", "OKX USDT swap instrument was not found"),
                "ohlcv": _stream("missing_instrument", "OKX instrument is missing"),
                "funding": _stream("missing_instrument", "OKX instrument is missing"),
                "open_interest": _stream("missing_instrument", "OKX instrument is missing"),
                "long_short_ratio": _stream("missing_instrument", "OKX instrument is missing"),
            }

        async with semaphore:
            ohlcv = await _request_json(
                client,
                f"{OKX_BASE_URL}/api/v5/market/history-candles",
                params={"instId": inst_id, "bar": "1H", "limit": "1"},
            )
            funding = await _request_json(
                client,
                f"{OKX_BASE_URL}/api/v5/public/funding-rate-history",
                params={"instId": inst_id, "limit": "1"},
            )
            oi = await _request_json(
                client,
                f"{OKX_BASE_URL}/api/v5/public/open-interest",
                params={"instType": "SWAP", "instId": inst_id},
            )
            long_short = await _request_json(
                client,
                f"{OKX_BASE_URL}/api/v5/rubik/stat/contracts/long-short-account-ratio",
                params={"ccy": symbol, "period": "1H"},
                retries=4,
                retry_backoff_seconds=1.5,
            )

        return symbol, {
            "alias": inst_id,
            "instrument": _stream(
                "available_instrument",
                "OKX USDT swap instrument is listed",
                state=instrument.get("state"),
                list_time=instrument.get("listTime"),
            ),
            "ohlcv": _okx_stream_status(ohlcv, "OKX OHLCV"),
            "funding": _okx_stream_status(funding, "OKX funding history"),
            "open_interest": _okx_stream_status(oi, "OKX open interest"),
            "long_short_ratio": _okx_stream_status(long_short, "OKX long/short account ratio"),
        }

    symbol_rows = dict(await asyncio.gather(*(probe(symbol) for symbol in symbols)))
    return {"provider": provider_status, "symbols": symbol_rows}


def _coinglass_headers() -> tuple[dict[str, str], bool]:
    api_key = os.getenv("COINGLASS_STANDARD_API_KEY") or os.getenv("COINGLASS_API_KEY")
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_key:
        headers["CG-API-KEY"] = api_key
    return headers, bool(api_key)


def _market_field_status(row: Optional[dict[str, Any]], keys: tuple[str, ...], label: str) -> dict[str, Any]:
    if not row:
        return _stream("missing", f"CoinGlass {label} row is missing")
    for key in keys:
        if row.get(key) is not None:
            return _stream("available", f"CoinGlass {label} field is present", field=key)
    return _stream("available_empty", f"CoinGlass market row exists, but {label} field was not present")


async def discover_coinglass(client: httpx.AsyncClient, symbols: tuple[str, ...]) -> dict[str, Any]:
    headers, has_key = _coinglass_headers()
    if not has_key:
        return {
            "provider": {
                "status": "auth_missing",
                "http_status": None,
                "reason": "COINGLASS_API_KEY or COINGLASS_STANDARD_API_KEY is not configured",
            },
            "symbols": {
                symbol: {
                    "alias": symbol,
                    "market_row": _stream("auth_missing", "CoinGlass API key is missing"),
                    "funding_snapshot": _stream("auth_missing", "CoinGlass API key is missing"),
                    "open_interest_snapshot": _stream("auth_missing", "CoinGlass API key is missing"),
                    "liquidations": _stream("auth_missing", "CoinGlass API key is missing"),
                }
                for symbol in symbols
            },
        }

    market_result = await _request_json(
        client,
        f"{COINGLASS_BASE_URL}/api/futures/coins-markets",
        headers=headers,
        params={"exchange_list": "OKX", "per_page": 100, "page": 1},
    )
    provider_status = {
        "status": "healthy" if market_result["ok"] else market_result["status"],
        "http_status": market_result["http_status"],
        "reason": "CoinGlass futures coins-markets endpoint reachable" if market_result["ok"] else market_result["error"],
    }

    rows = _extract_provider_data(market_result["payload"]) if market_result["ok"] else None
    market_rows = rows if isinstance(rows, list) else []
    markets_by_symbol = {
        str(row.get("symbol", "")).upper(): row
        for row in market_rows
        if isinstance(row, dict)
    }

    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(hours=24)).timestamp() * 1000)
    end_ms = int(now.timestamp() * 1000)
    semaphore = asyncio.Semaphore(4)

    async def liquidation_status(symbol: str) -> tuple[str, dict[str, Any]]:
        async with semaphore:
            result = await _request_json(
                client,
                f"{COINGLASS_BASE_URL}/api/futures/liquidation/aggregated-history",
                headers=headers,
                params={
                    "exchange_list": "OKX",
                    "symbol": symbol,
                    "interval": "1h",
                    "limit": 24,
                    "start_time": start_ms,
                    "end_time": end_ms,
                },
            )
        if not result["ok"]:
            return symbol, _stream(result["status"], "CoinGlass liquidation history request failed", http_status=result["http_status"])
        data = _extract_provider_data(result["payload"])
        if isinstance(data, dict):
            for key in ("list", "items", "rows", "data"):
                if isinstance(data.get(key), list):
                    data = data[key]
                    break
        if isinstance(data, list) and data:
            return symbol, _stream("available", "CoinGlass liquidation history returned rows", rows=len(data))
        if isinstance(data, list):
            return symbol, _stream("available_empty", "CoinGlass liquidation endpoint works; no events in 24h window", rows=0)
        return symbol, _stream("invalid_response", "CoinGlass liquidation response did not contain a list")

    liquidation_rows = dict(await asyncio.gather(*(liquidation_status(symbol) for symbol in symbols)))
    symbol_rows: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        row = markets_by_symbol.get(symbol)
        symbol_rows[symbol] = {
            "alias": symbol,
            "market_row": _stream("available", "CoinGlass OKX market row exists") if row else _stream("missing", "CoinGlass OKX market row is missing"),
            "funding_snapshot": _market_field_status(
                row,
                ("avg_funding_rate_by_oi", "avg_funding_rate_by_vol", "fundingRate", "funding_rate"),
                "funding snapshot",
            ),
            "open_interest_snapshot": _market_field_status(
                row,
                ("open_interest_usd", "openInterestUsd", "open_interest_quantity", "openInterest"),
                "open interest snapshot",
            ),
            "liquidations": liquidation_rows[symbol],
        }

    return {"provider": provider_status, "symbols": symbol_rows}


async def _coingecko_simple_price(
    client: httpx.AsyncClient,
    ids: list[str],
    *,
    api_key: Optional[str],
) -> tuple[dict[str, Any], str]:
    if api_key:
        result = await _request_json(
            client,
            f"{COINGECKO_PRO_BASE_URL}/simple/price",
            headers={"Accept": "application/json", "x-cg-pro-api-key": api_key},
            params={
                "ids": ",".join(ids),
                "vs_currencies": "usd",
                "include_24hr_vol": "true",
                "include_last_updated_at": "true",
            },
        )
        if result["ok"]:
            return result, "pro"

    result = await _request_json(
        client,
        f"{COINGECKO_DEMO_BASE_URL}/simple/price",
        headers={"Accept": "application/json"},
        params={
            "ids": ",".join(ids),
            "vs_currencies": "usd",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        },
    )
    return result, "demo"


async def discover_coingecko(client: httpx.AsyncClient, symbols: tuple[str, ...]) -> dict[str, Any]:
    ids_by_symbol = {
        symbol: COINGECKO_IDS_BY_SYMBOL.get(symbol)
        for symbol in symbols
    }
    ids = [coin_id for coin_id in ids_by_symbol.values() if coin_id]
    api_key = os.getenv("COINGECKO_API_KEY")

    if not ids:
        return {
            "provider": {"status": "not_configured", "http_status": None, "reason": "no CoinGecko ids mapped"},
            "symbols": {
                symbol: {
                    "alias": None,
                    "spot_price": _stream("missing_mapping", "CoinGecko id mapping is missing"),
                }
                for symbol in symbols
            },
        }

    result, mode = await _coingecko_simple_price(client, ids, api_key=api_key)
    provider_status = {
        "status": "healthy" if result["ok"] else result["status"],
        "http_status": result["http_status"],
        "reason": f"CoinGecko simple price endpoint reachable via {mode} base" if result["ok"] else result["error"],
        "mode": mode,
        "api_key_configured": bool(api_key),
    }

    payload = result["payload"] if result["ok"] and isinstance(result["payload"], dict) else {}
    symbol_rows: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        coin_id = ids_by_symbol.get(symbol)
        if not coin_id:
            spot_status = _stream("missing_mapping", "CoinGecko id mapping is missing")
        else:
            row = payload.get(coin_id)
            if isinstance(row, dict) and row.get("usd") is not None:
                spot_status = _stream(
                    "available",
                    "CoinGecko spot price returned",
                    price_usd=row.get("usd"),
                    volume_24h_usd=row.get("usd_24h_vol"),
                    last_updated_at=row.get("last_updated_at"),
                )
            else:
                spot_status = _stream("missing", "CoinGecko spot price was not returned", coin_id=coin_id)

        symbol_rows[symbol] = {
            "alias": coin_id,
            "spot_price": spot_status,
        }

    return {"provider": provider_status, "symbols": symbol_rows}


async def discover_binance(client: httpx.AsyncClient, symbols: tuple[str, ...]) -> dict[str, Any]:
    result = await _request_json(client, f"{BINANCE_FAPI_BASE_URL}/fapi/v1/exchangeInfo")
    provider_status = {
        "status": "healthy" if result["ok"] else result["status"],
        "http_status": result["http_status"],
        "reason": "Binance USD-M Futures exchangeInfo reachable" if result["ok"] else result["error"],
        "role": "legacy_diagnostic",
    }

    payload = result["payload"] if result["ok"] and isinstance(result["payload"], dict) else {}
    raw_symbols = payload.get("symbols", []) if isinstance(payload, dict) else []
    trading_symbols = {
        row.get("symbol"): row
        for row in raw_symbols
        if isinstance(row, dict) and row.get("status") == "TRADING"
    }

    symbol_rows: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        alias = f"{symbol}USDT"
        if not result["ok"]:
            status_row = _stream(result["status"], "Binance legacy provider is not reachable from this runtime", http_status=result["http_status"])
        elif alias in trading_symbols:
            status_row = _stream("available_instrument", "Binance USD-M instrument is listed", alias=alias)
        else:
            status_row = _stream("missing_instrument", "Binance USD-M instrument is missing", alias=alias)
        symbol_rows[symbol] = {
            "alias": alias,
            "instrument": status_row,
        }

    return {"provider": provider_status, "symbols": symbol_rows}


def build_symbol_readiness(
    symbol: str,
    okx: dict[str, Any],
    coinglass: dict[str, Any],
    coingecko: dict[str, Any],
    binance: dict[str, Any],
) -> dict[str, Any]:
    okx_core_keys = ("instrument", "ohlcv", "funding", "open_interest", "long_short_ratio")
    okx_core_ready = all(okx[key]["available"] for key in okx_core_keys)
    coinglass_ready = (
        coinglass["market_row"]["available"]
        and coinglass["funding_snapshot"]["available"]
        and coinglass["open_interest_snapshot"]["available"]
        and coinglass["liquidations"]["available"]
    )
    spot_ready = coingecko["spot_price"]["available"]
    basis_possible = okx["ohlcv"]["available"] and spot_ready
    binance_reachable = binance["instrument"]["available"]

    blocking_reasons: list[str] = []
    if not okx_core_ready:
        blocking_reasons.append("OKX core streams are incomplete")
    if not coinglass_ready:
        blocking_reasons.append("CoinGlass enrichment streams are incomplete")
    if not spot_ready:
        blocking_reasons.append("CoinGecko spot price is missing")

    if okx_core_ready and coinglass_ready and spot_ready:
        next_action = "eligible_for_24h_sync_dry_run"
    elif okx_core_ready and spot_ready:
        next_action = "okx_core_only_review"
    else:
        next_action = "do_not_expand_sync_yet"

    return {
        "okx_core_ready": okx_core_ready,
        "coinglass_enrichment_ready": coinglass_ready,
        "coingecko_spot_ready": spot_ready,
        "basis_possible": basis_possible,
        "binance_legacy_reachable": binance_reachable,
        "next_action": next_action,
        "blocking_reasons": blocking_reasons,
    }


def build_report(
    symbols: tuple[str, ...],
    okx_report: dict[str, Any],
    coinglass_report: dict[str, Any],
    coingecko_report: dict[str, Any],
    binance_report: dict[str, Any],
) -> dict[str, Any]:
    symbol_rows: list[dict[str, Any]] = []
    summary = {
        "total": 0,
        "eligible_for_24h_sync_dry_run": 0,
        "okx_core_ready": 0,
        "coinglass_enrichment_ready": 0,
        "coingecko_spot_ready": 0,
        "basis_possible": 0,
        "binance_legacy_reachable": 0,
        "do_not_expand_sync_yet": 0,
        "okx_core_only_review": 0,
    }

    for symbol in symbols:
        okx = okx_report["symbols"][symbol]
        coinglass = coinglass_report["symbols"][symbol]
        coingecko = coingecko_report["symbols"][symbol]
        binance = binance_report["symbols"][symbol]
        readiness = build_symbol_readiness(symbol, okx, coinglass, coingecko, binance)

        summary["total"] += 1
        for key in (
            "okx_core_ready",
            "coinglass_enrichment_ready",
            "coingecko_spot_ready",
            "basis_possible",
            "binance_legacy_reachable",
        ):
            if readiness[key]:
                summary[key] += 1
        summary[readiness["next_action"]] += 1

        symbol_rows.append(
            {
                "symbol": symbol,
                "aliases": {
                    "okx": okx["alias"],
                    "coinglass": coinglass["alias"],
                    "coingecko": coingecko["alias"],
                    "binance": binance["alias"],
                },
                "streams": {
                    "okx": {
                        "instrument": okx["instrument"],
                        "ohlcv": okx["ohlcv"],
                        "funding": okx["funding"],
                        "open_interest": okx["open_interest"],
                        "long_short_ratio": okx["long_short_ratio"],
                    },
                    "coinglass": {
                        "market_row": coinglass["market_row"],
                        "funding_snapshot": coinglass["funding_snapshot"],
                        "open_interest_snapshot": coinglass["open_interest_snapshot"],
                        "liquidations": coinglass["liquidations"],
                    },
                    "coingecko": {
                        "spot_price": coingecko["spot_price"],
                    },
                    "binance_legacy": {
                        "instrument": binance["instrument"],
                    },
                },
                "readiness": readiness,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "symbols": list(symbols),
            "providers": ["okx", "coinglass", "coingecko", "binance_legacy"],
            "primary_perp_exchange": "okx",
            "read_only": True,
            "writes_database": False,
        },
        "providers": {
            "okx": okx_report["provider"],
            "coinglass": coinglass_report["provider"],
            "coingecko": coingecko_report["provider"],
            "binance_legacy": binance_report["provider"],
        },
        "summary": summary,
        "symbols": symbol_rows,
    }


def _status_text(row: dict[str, Any]) -> str:
    return row["status"]


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Provider discovery v1 — DeltaGrid",
        "",
        f"Сгенерировано: `{report['generated_at']}`.",
        "",
        "Режим: read-only, без записи в PostgreSQL и без изменения sync/UI-конфигурации.",
        "",
        "## Сводка",
        "",
    ]
    summary = report["summary"]
    lines.extend(
        [
            f"- Всего symbols: `{summary['total']}`.",
            f"- Готовы к 24h sync dry-run: `{summary['eligible_for_24h_sync_dry_run']}`.",
            f"- OKX core ready: `{summary['okx_core_ready']}`.",
            f"- CoinGlass enrichment ready: `{summary['coinglass_enrichment_ready']}`.",
            f"- CoinGecko spot ready: `{summary['coingecko_spot_ready']}`.",
            f"- Basis possible: `{summary['basis_possible']}`.",
            f"- Binance legacy reachable: `{summary['binance_legacy_reachable']}`.",
            "",
            "## Provider status",
            "",
            "| Provider | Status | HTTP | Reason |",
            "|---|---:|---:|---|",
        ]
    )
    for provider_name, provider in report["providers"].items():
        reason = str(provider.get("reason") or "").replace("|", "\\|")
        lines.append(
            f"| `{provider_name}` | `{provider.get('status')}` | `{provider.get('http_status')}` | {reason} |"
        )

    lines.extend(
        [
            "",
            "## Symbols",
            "",
            "| Symbol | OKX core | CoinGlass | CoinGecko spot | Binance legacy | Next action |",
            "|---|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["symbols"]:
        okx = row["streams"]["okx"]
        coinglass = row["streams"]["coinglass"]
        coingecko = row["streams"]["coingecko"]
        binance = row["streams"]["binance_legacy"]
        okx_core = ",".join(
            _status_text(okx[key])
            for key in ("ohlcv", "funding", "open_interest", "long_short_ratio")
        )
        coinglass_status = ",".join(
            _status_text(coinglass[key])
            for key in ("funding_snapshot", "open_interest_snapshot", "liquidations")
        )
        lines.append(
            "| "
            f"`{row['symbol']}` | "
            f"`{okx_core}` | "
            f"`{coinglass_status}` | "
            f"`{_status_text(coingecko['spot_price'])}` | "
            f"`{_status_text(binance['instrument'])}` | "
            f"`{row['readiness']['next_action']}` |"
        )

    lines.extend(
        [
            "",
            "## Интерпретация",
            "",
            "- `eligible_for_24h_sync_dry_run` означает, что symbol можно брать в следующий безопасный 24h backfill dry-run.",
            "- `okx_core_only_review` означает, что OKX и spot готовы, но enrichment слой CoinGlass неполный.",
            "- `do_not_expand_sync_yet` означает, что symbol нельзя добавлять в sync/UI до устранения блокеров.",
            "- `available_empty` для liquidations допустим: endpoint работает, но в 24h окне могло не быть событий.",
        ]
    )
    return "\n".join(lines) + "\n"


async def run_discovery(symbols: tuple[str, ...], timeout_seconds: float) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        okx_report, coinglass_report, coingecko_report, binance_report = await asyncio.gather(
            discover_okx(client, symbols),
            discover_coinglass(client, symbols),
            discover_coingecko(client, symbols),
            discover_binance(client, symbols),
        )
    return build_report(symbols, okx_report, coinglass_report, coingecko_report, binance_report)


def write_outputs(report: dict[str, Any], output_dir: str, output_format: str) -> list[Path]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    paths: list[Path] = []

    if output_format in ("json", "both"):
        path = target_dir / f"provider_discovery_{timestamp}.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(path)

    if output_format in ("markdown", "both"):
        path = target_dir / f"provider_discovery_{timestamp}.md"
        path.write_text(render_markdown_report(report), encoding="utf-8")
        paths.append(path)

    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run read-only provider discovery for candidate perp symbols.")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS), help="Comma-separated canonical symbols.")
    parser.add_argument("--env-file", action="append", default=[], help="Optional KEY=VALUE env file; can be repeated.")
    parser.add_argument("--timeout", type=float, default=20.0, help="HTTP timeout in seconds.")
    parser.add_argument("--format", choices=("json", "markdown", "both"), default="json", help="Output format.")
    parser.add_argument("--output-dir", default=None, help="Write report files to this directory instead of stdout.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    for env_file in args.env_file:
        load_env_file(env_file)

    report = asyncio.run(run_discovery(parse_symbols(args.symbols), args.timeout))
    if args.output_dir:
        paths = write_outputs(report, args.output_dir, args.format)
        print(json.dumps({"written": [str(path) for path in paths]}, ensure_ascii=False))
        return

    if args.format == "markdown":
        print(render_markdown_report(report), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.format == "both":
            print()
            print(render_markdown_report(report), end="")


if __name__ == "__main__":
    main()
