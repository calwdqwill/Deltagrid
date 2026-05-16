from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.billing import PlanResponse, SubscriptionResponse
from app.services.billing_service import BillingService
from app.services.referral_service import ReferralService
from app.services.capability_service import CapabilityService
from app.core.dependencies import get_db, require_auth

router = APIRouter(prefix="/billing", tags=["billing"])


def get_billing_service() -> BillingService:
    return BillingService()


def get_referral_service(db: Session = Depends(get_db)) -> ReferralService:
    return ReferralService(db)


@router.get("/plans", response_model=ApiResponse)
async def list_plans(
    service: BillingService = Depends(get_billing_service),
    db: Session = Depends(get_db),
):
    """@public_ready — List available subscription plans with capabilities."""
    capability = CapabilityService(db)
    plans = service.list_plans()
    result = []
    for plan in plans:
        caps = capability.list_capabilities(plan.id)
        result.append({
            **plan.model_dump(),
            "capabilities": [
                {
                    "feature_key": c.feature_key,
                    "is_enabled": c.is_enabled,
                    "limit": c.limit_value,
                }
                for c in caps
            ],
        })
    return ApiResponse(data=result)


@router.get("/subscriptions", response_model=ApiResponse)
async def get_subscription(
    user_id: str = Depends(require_auth),
    service: BillingService = Depends(get_billing_service),
):
    sub = service.get_subscription(user_id)
    return ApiResponse(data=sub)


@router.get("/referrals/code", response_model=ApiResponse)
async def get_referral_code(
    user_id: str = Depends(require_auth),
    service: ReferralService = Depends(get_referral_service),
):
    code = service.generate_code(user_id)
    return ApiResponse(data={"code": code})


@router.get("/referrals/stats", response_model=ApiResponse)
async def get_referral_stats(
    user_id: str = Depends(require_auth),
    service: ReferralService = Depends(get_referral_service),
):
    stats = service.get_referral_stats(user_id)
    return ApiResponse(data=stats)
