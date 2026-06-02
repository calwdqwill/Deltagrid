"""Two-component slippage model for backtesting."""

from typing import Dict


# Token-specific slippage (in basis points, as decimal)
TOKEN_SLIPPAGE: Dict[str, Dict[str, float]] = {
    # normal: typical slippage for normal market conditions
    # stress: slippage during high volatility / low liquidity
    "BTC": {"normal": 0.0001, "stress": 0.0010},   # 1 bps / 10 bps
    "ETH": {"normal": 0.0002, "stress": 0.0015},   # 2 bps / 15 bps
    "SOL": {"normal": 0.0005, "stress": 0.0030},   # 5 bps / 30 bps
    "HYPE": {"normal": 0.0010, "stress": 0.0050},  # 10 bps / 50 bps
}


def calculate_slippage(
    trade_value_usd: float,
    volume_1m: float,  # 1-minute volume in USD
    token: str,
    exchange: str,
    mode: str = "normal",  # "normal" | "stress" | "conservative"
) -> float:
    """Two-component slippage model.

    1. Fixed component: token-specific base slippage
    2. Volume component: increases when trade_size / volume_ratio is high

    volume_ratio = trade_value_usd / volume_1m (if volume_1m > 0)
    if volume_ratio > 0.01 (trade > 1% of 1m volume): apply stress slippage
    if volume_ratio > 0.05 (trade > 5% of 1m volume): apply 2x stress slippage

    Conservative mode: uses 2x normal + stress slippage

    Returns:
        slippage in USD
    """
    token = token.upper()
    if token not in TOKEN_SLIPPAGE:
        token = "BTC"  # fallback

    slippage_cfg = TOKEN_SLIPPAGE[token]

    # Determine base slippage rate
    if mode == "conservative":
        base_rate = slippage_cfg["normal"] * 2 + slippage_cfg["stress"]
    elif mode == "stress":
        base_rate = slippage_cfg["stress"]
    else:
        base_rate = slippage_cfg["normal"]

    # Volume-based multiplier
    volume_multiplier = 1.0
    if volume_1m and volume_1m > 0:
        volume_ratio = trade_value_usd / volume_1m
        if volume_ratio > 0.05:
            volume_multiplier = 2.0
        elif volume_ratio > 0.01:
            volume_multiplier = 1.0  # already using stress rate, but keep explicit
            if mode == "normal":
                base_rate = slippage_cfg["stress"]

    slippage_rate = base_rate * volume_multiplier
    return trade_value_usd * slippage_rate
