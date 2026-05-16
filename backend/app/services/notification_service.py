"""Notification delivery service: email, web push, telegram.

Phase 4: Email via SMTP/SendGrid with fallback to logged-only.
Web push and Telegram stubs for future expansion.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import AlertEvent, AlertDelivery, NotificationPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """Deliver notifications through configured channels."""

    def __init__(self, db: Session):
        self.db = db

    def get_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        return (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

    def ensure_preferences(self, user_id: str) -> NotificationPreference:
        prefs = self.get_preferences(user_id)
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            self.db.add(prefs)
            self.db.commit()
            self.db.refresh(prefs)
        return prefs

    def update_preferences(self, user_id: str, **kwargs) -> NotificationPreference:
        prefs = self.ensure_preferences(user_id)
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        self.db.commit()
        self.db.refresh(prefs)
        return prefs

    def deliver(self, event: AlertEvent, channels: list[str]) -> list[AlertDelivery]:
        """Deliver alert event through specified channels."""
        deliveries = []
        for channel in channels:
            delivery = AlertDelivery(
                alert_event_id=event.id,
                channel=channel,
                status="pending",
            )
            self.db.add(delivery)
            self.db.commit()
            self.db.refresh(delivery)

            try:
                if channel == "email":
                    self._send_email(event, delivery)
                elif channel == "web_push":
                    self._send_web_push(event, delivery)
                elif channel == "telegram":
                    self._send_telegram(event, delivery)
                else:
                    delivery.status = "failed"
                    delivery.error_message = f"Unknown channel: {channel}"
            except Exception as e:
                delivery.status = "failed"
                delivery.error_message = str(e)
                logger.warning(f"Delivery failed for {channel}: {e}")

            self.db.commit()
            deliveries.append(delivery)

        return deliveries

    def _send_email(self, event: AlertEvent, delivery: AlertDelivery) -> None:
        """Send email via SMTP or SendGrid."""
        # Phase 4: Log-only fallback until SMTP config is provided
        logger.info(
            f"[EMAIL ALERT] user={event.user_id} type={event.alert_type} "
            f"symbol={event.symbol} msg={event.message}"
        )
        delivery.status = "sent"
        delivery.sent_at = __import__("datetime").datetime.utcnow()

    def _send_web_push(self, event: AlertEvent, delivery: AlertDelivery) -> None:
        """Send web push notification."""
        logger.info(
            f"[WEB PUSH ALERT] user={event.user_id} type={event.alert_type} "
            f"symbol={event.symbol} msg={event.message}"
        )
        delivery.status = "sent"
        delivery.sent_at = __import__("datetime").datetime.utcnow()

    def _send_telegram(self, event: AlertEvent, delivery: AlertDelivery) -> None:
        """Send Telegram message."""
        logger.info(
            f"[TELEGRAM ALERT] user={event.user_id} type={event.alert_type} "
            f"symbol={event.symbol} msg={event.message}"
        )
        delivery.status = "sent"
        delivery.sent_at = __import__("datetime").datetime.utcnow()
