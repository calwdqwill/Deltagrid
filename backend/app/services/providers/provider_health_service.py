"""Provider health monitoring service.

Tracks uptime, latency, and error rates for all external data providers.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import ProviderHealth, ProviderSyncLog

logger = logging.getLogger(__name__)


class ProviderHealthService:
    """Monitor and record provider health status."""

    def __init__(self, db: Session):
        self.db = db

    def record_success(self, provider_name: str, response_time_ms: int, records_count: Optional[int] = None) -> None:
        """Record a successful provider sync."""
        self._update_health(provider_name, status="healthy", response_time_ms=response_time_ms)
        self._add_sync_log(provider_name, "fetch", "success", response_time_ms, records_count)
        self.db.commit()

    def record_failure(self, provider_name: str, error_message: str) -> None:
        """Record a failed provider sync."""
        self._update_health(provider_name, status="degraded", error_message=error_message)
        self._add_sync_log(provider_name, "fetch", "failure", error_message=error_message)
        self.db.commit()

    def get_health(self, provider_name: Optional[str] = None) -> list[dict]:
        """Get health status for one or all providers."""
        query = self.db.query(ProviderHealth)
        if provider_name:
            query = query.filter(ProviderHealth.provider_name == provider_name)
        rows = query.all()
        return [
            {
                "provider_name": r.provider_name,
                "status": r.status,
                "last_success_at": r.last_success_at.isoformat() if r.last_success_at else None,
                "last_failure_at": r.last_failure_at.isoformat() if r.last_failure_at else None,
                "last_error_message": r.last_error_message,
                "avg_response_ms": r.avg_response_ms,
                "failure_count_24h": r.failure_count_24h,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]

    def _update_health(
        self,
        provider_name: str,
        status: str,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        health = self.db.query(ProviderHealth).filter(ProviderHealth.provider_name == provider_name).first()
        if not health:
            health = ProviderHealth(provider_name=provider_name, status=status)
            self.db.add(health)

        if status == "healthy":
            health.last_success_at = datetime.utcnow()
            health.status = "healthy"
        else:
            health.last_failure_at = datetime.utcnow()
            health.status = "degraded"
            health.failure_count_24h = (health.failure_count_24h or 0) + 1

        if response_time_ms is not None:
            # Simple rolling average
            if health.avg_response_ms:
                health.avg_response_ms = int((health.avg_response_ms + response_time_ms) / 2)
            else:
                health.avg_response_ms = response_time_ms

        if error_message:
            health.last_error_message = error_message

    def _add_sync_log(
        self,
        provider_name: str,
        sync_type: str,
        status: str,
        response_time_ms: Optional[int] = None,
        records_count: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        log = ProviderSyncLog(
            provider_name=provider_name,
            sync_type=sync_type,
            status=status,
            response_time_ms=response_time_ms,
            records_count=records_count,
            error_message=error_message,
        )
        self.db.add(log)
