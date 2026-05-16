"""Capability and feature flag service.

Phase 6 foundation: plan-based feature gating + user-level overrides.
No business logic changes to existing services — this is a query-only
enrichment layer that other services CAN use but are NOT required to.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import PlanCapability, FeatureFlag, User

logger = logging.getLogger(__name__)


class CapabilityService:
    """Check plan entitlements and user-level feature flags."""

    def __init__(self, db: Session):
        self.db = db

    def check(self, user: User, feature_key: str) -> bool:
        """Return True if user has access to feature_key.

        Priority: user-level feature flag override > plan capability.
        """
        # 1. Check user-level feature flag override
        flag_override = self._get_user_flag(user.id, feature_key)
        if flag_override is not None:
            return flag_override.lower() in ("true", "1", "enabled", "yes")

        # 2. Check plan capability
        capability = (
            self.db.query(PlanCapability)
            .filter(
                PlanCapability.plan_id == user.plan,
                PlanCapability.feature_key == feature_key,
            )
            .first()
        )
        if capability:
            return capability.is_enabled

        # 3. Enterprise wildcard: if plan is enterprise and no explicit deny
        if user.plan == "enterprise":
            return True

        return False

    def get_limit(self, user: User, feature_key: str) -> Optional[int]:
        """Return limit value for a feature, or None if unlimited."""
        capability = (
            self.db.query(PlanCapability)
            .filter(
                PlanCapability.plan_id == user.plan,
                PlanCapability.feature_key == feature_key,
            )
            .first()
        )
        return capability.limit_value if capability else None

    def list_capabilities(self, plan_id: str) -> list[PlanCapability]:
        """List all capabilities for a plan."""
        return (
            self.db.query(PlanCapability)
            .filter(PlanCapability.plan_id == plan_id)
            .all()
        )

    def get_user_feature_flags(self, user_id: str) -> dict[str, str]:
        """Return all active feature flags for a user."""
        from datetime import datetime

        flags = (
            self.db.query(FeatureFlag)
            .filter(FeatureFlag.user_id == user_id)
            .filter(
                (FeatureFlag.expires_at == None) | (FeatureFlag.expires_at > datetime.utcnow())
            )
            .all()
        )
        return {f.flag_key: f.flag_value for f in flags}

    def refresh_user_flags_cache(self, user: User) -> None:
        """Recompute and store feature_flags_json on user record."""
        flags = self.get_user_feature_flags(user.id)
        user.feature_flags_json = json.dumps(flags) if flags else None
        self.db.commit()

    def _get_user_flag(self, user_id: str, flag_key: str) -> Optional[str]:
        """Get a single active feature flag value for a user."""
        from datetime import datetime

        flag = (
            self.db.query(FeatureFlag)
            .filter(
                FeatureFlag.user_id == user_id,
                FeatureFlag.flag_key == flag_key,
            )
            .filter(
                (FeatureFlag.expires_at == None) | (FeatureFlag.expires_at > datetime.utcnow())
            )
            .first()
        )
        return flag.flag_value if flag else None
