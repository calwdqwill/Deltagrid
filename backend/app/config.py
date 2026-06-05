from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "DeltaGrid"
    app_version: str = "1.0.0"
    debug: bool = False

    # CoinGecko
    coingecko_api_key: str | None = None
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_demo_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_pro_base_url: str = "https://pro-api.coingecko.com/api/v3"

    # Cache
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # Scanner defaults
    default_min_spread_pct: float = 0.1
    default_refresh_interval_sec: int = 60
    default_fee_buy_pct: float = 0.1
    default_fee_sell_pct: float = 0.1
    default_slippage_pct: float = 0.0

    # Database
    database_url: str = "postgresql://deltagrid:deltagrid@127.0.0.1:5432/deltagrid"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_timeout_seconds: int = 10

    # Cache
    cache_backend: str = "in_memory"  # or "redis"
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    cors_allow_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    cors_allow_headers: str = "Content-Type,Authorization,X-Request-ID,X-API-Version"

    # Secrets Vault (Fernet encryption for API keys)
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    vault_master_key: str = ""

    # Phase 4: Provider API keys
    coinglass_api_key: str | None = None
    coinglass_standard_api_key: str | None = None
    coinglass_base_url: str = "https://open-api-v4.coinglass.com"
    geckoterminal_base_url: str = "https://api.geckoterminal.com/api/v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
