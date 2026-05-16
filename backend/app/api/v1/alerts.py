import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertEventResponse
from app.services.alert_service import AlertService
from app.core.dependencies import get_db, require_auth

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_service(db: Session = Depends(get_db)) -> AlertService:
    return AlertService(db)


@router.get("/rules", response_model=ApiResponse)
async def list_rules(
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    rules = service.list_rules(user_id)
    return ApiResponse(data=[
        AlertRuleResponse(
            id=r.id,
            user_id=r.user_id,
            name=r.name,
            rule_type=r.rule_type,
            symbol=r.symbol,
            threshold_value=float(r.threshold_value) if r.threshold_value else None,
            comparison=r.comparison,
            cooldown_minutes=r.cooldown_minutes,
            is_active=r.is_active,
            severity=r.severity,
            channels=json.loads(r.channels_json) if r.channels_json else ["email"],
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in rules
    ])


@router.post("/rules", response_model=ApiResponse)
async def create_rule(
    data: AlertRuleCreate,
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    rule = service.create_rule(
        user_id=user_id,
        name=data.name,
        rule_type=data.rule_type,
        symbol=data.symbol,
        threshold_value=data.threshold_value,
        comparison=data.comparison,
        cooldown_minutes=data.cooldown_minutes,
        severity=data.severity,
        channels=data.channels,
    )
    return ApiResponse(data=AlertRuleResponse(
        id=rule.id,
        user_id=rule.user_id,
        name=rule.name,
        rule_type=rule.rule_type,
        symbol=rule.symbol,
        threshold_value=float(rule.threshold_value) if rule.threshold_value else None,
        comparison=rule.comparison,
        cooldown_minutes=rule.cooldown_minutes,
        is_active=rule.is_active,
        severity=rule.severity,
        channels=data.channels,
        created_at=rule.created_at.isoformat() if rule.created_at else None,
        updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
    ))


@router.patch("/rules/{rule_id}", response_model=ApiResponse)
async def update_rule(
    rule_id: str,
    data: AlertRuleUpdate,
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    update_dict = data.model_dump(exclude_unset=True)
    if "channels" in update_dict:
        update_dict["channels_json"] = json.dumps(update_dict.pop("channels"))
    rule = service.update_rule(rule_id, user_id, **update_dict)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return ApiResponse(data=AlertRuleResponse(
        id=rule.id,
        user_id=rule.user_id,
        name=rule.name,
        rule_type=rule.rule_type,
        symbol=rule.symbol,
        threshold_value=float(rule.threshold_value) if rule.threshold_value else None,
        comparison=rule.comparison,
        cooldown_minutes=rule.cooldown_minutes,
        is_active=rule.is_active,
        severity=rule.severity,
        channels=json.loads(rule.channels_json) if rule.channels_json else ["email"],
        created_at=rule.created_at.isoformat() if rule.created_at else None,
        updated_at=rule.updated_at.isoformat() if rule.updated_at else None,
    ))


@router.post("/rules/{rule_id}/toggle", response_model=ApiResponse)
async def toggle_rule(
    rule_id: str,
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    rule = service.toggle_rule(rule_id, user_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return ApiResponse(data={"is_active": rule.is_active})


@router.delete("/rules/{rule_id}", response_model=ApiResponse)
async def delete_rule(
    rule_id: str,
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    success = service.delete_rule(rule_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return ApiResponse(data={"deleted": True})


@router.get("/events", response_model=ApiResponse)
async def list_events(
    limit: int = 50,
    user_id: str = Depends(require_auth),
    service: AlertService = Depends(get_alert_service),
):
    events = service.list_events(user_id, limit=limit)
    return ApiResponse(data=[
        AlertEventResponse(
            id=e.id,
            rule_id=e.rule_id,
            alert_type=e.alert_type,
            symbol=e.symbol,
            message=e.message,
            severity=e.severity,
            triggered_at=e.triggered_at.isoformat() if e.triggered_at else None,
        )
        for e in events
    ])
