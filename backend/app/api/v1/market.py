from datetime import datetime

from fastapi import APIRouter

from app.schemas.common import ApiResponse
from app.services.market_service import MarketService
from app.services.providers.coinglass_client import CoinGlassClient
from app.services.providers.geckoterminal_client import GeckoTerminalClient

router = APIRouter(prefix="/market", tags=["market"])

_market_service = MarketService()


@router.get("/trending", response_model=ApiResponse)
async def get_trending():
    data = await _market_service.get_trending()
    return ApiResponse(data=data)


@router.get("/gainers", response_model=ApiResponse)
async def get_gainers():
    data = await _market_service.get_gainers()
    return ApiResponse(data=data)


@router.get("/losers", response_model=ApiResponse)
async def get_losers():
    data = await _market_service.get_losers()
    return ApiResponse(data=data)


@router.get("/global", response_model=ApiResponse)
async def get_global():
    data = await _market_service.get_global()
    return ApiResponse(data=data)


@router.get("/fear-greed", response_model=ApiResponse)
async def get_fear_greed():
    data = await _market_service.get_fear_greed()
    return ApiResponse(data=data)


@router.get("/new-listings", response_model=ApiResponse)
async def get_new_listings():
    data = await _market_service.get_new_listings()
    return ApiResponse(data=data)


@router.get("/funding-rates", response_model=ApiResponse)
async def get_funding_rates():
    data = await _market_service.get_funding_rates()
    return ApiResponse(data=data)


@router.get("/enrichments", response_model=ApiResponse)
async def get_enrichments():
    """List available market enrichments (funding, OI, DEX data)."""
    cg_client = CoinGlassClient()
    gt_client = GeckoTerminalClient()
    try:
        cg_healthy = await cg_client.health_check()
        gt_healthy = await gt_client.health_check()
        return ApiResponse(data={
            "coinglass": {"available": cg_healthy, "features": ["funding_rates", "open_interest"]},
            "geckoterminal": {"available": gt_healthy, "features": ["dex_pools", "dex_volume"]},
            "timestamp": datetime.utcnow().isoformat(),
        })
    finally:
        await cg_client.close()
        await gt_client.close()
