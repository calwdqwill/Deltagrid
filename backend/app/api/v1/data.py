from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.domain.models import (
    BasisPremium,
    DataFundingRate,
    DataLiquidation,
    DataLongShortRatio,
    DataOhlcv,
    DataOpenInterest,
    DataQualityLog,
    ProviderHealth,
    ProviderSyncLog,
    ProviderSyncRun,
)
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/data", tags=["data"])

MAX_ROWS = 1000
OHLCV_WINDOW_MAX_ROWS = 20_000
OHLCV_WINDOW_RANGES_MS = {
    "2h": 2 * 60 * 60_000,
    "8h": 8 * 60 * 60_000,
    "24h": 24 * 60 * 60_000,
    "7d": 7 * 24 * 60 * 60_000,
}
OHLCV_INTERVAL_MS = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "1h": 60 * 60_000,
}
COVERAGE_RANGES_MS = {
    "24h": 24 * 60 * 60_000,
    "7d": 7 * 24 * 60 * 60_000,
}
COVERAGE_MIN_RATIO = 0.98
UNIVERSE_RANGES = ("24h", "7d")
UNIVERSE_CHART_STREAMS = {"ohlcv"}
WATCHED_PROVIDERS = ("okx", "binance", "coinglass", "coingecko")
WATCHED_SYMBOLS = ("BTC", "ETH", "SOL")
PROVIDER_INVENTORY_SYMBOLS = (
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
PROVIDER_INVENTORY_PROMOTION_STATUSES = {"complete_history", "core_perp_ready"}
PRIMARY_PERP_EXCHANGE = "okx"
CRON_EXPECTED_INTERVAL_MINUTES = 15
RECENT_SYNC_WINDOW_HOURS = 24
SYNC_SUCCESS_STATUSES = {"completed", "success"}
SYNC_DEGRADED_STATUSES = {"partial", "failure", "failed", "error"}

FRESHNESS_SPECS: tuple[dict[str, Any], ...] = (
    {
        "stream": "ohlcv",
        "model": DataOhlcv,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1m", "5m", "1h"),
        "expected_cadence": {"1m": 1, "5m": 5, "1h": 60},
        "stale_after": {"1m": 30, "5m": 30, "1h": 120},
        "degraded_after": {"1m": 60, "5m": 90, "1h": 240},
    },
    {
        "stream": "funding_rates",
        "model": DataFundingRate,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("8h",),
        "expected_cadence": {"8h": 480},
        "stale_after": {"8h": 540},
        "degraded_after": {"8h": 720},
    },
    {
        "stream": "open_interest",
        "model": DataOpenInterest,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "expected_cadence": {"1h": 60},
        "stale_after": {"1h": 90},
        "degraded_after": {"1h": 180},
    },
    {
        "stream": "long_short_ratio",
        "model": DataLongShortRatio,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "expected_cadence": {"1h": 60},
        "stale_after": {"1h": 90},
        "degraded_after": {"1h": 180},
    },
    {
        "stream": "liquidations",
        "model": DataLiquidation,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "expected_cadence": {"1h": 60},
        "stale_after": {"1h": 180},
        "degraded_after": {"1h": 360},
        "sparse_event_stream": True,
        "sync_provider": "coinglass",
        "sync_type": "liquidations",
        "sync_stale_after": {"1h": CRON_EXPECTED_INTERVAL_MINUTES * 2},
        "sync_degraded_after": {"1h": CRON_EXPECTED_INTERVAL_MINUTES * 4},
    },
    {
        "stream": "basis_premium",
        "model": BasisPremium,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("snapshot",),
        "expected_cadence": {"snapshot": 15},
        "stale_after": {"snapshot": 45},
        "degraded_after": {"snapshot": 120},
    },
)

COVERAGE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "stream": "ohlcv",
        "model": DataOhlcv,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1m", "5m", "1h"),
        "expected_cadence": {"1m": 1, "5m": 5, "1h": 60},
    },
    {
        "stream": "funding_rates",
        "model": DataFundingRate,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("8h",),
        "expected_cadence": {"8h": 480},
    },
    {
        "stream": "open_interest",
        "model": DataOpenInterest,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "expected_cadence": {"1h": 60},
    },
    {
        "stream": "long_short_ratio",
        "model": DataLongShortRatio,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "expected_cadence": {"1h": 60},
    },
    {
        "stream": "liquidations",
        "model": DataLiquidation,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("1h",),
        "sparse_event_stream": True,
        "sync_provider": "coinglass",
        "sync_type": "liquidations",
    },
    {
        "stream": "basis_premium",
        "model": BasisPremium,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("snapshot",),
        "expected_cadence": {"snapshot": 15},
    },
    {
        "stream": "spot_perp_price",
        "model": BasisPremium,
        "exchange": PRIMARY_PERP_EXCHANGE,
        "intervals": ("snapshot",),
        "expected_cadence": {"snapshot": 15},
        "extra_filters": lambda: [BasisPremium.spot_price.isnot(None), BasisPremium.perp_price.isnot(None)],
    },
)


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _normalize_exchange(exchange: str) -> str:
    return exchange.strip().lower()


def _parse_symbols(symbols: Optional[str], default: tuple[str, ...] = WATCHED_SYMBOLS) -> tuple[str, ...]:
    if symbols is None or not symbols.strip():
        return default
    parsed = tuple(dict.fromkeys(item.strip().upper() for item in symbols.split(",") if item.strip()))
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="symbols must contain at least one symbol",
        )
    return parsed


def _validate_time_range(start: Optional[int], end: Optional[int]) -> None:
    if start is not None and end is not None and start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start must be less than or equal to end",
        )


def _fetch_time_series(query, model, start: Optional[int], end: Optional[int]) -> list[Any]:
    if start is not None:
        query = query.filter(model.timestamp >= start)
    if end is not None:
        query = query.filter(model.timestamp <= end)

    if start is None:
        rows = query.order_by(model.timestamp.desc()).limit(MAX_ROWS).all()
        return list(reversed(rows))

    return query.order_by(model.timestamp.asc()).limit(MAX_ROWS).all()


def _fetch_ohlcv_rows(
    db: Session,
    symbol: str,
    exchange: str,
    interval: str,
    start: int,
    end: int,
    limit: int,
) -> list[Any]:
    return (
        db.query(
            DataOhlcv.timestamp,
            DataOhlcv.symbol,
            DataOhlcv.exchange,
            DataOhlcv.interval,
            DataOhlcv.open,
            DataOhlcv.high,
            DataOhlcv.low,
            DataOhlcv.close,
            DataOhlcv.volume,
            DataOhlcv.quote_volume,
            DataOhlcv.trades_count,
        )
        .filter(
            func.upper(DataOhlcv.symbol) == symbol,
            func.lower(DataOhlcv.exchange) == exchange,
            DataOhlcv.interval == interval,
            DataOhlcv.timestamp >= start,
            DataOhlcv.timestamp <= end,
        )
        .order_by(DataOhlcv.timestamp.asc())
        .limit(limit)
        .all()
    )


