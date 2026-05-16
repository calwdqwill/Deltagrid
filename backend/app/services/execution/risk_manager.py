"""Risk Manager: position sizing, max exposure, stop-loss, kill-switch.

Evaluates order intents against user-defined risk rules.
Dry-run safe: never interacts with exchanges.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import RiskRule, RealOrder, PositionSnapshot, ExchangeAccount
from app.schemas.risk import RiskCheckResult, RiskRuleCreate
from app.schemas.execution import OrderIntentCreate
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class RiskManager:
    """Evaluate order intents against risk rules."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Rule CRUD
    # ------------------------------------------------------------------
    def create_rule(self, user_id: str, data: RiskRuleCreate) -> RiskRule:
        rule = RiskRule(
            user_id=user_id,
            account_id=data.account_id,
            rule_type=data.rule_type,
            symbol=data.symbol,
            threshold_value=data.threshold_value,
            comparison=data.comparison,
            action=data.action,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def list_rules(self, user_id: str, account_id: Optional[str] = None) -> list[RiskRule]:
        query = self.db.query(RiskRule).filter(RiskRule.user_id == user_id)
        if account_id:
            query = query.filter(RiskRule.account_id == account_id)
        return query.order_by(RiskRule.created_at.desc()).all()

    def get_rule(self, rule_id: str, user_id: str) -> Optional[RiskRule]:
        return (
            self.db.query(RiskRule)
            .filter(RiskRule.id == rule_id, RiskRule.user_id == user_id)
            .first()
        )

    def update_rule(self, rule_id: str, user_id: str, data: dict) -> RiskRule:
        rule = self.get_rule(rule_id, user_id)
        if not rule:
            raise ValidationError("Risk rule not found")
        for key, value in data.items():
            if hasattr(rule, key) and key not in ("id", "user_id", "created_at"):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: str, user_id: str) -> None:
        rule = self.get_rule(rule_id, user_id)
        if not rule:
            raise ValidationError("Risk rule not found")
        self.db.delete(rule)
        self.db.commit()

    # ------------------------------------------------------------------
    # Risk check
    # ------------------------------------------------------------------
    def check_intent(self, user_id: str, intent: OrderIntentCreate) -> RiskCheckResult:
        """Evaluate an order intent against all active risk rules."""
        rules = self.list_rules(user_id, intent.account_id)
        active_rules = [r for r in rules if r.is_active]

        blocking_rules: list[str] = []
        warning_rules: list[str] = []
        current_exposure: Optional[float] = None
        current_position_size: Optional[float] = None

        # Calculate current position / exposure for this symbol/account
        position = self._get_current_position(user_id, intent.account_id, intent.symbol)
        if position:
            current_position_size = float(position.quantity)
            current_exposure = float(position.quantity) * (float(position.avg_entry_price or 0) or 1)

        # Check kill switch first (highest priority)
        kill_switch_rules = [r for r in active_rules if r.rule_type == "kill_switch"]
        for ks in kill_switch_rules:
            blocking_rules.append(ks.id)
            return RiskCheckResult(
                passed=False,
                blocking_rules=blocking_rules,
                warning_rules=warning_rules,
                current_exposure=current_exposure,
                current_position_size=current_position_size,
                message="Kill switch is active. All live trading blocked.",
            )

        for rule in active_rules:
            violated = self._evaluate_rule(rule, intent, current_position_size, current_exposure)
            if violated:
                if rule.action == "block":
                    blocking_rules.append(rule.id)
                elif rule.action == "warn":
                    warning_rules.append(rule.id)

        passed = len(blocking_rules) == 0
        message = None
        if not passed:
            message = f"Blocked by {len(blocking_rules)} risk rule(s)."
        elif warning_rules:
            message = f"Warning: {len(warning_rules)} risk rule(s) triggered."

        return RiskCheckResult(
            passed=passed,
            blocking_rules=blocking_rules,
            warning_rules=warning_rules,
            current_exposure=current_exposure,
            current_position_size=current_position_size,
            message=message,
        )

    def dry_run_check(self, user_id: str, data: OrderIntentCreate) -> RiskCheckResult:
        """Public dry-run risk check for UI feedback."""
        return self.check_intent(user_id, data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_current_position(
        self,
        user_id: str,
        account_id: str,
        symbol: str,
    ) -> Optional[PositionSnapshot]:
        return (
            self.db.query(PositionSnapshot)
            .filter(
                PositionSnapshot.user_id == user_id,
                PositionSnapshot.account_id == account_id,
                PositionSnapshot.symbol == symbol,
            )
            .order_by(PositionSnapshot.snapshot_at.desc())
            .first()
        )

    def _evaluate_rule(
        self,
        rule: RiskRule,
        intent: OrderIntentCreate,
        current_position_size: Optional[float],
        current_exposure: Optional[float],
    ) -> bool:
        """Return True if rule is violated."""
        threshold = float(rule.threshold_value)
        comparison = rule.comparison

        if rule.rule_type == "max_position_size":
            value = (current_position_size or 0) + intent.quantity
        elif rule.rule_type == "max_exposure_usd":
            # Approximate exposure using current price (if intent has price) or 1
            price = intent.price or 1.0
            value = (current_exposure or 0) + (intent.quantity * price)
        elif rule.rule_type == "max_order_size":
            value = intent.quantity
        else:
            # Generic: intent quantity as proxy
            value = intent.quantity

        if comparison == "lte":
            return value > threshold
        elif comparison == "gte":
            return value < threshold
        elif comparison == "eq":
            return value != threshold

        return False
