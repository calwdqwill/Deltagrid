"""Fee model for backtesting — hardcoded per-exchange fee schedules.

NOTE: DB stores fees as percentage points (e.g. 0.02 = 2%).
This module uses decimal form (e.g. 0.0002 = 0.02%) for direct math.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FeeConfig:
    maker: float  # maker fee as decimal (e.g., 0.0002 = 0.02%)
    taker: float  # taker fee as decimal
    funding_interval_hours: int  # 8 for CEX, 1 for Hyperliquid


EXCHANGE_FEES: Dict[str, FeeConfig] = {
    "binance": FeeConfig(maker=0.0002, taker=0.0005, funding_interval_hours=8),
    "bybit": FeeConfig(maker=0.0002, taker=0.00055, funding_interval_hours=8),
    "okx": FeeConfig(maker=0.0002, taker=0.0005, funding_interval_hours=8),
    "hyperliquid": FeeConfig(maker=0.0001, taker=0.00035, funding_interval_hours=1),
}


def get_fee_config(exchange: str) -> FeeConfig:
    """Returns fee config for given exchange."""
    exchange = exchange.lower()
    if exchange not in EXCHANGE_FEES:
        raise ValueError(f"Unknown exchange: {exchange}. Supported: {list(EXCHANGE_FEES.keys())}")
    return EXCHANGE_FEES[exchange]


def calculate_trade_fee(trade_value_usd: float, is_maker: bool, exchange: str) -> float:
    """Returns fee in USD for a single trade."""
    config = get_fee_config(exchange)
    rate = config.maker if is_maker else config.taker
    return trade_value_usd * rate
