"""Alert engine service: rule evaluation, deduplication, event creation.

Isolated bounded context — no direct UI or scanner logic.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import AlertRule, AlertEvent, AlertDelivery, NotificationPreference

logger = logging.getLogger(__name__)


class AlertService:
    """CRUD alert rules and evaluate them against market/execution events."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Alert Rules CRUD
    # ------------------------------------------------------------------

    def list_rules(self, user_id: str) -> list[AlertRule]:
        return (
            self.db.query(AlertRule)
            .filter(AlertRule.user_id == user_id)
            .order_by(AlertRule.created_at.desc())
            .all()
        )

    def get_rule(self, rule_id: str, user_id: str) -> Optional[AlertRule]:
        return (
            self.db.query(AlertRule)
            .filter(AlertRule.id == rule_id, AlertRule.user_id == user_id)
            .first()
        )

    def create_rule(
        self,
        user_id: str,
        name: str,
        rule_type: str,
        symbol: Optional[str] = None,
        threshold_value: Optional[float] = None,
        comparison: str = "gte",
        cooldown_minutes: int = 60,
        severity: str = "info",
        channels: Optional[list[str]] = None,
    ) -> AlertRule:
        rule = AlertRule(
            user_id=user_id,
            name=name,
            rule_type=rule_type,
            symbol=symbol,
            threshold_value=threshold_value,
            comparison=comparison,
            cooldown_minutes=cooldown_minutes,
            severity=severity,
            channels_json=json.dumps(channels or ["email"]),
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, rule_id: str, user_id: str, **kwargs) -> Optional[AlertRule]:
        rule = self.get_rule(rule_id, user_id)
        if not rule:
            return None
        for key, value in kwargs.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def toggle_rule(self, rule_id: str, user_id: str) -> Optional[AlertRule]:
        rule = self.get_rule(rule_id, user_id)
        if not rule:
            return None
        rule.is_active = not rule.is_active
        self.db.commit()
        return rule

    def delete_rule(self, rule_id: str, user_id: str) -> bool:
        rule = self.get_rule(rule_id, user_id)
        if not rule:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Event Evaluation & Deduplication
    # ------------------------------------------------------------------

    def evaluate_and_create(
        self,
        user_id: str,
        alert_type: str,
        symbol: Optional[str],
        current_value: float,
        message: str,
        severity: str = "info",
    ) -> Optional[AlertEvent]:
        """Evaluate active rules and create alert event if any match."""
        rules = (
            self.db.query(AlertRule)
            .filter(
                AlertRule.user_id == user_id,
                AlertRule.is_active == True,
                AlertRule.rule_type == alert_type,
            )
            .all()
        )

        for rule in rules:
            if rule.symbol and rule.symbol != symbol:
                continue
            if rule.threshold_value is not None:
                if not self._compare(current_value, float(rule.threshold_value), rule.comparison):
                    continue

            # Deduplication: check cooldown
            if self._is_in_cooldown(rule.id, rule.cooldown_minutes):
                continue

            event = self._create_event(rule, symbol, message, severity)
            return event

        return None

    def list_events(self, user_id: str, limit: int = 50) -> list[AlertEvent]:
        return (
            self.db.query(AlertEvent)
            .filter(AlertEvent.user_id == user_id)
            .order_by(AlertEvent.triggered_at.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _compare(self, value: float, threshold: float, comparison: str) -> bool:
        if comparison == "gte":
            return value >= threshold
        if comparison == "lte":
            return value <= threshold
        if comparison == "eq":
            return value == threshold
        if comparison == "pct_change":
            return abs(value) >= threshold
        return False

    def _is_in_cooldown(self, rule_id: str, cooldown_minutes: int) -> bool:
        since = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
        recent = (
            self.db.query(AlertEvent)
            .filter(AlertEvent.rule_id == rule_id, AlertEvent.triggered_at >= since)
            .first()
        )
        return recent is not None

    def _create_event(
        self,
        rule: AlertRule,
        symbol: Optional[str],
        message: str,
        severity: str,
    ) -> AlertEvent:
        dedup_hash = self._dedup_hash(rule.id, symbol, rule.threshold_value)
        event = AlertEvent(
            rule_id=rule.id,
            user_id=rule.user_id,
            alert_type=rule.rule_type,
            symbol=symbol,
            message=message,
            severity=severity,
            dedup_hash=dedup_hash,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def _dedup_hash(self, rule_id: str, symbol: Optional[str], threshold) -> str:
        payload = f"{rule_id}:{symbol}:{threshold}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
