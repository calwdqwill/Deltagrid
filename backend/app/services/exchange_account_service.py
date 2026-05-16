"""Exchange account and key management service.

Handles CRUD for exchange account metadata and encrypted API key storage.
Secrets are never returned to the caller.
"""

import json
import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import ExchangeAccount, ExchangeKey, ConnectorCapability
from app.schemas.exchange import ExchangeAccountCreate, ExchangeAccountResponse, ExchangeKeyStoreRequest
from app.services.secrets.vault_service import SecretsVaultService
from app.core.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


class ExchangeAccountService:
    def __init__(self, db: Session):
        self.db = db
        self.vault = SecretsVaultService()

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------
    def list_accounts(self, user_id: str) -> list[ExchangeAccountResponse]:
        accounts = (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.user_id == user_id)
            .order_by(ExchangeAccount.created_at.desc())
            .all()
        )
        return [self._to_account_response(a) for a in accounts]

    def get_account(self, account_id: str, user_id: str) -> ExchangeAccountResponse:
        account = self._get_account_or_404(account_id, user_id)
        return self._to_account_response(account)

    def create_account(self, user_id: str, data: ExchangeAccountCreate) -> ExchangeAccountResponse:
        account = ExchangeAccount(
            user_id=user_id,
            exchange_name=data.exchange_name.lower(),
            account_label=data.account_label,
            account_type=data.account_type,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_response(account)

    def delete_account(self, account_id: str, user_id: str) -> None:
        account = self._get_account_or_404(account_id, user_id)
        self.db.delete(account)
        self.db.commit()

    def update_account(
        self,
        account_id: str,
        user_id: str,
        data: dict,
    ) -> ExchangeAccountResponse:
        account = self._get_account_or_404(account_id, user_id)
        for key, value in data.items():
            if hasattr(account, key) and key not in ("id", "user_id", "created_at"):
                setattr(account, key, value)
        self.db.commit()
        self.db.refresh(account)
        return self._to_account_response(account)

    # ------------------------------------------------------------------
    # Keys (one-way storage)
    # ------------------------------------------------------------------
    def store_keys(
        self,
        account_id: str,
        user_id: str,
        data: ExchangeKeyStoreRequest,
    ) -> None:
        account = self._get_account_or_404(account_id, user_id)

        # Encrypt secrets
        encrypted_api_key = self.vault.encrypt(data.api_key)
        encrypted_api_secret = self.vault.encrypt(data.api_secret)
        encrypted_passphrase = self.vault.encrypt(data.passphrase) if data.passphrase else None

        # Delete existing keys for this account (single key per account for now)
        existing = (
            self.db.query(ExchangeKey)
            .filter(ExchangeKey.account_id == account_id)
            .first()
        )
        if existing:
            self.db.delete(existing)

        key_record = ExchangeKey(
            account_id=account_id,
            api_key_encrypted=encrypted_api_key,
            api_secret_encrypted=encrypted_api_secret,
            passphrase_encrypted=encrypted_passphrase,
            is_testnet=data.is_testnet,
        )
        self.db.add(key_record)
        self.db.commit()

    def delete_keys(self, account_id: str, user_id: str) -> None:
        account = self._get_account_or_404(account_id, user_id)
        self.db.query(ExchangeKey).filter(ExchangeKey.account_id == account.id).delete()
        self.db.commit()

    def get_decrypted_keys(self, account_id: str, user_id: str) -> dict:
        """Return decrypted keys for internal connector use ONLY.

        Never expose this method via API.
        """
        account = self._get_account_or_404(account_id, user_id)
        key_record = (
            self.db.query(ExchangeKey)
            .filter(ExchangeKey.account_id == account.id)
            .first()
        )
        if not key_record:
            raise NotFoundError("API keys not found for this account")

        return {
            "api_key": self.vault.decrypt(key_record.api_key_encrypted),
            "api_secret": self.vault.decrypt(key_record.api_secret_encrypted),
            "passphrase": self.vault.decrypt(key_record.passphrase_encrypted) if key_record.passphrase_encrypted else None,
            "is_testnet": key_record.is_testnet,
        }

    # ------------------------------------------------------------------
    # Connector capabilities
    # ------------------------------------------------------------------
    @staticmethod
    def list_capabilities(db: Session) -> list[ConnectorCapability]:
        return db.query(ConnectorCapability).order_by(ConnectorCapability.exchange_name).all()

    @staticmethod
    def get_capability(db: Session, exchange_name: str) -> Optional[ConnectorCapability]:
        return db.query(ConnectorCapability).filter(
            ConnectorCapability.exchange_name == exchange_name.lower()
        ).first()

    @staticmethod
    def seed_capabilities(db: Session) -> None:
        """Seed static connector capability data. Idempotent."""
        defaults = [
            {
                "exchange_name": "binance",
                "supports_spot": True,
                "supports_perp": True,
                "supports_margin": True,
                "supports_market_order": True,
                "supports_limit_order": True,
                "supports_stop_loss": True,
                "supports_cancel": True,
                "supports_ws": True,
                "rate_limit_requests_per_minute": 1200,
            },
            {
                "exchange_name": "bybit",
                "supports_spot": True,
                "supports_perp": True,
                "supports_margin": False,
                "supports_market_order": True,
                "supports_limit_order": True,
                "supports_stop_loss": True,
                "supports_cancel": True,
                "supports_ws": True,
                "rate_limit_requests_per_minute": 1200,
            },
            {
                "exchange_name": "okx",
                "supports_spot": True,
                "supports_perp": True,
                "supports_margin": True,
                "supports_market_order": True,
                "supports_limit_order": True,
                "supports_stop_loss": True,
                "supports_cancel": True,
                "supports_ws": True,
                "rate_limit_requests_per_minute": 1200,
            },
            {
                "exchange_name": "hyperliquid",
                "supports_spot": False,
                "supports_perp": True,
                "supports_margin": False,
                "supports_market_order": True,
                "supports_limit_order": True,
                "supports_stop_loss": True,
                "supports_cancel": True,
                "supports_ws": True,
                "rate_limit_requests_per_minute": 6000,
            },
            {
                "exchange_name": "aster",
                "supports_spot": False,
                "supports_perp": True,
                "supports_margin": False,
                "supports_market_order": True,
                "supports_limit_order": True,
                "supports_stop_loss": False,
                "supports_cancel": True,
                "supports_ws": False,
                "rate_limit_requests_per_minute": 600,
            },
        ]
        for cap in defaults:
            existing = db.query(ConnectorCapability).filter(
                ConnectorCapability.exchange_name == cap["exchange_name"]
            ).first()
            if not existing:
                db.add(ConnectorCapability(**cap))
        db.commit()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _get_account_or_404(self, account_id: str, user_id: str) -> ExchangeAccount:
        account = (
            self.db.query(ExchangeAccount)
            .filter(ExchangeAccount.id == account_id, ExchangeAccount.user_id == user_id)
            .first()
        )
        if not account:
            raise NotFoundError("Exchange account not found")
        return account

    def _to_account_response(self, account: ExchangeAccount) -> ExchangeAccountResponse:
        has_keys = (
            self.db.query(ExchangeKey.id)
            .filter(ExchangeKey.account_id == account.id)
            .first()
            is not None
        )
        return ExchangeAccountResponse(
            id=account.id,
            exchange_name=account.exchange_name,
            account_label=account.account_label,
            account_type=account.account_type,
            is_active=account.is_active,
            is_default=account.is_default,
            has_keys=has_keys,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )
