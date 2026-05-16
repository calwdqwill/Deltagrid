"""Billing service — Phase 2 placeholder.

Provides plan definitions and subscription interfaces.
Real payment processing deferred to Phase 2+ implementation.
"""

from typing import Optional
from datetime import datetime

from app.schemas.billing import PlanResponse, SubscriptionResponse


class BillingService:
    """Placeholder for billing logic. Returns static plan config."""

    PLANS = [
        PlanResponse(
            id="free",
            name="Free",
            price_monthly=0.0,
            features=["Scanner access", "Basic filters", "5 favorites"],
        ),
        PlanResponse(
            id="pro",
            name="Pro",
            price_monthly=29.0,
            features=["All scanner features", "Unlimited favorites", "Paper trading", "Performance tracking"],
        ),
        PlanResponse(
            id="enterprise",
            name="Enterprise",
            price_monthly=299.0,
            features=["Everything in Pro", "B2B API", "White-label", "Priority support"],
        ),
    ]

    def list_plans(self) -> list[PlanResponse]:
        return self.PLANS

    def get_subscription(self, user_id: str) -> SubscriptionResponse:
        # Placeholder: always returns free plan
        return SubscriptionResponse(
            user_id=user_id,
            plan="free",
            status="active",
            started_at=datetime.utcnow(),
            expires_at=None,
        )
