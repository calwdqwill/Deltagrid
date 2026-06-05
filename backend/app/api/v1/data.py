from datetime import datetime, timedelta
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
WATCHED_PROVIDERS = ("binance", "coinglass", "coingecko")


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def _normalize_exchange(exchange: str) -> str:
    return exchange.strip().lower()


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
    window_start = datetime.utcnow() - timedelta(hours=24)
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


@router.get("/health", response_model=ApiResponse)
async def get_data_health(db: Session = Depends(get_db)):
    """Summarize local data-layer health without calling external providers."""
    counts = _row_counts(db)
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
        },
        meta={
            "timestamp": datetime.utcnow().isoformat(),
            "read_only": True,
        },
    )
