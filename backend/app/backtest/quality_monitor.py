"""Data Quality Monitor для DeltaGrid.

Проверяет данные перед backtest: gaps, stale data, coverage.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Type

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models import (
    DataQualityLog,
    FundingRate,
    OHLCV,
    ProviderSyncRun,
)


@dataclass
class Gap:
    """Описание разрыва в данных."""

    symbol: str
    exchange: str
    start_ms: int           # начало gap
    end_ms: int             # конец gap
    expected_candles: int   # сколько должно было быть
    actual_candles: int     # сколько реально
    duration_min: int       # длительность gap в минутах


@dataclass
class QualityReport:
    """Полный отчёт о качестве данных."""

    symbol: str
    exchange: str
    ohlcv_score: int = 0        # 0-100
    funding_score: int = 0      # 0-100
    overall_score: int = 0      # 0-100 (weighted average)
    gaps: List[Gap] = field(default_factory=list)
    stale_metrics: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def is_backtest_ready(self) -> bool:
        """True если данные достаточно хороши для backtest."""
        return self.overall_score >= 80


class DataQualityMonitor:
    """Монитор качества данных."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def check_ohlcv_gaps(
        self,
        symbol: str,
        exchange: str,
        max_gap_min: int = 5,
    ) -> List[Gap]:
        """Находит разрывы в OHLCV данных.

        Алгоритм:
        1. Загружает все timestamps для symbol+exchange, сортирует
        2. Вычисляет diff между соседними timestamps
        3. Если diff > max_gap_min * 60000 ms → это gap
        4. Возвращает список Gap объектов
        """
        rows = (
            self.db.query(OHLCV.timestamp)
            .filter(OHLCV.symbol == symbol)
            .filter(OHLCV.exchange == exchange)
            .filter(OHLCV.interval == "1m")
            .order_by(OHLCV.timestamp)
            .all()
        )

        if len(rows) < 2:
            return []

        timestamps = [r[0] for r in rows]
        gaps = []
        expected_diff = 60_000  # 1 минута

        for i in range(1, len(timestamps)):
            diff_ms = timestamps[i] - timestamps[i - 1]

            if diff_ms > max_gap_min * expected_diff:
                gap_min = (diff_ms - expected_diff) // 60_000
                gaps.append(
                    Gap(
                        symbol=symbol,
                        exchange=exchange,
                        start_ms=timestamps[i - 1] + expected_diff,
                        end_ms=timestamps[i],
                        expected_candles=diff_ms // expected_diff,
                        actual_candles=1,
                        duration_min=int(gap_min),
                    )
                )

        return gaps

    def check_stale_data(
        self,
        model_class: Type,
        symbol: str,
        exchange: str,
        max_age_min: int = 15,
        interval: Optional[str] = None,
    ) -> bool:
        """Проверяет что данные не устарели.

        Args:
            model_class: SQLAlchemy model (OHLCV, FundingRate, etc.)
            symbol: Canonical symbol
            exchange: Exchange name
            max_age_min: максимальный допустимый возраст в минутах
            interval: Optional interval filter for OHLCV/OpenInterest/LongShortRatio

        Returns:
            True если данные stale (устарели)
        """
        query = (
            self.db.query(model_class)
            .filter(model_class.symbol == symbol)
            .filter(model_class.exchange == exchange)
        )
        if interval is not None and hasattr(model_class, "interval"):
            query = query.filter(model_class.interval == interval)

        last_row = query.order_by(model_class.timestamp.desc()).first()

        if not last_row:
            return True  # нет данных = stale

        now_ms = int(datetime.utcnow().timestamp() * 1000)
        age_min = (now_ms - last_row.timestamp) // 60_000

        return age_min > max_age_min

    def check_coverage(
        self,
        symbol: str,
        exchange: str,
        start_ms: int,
        end_ms: int,
    ) -> float:
        """Вычисляет процент покрытия OHLCV данных за период.

        Returns:
            float 0.0-1.0 — доля минут, для которых есть данные
        """
        total_minutes = (end_ms - start_ms) // 60_000
        if total_minutes <= 0:
            return 0.0

        count = (
            self.db.query(func.count(OHLCV.timestamp))
            .filter(OHLCV.symbol == symbol)
            .filter(OHLCV.exchange == exchange)
            .filter(OHLCV.interval == "1m")
            .filter(OHLCV.timestamp >= start_ms)
            .filter(OHLCV.timestamp <= end_ms)
            .scalar()
        )

        return min(count / total_minutes, 1.0)

    def get_quality_score(self, symbol: str, exchange: str) -> int:
        """Вычисляет агрегированный quality score (0-100).

        Алгоритм:
        - Начинаем с 100
        - -20 за каждый gap > 60 минут
        - -30 если данные stale (> 1 час)
        - -10 если coverage < 95%
        - -5 за каждый gap 5-60 минут
        """
        score = 100

        # Gaps
        gaps = self.check_ohlcv_gaps(symbol, exchange, max_gap_min=5)
        for gap in gaps:
            if gap.duration_min > 60:
                score -= 20
            else:
                score -= 5

        # Stale OHLCV
        if self.check_stale_data(OHLCV, symbol, exchange, max_age_min=60, interval="1m"):
            score -= 30

        # Coverage (последние 7 дней)
        now_ms = int(datetime.utcnow().timestamp() * 1000)
        week_ms = now_ms - (7 * 24 * 3600 * 1000)
        coverage = self.check_coverage(symbol, exchange, week_ms, now_ms)
        if coverage < 0.95:
            score -= 10

        return max(score, 0)

    def run_all_checks(self) -> List[QualityReport]:
        """Запускает все проверки для всех токенов.

        Пишет результаты в data_quality_logs.
        Возвращает список QualityReport (по одному на токен).
        """
        symbols = ["BTC", "ETH", "SOL", "HYPE"]
        exchange = "binance"
        reports = []

        for symbol in symbols:
            report = QualityReport(symbol=symbol, exchange=exchange)

            # OHLCV checks
            report.gaps = self.check_ohlcv_gaps(symbol, exchange)
            ohlcv_score = self.get_quality_score(symbol, exchange)
            report.ohlcv_score = ohlcv_score

            # Funding checks
            funding_stale = self.check_stale_data(
                FundingRate, symbol, exchange, max_age_min=60
            )
            report.funding_score = 70 if funding_stale else 95

            # Overall
            report.overall_score = int(ohlcv_score * 0.7 + report.funding_score * 0.3)

            # Warnings
            if report.gaps:
                report.warnings.append(f"Found {len(report.gaps)} OHLCV gaps")
            if funding_stale:
                report.warnings.append("Funding data is stale")
            if report.overall_score < 80:
                report.warnings.append("Data quality below threshold for backtest")

            # Log to database
            self._log_quality_check(report)

            reports.append(report)

        return reports

    def _log_quality_check(self, report: QualityReport) -> None:
        """Пишет результаты проверки в data_quality_logs."""
        status = "ok" if report.overall_score >= 80 else "warning"
        details = "; ".join(report.warnings) if report.warnings else "All checks passed"

        log = DataQualityLog(
            table_name="ohlcv",
            check_type="aggregate",
            severity=status,
            symbol=report.symbol,
            exchange=report.exchange,
            interval="1m",
            expected_count=100,
            actual_count=report.overall_score,
            details_json=f'{{"score": {report.overall_score}, "ohlcv_score": {report.ohlcv_score}, "funding_score": {report.funding_score}, "details": "{details}"}}',
        )
        self.db.add(log)
        self.db.commit()
