"""Execution Service: order intent lifecycle.

Transforms user intents into orders with risk checks and audit trails.
No real exchange interaction at this stage — that is OrderManager's job.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import RealOrder, OrderEvent, AuditLog
from app.schemas.execution import OrderIntentCreate, OrderIntentResponse, OrderResponse
from app.schemas.risk import RiskCheckResult
from app.services.execution.risk_manager import RiskManager
from app.services.execution.order_manager import OrderManager
from app.core.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

ORDER_STATUS_TRANSITIONS = {
    "intent": ["risk_check", "pending_confirmation"],
    "risk_check": ["pending_confirmation", "failed"],
    "pending_confirmation": ["submitted", "cancelled"],
    "submitted": ["pending", "filled", "partially_filled", "rejected", "cancelled"],
    "pending": ["filled", "partially_filled", "rejected", "cancelled"],
    "partially_filled": ["filled", "cancelled"],
}


class ExecutionService:
    def __init__(self, db: Session):
        self.db = db
        self.risk_manager = RiskManager(db)
        self.order_manager = OrderManager(db)

    # ------------------------------------------------------------------
    # Order Intents
    # ------------------------------------------------------------------
    def create_intent(self, user_id: str, data: OrderIntentCreate) -> OrderIntentResponse:
        """Create an order intent. Risk check is performed but not blocking at this stage."""
        intent_id = str(uuid.uuid4())
        client_order_id = f"dg-{intent_id[:8]}"

        # Run risk check (informational at intent creation)
        risk_result = self.risk_manager.check_intent(user_id, data)

        # Persist as RealOrder with status 'intent'
        order = RealOrder(
            id=intent_id,
            user_id=user_id,
            account_id=data.account_id,
            client_order_id=client_order_id,
            symbol=data.symbol.upper(),
            side=data.side.lower(),
            order_type=data.order_type.lower(),
            quantity=data.quantity,
            remaining_quantity=data.quantity,
            price=data.price,
            status="intent",
            strategy=data.strategy,
            metadata_json=json.dumps({
                "risk_check_at_create": risk_result.model_dump(),
            }),
        )
        self.db.add(order)
        self._log_event(order.id, "created", None, "intent", {"risk_check": risk_result.model_dump()})
        self._audit_log(user_id, "order_created", "order", order.id, {"symbol": data.symbol, "side": data.side})

        self.db.commit()
        self.db.refresh(order)

        return OrderIntentResponse(
            id=order.id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=float(order.quantity),
            price=float(order.price) if order.price else None,
            status=order.status,
            risk_check_result=risk_result.model_dump(),
            created_at=order.created_at,
        )

    def list_intents(self, user_id: str, status: Optional[str] = None) -> list[OrderIntentResponse]:
        """List order intents (orders with status in early lifecycle)."""
        query = self.db.query(RealOrder).filter(RealOrder.user_id == user_id)
        if status:
            query = query.filter(RealOrder.status == status)
        else:
            query = query.filter(RealOrder.status.in_(["intent", "risk_check", "pending_confirmation"]))
        orders = query.order_by(RealOrder.created_at.desc()).all()
        return [self._to_intent_response(o) for o in orders]

    def get_intent(self, user_id: str, intent_id: str) -> OrderIntentResponse:
        order = self._get_order_or_404(intent_id, user_id)
        if order.status not in ("intent", "risk_check", "pending_confirmation"):
            raise ValidationError("Order is no longer an intent")
        return self._to_intent_response(order)

    def confirm_intent(self, user_id: str, intent_id: str, is_live: bool = False) -> OrderResponse:
        """Confirm an intent and transition to 'submitted' status.

        If is_live=False (default), the order is rejected with a safe message.
        If is_live=True, risk check is re-run and must pass.
        """
        order = self._get_order_or_404(intent_id, user_id)
        if order.status != "intent":
            raise ValidationError(f"Cannot confirm order in status '{order.status}'")

        # Re-run risk check at confirmation time
        intent_data = OrderIntentCreate(
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=float(order.quantity),
            price=float(order.price) if order.price else None,
            strategy=order.strategy,
        )
        risk_result = self.risk_manager.check_intent(user_id, intent_data)

        if not risk_result.passed:
            order.status = "failed"
            order.failed_at = datetime.utcnow()
            self._log_event(order.id, "risk_checked", "intent", "failed", risk_result.model_dump())
            self._audit_log(user_id, "risk_blocked", "order", order.id, risk_result.model_dump())
            self.db.commit()
            raise ValidationError(f"Risk check failed: {risk_result.message}")

        # Transition to risk_checked → pending_confirmation → submitted
        order.status = "pending_confirmation"
        self._log_event(order.id, "risk_checked", "intent", "pending_confirmation", risk_result.model_dump())

        if not is_live:
            # SAFE DEFAULT: reject if not explicitly live
            order.status = "failed"
            order.failed_at = datetime.utcnow()
            self._log_event(
                order.id,
                "error",
                "pending_confirmation",
                "failed",
                {"reason": "Live trading not enabled (is_live=False)"},
            )
            self._audit_log(user_id, "order_failed", "order", order.id, {"reason": "dry_run_default"})
            self.db.commit()
            return self._to_order_response(order)

        # Mark as submitted and delegate to OrderManager for exchange placement
        order.status = "submitted"
        order.submitted_at = datetime.utcnow()
        self._log_event(order.id, "submitted", "pending_confirmation", "submitted", {})
        self._audit_log(user_id, "order_submitted", "order", order.id, {"symbol": order.symbol, "side": order.side})
        self.db.commit()
        self.db.refresh(order)

        # Async exchange call — fire and forget for now, status will be updated on next sync
        import asyncio
        asyncio.create_task(self.order_manager.submit_order(order))

        return self._to_order_response(order)

    def cancel_intent(self, user_id: str, intent_id: str) -> OrderResponse:
        order = self._get_order_or_404(intent_id, user_id)
        if order.status not in ("intent", "risk_check", "pending_confirmation"):
            raise ValidationError(f"Cannot cancel order in status '{order.status}'")
        old_status = order.status
        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        self._log_event(order.id, "cancelled", old_status, "cancelled", {"by": "user"})
        self._audit_log(user_id, "order_cancelled", "order", order.id, {})
        self.db.commit()
        self.db.refresh(order)
        return self._to_order_response(order)

    # ------------------------------------------------------------------
    # Orders (full lifecycle)
    # ------------------------------------------------------------------
    def list_orders(self, user_id: str, status: Optional[str] = None) -> list[OrderResponse]:
        query = self.db.query(RealOrder).filter(RealOrder.user_id == user_id)
        if status:
            query = query.filter(RealOrder.status == status)
        orders = query.order_by(RealOrder.created_at.desc()).all()
        return [self._to_order_response(o) for o in orders]

    def get_order(self, user_id: str, order_id: str) -> OrderResponse:
        order = self._get_order_or_404(order_id, user_id)
        return self._to_order_response(order)

    def get_order_events(self, user_id: str, order_id: str) -> list[dict]:
        order = self._get_order_or_404(order_id, user_id)
        events = (
            self.db.query(OrderEvent)
            .filter(OrderEvent.order_id == order.id)
            .order_by(OrderEvent.created_at.asc())
            .all()
        )
        return [
            {
                "id": e.id,
                "order_id": e.order_id,
                "event_type": e.event_type,
                "from_status": e.from_status,
                "to_status": e.to_status,
                "payload_json": e.payload_json,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------
    def list_audit_logs(self, user_id: str, limit: int = 100, offset: int = 0) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_order_or_404(self, order_id: str, user_id: str) -> RealOrder:
        order = (
            self.db.query(RealOrder)
            .filter(RealOrder.id == order_id, RealOrder.user_id == user_id)
            .first()
        )
        if not order:
            raise NotFoundError("Order not found")
        return order

    def _log_event(
        self,
        order_id: str,
        event_type: str,
        from_status: Optional[str],
        to_status: Optional[str],
        payload: dict,
    ) -> None:
        event = OrderEvent(
            order_id=order_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            payload_json=json.dumps(payload) if payload else None,
        )
        self.db.add(event)

    def _audit_log(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
    ) -> None:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details) if details else None,
        )
        self.db.add(log)

    def _to_intent_response(self, order: RealOrder) -> OrderIntentResponse:
        risk_result = None
        if order.metadata_json:
            try:
                meta = json.loads(order.metadata_json)
                if "risk_check_at_create" in meta:
                    risk_result = meta["risk_check_at_create"]
            except Exception:
                pass

        return OrderIntentResponse(
            id=order.id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=float(order.quantity),
            price=float(order.price) if order.price else None,
            status=order.status,
            risk_check_result=risk_result,
            created_at=order.created_at,
        )

    def _to_order_response(self, order: RealOrder) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            account_id=order.account_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=float(order.quantity),
            filled_quantity=float(order.filled_quantity) if order.filled_quantity else 0,
            remaining_quantity=float(order.remaining_quantity) if order.remaining_quantity else None,
            price=float(order.price) if order.price else None,
            avg_fill_price=float(order.avg_fill_price) if order.avg_fill_price else None,
            status=order.status,
            fee_amount=float(order.fee_amount) if order.fee_amount else None,
            fee_currency=order.fee_currency,
            created_at=order.created_at,
            submitted_at=order.submitted_at,
            filled_at=order.filled_at,
        )
