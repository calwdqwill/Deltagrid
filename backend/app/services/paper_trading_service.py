"""Paper trading service: virtual balance, trade simulation, portfolio state.

No real execution. Separate domain from scanner and execution.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import PaperAccount, PaperTrade, StrategyRun
from app.schemas.paper import (
    PaperAccountCreate,
    PaperAccountResponse,
    PaperTradeCreate,
    PaperTradeResponse,
    PortfolioState,
)
from app.core.exceptions import NotFoundError, ValidationError


class PaperTradingService:
    def __init__(self, db: Session):
        self.db = db

    def create_account(self, user_id: str, data: PaperAccountCreate) -> PaperAccountResponse:
        account = PaperAccount(
            user_id=user_id,
            name=data.name or "Demo Account",
            initial_balance=data.initial_balance,
            current_balance=data.initial_balance,
            currency=data.currency,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_response(account)

    def list_accounts(self, user_id: str) -> list[PaperAccountResponse]:
        accounts = self.db.query(PaperAccount).filter(
            PaperAccount.user_id == user_id,
            PaperAccount.is_active == True,
        ).all()
        return [self._to_account_response(a) for a in accounts]

    def get_account(self, account_id: str, user_id: str) -> PaperAccountResponse:
        account = self._get_account_or_404(account_id, user_id)
        return self._to_account_response(account)

    def create_trade(self, account_id: str, user_id: str, data: PaperTradeCreate) -> PaperTradeResponse:
        account = self._get_account_or_404(account_id, user_id)

        if account.current_balance <= 0:
            raise ValidationError("Insufficient balance")

        trade_value = data.entry_price * data.quantity
        fee = trade_value * (data.fee_pct / 100)
        total_cost = trade_value + fee

        if float(account.current_balance) < total_cost:
            raise ValidationError("Insufficient balance for trade")

        trade = PaperTrade(
            account_id=account_id,
            strategy=data.strategy,
            instrument_id=data.instrument_id,
            side=data.side,
            entry_price=data.entry_price,
            quantity=data.quantity,
            status="open",
            fee_pct=data.fee_pct,
            slippage_pct=data.slippage_pct,
        )
        self.db.add(trade)

        # Deduct from balance
        account.current_balance = float(account.current_balance) - total_cost
        self.db.commit()
        self.db.refresh(trade)
        return self._to_trade_response(trade)

    def close_trade(
        self,
        account_id: str,
        trade_id: str,
        user_id: str,
        exit_price: float,
    ) -> PaperTradeResponse:
        account = self._get_account_or_404(account_id, user_id)
        trade = self.db.query(PaperTrade).filter(
            PaperTrade.id == trade_id,
            PaperTrade.account_id == account_id,
            PaperTrade.status == "open",
        ).first()
        if not trade:
            raise NotFoundError("Open trade not found")

        entry_value = float(trade.entry_price) * float(trade.quantity)
        exit_value = exit_price * float(trade.quantity)
        fee = exit_value * (float(trade.fee_pct) / 100)

        if trade.side == "buy":
            pnl = exit_value - entry_value - fee
        else:
            pnl = entry_value - exit_value - fee

        pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0

        trade.exit_price = exit_price
        trade.status = "closed"
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct

        # Credit balance
        account.current_balance = float(account.current_balance) + exit_value - fee
        self.db.commit()
        self.db.refresh(trade)
        return self._to_trade_response(trade)

    def list_trades(self, account_id: str, user_id: str, status: Optional[str] = None) -> list[PaperTradeResponse]:
        self._get_account_or_404(account_id, user_id)
        query = self.db.query(PaperTrade).filter(PaperTrade.account_id == account_id)
        if status:
            query = query.filter(PaperTrade.status == status)
        trades = query.order_by(PaperTrade.opened_at.desc()).all()
        return [self._to_trade_response(t) for t in trades]

    def get_portfolio(self, account_id: str, user_id: str) -> PortfolioState:
        account = self._get_account_or_404(account_id, user_id)
        trades = self.db.query(PaperTrade).filter(PaperTrade.account_id == account_id).all()
        open_trades = [t for t in trades if t.status == "open"]
        closed_trades = [t for t in trades if t.status == "closed"]
        total_pnl = sum(float(t.pnl or 0) for t in closed_trades)

        strategies = list({t.strategy for t in trades})

        return PortfolioState(
            account_id=account_id,
            current_balance=float(account.current_balance),
            total_pnl=total_pnl,
            open_trades=len(open_trades),
            closed_trades=len(closed_trades),
            active_strategies=strategies,
        )

    def _get_account_or_404(self, account_id: str, user_id: str) -> PaperAccount:
        account = self.db.query(PaperAccount).filter(
            PaperAccount.id == account_id,
            PaperAccount.user_id == user_id,
        ).first()
        if not account:
            raise NotFoundError("Paper account not found")
        return account

    def _to_account_response(self, account: PaperAccount) -> PaperAccountResponse:
        return PaperAccountResponse(
            id=account.id,
            user_id=account.user_id,
            name=account.name,
            initial_balance=float(account.initial_balance),
            current_balance=float(account.current_balance),
            currency=account.currency,
            is_active=account.is_active,
            created_at=account.created_at,
        )

    def _to_trade_response(self, trade: PaperTrade) -> PaperTradeResponse:
        return PaperTradeResponse(
            id=trade.id,
            account_id=trade.account_id,
            strategy=trade.strategy,
            instrument_id=trade.instrument_id,
            side=trade.side,
            entry_price=float(trade.entry_price),
            exit_price=float(trade.exit_price) if trade.exit_price else None,
            quantity=float(trade.quantity),
            status=trade.status,
            pnl=float(trade.pnl) if trade.pnl else None,
            pnl_pct=float(trade.pnl_pct) if trade.pnl_pct else None,
            fee_pct=float(trade.fee_pct),
            slippage_pct=float(trade.slippage_pct),
            opened_at=trade.opened_at,
            closed_at=trade.closed_at,
        )
