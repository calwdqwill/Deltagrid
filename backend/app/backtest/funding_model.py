"""Funding rate model — exact settlement times, NO interpolation.

Critical rules:
- Binance/Bybit/OKX: settlement at 00:00, 08:00, 16:00 UTC (every 8 hours)
- Hyperliquid: settlement every hour
- Uses exact rate at most recent funding timestamp (no interpolation)
"""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd


def is_funding_settlement_time(timestamp_ms: int, exchange: str) -> bool:
    """Returns True if timestamp matches funding settlement schedule."""
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
    exchange = exchange.lower()

    if exchange == "hyperliquid":
        # Hyperliquid settles every hour
        return True

    # CEX (binance, bybit, okx): settle at 00:00, 08:00, 16:00 UTC
    if dt.hour in (0, 8, 16) and dt.minute == 0:
        return True

    return False


def get_funding_payment(
    timestamp_ms: int,
    position_side: str,  # "long" | "short" | "flat"
    size_usd: float,
    funding_rate: float,  # current funding rate (e.g., 0.000312 = 0.0312%)
    exchange: str,
) -> float:
    """Calculates funding payment for given timestamp.

    Returns:
        Payment amount in USD.
        positive = trader pays
        negative = trader receives
    """
    if position_side == "flat" or size_usd <= 0:
        return 0.0

    if not is_funding_settlement_time(timestamp_ms, exchange):
        return 0.0

    # Long pays when rate > 0, receives when rate < 0
    # Short receives when rate > 0, pays when rate < 0
    if position_side == "long":
        payment = funding_rate * size_usd
    elif position_side == "short":
        payment = -funding_rate * size_usd
    else:
        return 0.0

    return payment


def get_funding_rate_at_time(timestamp_ms: int, df_funding: pd.DataFrame) -> float:
    """Gets applicable funding rate for given timestamp.

    Uses most recent funding rate before or at timestamp.
    NO interpolation — uses exact rate.

    Args:
        timestamp_ms: target timestamp in milliseconds
        df_funding: DataFrame with index=timestamp_ms, column 'funding_rate'

    Returns:
        funding_rate float, or 0.0 if no data available
    """
    if df_funding is None or df_funding.empty:
        return 0.0

    # Get all funding rows at or before timestamp
    mask = df_funding.index <= timestamp_ms
    if not mask.any():
        return 0.0

    return float(df_funding.loc[mask, "funding_rate"].iloc[-1])
