"""APScheduler для фоновых задач DeltaGrid.

Запускается при старте FastAPI.
"""

import asyncio
import logging
import os
import sys

# Ensure backend/ is on path for script imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def job_incremental_ohlcv():
    """Обновление OHLCV каждые 5 минут."""
    try:
        from scripts.incremental_update import incremental_update_ohlcv

        await incremental_update_ohlcv()
        logger.info("Incremental OHLCV update completed")
    except Exception as e:
        logger.error(f"Incremental OHLCV failed: {e}")


async def job_incremental_coinglass():
    """Обновление CoinGlass данных каждые 5 минут."""
    try:
        from scripts.incremental_update import incremental_update_coinglass

        await incremental_update_coinglass()
        logger.info("Incremental CoinGlass update completed")
    except Exception as e:
        logger.error(f"Incremental CoinGlass failed: {e}")


async def job_quality_check():
    """Проверка качества данных каждые 15 минут."""
    try:
        from app.persistence.database import SessionLocal
        from app.backtest.quality_monitor import DataQualityMonitor

        db = SessionLocal()
        monitor = DataQualityMonitor(db)
        reports = monitor.run_all_checks()
        for r in reports:
            logger.info(f"Quality {r.symbol}: {r.overall_score}/100")
        db.close()
    except Exception as e:
        logger.error(f"Quality check failed: {e}")


def start_scheduler():
    """Запускает все scheduled jobs."""
    scheduler.add_job(
        job_incremental_ohlcv,
        IntervalTrigger(minutes=5),
        id="ohlcv_update",
        name="OHLCV Incremental Update",
        replace_existing=True,
    )
    scheduler.add_job(
        job_incremental_coinglass,
        IntervalTrigger(minutes=5),
        id="coinglass_update",
        name="CoinGlass Incremental Update",
        replace_existing=True,
    )
    scheduler.add_job(
        job_quality_check,
        IntervalTrigger(minutes=15),
        id="quality_check",
        name="Data Quality Check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with 3 jobs")


def shutdown_scheduler():
    """Останавливает scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
