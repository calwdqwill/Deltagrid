"""OrderManager: bridge between ExecutionService and ExchangeConnector.

Handles order submission, retry logic, partial fill tracking,
and status polling. NEVER stores decrypted keys.
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import RealOrder, OrderEvent, ExchangeAccount
from app.services.exchange_account_service import ExchangeAccountService
from app.services.connectors.connector_registry import ConnectorRegistry
from app.services.connectors.base_connector import (
    OrderRequest,
    OrderStatus,
    DecryptedCredentials,
)
from app.services.secrets.vault_service import SecretsVaultService

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1.0


class OrderManager:
    def __init__(self, db: Session):
        self.db = db
        self.vault = SecretsVaultService()

    async def submit_order(self, order: RealOrder) -> None:
        """Submit a real order to the exchange. Updates order in-place."""
        account = (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.id == order.account_id)
            .first()
        )
        if not account:
            raise ValueError("Exchange account not found")

        connector_class = ConnectorRegistry.get(account.exchange_name)
        if not connector_class:
            raise ValueError(f"Connector not found for exchange: {account.exchange_name}")

        # Decrypt credentials (short-lived, only for this request)
        creds = self._get_credentials(order.account_id)
        if not creds:
            raise ValueError("API keys not configured for this account")

        connector = connector_class()
        try:
            request = OrderRequest(
                symbol=order.symbol,
                side=order.side,
                order_type=order.order_type,
                quantity=float(order.quantity),
                price=float(order.price) if order.price else None,
                client_order_id=order.client_order_id,
            )

            # Retry logic
            last_error: Optional[str] = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    result = await connector.place_order(request, creds)
                    self._apply_result(order, result)
                    self._log_event(
                        order.id,
                        "submitted",
                        "pending_confirmation",
                        order.status,
                        {
                            "exchange_order_id": result.exchange_order_id,
                            "attempt": attempt,
                            "raw": result.raw_response,
                        },
                    )
                    logger.info(f"Order {order.id} submitted on attempt {attempt}")
                    return
                except Exception as e:
                    last_error = str(e)
                    logger.warning(f"Order submission attempt {attempt} failed: {e}")
                    if attempt < MAX_RETRIES:
                        delay = BASE_DELAY * (2 ** (attempt - 1))
                        await asyncio.sleep(delay)

            # All retries exhausted
            order.status = "failed"
            order.failed_at = __import__("datetime").datetime.utcnow()
            self._log_event(
                order.id,
                "error",
                "pending_confirmation",
                "failed",
                {"error": last_error, "retries": MAX_RETRIES},
            )
            logger.error(f"Order {order.id} failed after {MAX_RETRIES} attempts: {last_error}")
        finally:
            await connector.close()

    async def sync_order_status(self, order: RealOrder) -> None:
        """Poll exchange for latest order status and update DB."""
        if order.status in ("filled", "cancelled", "rejected", "failed"):
            return

        account = (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.id == order.account_id)
            .first()
        )
        if not account:
            return

        connector_class = ConnectorRegistry.get(account.exchange_name)
        if not connector_class:
            return

        creds = self._get_credentials(order.account_id)
        if not creds:
            return

        connector = connector_class()
        try:
            result = await connector.get_order_status(
                order_id=order.exchange_order_id or "",
                symbol=order.symbol,
                credentials=creds,
            )
            old_status = order.status
            self._apply_result(order, result)
            if old_status != order.status:
                self._log_event(
                    order.id,
                    "sync" if result.status != OrderStatus.ERROR else "error",
                    old_status,
                    order.status,
                    {"exchange_order_id": result.exchange_order_id, "raw": result.raw_response},
                )
        except Exception as e:
            logger.warning(f"Order status sync failed for {order.id}: {e}")
        finally:
            await connector.close()

    def _get_credentials(self, account_id: str) -> Optional[DecryptedCredentials]:
        """Fetch and decrypt credentials for an account."""
        key_record = (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.id == account_id)
            .first()
        )
        if not key_record:
            return None

        # Use ExchangeAccountService to get decrypted keys
        service = ExchangeAccountService(self.db)
        try:
            keys = service.get_decrypted_keys(account_id, key_record.user_id)
            return DecryptedCredentials(
                api_key=keys["api_key"],
                api_secret=keys["api_secret"],
                passphrase=keys.get("passphrase"),
                is_testnet=keys.get("is_testnet", False),
            )
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for account {account_id}: {e}")
            return None

    def _apply_result(self, order: RealOrder, result) -> None:
        """Map connector OrderResult to RealOrder fields."""
        if result.exchange_order_id:
            order.exchange_order_id = result.exchange_order_id

        status_map = {
            OrderStatus.PENDING: "pending",
            OrderStatus.PARTIALLY_FILLED: "partially_filled",
            OrderStatus.FILLED: "filled",
            OrderStatus.CANCELLED: "cancelled",
            OrderStatus.REJECTED: "rejected",
            OrderStatus.ERROR: "failed",
        }
        order.status = status_map.get(result.status, "failed")
        order.filled_quantity = result.filled_quantity
        order.remaining_quantity = result.remaining_quantity
        order.avg_fill_price = result.avg_fill_price
        if result.fee_amount:
            order.fee_amount = result.fee_amount
        if result.fee_currency:
            order.fee_currency = result.fee_currency

        if order.status == "filled":
            order.filled_at = __import__("datetime").datetime.utcnow()
        elif order.status == "failed":
            order.failed_at = __import__("datetime").datetime.utcnow()

    def _log_event(self, order_id: str, event_type: str, from_status: Optional[str], to_status: Optional[str], payload: dict) -> None:
        import json
        from app.domain.models import OrderEvent
        event = OrderEvent(
            order_id=order_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            payload_json=json.dumps(payload) if payload else None,
        )
        self.db.add(event)
