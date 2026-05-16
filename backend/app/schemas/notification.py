from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    web_push_enabled: Optional[bool] = None
    web_push_subscription_json: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_chat_id: Optional[str] = None
    market_alerts_enabled: Optional[bool] = None
    execution_alerts_enabled: Optional[bool] = None
    risk_alerts_enabled: Optional[bool] = None
    rwa_alerts_enabled: Optional[bool] = None
    min_severity: Optional[str] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None


class NotificationPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    email_enabled: bool
    email_address: Optional[str]
    web_push_enabled: bool
    web_push_subscription_json: Optional[str]
    telegram_enabled: bool
    telegram_chat_id: Optional[str]
    market_alerts_enabled: bool
    execution_alerts_enabled: bool
    risk_alerts_enabled: bool
    rwa_alerts_enabled: bool
    min_severity: str
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]


class WebPushSubscribeRequest(BaseModel):
    subscription_json: str