def _serialize_ohlcv(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "interval": row.interval,
        "open": row.open,
        "high": row.high,
        "low": row.low,
        "close": row.close,
        "volume": row.volume,
        "quote_volume": row.quote_volume,
        "trades_count": row.trades_count,
    }


def _serialize_funding(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "funding_rate": row.funding_rate,
        "next_funding_time": row.next_funding_time,
        "interval": row.interval,
    }


def _serialize_open_interest(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "interval": row.interval,
        "oi_usd": row.oi_usd,
        "oi_coins": row.oi_coins,
    }


def _serialize_liquidation(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "side": row.side,
        "quantity": row.quantity,
        "price": row.price,
        "value_usd": row.value_usd,
    }


def _serialize_long_short_ratio(row: Any) -> dict[str, Any]:
    return {
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "interval": row.interval,
        "long_ratio": row.long_ratio,
        "short_ratio": row.short_ratio,
        "long_account_ratio": row.long_account_ratio,
        "short_account_ratio": row.short_account_ratio,
    }


def _serialize_basis_premium(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "timestamp": row.timestamp,
        "symbol": row.symbol,
        "exchange": row.exchange,
        "spot_price": row.spot_price,
        "perp_price": row.perp_price,
        "basis_pct": row.basis_pct,
        "premium_pct": row.premium_pct,
    }


def _latest_sync_from_runs(db: Session, provider_name: str) -> Optional[dict[str, Any]]:
    row = (
        db.query(ProviderSyncRun)
        .filter(func.lower(ProviderSyncRun.provider_name) == provider_name)
        .order_by(ProviderSyncRun.created_at.desc())
        .first()
    )
    if not row:
        return None

    return {
        "provider_name": row.provider_name,
        "sync_type": row.sync_type,
        "status": row.status,
        "last_sync_at": _iso(row.created_at),
        "records_fetched": row.records_fetched,
        "records_inserted": row.records_inserted,
        "error_message": row.error_message,
        "source_table": ProviderSyncRun.__tablename__,
    }


def _latest_sync_from_logs(db: Session, provider_name: str) -> Optional[dict[str, Any]]:
    row = (
        db.query(ProviderSyncLog)
        .filter(func.lower(ProviderSyncLog.provider_name) == provider_name)
        .order_by(ProviderSyncLog.created_at.desc())
        .first()
    )
    if not row:
        return None

    return {
        "provider_name": row.provider_name,
        "sync_type": row.sync_type,
        "status": row.status,
        "last_sync_at": _iso(row.created_at),
        "records_count": row.records_count,
        "response_time_ms": row.response_time_ms,
        "error_message": row.error_message,
        "source_table": ProviderSyncLog.__tablename__,
    }


def _latest_provider_sync(db: Session, provider_name: str) -> Optional[dict[str, Any]]:
    candidates = [
        sync
        for sync in (
            _latest_sync_from_runs(db, provider_name),
            _latest_sync_from_logs(db, provider_name),
        )
        if sync is not None
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda item: item.get("last_sync_at") or "")


def _provider_snapshot(db: Session, provider_name: str) -> dict[str, Any]:
    health = (
        db.query(ProviderHealth)
        .filter(func.lower(ProviderHealth.provider_name) == provider_name)
        .first()
    )
    last_sync = _latest_provider_sync(db, provider_name)

    if health:
        provider_status = health.status
        healthy = provider_status.lower() in {"healthy", "ok"}
    elif last_sync and last_sync.get("status") in {"success", "completed"}:
        provider_status = "healthy"
        healthy = True
    elif last_sync and last_sync.get("status") in {"failure", "failed", "partial"}:
        provider_status = "degraded"
        healthy = False
    else:
        provider_status = "unknown"
        healthy = False

    return {
        "provider_name": provider_name,
        "status": provider_status,
        "healthy": healthy,
        "last_success_at": _iso(health.last_success_at) if health else None,
        "last_failure_at": _iso(health.last_failure_at) if health else None,
        "last_error_message": health.last_error_message if health else None,
        "avg_response_ms": health.avg_response_ms if health else None,
        "failure_count_24h": health.failure_count_24h if health else 0,
        "updated_at": _iso(health.updated_at) if health else None,
        "last_sync": last_sync,
    }


def _milliseconds_now() -> int:
    return int(_utc_now().timestamp() * 1000)


def _age_minutes_from_ms(now_ms: int, timestamp_ms: Optional[int]) -> Optional[float]:
    if timestamp_ms is None:
        return None
    return max(0.0, round((now_ms - timestamp_ms) / 60_000, 2))


def _latest_timestamp(
    db: Session,
    model: Any,
    symbol: str,
    exchange: str,
    interval: Optional[str],
    extra_filters: Optional[list[Any]] = None,
) -> Optional[int]:
    query = db.query(func.max(model.timestamp)).filter(
        func.upper(model.symbol) == symbol,
        func.lower(model.exchange) == exchange,
    )
    if interval and interval != "snapshot" and hasattr(model, "interval"):
        query = query.filter(model.interval == interval)
    if extra_filters:
        query = query.filter(*extra_filters)
    return query.scalar()


def _freshness_status(age_minutes: Optional[float], stale_after: int, degraded_after: int) -> tuple[str, str]:
    if age_minutes is None:
        return "degraded", "no rows found for expected stream"
    if age_minutes <= stale_after:
        return "fresh", "within freshness SLA"
    if age_minutes <= degraded_after:
        return "stale", f"age exceeds stale SLA of {stale_after} minutes"
    return "degraded", f"age exceeds degraded SLA of {degraded_after} minutes"


def _age_minutes_from_datetime(now: datetime, value: Optional[datetime]) -> Optional[float]:
    if value is None:
        return None
    return max(0.0, round((now - value).total_seconds() / 60, 2))


def _latest_sync_run(
    db: Session,
    provider_name: str,
    sync_type: str,
    success_only: bool = False,
) -> Optional[ProviderSyncRun]:
    query = db.query(ProviderSyncRun).filter(
        func.lower(ProviderSyncRun.provider_name) == provider_name.lower(),
        func.lower(ProviderSyncRun.sync_type) == sync_type.lower(),
    )
    if success_only:
        query = query.filter(func.lower(ProviderSyncRun.status).in_(SYNC_SUCCESS_STATUSES))
    return query.order_by(ProviderSyncRun.created_at.desc()).first()


