"""Pre-backtest Quality Gate.

Проверяет данные ПЕРЕД запуском бэктеста.
Если данные плохие — бэктест не запускаем.
"""

from typing import List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.backtest.config import BacktestConfig
from app.backtest.quality_monitor import DataQualityMonitor
from app.domain.models import FundingRate, OHLCV


def pre_backtest_gate(db: Session, config: BacktestConfig) -> Tuple[bool, List[str]]:
    """Проверяет качество данных перед запуском backtest.

    Args:
        db: SQLAlchemy session
        config: BacktestConfig с параметрами backtest

    Returns:
        (can_run, warnings)
        - can_run=True: можно запускать (возможно с warnings)
        - can_run=False: данные непригодны
        - warnings: список предупреждений для пользователя

    Проверки:
        1. OHLCV coverage > 95% за запрошенный период
        2. Funding data coverage > 90%
        3. Нет gaps > 60 минут
        4. Данные не stale (MAX(timestamp) < 1 час назад)
        5. Достаточно данных (> 1000 баров)
    """
    monitor = DataQualityMonitor(db)
    warnings: List[str] = []
    can_run = True

    # 1. OHLCV coverage
    ohlcv_coverage = monitor.check_coverage(
        config.symbol, config.exchange, config.start_ms, config.end_ms
    )
    if ohlcv_coverage < 0.95:
        warnings.append(
            f"OHLCV coverage is {ohlcv_coverage * 100:.1f}% (minimum 95%)"
        )
        can_run = False
    elif ohlcv_coverage < 0.98:
        warnings.append(
            f"OHLCV coverage is {ohlcv_coverage * 100:.1f}% (optimal > 98%)"
        )

    # 2. Funding coverage
    funding_coverage = _check_funding_coverage(db, config)
    if funding_coverage < 0.90:
        warnings.append(
            f"Funding data coverage is {funding_coverage * 100:.1f}% (minimum 90%)"
        )
        can_run = False

    # 3. Gaps
    gaps = monitor.check_ohlcv_gaps(config.symbol, config.exchange, max_gap_min=60)
    if gaps:
        total_gap_min = sum(g.duration_min for g in gaps)
        warnings.append(
            f"Found {len(gaps)} gaps > 60 min (total: {total_gap_min} min)"
        )
        if total_gap_min > 120:
            can_run = False

    # 4. Stale data
    if monitor.check_stale_data(
        OHLCV, config.symbol, config.exchange, max_age_min=60, interval="1m"
    ):
        warnings.append("OHLCV data is stale (> 1 hour old)")
        can_run = False

    # 5. Minimum bars
    total_minutes = (config.end_ms - config.start_ms) // 60_000
    if total_minutes < 1000:
        warnings.append(
            f"Backtest period too short: {total_minutes} minutes (minimum 1000)"
        )
        can_run = False

    # Quality score
    score = monitor.get_quality_score(config.symbol, config.exchange)
    if score < 50:
        warnings.append(f"Data quality score is {score}/100 (critical)")
        can_run = False
    elif score < 80:
        warnings.append(f"Data quality score is {score}/100 (below optimal)")

    return can_run, warnings


def _check_funding_coverage(db: Session, config: BacktestConfig) -> float:
    """Вспомогательная: coverage funding data."""
    total_hours = (config.end_ms - config.start_ms) // 3_600_000
    if total_hours <= 0:
        return 0.0

    count = (
        db.query(func.count(FundingRate.timestamp))
        .filter(FundingRate.symbol == config.symbol)
        .filter(FundingRate.exchange == config.exchange)
        .filter(FundingRate.timestamp >= config.start_ms)
        .filter(FundingRate.timestamp <= config.end_ms)
        .scalar()
    )

    # Ожидаем 3 funding events per day для CEX (8h intervals)
    expected = total_hours / 8
    return min(count / expected, 1.0) if expected > 0 else 0.0
