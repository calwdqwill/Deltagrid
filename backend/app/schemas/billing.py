from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PlanResponse(BaseModel):
    id: str
    name: str
    price_monthly: float
    features: list[str]


class SubscriptionResponse(BaseModel):
    user_id: str
    plan: str
    status: str  # active, cancelled, expired
    started_at: datetime
    expires_at: Optional[datetime]


class PaymentIntent(BaseModel):
    amount: float
    currency: str
    provider: str
    status: str
