"""Secure API key encryption using Fernet (AES-256 in CBC mode via PBKDF2HMAC).

Backend-only secret handling. No secret ever leaves the backend unencrypted.
"""

import json
import base64
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import get_settings

logger = logging.getLogger(__name__)


class SecretsVaultService:
    """Encrypt and decrypt exchange API credentials.

    Master key is derived from VAULT_MASTER_KEY env var via PBKDF2.
    If master key is empty/short, a development-only key is derived
    with a fixed salt (NOT for production).
    """

    _instance: Optional["SecretsVaultService"] = None
    _fernet: Optional[Fernet] = None

    def __new__(cls) -> "SecretsVaultService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_fernet()
        return cls._instance

    def _init_fernet(self) -> None:
        settings = get_settings()
        master_key = settings.vault_master_key.strip()

        if not master_key:
            logger.warning("VAULT_MASTER_KEY not set. Using development-only key derivation. DO NOT USE IN PRODUCTION.")
            master_key = "dev-only-change-me"
            salt = b"deltagrid-dev-salt"
        else:
            # Derive salt from first 16 bytes of key hash for deterministic but unique salt per key
            import hashlib
            salt = hashlib.sha256(master_key.encode()).digest()[:16]

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
        if not self._fernet:
            raise RuntimeError("Vault not initialized")
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a ciphertext string. Returns plaintext."""
        if not self._fernet:
            raise RuntimeError("Vault not initialized")
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt secret: invalid token or corrupted data")
            raise ValueError("Invalid or corrupted encrypted secret")

    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dict. Non-string values are JSON-serialized first."""
        encrypted = {}
        for key, value in data.items():
            if value is None:
                encrypted[key] = None
            elif isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = self.encrypt(json.dumps(value))
        return encrypted

    def decrypt_dict(self, data: dict) -> dict:
        """Decrypt all string values in a dict."""
        decrypted = {}
        for key, value in data.items():
            if value is None:
                decrypted[key] = None
            else:
                try:
                    decrypted[key] = self.decrypt(value)
                except ValueError:
                    decrypted[key] = value  # fallback: maybe not encrypted
        return decrypted
