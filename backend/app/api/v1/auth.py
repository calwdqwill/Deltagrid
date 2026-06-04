from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.schemas.auth import UserCreate, UserLogin, AuthResponse, UserResponse, RefreshRequest, TelegramAuthRequest, Web3ChallengeRequest, Web3VerifyRequest
from app.services.auth_service import AuthService
from app.core.dependencies import get_db, get_current_user_id, require_auth
from app.core.exceptions import AuthenticationError, ConflictError
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _require_debug_for_stubs():
    """Raise 501 if Telegram/Web3 auth stubs are hit in production."""
    if not get_settings().debug:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Telegram/Web3 authentication is not enabled in production",
        )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=ApiResponse)
async def register(
    data: UserCreate,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = service.register(data)
        return ApiResponse(data=result)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=ApiResponse)
async def login(
    data: UserLogin,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = service.login(data)
        return ApiResponse(data=result)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=ApiResponse)
async def refresh_token(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        result = service.refresh(data.refresh_token)
        return ApiResponse(data=result)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/telegram", response_model=ApiResponse)
async def telegram_auth(
    data: TelegramAuthRequest,
    service: AuthService = Depends(get_auth_service),
    _=Depends(_require_debug_for_stubs),
):
    try:
        result = service.telegram_auth(data.model_dump())
        return ApiResponse(data=result)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/web3/challenge", response_model=ApiResponse)
async def web3_challenge(
    data: Web3ChallengeRequest,
    service: AuthService = Depends(get_auth_service),
    _=Depends(_require_debug_for_stubs),
):
    nonce = service.get_web3_nonce(data.wallet_address)
    return ApiResponse(data={"nonce": nonce, "message": f"DeltaGrid login: {nonce}"})


@router.post("/web3/verify", response_model=ApiResponse)
async def web3_verify(
    data: Web3VerifyRequest,
    service: AuthService = Depends(get_auth_service),
    _=Depends(_require_debug_for_stubs),
):
    try:
        result = service.verify_web3_signature(data.wallet_address, data.signature, data.nonce)
        return ApiResponse(data=result)
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/me", response_model=ApiResponse)
async def me(
    user_id: str = Depends(require_auth),
    service: AuthService = Depends(get_auth_service),
):
    """@internal — Current user profile. Frontend-only."""
    from app.services.capability_service import CapabilityService

    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    flags = CapabilityService(service.db).get_user_feature_flags(user_id)
    return ApiResponse(data=UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        plan=user.plan,
        feature_flags=flags if flags else None,
    ))
