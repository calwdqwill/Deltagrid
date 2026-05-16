from enum import Enum


class DataStatus(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    STALE = "stale"
    FALLBACK = "fallback"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class SignalLevel(str, Enum):
    STRONG = "STRONG"
    BUY_SELL = "BUY_SELL"
    MARGINAL = "MARGINAL"
    HOLD = "HOLD"


class ScannerType(str, Enum):
    CEX_CEX = "cex-cex"
    DEX_CEX = "dex-cex"
    SPOT_PERP = "spot-perp"


# Signal classification thresholds (net profit %)
SIGNAL_THRESHOLD_STRONG = 2.0
SIGNAL_THRESHOLD_BUY_SELL = 1.0
SIGNAL_THRESHOLD_MARGINAL = 0.5

# Default fees (%)
DEFAULT_FEE_BUY_PCT = 0.10
DEFAULT_FEE_SELL_PCT = 0.10
DEFAULT_SLIPPAGE_PCT = 0.0

# CoinGecko instrument mapping
# Format: coingecko_id -> { symbol, name, icon_url }
DEFAULT_INSTRUMENTS = {
    "bitcoin": {"symbol": "BTC", "name": "Bitcoin", "icon_url": "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"},
    "ethereum": {"symbol": "ETH", "name": "Ethereum", "icon_url": "https://assets.coingecko.com/coins/images/279/small/ethereum.png"},
    "solana": {"symbol": "SOL", "name": "Solana", "icon_url": "https://assets.coingecko.com/coins/images/4128/small/solana.png"},
    "ripple": {"symbol": "XRP", "name": "XRP", "icon_url": "https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png"},
    "dogecoin": {"symbol": "DOGE", "name": "Dogecoin", "icon_url": "https://assets.coingecko.com/coins/images/5/small/dogecoin.png"},
}

# Exchange/venue configuration
# Format: exchange_id -> { name, type, fee_pct }
DEFAULT_EXCHANGES = {
    "binance": {"name": "Binance", "type": "cex", "fee_pct": 0.10},
    "coinbase": {"name": "Coinbase", "type": "cex", "fee_pct": 0.10},
    "kraken": {"name": "Kraken", "type": "cex", "fee_pct": 0.10},
    "okx": {"name": "OKX", "type": "cex", "fee_pct": 0.10},
    "hyperliquid": {"name": "Hyperliquid", "type": "perp_dex", "fee_pct": 0.01},
    "aster": {"name": "Aster", "type": "perp_dex", "fee_pct": 0.02},
    "lighter": {"name": "Lighter", "type": "perp_dex", "fee_pct": 0.02},
}

# Mock fallback data for when API is unavailable
MOCK_SPOT_PRICES = {
    "bitcoin": {"binance": 67200.0, "coinbase": 67350.0, "kraken": 67300.0},
    "ethereum": {"binance": 3450.0, "coinbase": 3460.0, "kraken": 3465.0},
    "solana": {"binance": 200.0, "coinbase": 198.5, "okx": 198.0},
    "ripple": {"binance": 0.6200, "coinbase": 0.6250, "kraken": 0.6220},
    "dogecoin": {"binance": 0.1680, "coinbase": 0.1700, "kraken": 0.1690},
}

MOCK_PERP_PRICES = {
    "bitcoin": {"hyperliquid": 67450.0, "aster": 67400.0},
    "ethereum": {"hyperliquid": 3420.0, "aster": 3430.0},
    "solana": {"hyperliquid": 200.50, "aster": 201.0},
}

MOCK_VOLUMES = {
    "bitcoin": 18_200_000_000,
    "ethereum": 8_500_000_000,
    "solana": 2_100_000_000,
    "ripple": 890_000_000,
    "dogecoin": 450_000_000,
}
