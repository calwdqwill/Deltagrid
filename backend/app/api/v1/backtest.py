"""Backtest API endpoint."""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.backtest.config import BacktestConfig
from app.backtest.engine import BacktestEngine
from app.backtest.metrics import BacktestResult
from app.backtest.strategies import STRATEGY_REGISTRY
from app.persistence.database import get_db

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    strategy: str  # "funding_mean_reversion" | "basis_compression" | "liquidation_cascade_fade"
    symbol: str  # "BTC" | "ETH" | "SOL" | "HYPE"
    exchange: str = "binance"
    start_date: Optional[str] = None  # "2026-04-01" (YYYY-MM-DD)
    end_date: Optional[str] = None  # "2026-06-01" (YYYY-MM-DD)
    days: int = 30  # if start_date not provided: backtest last N days
    position_size_usd: float = 10_000
    leverage: float = 1.0
    fee_type: str = "taker"
    use_slippage: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)  # strategy-specific parameter overrides


class BacktestResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_ms: int


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    POST /api/v1/backtest/run

    Executes backtest with specified strategy and parameters.
    Returns full BacktestResult with metrics, trades, and equity curve.
    """
    start_time = time.time()

    try:
        # Validate strategy
        if request.strategy not in STRATEGY_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown strategy: {request.strategy}. Available: {list(STRATEGY_REGISTRY.keys())}",
            )

        # Resolve time range
        if request.start_date and request.end_date:
            start_dt = datetime.strptime(request.start_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc
            )
            end_dt = datetime.strptime(request.end_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc, hour=23, minute=59, second=59
            )
            start_ms = int(start_dt.timestamp() * 1000)
            end_ms = int(end_dt.timestamp() * 1000)
        else:
            now = datetime.now(timezone.utc)
            end_ms = int(now.timestamp() * 1000)
            start_ms = int((now.timestamp() - request.days * 86400) * 1000)

        config = BacktestConfig(
            strategy_type=request.strategy,
            symbol=request.symbol.upper(),
            exchange=request.exchange.lower(),
            start_ms=start_ms,
            end_ms=end_ms,
            position_size_usd=request.position_size_usd,
            leverage=request.leverage,
            fee_type=request.fee_type,
            use_slippage=request.use_slippage,
            params=request.params,
        )

        engine = BacktestEngine(db, config)
        result: BacktestResult = engine.run()

        return BacktestResponse(
            success=True,
            result=result.to_dict(),
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    except HTTPException:
        raise
    except Exception as e:
        return BacktestResponse(
            success=False,
            error=str(e),
            elapsed_ms=int((time.time() - start_time) * 1000),
        )