def _sparse_event_status(
    db: Session,
    spec: dict[str, Any],
    interval: str,
    event_status: str,
    event_reason: str,
    event_age_minutes: Optional[float],
    now: datetime,
) -> tuple[str, str, dict[str, Any]]:
    provider_name = spec["sync_provider"]
    sync_type = spec["sync_type"]
    latest_sync = _latest_sync_run(db, provider_name, sync_type)
    latest_successful_sync = _latest_sync_run(db, provider_name, sync_type, success_only=True)
    sync_age_minutes = _age_minutes_from_datetime(now, latest_sync.created_at if latest_sync else None)
    sync_stale_after = spec["sync_stale_after"][interval]
    sync_degraded_after = spec["sync_degraded_after"][interval]

    metadata = {
        "freshness_mode": "sparse_event",
        "event_age_minutes": event_age_minutes,
        "sync_provider": provider_name,
        "sync_type": sync_type,
        "latest_sync_status": (latest_sync.status if latest_sync else None),
        "latest_sync_at": _iso(latest_sync.created_at) if latest_sync else None,
        "latest_successful_sync_at": _iso(latest_successful_sync.created_at) if latest_successful_sync else None,
        "sync_age_minutes": sync_age_minutes,
        "sync_stale_after_minutes": sync_stale_after,
        "sync_degraded_after_minutes": sync_degraded_after,
    }

    if event_status == "fresh":
        return event_status, event_reason, metadata

    if latest_sync is None:
        return "degraded", f"{event_reason}; no {provider_name}/{sync_type} sync runs recorded", metadata

    latest_sync_status = (latest_sync.status or "").lower()
    if latest_sync_status not in SYNC_SUCCESS_STATUSES:
        return (
            "degraded",
            f"{event_reason}; latest {provider_name}/{sync_type} sync status is {latest_sync_status or 'unknown'}",
            metadata,
        )

    if sync_age_minutes is None:
        return "degraded", f"{event_reason}; latest {provider_name}/{sync_type} sync has no timestamp", metadata

    if sync_age_minutes <= sync_stale_after:
        return (
            "fresh",
            (
                "no recent liquidation events; "
                f"latest successful {provider_name}/{sync_type} sync is fresh ({sync_age_minutes}m ago)"
            ),
            metadata,
        )
    if sync_age_minutes <= sync_degraded_after:
        return (
            "stale",
            (
                "no recent liquidation events; "
                f"latest successful {provider_name}/{sync_type} sync is late ({sync_age_minutes}m ago)"
            ),
            metadata,
        )
    return (
        "degraded",
        (
            "no recent liquidation events; "
            f"latest successful {provider_name}/{sync_type} sync is outside SLA ({sync_age_minutes}m ago)"
        ),
        metadata,
    )


def _build_freshness_report(db: Session) -> dict[str, Any]:
    now = _utc_now()
    now_ms = _milliseconds_now()
    streams: list[dict[str, Any]] = []
    summary = {"fresh": 0, "stale": 0, "degraded": 0}
    by_stream: dict[str, dict[str, int]] = {}

    for spec in FRESHNESS_SPECS:
        stream_name = spec["stream"]
        stream_summary = {"fresh": 0, "stale": 0, "degraded": 0}
        for symbol in WATCHED_SYMBOLS:
            for interval in spec["intervals"]:
                latest_ts = _latest_timestamp(
                    db,
                    spec["model"],
                    symbol,
                    spec["exchange"],
                    interval,
                )
                age_minutes = _age_minutes_from_ms(now_ms, latest_ts)
                stale_after = spec["stale_after"][interval]
                degraded_after = spec["degraded_after"][interval]
                status_value, reason = _freshness_status(age_minutes, stale_after, degraded_after)
                extra_fields = {"freshness_mode": "event"}
                if spec.get("sparse_event_stream"):
                    status_value, reason, extra_fields = _sparse_event_status(
                        db,
                        spec,
                        interval,
                        status_value,
                        reason,
                        age_minutes,
                        now,
                    )
                summary[status_value] += 1
                stream_summary[status_value] += 1
                streams.append(
                    {
                        "symbol": symbol,
                        "exchange": spec["exchange"],
                        "stream": stream_name,
                        "interval": interval,
                        "latest_timestamp": latest_ts,
                        "latest_timestamp_iso": (
                            datetime.fromtimestamp(latest_ts / 1000, timezone.utc).replace(tzinfo=None).isoformat()
                            if latest_ts is not None
                            else None
                        ),
                        "age_minutes": age_minutes,
                        "expected_cadence_minutes": spec["expected_cadence"][interval],
                        "stale_after_minutes": stale_after,
                        "degraded_after_minutes": degraded_after,
                        "status": status_value,
                        "reason": reason,
                        **extra_fields,
                    }
                )
        by_stream[stream_name] = stream_summary

    total = sum(summary.values())
    if summary["degraded"]:
        worst_status = "degraded"
    elif summary["stale"]:
        worst_status = "stale"
    elif summary["fresh"]:
        worst_status = "fresh"
    else:
        worst_status = "unknown"

    return {
        "scope": {
            "symbols": list(WATCHED_SYMBOLS),
            "primary_exchange": PRIMARY_PERP_EXCHANGE,
            "streams": [spec["stream"] for spec in FRESHNESS_SPECS],
        },
        "summary": {
            **summary,
            "total": total,
            "worst_status": worst_status,
        },
        "by_stream": by_stream,
        "streams": streams,
    }


def _classify_sync_error(error_message: Optional[str]) -> Optional[str]:
    if not error_message:
        return None
    normalized = error_message.lower()
    if "451" in normalized:
        return "http_451"
    if "429" in normalized or "rate limit" in normalized or "too many requests" in normalized:
        return "rate_limit"
    if "circuit breaker" in normalized:
        return "circuit_breaker"
    if "no coinglass data returned" in normalized or "empty" in normalized or "no data" in normalized:
        return "empty_response"
    if "timeout" in normalized or "timed out" in normalized:
        return "timeout"
    if "connection" in normalized or "network" in normalized:
        return "network"
    return "provider_error"


def _serialize_sync_run(row: Optional[ProviderSyncRun]) -> Optional[dict[str, Any]]:
    if not row:
        return None
    return {
        "provider_name": row.provider_name,
        "sync_type": row.sync_type,
        "status": row.status,
        "last_sync_at": _iso(row.created_at),
        "start_time": row.start_time,
        "end_time": row.end_time,
        "records_fetched": row.records_fetched,
        "records_inserted": row.records_inserted,
        "error_message": row.error_message,
        "error_class": _classify_sync_error(row.error_message),
        "source_table": ProviderSyncRun.__tablename__,
    }


def _sync_status(last_run: Optional[ProviderSyncRun], age_minutes: Optional[float]) -> tuple[str, bool, str]:
    if not last_run:
        return "unknown", False, "no sync run recorded"
    raw_status = (last_run.status or "").lower()
    if raw_status in SYNC_SUCCESS_STATUSES and (age_minutes is None or age_minutes <= CRON_EXPECTED_INTERVAL_MINUTES * 2):
        return "healthy", True, "latest run completed within expected cron window"
    if raw_status in SYNC_SUCCESS_STATUSES:
        return "stale", False, "latest successful run is older than expected cron window"
    if raw_status in SYNC_DEGRADED_STATUSES:
        return "degraded", False, "latest run finished with errors or partial coverage"
    return "unknown", False, "latest run status is not recognized"


