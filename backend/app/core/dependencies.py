"""FastAPI dependencies for injection.

Provides: get_db, get_current_user, get_cache, get_settings.
"""

from typing import Optional, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import Settings, get_settings
from app.persistence.database import SessionLocal
from app.services.cache_service import CacheService, InMemoryCacheService
from app.core.auth import decode_token

security = HTTPBearer(auto_error=False)


def get_db():
    """Yield a synchronous SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_cache(settings: Settings = Depends(get_settings)) -> CacheService:
    """Return the configured cache backend."""
    if settings.cache_backend == "redis":
        from app.services.cache_service import RedisCacheService
        return RedisCacheService(redis_url=settings.redis_url)
    return InMemoryCacheService(
        max_size=settings.cache_max_size,
        default_ttl=settings.cache_ttl_seconds,
    )


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """Extract user_id from JWT if present. Returns None for anonymous users.

    This is intentionally non-blocking: public routes stay public.
    """
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    user_id: Optional[str] = payload.get("sub")
    return user_id


def require_auth(user_id: Optional[str] = Depends(get_current_user_id)) -> str:
    """Require a valid authenticated user. Raise 401 otherwise."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
