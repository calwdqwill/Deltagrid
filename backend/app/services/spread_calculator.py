from dataclasses import dataclass
from typing import Optional


@dataclass
class SpreadResult:
    gross_spread_pct: float
    net_profit_pct: float
    fee_buy_pct: float
    fee_sell_pct: float
    slippage_pct: float
    buy_price: float
    sell_price: float


class SpreadCalculator:
    """Pure domain logic for spread and net profit calculation.

    No external dependencies. Fully testable.
    """

    @staticmethod
    def calculate(
        buy_price: float,
        sell_price: float,
        fee_buy_pct: float = 0.10,
        fee_sell_pct: float = 0.10,
        slippage_pct: float = 0.0,
    ) -> SpreadResult:
        if buy_price <= 0:
            return SpreadResult(
                gross_spread_pct=0.0,
                net_profit_pct=0.0,
                fee_buy_pct=fee_buy_pct,
                fee_sell_pct=fee_sell_pct,
                slippage_pct=slippage_pct,
                buy_price=buy_price,
                sell_price=sell_price,
            )

        gross_spread_pct = ((sell_price - buy_price) / buy_price) * 100
        total_costs = fee_buy_pct + fee_sell_pct + slippage_pct
        net_profit_pct = gross_spread_pct - total_costs

        return SpreadResult(
            gross_spread_pct=gross_spread_pct,
            net_profit_pct=net_profit_pct,
            fee_buy_pct=fee_buy_pct,
            fee_sell_pct=fee_sell_pct,
            slippage_pct=slippage_pct,
            buy_price=buy_price,
            sell_price=sell_price,
        )