def _sync_health_by_type(db: Session) -> dict[str, dict[str, Any]]:
    now = _utc_now()
    rows = (
        db.query(ProviderSyncRun)
        .order_by(ProviderSyncRun.created_at.desc())
        .limit(1000)
        .all()
    )
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for row in rows:
        key = (row.provider_name.lower(), row.sync_type)
        bucket = grouped.setdefault(
            key,
            {
                "last_run": None,
                "last_successful_run": None,
                "last_problem_run": None,
                "recent_status_counts": {},
                "recent_error_classes": {},
            },
        )
        raw_status = (row.status or "unknown").lower()
        if bucket["last_run"] is None:
            bucket["last_run"] = row
        if raw_status in SYNC_SUCCESS_STATUSES and bucket["last_successful_run"] is None:
            bucket["last_successful_run"] = row
        if raw_status in SYNC_DEGRADED_STATUSES and bucket["last_problem_run"] is None:
            bucket["last_problem_run"] = row

        if row.created_at and row.created_at >= now - timedelta(hours=RECENT_SYNC_WINDOW_HOURS):
            bucket["recent_status_counts"][raw_status] = bucket["recent_status_counts"].get(raw_status, 0) + 1
            error_class = _classify_sync_error(row.error_message)
            if error_class:
                bucket["recent_error_classes"][error_class] = bucket["recent_error_classes"].get(error_class, 0) + 1

    result: dict[str, dict[str, Any]] = {}
    for (provider_name, sync_type), bucket in grouped.items():
        last_run = bucket["last_run"]
        age_minutes = None
        if last_run and last_run.created_at:
            age_minutes = max(0.0, round((now - last_run.created_at).total_seconds() / 60, 2))
        status_value, healthy, reason = _sync_status(last_run, age_minutes)
        result.setdefault(provider_name, {})[sync_type] = {
            "provider_name": provider_name,
            "sync_type": sync_type,
            "status": status_value,
            "healthy": healthy,
            "reason": reason,
            "last_run_age_minutes": age_minutes,
            "expected_cron_interval_minutes": CRON_EXPECTED_INTERVAL_MINUTES,
            "last_run": _serialize_sync_run(last_run),
            "last_successful_run": _serialize_sync_run(bucket["last_successful_run"]),
            "last_problem_run": _serialize_sync_run(bucket["last_problem_run"]),
            "recent_window_hours": RECENT_SYNC_WINDOW_HOURS,
            "recent_status_counts": bucket["recent_status_counts"],
            "recent_error_classes": bucket["recent_error_classes"],
        }

    return result


def _sync_diagnostics(db: Session) -> dict[str, Any]:
    now = _utc_now()
    window_start = now - timedelta(hours=RECENT_SYNC_WINDOW_HOURS)
    rows = (
        db.query(ProviderSyncRun)
        .filter(ProviderSyncRun.created_at >= window_start)
        .order_by(ProviderSyncRun.created_at.desc())
        .all()
    )
    last_run = rows[0] if rows else db.query(ProviderSyncRun).order_by(ProviderSyncRun.created_at.desc()).first()
    last_successful_run = next(
        (row for row in rows if (row.status or "").lower() in SYNC_SUCCESS_STATUSES),
        db.query(ProviderSyncRun)
        .filter(func.lower(ProviderSyncRun.status).in_(SYNC_SUCCESS_STATUSES))
        .order_by(ProviderSyncRun.created_at.desc())
        .first(),
    )

    status_counts: dict[str, int] = {}
    error_classes: dict[str, int] = {}
    for row in rows:
        raw_status = (row.status or "unknown").lower()
        status_counts[raw_status] = status_counts.get(raw_status, 0) + 1
        error_class = _classify_sync_error(row.error_message)
        if error_class:
            error_classes[error_class] = error_classes.get(error_class, 0) + 1

    last_run_age = None
    if last_run and last_run.created_at:
        last_run_age = max(0.0, round((now - last_run.created_at).total_seconds() / 60, 2))

    if last_run is None:
        cron_status = "unknown"
        cron_reason = "no provider sync runs recorded"
    elif (last_run.status or "").lower() not in SYNC_SUCCESS_STATUSES:
        cron_status = "degraded"
        cron_reason = "latest cron-path run is not fully completed"
    elif last_run_age is not None and last_run_age <= CRON_EXPECTED_INTERVAL_MINUTES * 2:
        cron_status = "healthy"
        cron_reason = "latest cron-path run is recent"
    elif last_run_age is not None and last_run_age <= CRON_EXPECTED_INTERVAL_MINUTES * 4:
        cron_status = "stale"
        cron_reason = "latest cron-path run is late"
    else:
        cron_status = "degraded"
        cron_reason = "latest cron-path run is outside SLA"

    return {
        "cron": {
            "status": cron_status,
            "reason": cron_reason,
            "expected_interval_minutes": CRON_EXPECTED_INTERVAL_MINUTES,
            "last_run_age_minutes": last_run_age,
            "last_run": _serialize_sync_run(last_run),
            "last_successful_run": _serialize_sync_run(last_successful_run),
        },
        "recent_window_hours": RECENT_SYNC_WINDOW_HOURS,
        "recent_runs": len(rows),
        "recent_status_counts": status_counts,
        "recent_error_classes": error_classes,
    }


def _timestamp_ms_to_iso(timestamp_ms: Optional[int]) -> Optional[str]:
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000, timezone.utc).replace(tzinfo=None).isoformat()


def _coverage_count(
    db: Session,
    model: Any,
    symbol: str,
    exchange: str,
    interval: str,
    start: int,
    end: int,
    extra_filters: Optional[list[Any]] = None,
) -> int:
    query = db.query(func.count()).select_from(model).filter(
        func.upper(model.symbol) == symbol,
        func.lower(model.exchange) == exchange,
        model.timestamp >= start,
        model.timestamp <= end,
    )
    if interval != "snapshot" and hasattr(model, "interval"):
        query = query.filter(model.interval == interval)
    if extra_filters:
        query = query.filter(*extra_filters)
    return query.scalar() or 0


def _coverage_status(rows: int, expected_rows: Optional[int]) -> tuple[str, Optional[float], str]:
    if expected_rows is None:
        if rows > 0:
            return "covered", None, "sparse stream has events inside the coverage window"
        return "missing", None, "sparse stream has no events inside the coverage window"

    if expected_rows <= 0:
        return "missing", 0.0, "coverage window is empty"

    coverage_pct = round(min(rows / expected_rows, 1.0) * 100, 2)
    if rows >= expected_rows * COVERAGE_MIN_RATIO:
        return "covered", coverage_pct, "row count meets expected cadence coverage"
    if rows > 0:
        return "partial", coverage_pct, "row count is below expected cadence coverage"
    return "missing", coverage_pct, "no rows found inside the coverage window"


