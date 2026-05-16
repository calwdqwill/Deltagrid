from typing import Optional
from pydantic import BaseModel, ConfigDict


class AlertRuleCreate(BaseModel):
    name: str
    rule_type: str
    symbol: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison: str = "gte"
    cooldown_minutes: int = 60
    severity: str = "info"
    channels: list[str] = ["email"]


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    symbol: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison: Optional[str] = None
    cooldown_minutes: Optional[int] = None
    severity: Optional[str] = None
    channels: Optional[list[str]] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    rule_type: str
    symbol: Optional[str]
    threshold_value: Optional[float]
    comparison: str
    cooldown_minutes: int
    is_active: bool
    severity: str
    channels: list[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: Optional[str]
    alert_type: str
    symbol: Optional[str]
    message: str
    severity: Optional[str]
    triggered_at: Optional[str]


class AlertDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_event_id: str
    channel: str
    status: str
    sent_at: Optional[str]
    delivered_at: Optional[str]
    failed_at: Optional[str]
    error_message: Optional[str]
    retry_count: int
