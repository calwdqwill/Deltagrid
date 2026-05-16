from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.risk import RiskRuleCreate, RiskRuleResponse, RiskCheckResult
from app.schemas.execution import OrderIntentCreate
from app.services.execution.risk_manager import RiskManager
from app.core.dependencies import get_db, require_auth
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/risk", tags=["risk"])


def get_service(db: Session = Depends(get_db)) -> RiskManager:
    return RiskManager(db)


@router.get("/rules", response_model=ApiResponse)
async def list_rules(
    account_id: Optional[str] = None,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    rules = service.list_rules(user_id, account_id=account_id)
    return ApiResponse(data=[RiskRuleResponse.model_validate(r) for r in rules])


@router.post("/rules", response_model=ApiResponse)
async def create_rule(
    data: RiskRuleCreate,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    try:
        rule = service.create_rule(user_id, data)
        return ApiResponse(data=RiskRuleResponse.model_validate(rule))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/rules/{rule_id}", response_model=ApiResponse)
async def update_rule(
    rule_id: str,
    data: dict,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    try:
        rule = service.update_rule(rule_id, user_id, data)
        return ApiResponse(data=RiskRuleResponse.model_validate(rule))
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/rules/{rule_id}", response_model=ApiResponse)
async def delete_rule(
    rule_id: str,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    try:
        service.delete_rule(rule_id, user_id)
        return ApiResponse(data={"deleted": True})
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/rules/{rule_id}/toggle", response_model=ApiResponse)
async def toggle_rule(
    rule_id: str,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    """Quick toggle is_active for a risk rule (useful for kill switch)."""
    try:
        rule = service.get_rule(rule_id, user_id)
        if not rule:
            raise NotFoundError("Rule not found")
        updated = service.update_rule(rule_id, user_id, {"is_active": not rule.is_active})
        return ApiResponse(data=RiskRuleResponse.model_validate(updated))
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/check", response_model=ApiResponse)
async def dry_run_risk_check(
    data: OrderIntentCreate,
    user_id: str = Depends(require_auth),
    service: RiskManager = Depends(get_service),
):
    result = service.dry_run_check(user_id, data)
    return ApiResponse(data=result)
