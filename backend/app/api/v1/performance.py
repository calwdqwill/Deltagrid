from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.performance import PerformanceMetrics, PerformanceSnapshotResponse
from app.services.performance_tracker import PerformanceTracker
from app.core.dependencies import get_db, require_auth
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/performance", tags=["performance"])


def get_performance_service(db: Session = Depends(get_db)) -> PerformanceTracker:
    return PerformanceTracker(db)


@router.get("/accounts/{account_id}", response_model=ApiResponse)
async def get_metrics(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: PerformanceTracker = Depends(get_performance_service),
):
    try:
        metrics = service.calculate_metrics(account_id)
        return ApiResponse(data=metrics)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.post("/accounts/{account_id}/snapshot", response_model=ApiResponse)
async def create_snapshot(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: PerformanceTracker = Depends(get_performance_service),
):
    try:
        snapshot = service.create_snapshot(account_id)
        return ApiResponse(data=snapshot)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.get("/accounts/{account_id}/history", response_model=ApiResponse)
async def get_history(
    account_id: str,
    limit: int = 30,
    user_id: str = Depends(require_auth),
    service: PerformanceTracker = Depends(get_performance_service),
):
    try:
        history = service.get_history(account_id, limit=limit)
        return ApiResponse(data=history)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
