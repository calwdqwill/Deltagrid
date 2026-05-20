from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.execution import OrderIntentCreate, OrderIntentResponse, OrderResponse, ExecutionSessionCreate
from app.services.execution.execution_service import ExecutionService
from app.core.dependencies import get_db, require_auth
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/execution", tags=["execution"])


def get_service(db: Session = Depends(get_db)) -> ExecutionService:
    return ExecutionService(db)


# ------------------------------------------------------------------
# Intents
# ------------------------------------------------------------------
@router.post("/intents", response_model=ApiResponse)
async def create_intent(
    data: OrderIntentCreate,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        intent = service.create_intent(user_id, data)
        return ApiResponse(data=intent)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/intents", response_model=ApiResponse)
async def list_intents(
    status: Optional[str] = None,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    intents = service.list_intents(user_id, status=status)
    return ApiResponse(data=intents)


@router.get("/intents/{intent_id}", response_model=ApiResponse)
async def get_intent(
    intent_id: str,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        intent = service.get_intent(user_id, intent_id)
        return ApiResponse(data=intent)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/intents/{intent_id}/confirm", response_model=ApiResponse)
async def confirm_intent(
    intent_id: str,
    is_live: bool = False,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        order = service.confirm_intent(user_id, intent_id, is_live=is_live)
        return ApiResponse(data=order)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/intents/{intent_id}", response_model=ApiResponse)
async def cancel_intent(
    intent_id: str,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        order = service.cancel_intent(user_id, intent_id)
        return ApiResponse(data=order)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ------------------------------------------------------------------
# Orders
# ------------------------------------------------------------------
@router.get("/orders", response_model=ApiResponse)
async def list_orders(
    status: Optional[str] = None,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    orders = service.list_orders(user_id, status=status)
    return ApiResponse(data=orders)


@router.get("/orders/{order_id}", response_model=ApiResponse)
async def get_order(
    order_id: str,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        order = service.get_order(user_id, order_id)
        return ApiResponse(data=order)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


@router.get("/orders/{order_id}/events", response_model=ApiResponse)
async def get_order_events(
    order_id: str,
    user_id: str = Depends(require_auth),
    service: ExecutionService = Depends(get_service),
):
    try:
        events = service.get_order_events(user_id, order_id)
        return ApiResponse(data=events)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")


# ------------------------------------------------------------------
# Execution Sessions
# ------------------------------------------------------------------
from app.domain.models import ExecutionRun
from sqlalchemy.orm import Session
from app.core.dependencies import get_db


@router.get("/sessions", response_model=ApiResponse)
async def list_sessions(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    sessions = (
        db.query(ExecutionRun)
        .filter(ExecutionRun.user_id == user_id)
        .order_by(ExecutionRun.started_at.desc())
        .all()
    )
    return ApiResponse(data=[{
        "id": s.id,
        "name": s.name,
        "strategy": s.strategy,
        "status": s.status,
        "is_live": s.is_live,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "stopped_at": s.stopped_at.isoformat() if s.stopped_at else None,
    } for s in sessions])


@router.post("/sessions", response_model=ApiResponse)
async def start_session(
    data: ExecutionSessionCreate,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    session = ExecutionRun(
        user_id=user_id,
        name=data.name or "Manual Session",
        strategy=data.strategy,
        is_live=data.is_live,
        status="running",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return ApiResponse(data={"id": session.id, "status": session.status, "is_live": session.is_live})


@router.post("/sessions/{session_id}/stop", response_model=ApiResponse)
async def stop_session(
    session_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    session = (
        db.query(ExecutionRun)
        .filter(ExecutionRun.id == session_id, ExecutionRun.user_id == user_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.status = "stopped"
    session.stopped_at = datetime.utcnow()
    db.commit()
    return ApiResponse(data={"id": session.id, "status": session.status})
