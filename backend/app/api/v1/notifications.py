import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.notification import NotificationPreferencesUpdate, NotificationPreferencesResponse, WebPushSubscribeRequest
from app.services.notification_service import NotificationService
from app.core.dependencies import get_db, require_auth

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("/preferences", response_model=ApiResponse)
async def get_preferences(
    user_id: str = Depends(require_auth),
    service: NotificationService = Depends(get_notification_service),
):
    prefs = service.ensure_preferences(user_id)
    return ApiResponse(data=NotificationPreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        email_enabled=prefs.email_enabled,
        email_address=prefs.email_address,
        web_push_enabled=prefs.web_push_enabled,
        web_push_subscription_json=prefs.web_push_subscription_json,
        telegram_enabled=prefs.telegram_enabled,
        telegram_chat_id=prefs.telegram_chat_id,
        market_alerts_enabled=prefs.market_alerts_enabled,
        execution_alerts_enabled=prefs.execution_alerts_enabled,
        risk_alerts_enabled=prefs.risk_alerts_enabled,
        min_severity=prefs.min_severity,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        created_at=prefs.created_at.isoformat() if prefs.created_at else None,
        updated_at=prefs.updated_at.isoformat() if prefs.updated_at else None,
    ))


@router.put("/preferences", response_model=ApiResponse)
async def update_preferences(
    data: NotificationPreferencesUpdate,
    user_id: str = Depends(require_auth),
    service: NotificationService = Depends(get_notification_service),
):
    prefs = service.update_preferences(user_id, **data.model_dump(exclude_unset=True))
    return ApiResponse(data=NotificationPreferencesResponse(
        id=prefs.id,
        user_id=prefs.user_id,
        email_enabled=prefs.email_enabled,
        email_address=prefs.email_address,
        web_push_enabled=prefs.web_push_enabled,
        web_push_subscription_json=prefs.web_push_subscription_json,
        telegram_enabled=prefs.telegram_enabled,
        telegram_chat_id=prefs.telegram_chat_id,
        market_alerts_enabled=prefs.market_alerts_enabled,
        execution_alerts_enabled=prefs.execution_alerts_enabled,
        risk_alerts_enabled=prefs.risk_alerts_enabled,
        min_severity=prefs.min_severity,
        quiet_hours_start=prefs.quiet_hours_start,
        quiet_hours_end=prefs.quiet_hours_end,
        created_at=prefs.created_at.isoformat() if prefs.created_at else None,
        updated_at=prefs.updated_at.isoformat() if prefs.updated_at else None,
    ))


@router.post("/web-push/subscribe", response_model=ApiResponse)
async def subscribe_web_push(
    data: WebPushSubscribeRequest,
    user_id: str = Depends(require_auth),
    service: NotificationService = Depends(get_notification_service),
):
    service.update_preferences(
        user_id,
        web_push_enabled=True,
        web_push_subscription_json=data.subscription_json,
    )
    return ApiResponse(data={"subscribed": True})


@router.post("/web-push/unsubscribe", response_model=ApiResponse)
async def unsubscribe_web_push(
    user_id: str = Depends(require_auth),
    service: NotificationService = Depends(get_notification_service),
):
    service.update_preferences(
        user_id,
        web_push_enabled=False,
        web_push_subscription_json=None,
    )
    return ApiResponse(data={"subscribed": False})
