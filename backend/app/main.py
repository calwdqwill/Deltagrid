from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.persistence.database import init_db
from app.api.v1 import (
    alerts,
    auth,
    billing,
    data,
    exchange_accounts,
    execution,
    health,
    market,
    notifications,
    paper,
    performance,
    preferences,
    risk,
    rwa,
    scanner,
    stream,
    treasury,
)
from app.services.scanner_service import ScannerService
from app.services.preference_service import PreferenceService
from app.services.exchange_account_service import ExchangeAccountService
from app.services.rwa.rwa_asset_service import RwaAssetService
from app.services.rwa.treasury_service import TreasuryService
from app.persistence.database import SessionLocal
from app.core.middleware import RequestIDMiddleware, add_exception_handlers

settings = get_settings()
logger = logging.getLogger(__name__)


def _validate_production_settings() -> None:
    """Fail-fast startup validation for production-like environments."""
    if settings.debug:
        return
    invalid = []
    if settings.secret_key == "change-me-in-production":
        invalid.append("SECRET_KEY must be changed from default in production")
    if not settings.vault_master_key or not settings.vault_master_key.strip():
        invalid.append("VAULT_MASTER_KEY must be set in production")
    if invalid:
        raise RuntimeError("Production startup blocked: " + "; ".join(invalid))


@asynccontextmanager
async def lifespan(app: FastAPI):
    _validate_production_settings()
    init_db()
    # Seed connector capabilities
    db = SessionLocal()
    try:
        ExchangeAccountService.seed_capabilities(db)
        RwaAssetService.seed_assets(db)
        TreasuryService.seed_entities(db)
        TreasuryService.seed_platforms(db)
    except Exception:
        logger.warning("Startup seeding failed", exc_info=True)
    finally:
        db.close()
    # Warm up scanner cache on startup so first frontend request is fast
    pref_service = None
    try:
        pref_service = PreferenceService(user_id=None)
        scanner_service = ScannerService(scanner._cache, scanner._cg_service, scanner._perp_service, pref_service)
        await scanner_service.fetch_all()
    except Exception:
        logger.warning("Scanner cache warm-up failed", exc_info=True)
    finally:
        if pref_service:
            pref_service.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Middleware: Request ID tracing (must be before CORS to inject headers)
app.add_middleware(RequestIDMiddleware)

# CORS — tighten in production, keep permissive in debug
origins = [o.strip() for o in settings.cors_origins.split(",")]
allow_methods = [m.strip() for m in settings.cors_allow_methods.split(",")] if not settings.debug else ["*"]
allow_headers = [h.strip() for h in settings.cors_allow_headers.split(",")] if not settings.debug else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
    expose_headers=["X-Request-ID"],
)

# Global exception handlers
add_exception_handlers(app)

# Routers
app.include_router(scanner.router, prefix="/api/v1")
app.include_router(preferences.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(paper.router, prefix="/api/v1")
app.include_router(performance.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(market.router, prefix="/api/v1")
app.include_router(exchange_accounts.router, prefix="/api/v1")
app.include_router(execution.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(stream.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(rwa.router, prefix="/api/v1")
app.include_router(treasury.router, prefix="/api/v1")
app.include_router(data.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "api_tier": "internal",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
