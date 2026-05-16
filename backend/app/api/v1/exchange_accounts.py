from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.exchange import (
    ExchangeAccountCreate,
    ExchangeAccountResponse,
    ExchangeKeyStoreRequest,
    ConnectorCapabilityResponse,
)
from app.services.exchange_account_service import ExchangeAccountService
from app.core.dependencies import get_db, require_auth
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/exchange-accounts", tags=["exchange-accounts"])


def get_service(db: Session = Depends(get_db)) -> ExchangeAccountService:
    return ExchangeAccountService(db)


@router.get("", response_model=ApiResponse)
async def list_accounts(
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    accounts = service.list_accounts(user_id)
    return ApiResponse(data=accounts)


@router.post("", response_model=ApiResponse)
async def create_account(
    data: ExchangeAccountCreate,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    account = service.create_account(user_id, data)
    return ApiResponse(data=account)


@router.get("/{account_id}", response_model=ApiResponse)
async def get_account(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    try:
        account = service.get_account(account_id, user_id)
        return ApiResponse(data=account)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.patch("/{account_id}", response_model=ApiResponse)
async def update_account(
    account_id: str,
    data: dict,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    try:
        account = service.update_account(account_id, user_id, data)
        return ApiResponse(data=account)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.delete("/{account_id}", response_model=ApiResponse)
async def delete_account(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    try:
        service.delete_account(account_id, user_id)
        return ApiResponse(data={"deleted": True})
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


# ------------------------------------------------------------------
# Keys (one-way storage)
# ------------------------------------------------------------------
@router.post("/{account_id}/keys", response_model=ApiResponse)
async def store_keys(
    account_id: str,
    data: ExchangeKeyStoreRequest,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    try:
        service.store_keys(account_id, user_id, data)
        return ApiResponse(data={"stored": True})
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{account_id}/keys", response_model=ApiResponse)
async def delete_keys(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: ExchangeAccountService = Depends(get_service),
):
    try:
        service.delete_keys(account_id, user_id)
        return ApiResponse(data={"deleted": True})
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


# ------------------------------------------------------------------
# Connector capabilities
# ------------------------------------------------------------------
@router.get("/connectors/capabilities", response_model=ApiResponse)
async def list_capabilities(
    db: Session = Depends(get_db),
):
    caps = ExchangeAccountService.list_capabilities(db)
    return ApiResponse(data=[ConnectorCapabilityResponse.model_validate(c) for c in caps])


@router.get("/connectors/capabilities/{exchange_name}", response_model=ApiResponse)
async def get_capability(
    exchange_name: str,
    db: Session = Depends(get_db),
):
    cap = ExchangeAccountService.get_capability(db, exchange_name)
    if not cap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    return ApiResponse(data=ConnectorCapabilityResponse.model_validate(cap))
