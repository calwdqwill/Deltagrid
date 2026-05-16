from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.paper import (
    PaperAccountCreate,
    PaperAccountResponse,
    PaperTradeCreate,
    PaperTradeResponse,
    PortfolioState,
)
from app.services.paper_trading_service import PaperTradingService
from app.services.strategy_executor import StrategyExecutor, StrategySignal
from app.core.dependencies import get_db, require_auth
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/paper", tags=["paper-trading"])


def get_paper_service(db: Session = Depends(get_db)) -> PaperTradingService:
    return PaperTradingService(db)


@router.get("/accounts", response_model=ApiResponse)
async def list_accounts(
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    accounts = service.list_accounts(user_id)
    return ApiResponse(data=accounts)


@router.post("/accounts", response_model=ApiResponse)
async def create_account(
    data: PaperAccountCreate,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    account = service.create_account(user_id, data)
    return ApiResponse(data=account)


@router.get("/accounts/{account_id}", response_model=ApiResponse)
async def get_account(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    try:
        account = service.get_account(account_id, user_id)
        return ApiResponse(data=account)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.get("/accounts/{account_id}/trades", response_model=ApiResponse)
async def list_trades(
    account_id: str,
    status: Optional[str] = None,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    try:
        trades = service.list_trades(account_id, user_id, status=status)
        return ApiResponse(data=trades)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.post("/accounts/{account_id}/trades", response_model=ApiResponse)
async def create_trade(
    account_id: str,
    data: PaperTradeCreate,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    try:
        trade = service.create_trade(account_id, user_id, data)
        return ApiResponse(data=trade)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/accounts/{account_id}/trades/{trade_id}/close", response_model=ApiResponse)
async def close_trade(
    account_id: str,
    trade_id: str,
    exit_price: float,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    try:
        trade = service.close_trade(account_id, trade_id, user_id, exit_price)
        return ApiResponse(data=trade)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trade or account not found")


@router.get("/accounts/{account_id}/portfolio", response_model=ApiResponse)
async def get_portfolio(
    account_id: str,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    try:
        portfolio = service.get_portfolio(account_id, user_id)
        return ApiResponse(data=portfolio)
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.post("/accounts/{account_id}/evaluate", response_model=ApiResponse)
async def evaluate_strategy(
    account_id: str,
    strategy: str,
    instrument_id: str,
    current_price: float,
    user_id: str = Depends(require_auth),
    service: PaperTradingService = Depends(get_paper_service),
):
    """Evaluate a strategy and return a signal (no trade created)."""
    try:
        service.get_account(account_id, user_id)  # validate access
    except NotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if strategy == "z_score":
        signal = StrategyExecutor.evaluate_z_score(
            instrument_id=instrument_id,
            current_price=current_price,
            mean_price=current_price * 0.98,
            std_dev=current_price * 0.02,
        )
    elif strategy == "basis":
        signal = StrategyExecutor.evaluate_basis(
            instrument_id=instrument_id,
            spot_price=current_price,
            perp_price=current_price * 1.005,
        )
    elif strategy == "cross_exchange":
        signal = StrategyExecutor.evaluate_cross_exchange(
            instrument_id=instrument_id,
            buy_price=current_price,
            sell_price=current_price * 1.003,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown strategy")

    return ApiResponse(data={
        "strategy": signal.strategy,
        "instrument_id": signal.instrument_id,
        "side": signal.side,
        "confidence": signal.confidence,
        "entry_price": signal.entry_price,
        "suggested_quantity": signal.suggested_quantity,
        "reason": signal.reason,
    })