def _sparse_coverage_status(
    db: Session,
    spec: dict[str, Any],
    rows: int,
    now: datetime,
) -> tuple[str, Optional[float], str, dict[str, Any]]:
    status_value, coverage_pct, reason = _coverage_status(rows, expected_rows=None)
    provider_name = spec["sync_provider"]
    sync_type = spec["sync_type"]
    latest_successful_sync = _latest_sync_run(db, provider_name, sync_type, success_only=True)
    sync_age_minutes = _age_minutes_from_datetime(now, latest_successful_sync.created_at if latest_successful_sync else None)
    extra_fields = {
        "coverage_mode": "sparse_event",
        "sync_provider": provider_name,
        "sync_type": sync_type,
        "latest_successful_sync_at": _iso(latest_successful_sync.created_at) if latest_successful_sync else None,
        "sync_age_minutes": sync_age_minutes,
    }

    if status_value == "covered":
        return status_value, coverage_pct, reason, extra_fields

    if latest_successful_sync and sync_age_minutes is not None and sync_age_minutes <= RECENT_SYNC_WINDOW_HOURS * 60:
        return (
            "covered",
            None,
            "sparse stream has no events; latest successful provider sync confirms coverage",
            extra_fields,
        )

    if latest_successful_sync:
        return (
            "partial",
            None,
            "sparse stream has no events and latest successful provider sync is outside the recent window",
            extra_fields,
        )

    return status_value, coverage_pct, reason, extra_fields


def _build_coverage_report(
    db: Session,
    symbols: tuple[str, ...] = WATCHED_SYMBOLS,
    exchange: str = PRIMARY_PERP_EXCHANGE,
    range_name: str = "7d",
) -> dict[str, Any]:
    normalized_exchange = _normalize_exchange(exchange)
    normalized_range = range_name.strip().lower()
    if normalized_range not in COVERAGE_RANGES_MS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported range; expected one of {', '.join(COVERAGE_RANGES_MS)}",
        )

    now = _utc_now()
    now_ms = int(now.timestamp() * 1000)
    range_ms = COVERAGE_RANGES_MS[normalized_range]
    rows: list[dict[str, Any]] = []
    summary = {"covered": 0, "partial": 0, "missing": 0}
    by_symbol: dict[str, dict[str, int]] = {}
    by_stream: dict[str, dict[str, int]] = {}

    for spec in COVERAGE_SPECS:
        stream_name = spec["stream"]
        model = spec["model"]
        extra_filters_factory = spec.get("extra_filters")
        extra_filters = extra_filters_factory() if callable(extra_filters_factory) else None
        for symbol in symbols:
            symbol_summary = by_symbol.setdefault(symbol, {"covered": 0, "partial": 0, "missing": 0})
            stream_summary = by_stream.setdefault(stream_name, {"covered": 0, "partial": 0, "missing": 0})
            for interval in spec["intervals"]:
                latest_ts = _latest_timestamp(db, model, symbol, normalized_exchange, interval, extra_filters)
                expected_rows: Optional[int] = None
                window_source = "latest_available"

                if spec.get("sparse_event_stream"):
                    end = now_ms
                    start = max(0, now_ms - range_ms + 1)
                    window_source = "wall_clock"
                elif latest_ts is None:
                    end = None
                    start = None
                else:
                    cadence_minutes = spec["expected_cadence"][interval]
                    cadence_ms = cadence_minutes * 60_000
                    expected_rows = max(1, range_ms // cadence_ms)
                    end = latest_ts
                    start = max(0, latest_ts - (expected_rows - 1) * cadence_ms)

                count = (
                    _coverage_count(db, model, symbol, normalized_exchange, interval, start, end, extra_filters)
                    if start is not None and end is not None
                    else 0
                )

                if spec.get("sparse_event_stream"):
                    status_value, coverage_pct, reason, extra_fields = _sparse_coverage_status(db, spec, count, now)
                else:
                    status_value, coverage_pct, reason = _coverage_status(count, expected_rows)
                    extra_fields = {"coverage_mode": "regular"}

                summary[status_value] += 1
                symbol_summary[status_value] += 1
                stream_summary[status_value] += 1
                rows.append(
                    {
                        "symbol": symbol,
                        "exchange": normalized_exchange,
                        "stream": stream_name,
                        "interval": interval,
                        "status": status_value,
                        "rows": count,
                        "expected_rows": expected_rows,
                        "coverage_pct": coverage_pct,
                        "window_start": start,
                        "window_end": end,
                        "window_start_iso": _timestamp_ms_to_iso(start),
                        "window_end_iso": _timestamp_ms_to_iso(end),
                        "latest_timestamp": latest_ts,
                        "latest_timestamp_iso": _timestamp_ms_to_iso(latest_ts),
                        "window_source": window_source,
                        "reason": reason,
                        **extra_fields,
                    }
                )

    total = sum(summary.values())
    if summary["missing"]:
        worst_status = "missing"
    elif summary["partial"]:
        worst_status = "partial"
    elif summary["covered"]:
        worst_status = "covered"
    else:
        worst_status = "unknown"

    return {
        "scope": {
            "symbols": list(symbols),
            "exchange": normalized_exchange,
            "range": normalized_range,
            "streams": [spec["stream"] for spec in COVERAGE_SPECS],
        },
        "summary": {
            **summary,
            "total": total,
            "coverage_pct": round((summary["covered"] / total) * 100, 2) if total else 0.0,
            "worst_status": worst_status,
        },
        "by_symbol": by_symbol,
        "by_stream": by_stream,
        "rows": rows,
    }


def _coverage_summary_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"covered": 0, "partial": 0, "missing": 0}
    for row in rows:
        status_value = row["status"]
        if status_value in summary:
            summary[status_value] += 1

    total = sum(summary.values())
    if summary["missing"]:
        worst_status = "missing"
    elif summary["partial"]:
        worst_status = "partial"
    elif summary["covered"]:
        worst_status = "covered"
    else:
        worst_status = "unknown"

    return {
        **summary,
        "total": total,
        "coverage_pct": round((summary["covered"] / total) * 100, 2) if total else 0.0,
        "worst_status": worst_status,
    }


def _freshness_summary_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {"fresh": 0, "stale": 0, "degraded": 0}
    for row in rows:
        status_value = row["status"]
        if status_value in summary:
            summary[status_value] += 1

    total = sum(summary.values())
    if summary["degraded"]:
        worst_status = "degraded"
    elif summary["stale"]:
        worst_status = "stale"
    elif summary["fresh"]:
        worst_status = "fresh"
    else:
        worst_status = "unknown"

    return {
        **summary,
        "total": total,
        "fresh_pct": round((summary["fresh"] / total) * 100, 2) if total else 0.0,
        "worst_status": worst_status,
    }


def _stream_interval_key(row: dict[str, Any]) -> str:
    return f"{row['stream']}:{row['interval']}"


