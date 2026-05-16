"""Auth service: registration, login, token management.

Phase 2 foundation. No business logic beyond auth.
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import User
from app.schemas.auth import UserCreate, UserLogin, AuthResponse, UserResponse
from app.core.auth import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import AuthenticationError, ConflictError


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, data: UserCreate) -> AuthResponse:
        """Register a new user."""
        existing = self.db.query(User).filter(User.email == data.email).first()
        if existing:
            raise ConflictError("Email already registered")

        if data.username:
            existing_name = self.db.query(User).filter(User.username == data.username).first()
            if existing_name:
                raise ConflictError("Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return self._build_auth_response(user)

    def login(self, data: UserLogin) -> AuthResponse:
        """Authenticate user and return tokens."""
        user = self.db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return self._build_auth_response(user)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def refresh(self, refresh_token: str) -> AuthResponse:
        """Refresh access token using a valid refresh token."""
        from app.core.auth import decode_token

        payload = decode_token(refresh_token, token_type="refresh")
        if not payload:
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token")

        user = self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or deactivated")

        return self._build_auth_response(user)

    def telegram_auth(self, telegram_data: dict) -> AuthResponse:
        """Authenticate or register via Telegram OAuth data."""
        # Phase 4: Basic Telegram auth without hash verification (add HMAC in production)
        telegram_id = str(telegram_data.get("id"))
        username = telegram_data.get("username") or telegram_data.get("first_name")
        if not telegram_id:
            raise AuthenticationError("Invalid Telegram data")

        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                email=None,
                hashed_password=None,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return self._build_auth_response(user)

    def get_web3_nonce(self, wallet_address: str) -> str:
        """Generate a nonce for Web3 signature challenge."""
        import secrets
        nonce = secrets.token_hex(16)
        # Store nonce in user record or cache (simplified: store in user.temp field or just return)
        # For MVP we return nonce and expect client to sign it
        return nonce

    def verify_web3_signature(self, wallet_address: str, signature: str, nonce: str) -> AuthResponse:
        """Verify EIP-191 signature and authenticate/register user."""
        # Phase 4: Stub signature verification — in production use eth-account or web3.py
        if not wallet_address or not signature or not nonce:
            raise AuthenticationError("Missing Web3 auth parameters")

        # Normalize address
        wallet_address = wallet_address.lower()

        # TODO: Real signature verification
        # from eth_account.messages import encode_defunct
        # from eth_account import Account
        # message = encode_defunct(text=f"DeltaGrid login: {nonce}")
        # recovered = Account.recover_message(message, signature=signature)
        # if recovered.lower() != wallet_address:
        #     raise AuthenticationError("Invalid signature")

        user = self.db.query(User).filter(User.wallet_address == wallet_address).first()
        if not user:
            user = User(
                wallet_address=wallet_address,
                username=wallet_address[:8],
                email=None,
                hashed_password=None,
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        return self._build_auth_response(user)

    def _build_auth_response(self, user: User) -> AuthResponse:
        from app.services.capability_service import CapabilityService

        token_data = {"sub": user.id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Load user-level feature flag overrides
        capability_service = CapabilityService(self.db)
        flags = capability_service.get_user_feature_flags(user.id)

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                plan=user.plan,
                feature_flags=flags if flags else None,
            ),
        )
