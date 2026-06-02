"""Data Quality API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.persistence.database import get_db
from app.backtest.quality_monitor import DataQualityMonitor
from app.domain.models import OHLCV

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/health")
async def data_health(db: Session = Depends(get_db)):
    """GET /api/v1/data/health

    Возвращает полный отчёт о качестве данных для всех токенов.
    """
    monitor = DataQualityMonitor(db)
    reports = monitor.run_all_checks()

    overall_status = (
        "healthy" if all(r.overall_score >= 80 for r in reports) else "degraded"
    )

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "reports": [
            {
                "symbol": r.symbol,
                "exchange": r.exchange,
                "overall_score": r.overall_score,
                "ohlcv_score": r.ohlcv_score,
                "funding_score": r.funding_score,
                "gaps_count": len(r.gaps),
                "warnings": r.warnings,
                "backtest_ready": r.is_backtest_ready(),
            }
            for r in reports
        ],
    }


@router.get("/quality/{symbol}")
async def data_quality_symbol(symbol: str, db: Session = Depends(get_db)):
    """GET /api/v1/data/quality/{symbol}

    Возвращает quality score для конкретного токена.
    """
    monitor = DataQualityMonitor(db)
    score = monitor.get_quality_score(symbol, "binance")
    gaps = monitor.check_ohlcv_gaps(symbol, "binance")
    is_stale = monitor.check_stale_data(
        OHLCV, symbol, "binance", max_age_min=15, interval="1m"
    )

    return {
        "symbol": symbol,
        "score": score,
        "gaps_found": len(gaps),
        "is_stale": is_stale,
        "backtest_ready": score >= 80,
    }