def _universe_status(
    coverage_7d_rows: list[dict[str, Any]],
    freshness_rows: list[dict[str, Any]],
) -> tuple[str, bool, bool, str]:
    coverage_summary = _coverage_summary_for_rows(coverage_7d_rows)
    freshness_summary = _freshness_summary_for_rows(freshness_rows)
    chart_rows = [row for row in coverage_7d_rows if row["stream"] in UNIVERSE_CHART_STREAMS]
    chart_ready = bool(chart_rows) and all(row["status"] == "covered" for row in chart_rows)
    freshness_ready = bool(freshness_rows) and freshness_summary["worst_status"] == "fresh"
    complete_7d = coverage_summary["total"] > 0 and coverage_summary["covered"] == coverage_summary["total"]

    if complete_7d and freshness_ready:
        return "complete_history", chart_ready, True, "all tracked streams are covered for 7d and freshness is green"
    if chart_ready and coverage_summary["missing"] == 0 and freshness_ready:
        return (
            "core_perp_ready",
            chart_ready,
            False,
            "chart-critical streams are covered; some enrichment streams have partial 7d history",
        )
    if coverage_summary["missing"] == 0 and coverage_summary["total"] > 0:
        return "partial_history", chart_ready, False, "no streams are missing, but coverage or freshness is not fully ready"
    return "not_ready", chart_ready, False, "one or more tracked streams are missing"


def _build_universe_report(
    db: Session,
    symbols: tuple[str, ...] = WATCHED_SYMBOLS,
    exchange: str = PRIMARY_PERP_EXCHANGE,
    coverage_7d: Optional[dict[str, Any]] = None,
    freshness: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    normalized_exchange = _normalize_exchange(exchange)
    coverage_reports = {
        "24h": _build_coverage_report(db, symbols, normalized_exchange, "24h"),
        "7d": coverage_7d or _build_coverage_report(db, symbols, normalized_exchange, "7d"),
    }
    freshness_report = freshness or _build_freshness_report(db)
    freshness_rows = freshness_report.get("streams", [])

    symbol_rows: list[dict[str, Any]] = []
    summary = {
        "complete_history": 0,
        "core_perp_ready": 0,
        "partial_history": 0,
        "not_ready": 0,
        "chart_ready": 0,
        "total": 0,
    }

    for symbol in symbols:
        coverage_by_range = {
            range_name: [
                row
                for row in report["rows"]
                if row["symbol"] == symbol and row["exchange"] == normalized_exchange
            ]
            for range_name, report in coverage_reports.items()
        }
        symbol_freshness_rows = [
            row
            for row in freshness_rows
            if row["symbol"] == symbol and row["exchange"] == normalized_exchange
        ]
        status_value, chart_ready, complete_history, reason = _universe_status(
            coverage_by_range["7d"],
            symbol_freshness_rows,
        )
        if status_value in summary:
            summary[status_value] += 1
        if chart_ready:
            summary["chart_ready"] += 1
        summary["total"] += 1

        partial_7d = [
            _stream_interval_key(row)
            for row in coverage_by_range["7d"]
            if row["status"] == "partial"
        ]
        missing_7d = [
            _stream_interval_key(row)
            for row in coverage_by_range["7d"]
            if row["status"] == "missing"
        ]
        covered_7d = [
            _stream_interval_key(row)
            for row in coverage_by_range["7d"]
            if row["status"] == "covered"
        ]

        symbol_rows.append(
            {
                "symbol": symbol,
                "exchange": normalized_exchange,
                "status": status_value,
                "chart_ready": chart_ready,
                "complete_history": complete_history,
                "ui_visible": status_value in {"complete_history", "core_perp_ready"},
                "coverage": {
                    range_name: _coverage_summary_for_rows(rows)
                    for range_name, rows in coverage_by_range.items()
                },
                "freshness": _freshness_summary_for_rows(symbol_freshness_rows),
                "covered_streams_7d": covered_7d,
                "partial_streams_7d": partial_7d,
                "missing_streams_7d": missing_7d,
                "reason": reason,
            }
        )

    ui_universe = [
        row["symbol"]
        for row in symbol_rows
        if row["ui_visible"]
    ]
    deferred_symbols = [
        row["symbol"]
        for row in symbol_rows
        if not row["ui_visible"]
    ]

    return {
        "scope": {
            "symbols": list(symbols),
            "exchange": normalized_exchange,
            "ranges": list(UNIVERSE_RANGES),
            "primary_range": "7d",
        },
        "summary": summary,
        "policy": {
            "ui_universe": ui_universe,
            "deferred_symbols": deferred_symbols,
            "rule": (
                "show symbols in primary UI only when chart-critical streams are covered, "
                "freshness is green and no tracked stream is missing"
            ),
        },
        "symbols": symbol_rows,
    }


def _provider_inventory_action(symbol_row: dict[str, Any]) -> tuple[str, str]:
    if symbol_row["status"] in PROVIDER_INVENTORY_PROMOTION_STATUSES:
        return "ready_for_ui_review", "symbol already passes the production universe readiness rule"
    if symbol_row["missing_streams_7d"]:
        return "backfill_required", "one or more tracked 7d streams are missing in persisted data"
    if symbol_row["freshness"]["total"] == 0:
        return "freshness_tracking_required", "coverage exists, but freshness SLA is not tracked for this symbol yet"
    if symbol_row["partial_streams_7d"]:
        return "history_completion_required", "all streams exist, but some 7d windows are still partial"
    return "manual_review_required", "symbol does not match an automated inventory action"


def _build_provider_inventory_report(
    db: Session,
    symbols: tuple[str, ...] = PROVIDER_INVENTORY_SYMBOLS,
    exchange: str = PRIMARY_PERP_EXCHANGE,
) -> dict[str, Any]:
    normalized_exchange = _normalize_exchange(exchange)
    coverage_7d = _build_coverage_report(db, symbols, normalized_exchange, "7d")
    freshness = _build_freshness_report(db)
    universe = _build_universe_report(
        db,
        symbols=symbols,
        exchange=normalized_exchange,
        coverage_7d=coverage_7d,
        freshness=freshness,
    )

    summary = {
        "total": 0,
        "promotion_candidates": 0,
        "ready_for_ui_review": 0,
        "backfill_required": 0,
        "freshness_tracking_required": 0,
        "history_completion_required": 0,
        "manual_review_required": 0,
    }
    inventory_rows: list[dict[str, Any]] = []

    for symbol_row in universe["symbols"]:
        next_action, action_reason = _provider_inventory_action(symbol_row)
        promotion_candidate = symbol_row["status"] in PROVIDER_INVENTORY_PROMOTION_STATUSES
        summary["total"] += 1
        if promotion_candidate:
            summary["promotion_candidates"] += 1
        summary[next_action] += 1

        inventory_rows.append(
            {
                **symbol_row,
                "promotion_candidate": promotion_candidate,
                "next_action": next_action,
                "next_action_reason": action_reason,
                "freshness_tracked": symbol_row["freshness"]["total"] > 0,
            }
        )

    return {
        "scope": {
            "symbols": list(symbols),
            "exchange": normalized_exchange,
            "ranges": list(UNIVERSE_RANGES),
            "primary_range": "7d",
            "inventory_mode": "persisted_data_only",
            "external_provider_calls": False,
        },
        "summary": summary,
        "policy": {
            "promotion_candidates": [
                row["symbol"]
                for row in inventory_rows
                if row["promotion_candidate"]
            ],
            "deferred_symbols": [
                row["symbol"]
                for row in inventory_rows
                if not row["promotion_candidate"]
            ],
            "rule": (
                "candidate symbols can move to UI review only after production universe readiness "
                "passes on persisted coverage and freshness signals"
            ),
        },
        "symbols": inventory_rows,
        "coverage": {
            "7d": {
                "summary": coverage_7d["summary"],
                "by_symbol": coverage_7d["by_symbol"],
                "by_stream": coverage_7d["by_stream"],
            },
        },
        "notes": [
            "This endpoint is read-only and does not call OKX, CoinGlass, CoinGecko or legacy Binance.",
            "Symbols outside the current freshness scope remain blocked until sync and SLA tracking are added.",
        ],
    }


def _row_counts(db: Session) -> dict[str, int]:
    tables = {
        DataOhlcv.__tablename__: DataOhlcv,
        DataFundingRate.__tablename__: DataFundingRate,
        DataOpenInterest.__tablename__: DataOpenInterest,
        DataLiquidation.__tablename__: DataLiquidation,
        DataLongShortRatio.__tablename__: DataLongShortRatio,
        BasisPremium.__tablename__: BasisPremium,
        ProviderHealth.__tablename__: ProviderHealth,
        ProviderSyncRun.__tablename__: ProviderSyncRun,
        ProviderSyncLog.__tablename__: ProviderSyncLog,
        DataQualityLog.__tablename__: DataQualityLog,
    }
    return {
        table_name: db.query(func.count()).select_from(model).scalar() or 0
        for table_name, model in tables.items()
    }


def _quality_score(db: Session, row_counts: dict[str, int]) -> dict[str, Any]:
    window_start = _utc_now() - timedelta(hours=24)
    severity_rows = (
        db.query(DataQualityLog.severity, func.count(DataQualityLog.id))
        .filter(DataQualityLog.created_at >= window_start)
        .group_by(DataQualityLog.severity)
        .all()
    )
    severity_counts = {severity or "unknown": count for severity, count in severity_rows}

    market_rows = sum(
        row_counts.get(table_name, 0)
        for table_name in (
            DataOhlcv.__tablename__,
            DataFundingRate.__tablename__,
            DataOpenInterest.__tablename__,
            DataLiquidation.__tablename__,
            DataLongShortRatio.__tablename__,
        )
    )
    if market_rows == 0:
        score = 0.0
    else:
        penalty = (
            severity_counts.get("critical", 0) * 15
            + severity_counts.get("warning", 0) * 5
            + severity_counts.get("info", 0)
        )
        score = max(0.0, min(100.0, 100.0 - penalty))

    return {
        "score": score,
        "window_hours": 24,
        "severity_counts": severity_counts,
        "method": "100 minus recent quality-log penalties; score is 0 when no market data rows exist",
    }


@router.get("/ohlcv/window", response_model=ApiResponse)
async def get_ohlcv_window(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    interval: str = Query(..., min_length=1),
    range_: str = Query("24h", alias="range", min_length=1),
    end: Optional[int] = Query(None, ge=0, description="Optional inclusive right edge as Unix timestamp in milliseconds"),
    db: Session = Depends(get_db),
):
    """Read a bounded OHLCV window for interactive charts without client-side pagination."""
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)
    normalized_interval = interval.strip()
    normalized_range = range_.strip().lower()

    if normalized_interval not in OHLCV_INTERVAL_MS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported interval; expected one of {', '.join(OHLCV_INTERVAL_MS)}",
        )
    if normalized_range not in OHLCV_WINDOW_RANGES_MS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported range; expected one of {', '.join(OHLCV_WINDOW_RANGES_MS)}",
        )

    latest_ts = _latest_timestamp(db, DataOhlcv, normalized_symbol, normalized_exchange, normalized_interval)
    if latest_ts is None:
        return ApiResponse(
            data=[],
            meta={
                "count": 0,
                "limit": OHLCV_WINDOW_MAX_ROWS,
                "symbol": normalized_symbol,
                "exchange": normalized_exchange,
                "interval": normalized_interval,
                "range": normalized_range,
                "start": None,
                "end": end,
                "latest_timestamp": None,
                "window_source": "latest_available",
            },
        )

    effective_end = min(end, latest_ts) if end is not None else latest_ts
    step_ms = OHLCV_INTERVAL_MS[normalized_interval]
    start = max(0, effective_end - OHLCV_WINDOW_RANGES_MS[normalized_range] + step_ms)
    expected_rows = ((effective_end - start) // step_ms) + 1 if effective_end >= start else 0
    if expected_rows > OHLCV_WINDOW_MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"requested OHLCV window is too large; max rows is {OHLCV_WINDOW_MAX_ROWS}",
        )

    rows = _fetch_ohlcv_rows(
        db,
        normalized_symbol,
        normalized_exchange,
        normalized_interval,
        start,
        effective_end,
        OHLCV_WINDOW_MAX_ROWS,
    )
    return ApiResponse(
        data=[_serialize_ohlcv(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": OHLCV_WINDOW_MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "interval": normalized_interval,
            "range": normalized_range,
            "start": start,
            "end": effective_end,
            "latest_timestamp": latest_ts,
            "expected_rows": expected_rows,
            "window_source": "latest_available" if end is None else "requested_end",
        },
    )


@router.get("/ohlcv", response_model=ApiResponse)
async def get_ohlcv(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    interval: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    """Read OHLCV candles from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        DataOhlcv.timestamp,
        DataOhlcv.symbol,
        DataOhlcv.exchange,
        DataOhlcv.interval,
        DataOhlcv.open,
        DataOhlcv.high,
        DataOhlcv.low,
        DataOhlcv.close,
        DataOhlcv.volume,
        DataOhlcv.quote_volume,
        DataOhlcv.trades_count,
    ).filter(
        func.upper(DataOhlcv.symbol) == normalized_symbol,
        func.lower(DataOhlcv.exchange) == normalized_exchange,
    )
    if interval:
        query = query.filter(DataOhlcv.interval == interval.strip())

    rows = _fetch_time_series(query, DataOhlcv, start, end)
    return ApiResponse(
        data=[_serialize_ohlcv(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "interval": interval.strip() if interval else None,
            "start": start,
            "end": end,
        },
    )


@router.get("/funding", response_model=ApiResponse)
async def get_funding(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    db: Session = Depends(get_db),
):
    """Read funding-rate history from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        DataFundingRate.timestamp,
        DataFundingRate.symbol,
        DataFundingRate.exchange,
        DataFundingRate.funding_rate,
        DataFundingRate.next_funding_time,
        DataFundingRate.interval,
    ).filter(
        func.upper(DataFundingRate.symbol) == normalized_symbol,
        func.lower(DataFundingRate.exchange) == normalized_exchange,
    )

    rows = _fetch_time_series(query, DataFundingRate, start, end)
    return ApiResponse(
        data=[_serialize_funding(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "start": start,
            "end": end,
        },
    )


@router.get("/open-interest", response_model=ApiResponse)
async def get_open_interest(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    interval: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    """Read open-interest history from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        DataOpenInterest.timestamp,
        DataOpenInterest.symbol,
        DataOpenInterest.exchange,
        DataOpenInterest.interval,
        DataOpenInterest.oi_usd,
        DataOpenInterest.oi_coins,
    ).filter(
        func.upper(DataOpenInterest.symbol) == normalized_symbol,
        func.lower(DataOpenInterest.exchange) == normalized_exchange,
    )
    if interval:
        query = query.filter(DataOpenInterest.interval == interval.strip())

    rows = _fetch_time_series(query, DataOpenInterest, start, end)
    return ApiResponse(
        data=[_serialize_open_interest(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "interval": interval.strip() if interval else None,
            "start": start,
            "end": end,
        },
    )


@router.get("/liquidations", response_model=ApiResponse)
async def get_liquidations(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    side: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    """Read liquidation history from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        DataLiquidation.timestamp,
        DataLiquidation.symbol,
        DataLiquidation.exchange,
        DataLiquidation.side,
        DataLiquidation.quantity,
        DataLiquidation.price,
        DataLiquidation.value_usd,
    ).filter(
        func.upper(DataLiquidation.symbol) == normalized_symbol,
        func.lower(DataLiquidation.exchange) == normalized_exchange,
    )
    if side:
        query = query.filter(func.lower(DataLiquidation.side) == side.strip().lower())

    rows = _fetch_time_series(query, DataLiquidation, start, end)
    return ApiResponse(
        data=[_serialize_liquidation(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "side": side.strip().lower() if side else None,
            "start": start,
            "end": end,
        },
    )


@router.get("/long-short-ratio", response_model=ApiResponse)
async def get_long_short_ratio(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    interval: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
):
    """Read long/short account ratio history from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        DataLongShortRatio.timestamp,
        DataLongShortRatio.symbol,
        DataLongShortRatio.exchange,
        DataLongShortRatio.interval,
        DataLongShortRatio.long_ratio,
        DataLongShortRatio.short_ratio,
        DataLongShortRatio.long_account_ratio,
        DataLongShortRatio.short_account_ratio,
    ).filter(
        func.upper(DataLongShortRatio.symbol) == normalized_symbol,
        func.lower(DataLongShortRatio.exchange) == normalized_exchange,
    )
    if interval:
        query = query.filter(DataLongShortRatio.interval == interval.strip())

    rows = _fetch_time_series(query, DataLongShortRatio, start, end)
    return ApiResponse(
        data=[_serialize_long_short_ratio(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "interval": interval.strip() if interval else None,
            "start": start,
            "end": end,
        },
    )


@router.get("/basis-premium", response_model=ApiResponse)
async def get_basis_premium(
    symbol: str = Query(..., min_length=1),
    exchange: str = Query(..., min_length=1),
    start: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    end: Optional[int] = Query(None, ge=0, description="Inclusive Unix timestamp in milliseconds"),
    db: Session = Depends(get_db),
):
    """Read spot/perp basis snapshots from the configured database. Limit is fixed at 1000 rows."""
    _validate_time_range(start, end)
    normalized_symbol = _normalize_symbol(symbol)
    normalized_exchange = _normalize_exchange(exchange)

    query = db.query(
        BasisPremium.id,
        BasisPremium.timestamp,
        BasisPremium.symbol,
        BasisPremium.exchange,
        BasisPremium.spot_price,
        BasisPremium.perp_price,
        BasisPremium.basis_pct,
        BasisPremium.premium_pct,
    ).filter(
        func.upper(BasisPremium.symbol) == normalized_symbol,
        func.lower(BasisPremium.exchange) == normalized_exchange,
    )

    rows = _fetch_time_series(query, BasisPremium, start, end)
    return ApiResponse(
        data=[_serialize_basis_premium(row) for row in rows],
        meta={
            "count": len(rows),
            "limit": MAX_ROWS,
            "symbol": normalized_symbol,
            "exchange": normalized_exchange,
            "start": start,
            "end": end,
        },
    )


@router.get("/coverage", response_model=ApiResponse)
async def get_data_coverage(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols; defaults to watched MVP symbols"),
    exchange: str = Query(PRIMARY_PERP_EXCHANGE, min_length=1),
    range_: str = Query("7d", alias="range", min_length=1),
    db: Session = Depends(get_db),
):
    """Inventory historical data coverage by symbol, stream and interval."""
    report = _build_coverage_report(
        db,
        symbols=_parse_symbols(symbols),
        exchange=exchange,
        range_name=range_,
    )
    return ApiResponse(
        data=report,
        meta={
            "timestamp": _utc_now().isoformat(),
            "read_only": True,
        },
    )


@router.get("/universe", response_model=ApiResponse)
async def get_data_universe(
    symbols: Optional[str] = Query(None, description="Comma-separated canonical symbols; defaults to watched MVP symbols"),
    exchange: str = Query(PRIMARY_PERP_EXCHANGE, min_length=1),
    db: Session = Depends(get_db),
):
    """Classify production universe readiness from coverage and freshness signals."""
    report = _build_universe_report(
        db,
        symbols=_parse_symbols(symbols),
        exchange=exchange,
    )
    return ApiResponse(
        data=report,
        meta={
            "timestamp": _utc_now().isoformat(),
            "read_only": True,
        },
    )


@router.get("/provider-inventory", response_model=ApiResponse)
async def get_provider_inventory(
    symbols: Optional[str] = Query(
        None,
        description="Comma-separated canonical symbols; defaults to MVP1 expansion candidates",
    ),
    exchange: str = Query(PRIMARY_PERP_EXCHANGE, min_length=1),
    db: Session = Depends(get_db),
):
    """Inventory expansion candidates from persisted coverage and freshness signals."""
    report = _build_provider_inventory_report(
        db,
        symbols=_parse_symbols(symbols, default=PROVIDER_INVENTORY_SYMBOLS),
        exchange=exchange,
    )
    return ApiResponse(
        data=report,
        meta={
            "timestamp": _utc_now().isoformat(),
            "read_only": True,
        },
    )


@router.get("/health", response_model=ApiResponse)
async def get_data_health(db: Session = Depends(get_db)):
    """Summarize local data-layer health without calling external providers."""
    counts = _row_counts(db)
    freshness = _build_freshness_report(db)
    coverage = _build_coverage_report(db)
    universe = _build_universe_report(db, coverage_7d=coverage, freshness=freshness)
    providers = {
        provider_name: _provider_snapshot(db, provider_name)
        for provider_name in WATCHED_PROVIDERS
    }
    last_sync = {
        provider_name: providers[provider_name]["last_sync"]
        for provider_name in WATCHED_PROVIDERS
    }

    return ApiResponse(
        data={
            "providers": providers,
            "last_sync": last_sync,
            "row_counts": counts,
            "data_quality": _quality_score(db, counts),
            "freshness": freshness,
            "coverage": coverage,
            "universe": universe,
            "sync_health_by_type": _sync_health_by_type(db),
            "sync_diagnostics": _sync_diagnostics(db),
        },
        meta={
            "timestamp": _utc_now().isoformat(),
            "read_only": True,
        },
    )
